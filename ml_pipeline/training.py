import os
import json
import time
import joblib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

from ml_pipeline.dataset_manager import (
    DatasetManager,
    EXPECTED_NUMERIC_COLUMNS,
    EXPECTED_CATEGORICAL_COLUMNS,
    TARGET_COLUMN
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, "placement_model_latest.joblib")
RESULTS_METADATA_PATH = os.path.join(MODELS_DIR, "model_comparison_results.json")
TRAINING_STATUS_PATH = os.path.join(MODELS_DIR, "training_status.json")


class ModelTrainingService:
    """
    Manages end-to-end model training, cross-validation, hyperparameter tuning,
    model comparison, evaluation metrics computation, and artifact persistence.
    """

    def __init__(self, dataset_manager: Optional[DatasetManager] = None):
        self.dm = dataset_manager or DatasetManager()
        os.makedirs(MODELS_DIR, exist_ok=True)

    def _set_status(self, state: str, progress: int, message: str, error: Optional[str] = None):
        status_data = {
            "state": state,          # "idle", "running", "completed", "failed"
            "progress": progress,    # 0 to 100
            "message": message,
            "error": error,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        with open(TRAINING_STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2)

    def get_status(self) -> Dict[str, Any]:
        if os.path.exists(TRAINING_STATUS_PATH):
            with open(TRAINING_STATUS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"state": "idle", "progress": 0, "message": "No training in progress", "error": None}

    def train_and_evaluate_all(self, test_size: float = 0.20, random_state: int = 42) -> Dict[str, Any]:
        """
        Executes complete training and comparison across 5 classifiers:
        1. DummyClassifier (Baseline)
        2. Logistic Regression
        3. Decision Tree
        4. Random Forest
        5. Gradient Boosting

        Uses 5-fold cross validation and GridSearchCV tuning on the training split.
        Evaluates strictly on held-out test split.
        """
        self._set_status("running", 5, "Loading active dataset and validating features...")
        try:
            df = self.dm.get_active_dataframe()
            metadata = self.dm.get_metadata()

            if df.empty or TARGET_COLUMN not in df.columns:
                raise ValueError("Active dataset is invalid or missing target column 'PlacementStatus'.")

            # Map target to binary integer: Placed -> 1, NotPlaced -> 0
            df = df.copy()
            target_series = df[TARGET_COLUMN].astype(str).str.strip()
            # Standardize common variants
            y = target_series.apply(
                lambda val: 1 if val.lower() in ["placed", "1", "1.0", "yes", "true"] else 0
            ).values

            numeric_features = [c for c in EXPECTED_NUMERIC_COLUMNS if c in df.columns]
            categorical_features = [c for c in EXPECTED_CATEGORICAL_COLUMNS if c in df.columns]
            all_features = numeric_features + categorical_features

            X = df[all_features]

            self._set_status("running", 15, "Splitting dataset into stratified train and test partitions...")
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=test_size,
                stratify=y,
                random_state=random_state
            )

            # Define Preprocessor
            numeric_transformer = Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ])

            categorical_transformer = Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", drop="first", sparse_output=False))
            ])

            preprocessor = ColumnTransformer(
                transformers=[
                    ("num", numeric_transformer, numeric_features),
                    ("cat", categorical_transformer, categorical_features)
                ]
            )

            # Candidate Models and Hyperparameter Grids
            model_configs = {
                "Dummy Baseline": {
                    "classifier": DummyClassifier(strategy="most_frequent"),
                    "param_grid": {}
                },
                "Logistic Regression": {
                    "classifier": LogisticRegression(max_iter=1000, random_state=random_state),
                    "param_grid": {
                        "classifier__C": [0.1, 1.0, 10.0],
                        "classifier__solver": ["lbfgs"]
                    }
                },
                "Decision Tree": {
                    "classifier": DecisionTreeClassifier(random_state=random_state),
                    "param_grid": {
                        "classifier__max_depth": [4, 6, 8, None],
                        "classifier__min_samples_split": [2, 5, 10]
                    }
                },
                "Random Forest": {
                    "classifier": RandomForestClassifier(random_state=random_state),
                    "param_grid": {
                        "classifier__n_estimators": [50, 100],
                        "classifier__max_depth": [6, 10, None]
                    }
                },
                "Gradient Boosting": {
                    "classifier": GradientBoostingClassifier(random_state=random_state),
                    "param_grid": {
                        "classifier__n_estimators": [50, 100],
                        "classifier__learning_rate": [0.05, 0.1],
                        "classifier__max_depth": [3, 5]
                    }
                }
            }

            results_list = []
            best_model_name = None
            best_f1_score = -1.0
            best_fitted_pipeline = None
            best_hyperparameters = {}

            total_models = len(model_configs)
            current_idx = 0

            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)

            for model_name, cfg in model_configs.items():
                current_idx += 1
                progress_pct = int(20 + (current_idx / total_models) * 65)
                self._set_status(
                    "running",
                    progress_pct,
                    f"Training and tuning model {current_idx}/{total_models}: {model_name}..."
                )

                pipe = Pipeline(steps=[
                    ("preprocessor", preprocessor),
                    ("classifier", cfg["classifier"])
                ])

                param_grid = cfg["param_grid"]
                start_time = time.time()

                if param_grid:
                    # Hyperparameter tuning on training partition ONLY
                    grid = GridSearchCV(
                        pipe,
                        param_grid,
                        cv=cv,
                        scoring="f1",
                        n_jobs=-1
                    )
                    grid.fit(X_train, y_train)
                    fitted_pipe = grid.best_estimator_
                    best_params = grid.best_params_
                    cv_f1_scores = grid.best_score_
                else:
                    fitted_pipe = pipe.fit(X_train, y_train)
                    best_params = {}
                    # Calculate baseline CV score
                    cv_scores = cross_val_score(fitted_pipe, X_train, y_train, cv=cv, scoring="f1")
                    cv_f1_scores = float(cv_scores.mean())

                train_time = round(time.time() - start_time, 3)

                # Cross-validation accuracy scores across folds
                cv_acc = cross_val_score(fitted_pipe, X_train, y_train, cv=cv, scoring="accuracy")
                cv_acc_mean = round(float(cv_acc.mean()), 4)
                cv_acc_std = round(float(cv_acc.std()), 4)

                # Evaluate on held-out test set
                y_pred = fitted_pipe.predict(X_test)
                if hasattr(fitted_pipe, "predict_proba"):
                    y_prob = fitted_pipe.predict_proba(X_test)[:, 1]
                    try:
                        roc_auc = round(float(roc_auc_score(y_test, y_prob)), 4)
                    except Exception:
                        roc_auc = None
                else:
                    roc_auc = None

                acc = round(float(accuracy_score(y_test, y_pred)), 4)
                prec = round(float(precision_score(y_test, y_pred, zero_division=0)), 4)
                rec = round(float(recall_score(y_test, y_pred, zero_division=0)), 4)
                f1 = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)
                cm = confusion_matrix(y_test, y_pred).tolist()  # [[TN, FP], [FN, TP]]

                model_result = {
                    "model_name": model_name,
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1_score": f1,
                    "roc_auc": roc_auc,
                    "cv_accuracy_mean": cv_acc_mean,
                    "cv_accuracy_std": cv_acc_std,
                    "cv_f1_mean": round(float(cv_f1_scores), 4),
                    "confusion_matrix": cm,
                    "hyperparameters": {k.replace("classifier__", ""): v for k, v in best_params.items()},
                    "training_time_seconds": train_time
                }
                results_list.append(model_result)

                # Update best model selection based on held-out test F1 score
                if model_name != "Dummy Baseline" and (f1 > best_f1_score or (f1 == best_f1_score and acc > (results_list[0].get("accuracy") or 0))):
                    best_f1_score = f1
                    best_model_name = model_name
                    best_fitted_pipeline = fitted_pipe
                    best_hyperparameters = model_result["hyperparameters"]

            # Fallback if no non-baseline model qualified
            if best_fitted_pipeline is None:
                best_model_name = "Logistic Regression"
                best_fitted_pipeline = results_list[1]

            self._set_status("running", 90, f"Persisting top model '{best_model_name}' and metadata...")

            # Extract transformed feature names for feature importance/explainability
            preprocessor_fitted = best_fitted_pipeline.named_steps["preprocessor"]
            try:
                all_transformed_feature_names = list(preprocessor_fitted.get_feature_names_out())
            except Exception:
                try:
                    cat_encoder = preprocessor_fitted.named_transformers_["cat"].named_steps["encoder"]
                    cat_feature_names = list(cat_encoder.get_feature_names_out(categorical_features))
                    all_transformed_feature_names = numeric_features + cat_feature_names
                except Exception:
                    all_transformed_feature_names = all_features

            # Feature importances / coefficients for best model
            classifier_step = best_fitted_pipeline.named_steps["classifier"]
            feature_importance_dict = {}

            if hasattr(classifier_step, "feature_importances_"):
                importances = classifier_step.feature_importances_
                for name, imp in zip(all_transformed_feature_names, importances):
                    feature_importance_dict[name] = round(float(imp), 4)
            elif hasattr(classifier_step, "coef_"):
                coefs = classifier_step.coef_[0]
                for name, coef in zip(all_transformed_feature_names, coefs):
                    feature_importance_dict[name] = round(float(coef), 4)

            # Sort feature importances descending
            sorted_importances = dict(
                sorted(feature_importance_dict.items(), key=lambda item: abs(item[1]), reverse=True)
            )

            # Save best pipeline artifact
            save_payload = {
                "pipeline": best_fitted_pipeline,
                "model_name": best_model_name,
                "numeric_features": numeric_features,
                "categorical_features": categorical_features,
                "all_transformed_features": all_transformed_feature_names,
                "classes": [0, 1],
                "target_labels": {0: "NotPlaced", 1: "Placed"},
                "best_hyperparameters": best_hyperparameters,
                "training_timestamp": datetime.now(timezone.utc).isoformat(),
                "dataset_name": metadata.get("name", "Active Placement Dataset"),
                "dataset_sha256": metadata.get("sha256", "Unknown")
            }
            joblib.dump(save_payload, MODEL_SAVE_PATH)

            # Comparison and metadata output
            output_report = {
                "selected_model": best_model_name,
                "selection_reason": f"Selected '{best_model_name}' based on the highest held-out test F1-score ({best_f1_score}) and 5-fold cross-validation performance.",
                "training_timestamp": datetime.now(timezone.utc).isoformat(),
                "dataset_info": {
                    "name": metadata.get("name", "Active Placement Dataset"),
                    "total_samples": len(df),
                    "train_samples": len(X_train),
                    "test_samples": len(X_test),
                    "features_used": all_features,
                    "target_column": TARGET_COLUMN
                },
                "comparison": results_list,
                "feature_importance": sorted_importances
            }

            with open(RESULTS_METADATA_PATH, "w", encoding="utf-8") as f:
                json.dump(output_report, f, indent=2)

            self._set_status("completed", 100, f"Training complete. Top model '{best_model_name}' saved.")
            return output_report

        except Exception as e:
            self._set_status("failed", 100, "Model training failed", error=str(e))
            raise e

    def get_comparison_results(self) -> Dict[str, Any]:
        """Returns previously trained model comparison report."""
        if os.path.exists(RESULTS_METADATA_PATH):
            with open(RESULTS_METADATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        # If not trained yet, run training once
        return self.train_and_evaluate_all()
