import unittest
import numpy as np
import pandas as pd
from ml_pipeline.dataset_manager import DatasetManager
from ml_pipeline.eda import EDAService
from ml_pipeline.training import ModelTrainingService
from ml_pipeline.prediction import PredictionService
from ml_pipeline.explainability import ExplainabilityService


class TestPredictiveAnalyticsPipeline(unittest.TestCase):
    """
    Comprehensive tests for the CSE3141 Predictive Analytics module:
    Dataset Ingestion, Validation, EDA, Model Training, Persistence,
    Inference, and Explainability.
    """

    @classmethod
    def setUpClass(cls):
        cls.dm = DatasetManager()
        cls.eda = EDAService(cls.dm)
        cls.trainer = ModelTrainingService(cls.dm)
        cls.predictor = PredictionService()
        cls.explainer = ExplainabilityService(cls.dm)

    def test_dataset_provenance_and_schema(self):
        meta = self.dm.get_metadata()
        self.assertIn("Krooz", meta["name"])
        self.assertEqual(meta["row_count"], 10000)
        self.assertEqual(meta["column_count"], 11)
        self.assertTrue(len(meta["sha256"]) == 64)
        self.assertIn("CC0-1.0", meta["license"])

        # Check required columns
        df = self.dm.get_active_dataframe()
        for col in ["CGPA", "AptitudeTestScore", "SoftSkillsRating", "PlacementStatus"]:
            self.assertIn(col, df.columns)

    def test_schema_validation_rejects_empty_and_invalid(self):
        empty_df = pd.DataFrame()
        val = self.dm.validate_dataframe(empty_df)
        self.assertFalse(val["is_valid"])

        # Missing target column
        bad_df = pd.DataFrame({"CGPA": [7.5, 8.0]})
        val2 = self.dm.validate_dataframe(bad_df)
        self.assertFalse(val2["is_valid"])
        self.assertTrue(any("Missing required columns" in e for e in val2["errors"]))

    def test_eda_statistics_and_distributions(self):
        eda_data = self.eda.get_full_eda()
        summary = eda_data["summary"]
        self.assertEqual(summary["total_rows"], 10000)
        self.assertIn("CGPA", eda_data["descriptive_statistics"])
        self.assertIn("AptitudeTestScore", eda_data["descriptive_statistics"])

        # Verify target counts
        self.assertIn("Placed", eda_data["target_distribution"])
        self.assertIn("NotPlaced", eda_data["target_distribution"])

        # Verify correlation matrix
        corr = eda_data["correlation_matrix"]
        self.assertTrue(len(corr["columns"]) >= 5)
        self.assertEqual(len(corr["values"]), len(corr["columns"]))

    def test_trained_models_comparison_metrics(self):
        results = self.trainer.get_comparison_results()
        self.assertIn("comparison", results)
        models = {m["model_name"]: m for m in results["comparison"]}

        # 5 distinct models compared
        self.assertIn("Dummy Baseline", models)
        self.assertIn("Logistic Regression", models)
        self.assertIn("Decision Tree", models)
        self.assertIn("Random Forest", models)
        self.assertIn("Gradient Boosting", models)

        # Baseline should have lower F1 than top models
        self.assertEqual(models["Dummy Baseline"]["f1_score"], 0.0)
        self.assertGreater(models["Logistic Regression"]["f1_score"], 0.70)
        self.assertGreater(models["Random Forest"]["f1_score"], 0.70)
        self.assertGreater(models["Gradient Boosting"]["f1_score"], 0.70)

        # Accuracy check
        self.assertGreater(models["Logistic Regression"]["accuracy"], 0.75)

    def test_prediction_service_valid_and_invalid_inputs(self):
        # Valid high-performing candidate
        high_candidate = {
            "CGPA": 8.7,
            "Internships": 2,
            "Projects": 3,
            "Workshops/Certifications": 2,
            "AptitudeTestScore": 90,
            "SoftSkillsRating": 4.8,
            "ExtracurricularActivities": "Yes",
            "PlacementTraining": "Yes",
            "SSC_Marks": 85,
            "HSC_Marks": 88
        }
        res = self.predictor.predict(high_candidate)
        self.assertEqual(res["prediction"], "Placed")
        self.assertGreater(res["placement_probability"], 60.0)
        self.assertIn("key_strengths", res)

        # Out-of-bounds input raises ValueError
        invalid_candidate = dict(high_candidate, CGPA=12.5)
        with self.assertRaises(ValueError):
            self.predictor.predict(invalid_candidate)

    def test_explainability_global_and_permutation(self):
        expl = self.explainer.get_global_explanations()
        self.assertIn("ranked_features", expl)
        self.assertTrue(len(expl["ranked_features"]) >= 5)
        self.assertIn("limitations", expl)


if __name__ == "__main__":
    unittest.main()
