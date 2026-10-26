import os
import io
import json
import hashlib
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DEFAULT_DATASET_FILENAME = "campus_recruitment_krooz.csv"
ACTIVE_DATASET_PATH = os.path.join(DATA_PROCESSED_DIR, "active_placement_data.csv")
METADATA_PATH = os.path.join(DATA_PROCESSED_DIR, "dataset_metadata.json")

# Candidate Expected Schema
EXPECTED_NUMERIC_COLUMNS = [
    "CGPA",
    "Internships",
    "Projects",
    "Workshops/Certifications",
    "AptitudeTestScore",
    "SoftSkillsRating",
    "SSC_Marks",
    "HSC_Marks",
]

EXPECTED_CATEGORICAL_COLUMNS = [
    "ExtracurricularActivities",
    "PlacementTraining",
]

TARGET_COLUMN = "PlacementStatus"
ALL_REQUIRED_COLUMNS = EXPECTED_NUMERIC_COLUMNS + EXPECTED_CATEGORICAL_COLUMNS + [TARGET_COLUMN]

HF_BASE_URL = "https://huggingface.co/datasets/Krooz/Campus_Recruitment_CSV/resolve/main/raw_datasets/"
HF_SPLITS = ["train.csv", "validation.csv", "test.csv"]


class DatasetManager:
    """
    Manages dataset ingestion, data provenance tracking, schema validation,
    and data quality auditing for the Placement Prediction System.
    """

    def __init__(self):
        os.makedirs(DATA_RAW_DIR, exist_ok=True)
        os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
        self._ensure_default_dataset()

    def _ensure_default_dataset(self):
        """Ensures that a valid active dataset is always available."""
        if not os.path.exists(ACTIVE_DATASET_PATH) or not os.path.exists(METADATA_PATH):
            raw_default = os.path.join(DATA_RAW_DIR, DEFAULT_DATASET_FILENAME)
            if not os.path.exists(raw_default):
                print("Downloading default Krooz campus recruitment dataset...")
                self.fetch_krooz_dataset()
            else:
                self._activate_file(
                    raw_default,
                    name="Krooz Campus Recruitment Dataset",
                    source="https://huggingface.co/datasets/Krooz/Campus_Recruitment_CSV",
                    license_str="CC0-1.0 (Public Domain)",
                    notes="Benchmark dataset from Hugging Face for placement prediction research."
                )

    def fetch_krooz_dataset(self) -> Dict[str, Any]:
        """
        Retrieves the Krooz recruitment dataset from Hugging Face resolve URLs,
        combines train/val/test splits, computes checksum, and stores it in data/raw.
        """
        dfs = []
        try:
            for split in HF_SPLITS:
                url = HF_BASE_URL + split
                req = urllib.request.Request(url, headers={"User-Agent": "PlacementPredictor/1.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    content = resp.read()
                    df_split = pd.read_csv(io.BytesIO(content))
                    dfs.append(df_split)
            combined_df = pd.concat(dfs, ignore_index=True)
        except Exception as e:
            # Fallback if offline and cached raw exists
            raw_default = os.path.join(DATA_RAW_DIR, DEFAULT_DATASET_FILENAME)
            if os.path.exists(raw_default):
                combined_df = pd.read_csv(raw_default)
            else:
                raise RuntimeError(f"Failed to fetch Krooz dataset from Hugging Face: {e}")

        raw_path = os.path.join(DATA_RAW_DIR, DEFAULT_DATASET_FILENAME)
        combined_df.to_csv(raw_path, index=False)

        return self._activate_file(
            raw_path,
            name="Krooz Campus Recruitment Dataset",
            source="https://huggingface.co/datasets/Krooz/Campus_Recruitment_CSV",
            license_str="CC0-1.0 (Public Domain)",
            notes="Benchmark campus recruitment dataset compiled for tabular placement prediction."
        )

    def ingest_uploaded_csv(
        self,
        file_bytes: bytes,
        filename: str,
        source_note: str = "Local CSV Upload"
    ) -> Dict[str, Any]:
        """
        Validates, saves raw copy, and activates an uploaded student placement CSV.
        """
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        # Compute SHA-256 before doing anything
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        # Parse CSV safely
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Could not parse uploaded file as CSV: {e}")

        # Validate schema
        validation = self.validate_dataframe(df)
        if not validation["is_valid"]:
            error_msg = "; ".join(validation["errors"])
            raise ValueError(f"Schema validation failed: {error_msg}")

        # Save immutable raw copy
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
        raw_filename = f"upload_{timestamp_str}_{safe_name}"
        raw_path = os.path.join(DATA_RAW_DIR, raw_filename)
        with open(raw_path, "wb") as f:
            f.write(file_bytes)

        # Activate
        metadata = self._activate_file(
            raw_path,
            name=filename,
            source=source_note,
            license_str="User Provided / Institutional",
            notes=f"Uploaded on {datetime.now(timezone.utc).isoformat()}",
            sha256_precomputed=sha256_hash
        )
        metadata["validation"] = validation
        return metadata

    def _activate_file(
        self,
        file_path: str,
        name: str,
        source: str,
        license_str: str,
        notes: str,
        sha256_precomputed: Optional[str] = None
    ) -> Dict[str, Any]:
        """Copies file to active processed location and generates metadata."""
        df = pd.read_csv(file_path)
        df.to_csv(ACTIVE_DATASET_PATH, index=False)

        if sha256_precomputed is None:
            with open(ACTIVE_DATASET_PATH, "rb") as f:
                sha256_hash = hashlib.sha256(f.read()).hexdigest()
        else:
            sha256_hash = sha256_precomputed

        quality_report = self.generate_quality_report(df)

        metadata = {
            "name": name,
            "source": source,
            "license": license_str,
            "notes": notes,
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
            "row_count": int(df.shape[0]),
            "column_count": int(df.shape[1]),
            "columns": list(df.columns),
            "sha256": sha256_hash,
            "quality_report": quality_report
        }

        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validates column presence, expected types, target values, and basic sanity.
        """
        errors = []
        warnings = []

        if df.empty:
            errors.append("Dataset contains 0 rows.")
            return {"is_valid": False, "errors": errors, "warnings": warnings}

        # Check required columns
        missing_cols = [c for c in ALL_REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")

        # Check target column
        if TARGET_COLUMN in df.columns:
            target_series = df[TARGET_COLUMN].dropna().astype(str).str.strip()
            unique_targets = set(target_series.unique())
            valid_targets = {"Placed", "NotPlaced", "1", "0", "1.0", "0.0", "placed", "not placed", "notplaced"}
            if not unique_targets.issubset(valid_targets):
                unexpected = unique_targets - valid_targets
                warnings.append(f"Target '{TARGET_COLUMN}' contains unexpected classes: {unexpected}")
            if len(unique_targets) < 2:
                errors.append(f"Target '{TARGET_COLUMN}' has fewer than 2 distinct classes. Binary classification requires both classes.")
        else:
            errors.append(f"Missing target column '{TARGET_COLUMN}'.")

        # Check for numeric coercibility
        for num_col in EXPECTED_NUMERIC_COLUMNS:
            if num_col in df.columns:
                non_numeric = pd.to_numeric(df[num_col], errors="coerce").isna() & df[num_col].notna()
                if non_numeric.any():
                    errors.append(f"Column '{num_col}' contains non-numeric values in {non_numeric.sum()} rows.")

        # Duplicate check
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            warnings.append(f"Dataset contains {dup_count} duplicate rows ({round(dup_count / len(df) * 100, 2)}%).")

        # Missing values check
        null_counts = df.isnull().sum()
        cols_with_nulls = null_counts[null_counts > 0].to_dict()
        if cols_with_nulls:
            warnings.append(f"Columns with missing values: {cols_with_nulls}")

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "columns_found": list(df.columns),
            "rows": len(df),
        }

    def generate_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Produces comprehensive data quality summary statistics for UI rendering.
        """
        total_rows = len(df)
        total_cols = len(df.columns)
        duplicates = int(df.duplicated().sum())

        missing_per_col = {}
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            missing_per_col[col] = {
                "count": null_count,
                "percentage": round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0
            }

        # Target distribution
        target_dist = {}
        if TARGET_COLUMN in df.columns:
            target_counts = df[TARGET_COLUMN].value_counts().to_dict()
            for k, v in target_counts.items():
                target_dist[str(k)] = {
                    "count": int(v),
                    "percentage": round((v / total_rows) * 100, 2)
                }

        # Numeric ranges check
        numeric_summaries = {}
        for col in EXPECTED_NUMERIC_COLUMNS:
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")
                numeric_summaries[col] = {
                    "min": float(series.min()) if not np.isnan(series.min()) else None,
                    "max": float(series.max()) if not np.isnan(series.max()) else None,
                    "mean": round(float(series.mean()), 2) if not np.isnan(series.mean()) else None,
                    "median": round(float(series.median()), 2) if not np.isnan(series.median()) else None,
                }

        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "duplicate_rows": duplicates,
            "duplicate_percentage": round((duplicates / total_rows) * 100, 2) if total_rows > 0 else 0,
            "missing_values": missing_per_col,
            "target_distribution": target_dist,
            "numeric_ranges": numeric_summaries,
            "has_class_imbalance": bool(
                target_dist and max(d["percentage"] for d in target_dist.values()) > 75.0
            )
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata of the current active dataset."""
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return self._ensure_default_dataset() or {}

    def get_active_dataframe(self) -> pd.DataFrame:
        """Loads and returns active dataframe."""
        if not os.path.exists(ACTIVE_DATASET_PATH):
            self._ensure_default_dataset()
        return pd.read_csv(ACTIVE_DATASET_PATH)

    def get_preview(self, limit: int = 50) -> Dict[str, Any]:
        """Returns preview records and schema description."""
        df = self.get_active_dataframe()
        preview_df = df.head(limit)
        return {
            "total_rows": len(df),
            "columns": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "records": preview_df.replace({np.nan: None}).to_dict(orient="records"),
            "metadata": self.get_metadata()
        }

    def reset_to_default(self) -> Dict[str, Any]:
        """Resets active dataset to the default Krooz campus recruitment benchmark."""
        raw_default = os.path.join(DATA_RAW_DIR, DEFAULT_DATASET_FILENAME)
        if not os.path.exists(raw_default):
            return self.fetch_krooz_dataset()
        return self._activate_file(
            raw_default,
            name="Krooz Campus Recruitment Dataset",
            source="https://huggingface.co/datasets/Krooz/Campus_Recruitment_CSV",
            license_str="CC0-1.0 (Public Domain)",
            notes="Benchmark campus recruitment dataset compiled for tabular placement prediction."
        )
