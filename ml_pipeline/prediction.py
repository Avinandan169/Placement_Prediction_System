import os
import joblib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from ml_pipeline.training import MODEL_SAVE_PATH, ModelTrainingService
from ml_pipeline.dataset_manager import (
    EXPECTED_NUMERIC_COLUMNS,
    EXPECTED_CATEGORICAL_COLUMNS
)

# Reference benchmark values for local explanation (derived from placed student distributions)
PLACED_BENCHMARKS = {
    "CGPA": 8.0,
    "Internships": 1.5,
    "Projects": 2.5,
    "Workshops/Certifications": 1.5,
    "AptitudeTestScore": 82.0,
    "SoftSkillsRating": 4.3,
    "SSC_Marks": 72.0,
    "HSC_Marks": 78.0
}


class PredictionService:
    """
    Handles student placement outcome prediction, probability estimation,
    input validation, and individual prediction feature contributions.
    """

    def __init__(self):
        self._model_payload = None

    def _get_model(self) -> Dict[str, Any]:
        """Loads persisted model pipeline from disk, training if not yet created."""
        if self._model_payload is None:
            if not os.path.exists(MODEL_SAVE_PATH):
                print("Model not found on disk. Initiating training...")
                trainer = ModelTrainingService()
                trainer.train_and_evaluate_all()

            self._model_payload = joblib.load(MODEL_SAVE_PATH)
        return self._model_payload

    def validate_inputs(self, student_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validates, coerces, and checks sanity of input student attributes.
        Returns cleaned dict and list of warnings.
        """
        cleaned = {}
        warnings = []

        # CGPA
        cgpa = float(student_data.get("CGPA", student_data.get("cgpa", 0.0)))
        if cgpa < 0.0 or cgpa > 10.0:
            raise ValueError(f"CGPA must be between 0.0 and 10.0. Received: {cgpa}")
        if cgpa < 5.0:
            warnings.append(f"CGPA {cgpa} is significantly below typical placement thresholds.")
        cleaned["CGPA"] = cgpa

        # Internships
        internships = int(student_data.get("Internships", student_data.get("internships", 0)))
        if internships < 0 or internships > 20:
            raise ValueError(f"Internships must be between 0 and 20. Received: {internships}")
        cleaned["Internships"] = internships

        # Projects
        projects = int(student_data.get("Projects", student_data.get("projects", 0)))
        if projects < 0 or projects > 50:
            raise ValueError(f"Projects count must be between 0 and 50. Received: {projects}")
        cleaned["Projects"] = projects

        # Workshops/Certifications
        workshops = int(student_data.get("Workshops/Certifications", student_data.get("workshops", 0)))
        if workshops < 0 or workshops > 50:
            raise ValueError(f"Workshops/Certifications must be between 0 and 50. Received: {workshops}")
        cleaned["Workshops/Certifications"] = workshops

        # AptitudeTestScore
        aptitude = float(student_data.get("AptitudeTestScore", student_data.get("aptitude_score", 70.0)))
        if aptitude < 0.0 or aptitude > 100.0:
            raise ValueError(f"Aptitude test score must be between 0 and 100. Received: {aptitude}")
        cleaned["AptitudeTestScore"] = aptitude

        # SoftSkillsRating
        soft_skills = float(student_data.get("SoftSkillsRating", student_data.get("soft_skills_rating", 3.5)))
        if soft_skills < 1.0 or soft_skills > 5.0:
            raise ValueError(f"Soft skills rating must be between 1.0 and 5.0. Received: {soft_skills}")
        cleaned["SoftSkillsRating"] = soft_skills

        # ExtracurricularActivities
        extra = str(student_data.get("ExtracurricularActivities", student_data.get("extracurriculars", "No"))).strip().title()
        cleaned["ExtracurricularActivities"] = "Yes" if extra in ["Yes", "True", "1", "Y"] else "No"

        # PlacementTraining
        training = str(student_data.get("PlacementTraining", student_data.get("placement_training", "No"))).strip().title()
        cleaned["PlacementTraining"] = "Yes" if training in ["Yes", "True", "1", "Y"] else "No"

        # SSC Marks
        ssc = float(student_data.get("SSC_Marks", student_data.get("tenth_percentage", 65.0)))
        if ssc < 0.0 or ssc > 100.0:
            raise ValueError(f"SSC marks must be between 0 and 100. Received: {ssc}")
        cleaned["SSC_Marks"] = ssc

        # HSC Marks
        hsc = float(student_data.get("HSC_Marks", student_data.get("twelfth_percentage", 65.0)))
        if hsc < 0.0 or hsc > 100.0:
            raise ValueError(f"HSC marks must be between 0 and 100. Received: {hsc}")
        cleaned["HSC_Marks"] = hsc

        return cleaned, warnings

    def predict(self, student_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes prediction using the active trained pipeline.
        Returns class outcome, probability percentage, confidence, and feature contributions.
        """
        model_payload = self._get_model()
        pipeline = model_payload["pipeline"]
        model_name = model_payload["model_name"]

        cleaned_inputs, warnings = self.validate_inputs(student_data)

        # Build single-row DataFrame for pipeline input
        input_df = pd.DataFrame([cleaned_inputs])

        # Predict class
        pred_class_idx = int(pipeline.predict(input_df)[0])
        pred_label = "Placed" if pred_class_idx == 1 else "NotPlaced"

        # Predict probabilities
        if hasattr(pipeline, "predict_proba"):
            probs = pipeline.predict_proba(input_df)[0]
            placed_prob = round(float(probs[1]) * 100, 2)
            not_placed_prob = round(float(probs[0]) * 100, 2)
        else:
            placed_prob = 100.0 if pred_class_idx == 1 else 0.0
            not_placed_prob = 100.0 - placed_prob

        # Calculate individual feature contributions relative to placed benchmarks
        contributions = []
        for feature, benchmark in PLACED_BENCHMARKS.items():
            actual = cleaned_inputs[feature]
            diff = actual - benchmark
            # Directional impact: positive if meeting or exceeding benchmark
            impact = "positive" if diff >= 0 else "negative"
            pct_diff = round((diff / benchmark) * 100, 1) if benchmark > 0 else 0

            contributions.append({
                "feature": feature,
                "student_value": actual,
                "benchmark_value": benchmark,
                "impact": impact,
                "difference": round(diff, 2),
                "percentage_difference": pct_diff,
                "description": f"{feature}: {actual} (Benchmark: {benchmark})"
            })

        # Categorical contributions
        for cat_feat in EXPECTED_CATEGORICAL_COLUMNS:
            val = cleaned_inputs[cat_feat]
            contributions.append({
                "feature": cat_feat,
                "student_value": val,
                "benchmark_value": "Yes",
                "impact": "positive" if val == "Yes" else "negative",
                "difference": 1 if val == "Yes" else -1,
                "percentage_difference": 0.0,
                "description": f"{cat_feat}: {val}"
            })

        # Top strengths and areas for improvement
        strengths = [c for c in contributions if c["impact"] == "positive"]
        strengths = sorted(strengths, key=lambda x: x["percentage_difference"], reverse=True)[:3]

        improvements = [c for c in contributions if c["impact"] == "negative"]
        improvements = sorted(improvements, key=lambda x: x["percentage_difference"])[:3]

        return {
            "prediction": pred_label,
            "placement_probability": placed_prob,
            "not_placed_probability": not_placed_prob,
            "model_used": model_name,
            "training_timestamp": model_payload.get("training_timestamp"),
            "dataset_name": model_payload.get("dataset_name"),
            "inputs_evaluated": cleaned_inputs,
            "feature_contributions": contributions,
            "key_strengths": strengths,
            "areas_for_improvement": improvements,
            "warnings": warnings,
            "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
            "disclaimer": "This estimate is generated by a predictive machine learning model and serves as academic guidance rather than a guarantee of recruitment."
        }
