import unittest
from fastapi.testclient import TestClient
from main import app


class TestAPIEndpoints(unittest.TestCase):
    """
    Integration tests for FastAPI REST endpoints:
    Dataset Management, EDA, Model Training, Prediction, Explainability,
    Fuzzy Placement Readiness, and A* Skill Planner.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_dataset_info_endpoint(self):
        resp = self.client.get("/api/dataset/info")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("name", data)
        self.assertEqual(data["row_count"], 10000)
        self.assertEqual(data["column_count"], 11)

    def test_dataset_preview_endpoint(self):
        resp = self.client.get("/api/dataset/preview?limit=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["records"]), 5)
        self.assertIn("CGPA", data["columns"])

    def test_eda_summary_endpoint(self):
        resp = self.client.get("/api/eda/summary")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("descriptive_statistics", data)
        self.assertIn("correlation_matrix", data)
        self.assertIn("target_distribution", data)

    def test_model_comparison_endpoint(self):
        resp = self.client.get("/api/model/comparison")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("comparison", data)
        self.assertTrue(len(data["comparison"]) >= 5)

    def test_model_prediction_endpoint(self):
        payload = {
            "CGPA": 8.5,
            "Internships": 2,
            "Projects": 3,
            "Workshops": 2,
            "AptitudeTestScore": 88,
            "SoftSkillsRating": 4.5,
            "ExtracurricularActivities": "Yes",
            "PlacementTraining": "Yes",
            "SSC_Marks": 82,
            "HSC_Marks": 85,
            "student_name": "Test Student"
        }
        resp = self.client.post("/api/model/predict", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["prediction"], "Placed")
        self.assertGreater(data["placement_probability"], 50.0)
        self.assertIn("feature_contributions", data)

    def test_model_explain_endpoint(self):
        resp = self.client.get("/api/model/explain")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ranked_features", data)
        self.assertIn("limitations", data)

    def test_fuzzy_readiness_endpoint(self):
        payload = {
            "cgpa": 8.2,
            "aptitude": 85.0,
            "soft_skills": 4.2,
            "projects": 2,
            "internships": 1
        }
        resp = self.client.post("/api/fuzzy/evaluate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("readiness_score", data)
        self.assertIn("readiness_tier", data)
        self.assertIn("activated_rules", data)
        self.assertIn("curves_data", data)

    def test_astar_roles_and_plan_endpoint(self):
        # Roles list
        roles_resp = self.client.get("/api/astar/roles")
        self.assertEqual(roles_resp.status_code, 200)
        roles = roles_resp.json()["roles"]
        self.assertTrue(len(roles) >= 5)

        # Plan generation
        plan_payload = {
            "target_role": "Data Scientist",
            "current_skills": ["python", "sql"]
        }
        plan_resp = self.client.post("/api/astar/plan", json=plan_payload)
        self.assertEqual(plan_resp.status_code, 200)
        plan_data = plan_resp.json()
        self.assertTrue(plan_data["reachable"])
        self.assertGreater(plan_data["total_effort_hours"], 0)
        self.assertTrue(len(plan_data["steps"]) > 0)


if __name__ == "__main__":
    unittest.main()
