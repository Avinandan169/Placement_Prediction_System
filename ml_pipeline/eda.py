import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from ml_pipeline.dataset_manager import (
    DatasetManager,
    EXPECTED_NUMERIC_COLUMNS,
    EXPECTED_CATEGORICAL_COLUMNS,
    TARGET_COLUMN
)


class EDAService:
    """
    Computes comprehensive Exploratory Data Analysis (EDA) metrics,
    distributions, correlations, outlier summaries, and group comparisons
    for the active placement dataset.
    """

    def __init__(self, dataset_manager: Optional[DatasetManager] = None):
        self.dm = dataset_manager or DatasetManager()

    def get_full_eda(self) -> Dict[str, Any]:
        """
        Executes complete exploratory data analysis on the active dataset.
        Returns JSON-serializable statistics and chart data payloads.
        """
        df = self.dm.get_active_dataframe()
        metadata = self.dm.get_metadata()

        total_rows = int(len(df))
        total_cols = int(len(df.columns))
        duplicates = int(df.duplicated().sum())

        # 1. Column summaries & Missing Values
        missing_summary = {}
        dtypes_summary = {}
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            missing_summary[col] = {
                "count": null_count,
                "percentage": round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0
            }
            dtypes_summary[col] = str(df[col].dtype)

        # 2. Target Distribution
        target_counts = {}
        if TARGET_COLUMN in df.columns:
            vc = df[TARGET_COLUMN].value_counts()
            for k, v in vc.items():
                target_counts[str(k)] = {
                    "count": int(v),
                    "percentage": round((v / total_rows) * 100, 2)
                }

        # 3. Numeric Descriptive Statistics & Histograms
        numeric_cols = [c for c in EXPECTED_NUMERIC_COLUMNS if c in df.columns]
        descriptive_stats = {}
        histograms = {}
        outliers_info = {}

        for col in numeric_cols:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if series.empty:
                continue

            q25 = float(series.quantile(0.25))
            q50 = float(series.median())
            q75 = float(series.quantile(0.75))
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            outlier_count = int(((series < lower_bound) | (series > upper_bound)).sum())

            descriptive_stats[col] = {
                "count": int(series.count()),
                "mean": round(float(series.mean()), 3),
                "std": round(float(series.std()), 3),
                "min": float(series.min()),
                "q25": round(q25, 3),
                "median": round(q50, 3),
                "q75": round(q75, 3),
                "max": float(series.max()),
                "skewness": round(float(series.skew()), 3) if len(series) > 2 else 0.0,
            }

            outliers_info[col] = {
                "iqr": round(iqr, 3),
                "lower_bound": round(lower_bound, 3),
                "upper_bound": round(upper_bound, 3),
                "outlier_count": outlier_count,
                "outlier_percentage": round((outlier_count / len(series)) * 100, 2)
            }

            # Histogram bins (10 equal-width bins)
            counts, bin_edges = np.histogram(series, bins=10)
            histograms[col] = {
                "counts": [int(c) for c in counts],
                "bin_edges": [round(float(b), 2) for b in bin_edges],
                "labels": [
                    f"{round(bin_edges[i], 1)}-{round(bin_edges[i+1], 1)}"
                    for i in range(len(counts))
                ]
            }

        # 4. Categorical Feature Frequencies
        cat_cols = [c for c in EXPECTED_CATEGORICAL_COLUMNS if c in df.columns]
        categorical_freqs = {}
        for col in cat_cols:
            vc = df[col].astype(str).value_counts()
            categorical_freqs[col] = {
                str(k): int(v) for k, v in vc.items()
            }

        # 5. Correlation Matrix (Numeric Features)
        numeric_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
        corr_matrix = numeric_df.corr().round(3).fillna(0)
        correlation_data = {
            "columns": list(corr_matrix.columns),
            "values": corr_matrix.values.tolist()
        }

        # 6. Feature vs Placement Outcome (Grouped breakdown)
        feature_vs_target = {}
        if TARGET_COLUMN in df.columns:
            target_groups = df.groupby(TARGET_COLUMN)
            for col in numeric_cols:
                group_stats = {}
                for grp_name, grp_df in target_groups:
                    s = pd.to_numeric(grp_df[col], errors="coerce").dropna()
                    if not s.empty:
                        group_stats[str(grp_name)] = {
                            "mean": round(float(s.mean()), 2),
                            "median": round(float(s.median()), 2),
                            "std": round(float(s.std()), 2)
                        }
                feature_vs_target[col] = group_stats

            # Categorical vs Target cross-tabulations
            categorical_vs_target = {}
            for col in cat_cols:
                ct = pd.crosstab(df[col], df[TARGET_COLUMN], normalize="index") * 100
                categorical_vs_target[col] = ct.round(2).to_dict(orient="index")
        else:
            categorical_vs_target = {}

        # 7. Insights & Warnings
        warnings = []
        insights = []

        if duplicates > 0:
            warnings.append(
                f"Detected {duplicates} duplicate records in the active dataset ({round(duplicates/total_rows*100, 2)}%)."
            )

        if target_counts:
            ratios = [v["percentage"] for v in target_counts.values()]
            if max(ratios) > 70.0:
                warnings.append(
                    f"Noticeable class imbalance: {max(ratios)}% in dominant class. Stratified sampling will be enforced during training."
                )

        if "CGPA" in descriptive_stats and "AptitudeTestScore" in descriptive_stats:
            cgpa_placed = feature_vs_target.get("CGPA", {}).get("Placed", {}).get("mean")
            cgpa_not = feature_vs_target.get("CGPA", {}).get("NotPlaced", {}).get("mean")
            if cgpa_placed and cgpa_not:
                diff = round(cgpa_placed - cgpa_not, 2)
                insights.append(
                    f"Placed students have an average CGPA of {cgpa_placed} compared to {cgpa_not} for unplaced students (+{diff} differential)."
                )

        if "Projects" in feature_vs_target:
            p_placed = feature_vs_target["Projects"].get("Placed", {}).get("mean")
            p_not = feature_vs_target["Projects"].get("NotPlaced", {}).get("mean")
            if p_placed and p_not:
                insights.append(
                    f"Placed candidates completed an average of {p_placed} projects vs {p_not} for non-placed candidates."
                )

        return {
            "summary": {
                "total_rows": total_rows,
                "total_columns": total_cols,
                "duplicate_rows": duplicates,
                "dataset_name": metadata.get("name", "Active Dataset"),
                "source": metadata.get("source", "Unknown"),
                "license": metadata.get("license", "Unknown"),
                "ingestion_timestamp": metadata.get("ingestion_timestamp")
            },
            "dtypes": dtypes_summary,
            "missing_summary": missing_summary,
            "target_distribution": target_counts,
            "descriptive_statistics": descriptive_stats,
            "histograms": histograms,
            "outliers_summary": outliers_info,
            "categorical_frequencies": categorical_freqs,
            "correlation_matrix": correlation_data,
            "feature_vs_target": feature_vs_target,
            "categorical_vs_target": categorical_vs_target,
            "warnings": warnings,
            "insights": insights
        }
