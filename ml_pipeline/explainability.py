import os
import json
import joblib
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

from ml_pipeline.training import MODEL_SAVE_PATH, RESULTS_METADATA_PATH
from ml_pipeline.dataset_manager import DatasetManager, TARGET_COLUMN


class ExplainabilityService:
    """
    Computes global feature importances, permutation importance,
    and interpretability insights for the placement prediction model.
    """

    def __init__(self, dataset_manager: Optional[DatasetManager] = None):
        self.dm = dataset_manager or DatasetManager()

    def get_global_explanations(self) -> Dict[str, Any]:
        """
        Retrieves global feature importance metrics and explains the relative
        influence of each feature on placement classification.
        """
        if not os.path.exists(MODEL_SAVE_PATH) or not os.path.exists(RESULTS_METADATA_PATH):
            raise RuntimeError("Model has not been trained yet. Please train models first.")

        model_payload = joblib.load(MODEL_SAVE_PATH)
        with open(RESULTS_METADATA_PATH, "r", encoding="utf-8") as f:
            comparison_results = json.load(f)

        model_name = model_payload.get("model_name", "Trained Model")
        pipeline = model_payload["pipeline"]
        feature_names = model_payload.get("all_transformed_features", [])

        # Feature importances from comparison results
        feature_importance_map = comparison_results.get("feature_importance", {})

        # Compute permutation importance if test sample available
        perm_importance_list = []
        try:
            df = self.dm.get_active_dataframe()
            if TARGET_COLUMN in df.columns:
                # Sample up to 500 rows for fast, reliable permutation importance
                sample_df = df.sample(n=min(500, len(df)), random_state=42)
                y_sample = sample_df[TARGET_COLUMN].astype(str).str.strip().apply(
                    lambda v: 1 if v.lower() in ["placed", "1", "1.0", "yes", "true"] else 0
                ).values
                X_sample = sample_df[[c for c in df.columns if c != TARGET_COLUMN]]

                perm_res = permutation_importance(
                    pipeline, X_sample, y_sample,
                    n_repeats=5,
                    random_state=42,
                    scoring="f1"
                )

                for feat, mean_imp, std_imp in zip(
                    X_sample.columns,
                    perm_res.importances_mean,
                    perm_res.importances_std
                ):
                    perm_importance_list.append({
                        "feature": feat,
                        "importance_mean": round(float(mean_imp), 4),
                        "importance_std": round(float(std_imp), 4)
                    })

                perm_importance_list = sorted(
                    perm_importance_list, key=lambda x: x["importance_mean"], reverse=True
                )
        except Exception as e:
            print(f"Notice: Permutation importance calculation bypassed: {e}")

        # Human-readable explanations
        descriptions = {
            "cat__PlacementTraining_Yes": "Completing placement training is one of the strongest positive indicators of recruitment readiness.",
            "cat__ExtracurricularActivities_Yes": "Active involvement in extracurricular activities demonstrates leadership, initiative, and team skills.",
            "num__AptitudeTestScore": "Aptitude test scores directly reflect quantitative, logical, and verbal problem-solving competency tested in screening rounds.",
            "num__CGPA": "Cumulative GPA reflects sustained academic discipline and fundamental engineering knowledge across university semesters.",
            "num__Projects": "Practical projects demonstrate hands-on software development experience, coding competence, and independent execution.",
            "num__SoftSkillsRating": "Communication clarity, articulation, and professional demeanour assessed during personal interview rounds.",
            "num__SSC_Marks": "Secondary school baseline performance providing long-term academic foundation context.",
            "num__HSC_Marks": "Higher secondary school performance in core pre-university subjects.",
            "num__Workshops/Certifications": "Self-driven upskilling through specialized workshops, hackathons, and certifications.",
            "num__Internships": "Prior industry exposure, professional workflows, and corporate teamwork experience."
        }

        ranked_features = []
        for feat, score in feature_importance_map.items():
            clean_name = feat.replace("num__", "").replace("cat__", "").replace("_Yes", " (Yes)")
            ranked_features.append({
                "raw_feature": feat,
                "display_name": clean_name,
                "importance_score": score,
                "abs_importance": abs(score),
                "insight": descriptions.get(feat, f"Impact coefficient of {score} in the classification pipeline.")
            })

        ranked_features = sorted(ranked_features, key=lambda x: x["abs_importance"], reverse=True)

        return {
            "model_name": model_name,
            "methodology": f"Feature impact measured via {model_name} parameters/weights and Permutation Feature Importance.",
            "ranked_features": ranked_features,
            "permutation_importance": perm_importance_list,
            "limitations": [
                "Feature importance reflects statistical associations learned by the classification model on training data, not strictly causal mechanisms.",
                "Correlations between academic indicators (such as CGPA, SSC, and HSC) may distribute importance across related features.",
                "A low global feature importance does not mean a skill is unimportant for specialized niche career tracks."
            ]
        }
