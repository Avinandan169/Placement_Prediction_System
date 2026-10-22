import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from job_recommender import JobRecommender


class TestMLPlacementInference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recommender = JobRecommender()

    def test_create_user_profile_structure(self):
        education = {
            "degree": "B.Tech",
            "field": "Computer Science",
            "place": "ABC University",
            "cgpa": "8.5"
        }
        skills = {
            "Languages": ["Python", "SQL"],
            "Machine Learning": ["PyTorch", "Scikit-Learn"]
        }
        projects = {
            "Job Predictor": {
                "skills": "Python, Machine Learning",
                "desc": "Built a recommender system"
            }
        }

        profile_text, user_skills = self.recommender._create_user_profile(
            education, skills, projects
        )

        self.assertIn("Education: B.Tech in Computer Science", profile_text)
        self.assertIn("Python", profile_text)
        self.assertIn("Job Predictor", profile_text)
        self.assertIn("python", user_skills)
        self.assertIn("sql", user_skills)
        self.assertIn("pytorch", user_skills)
        self.assertIn("scikit-learn", user_skills)

    def test_recommend_jobs_returns_top_k(self):
        education = {"degree": "B.Tech", "field": "Computer Science"}
        skills = {
            "Languages": ["Python", "SQL"],
            "Machine Learning": ["PyTorch", "TensorFlow", "Scikit-Learn"]
        }
        projects = {
            "Vision AI": {
                "skills": "Python, OpenCV, PyTorch",
                "desc": "Object detection application"
            }
        }

        recommendations = self.recommender.recommend_jobs(
            education, skills, projects, top_k=3
        )

        self.assertEqual(len(recommendations), 3)
        for rec in recommendations:
            self.assertIn("job_profile", rec)
            self.assertIn("match_score", rec)
            self.assertIn("skill_gap", rec)
            self.assertIsInstance(rec["match_score"], float)

        # Check descending sort order
        scores = [r["match_score"] for r in recommendations]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_tiered_skill_gap_analysis(self):
        education = {"degree": "BE", "field": "Data Science"}
        # Provide only Python and SQL
        skills = {"Languages": ["Python", "SQL"]}
        projects = {}

        recommendations = self.recommender.recommend_jobs(
            education, skills, projects, top_k=5
        )

        for rec in recommendations:
            gap = rec["skill_gap"]
            self.assertIn("basic_missing", gap)
            self.assertIn("intermediate_missing", gap)
            self.assertIn("advanced_missing", gap)
            self.assertIsInstance(gap["basic_missing"], list)
            self.assertIsInstance(gap["intermediate_missing"], list)
            self.assertIsInstance(gap["advanced_missing"], list)

            # Neither python nor sql should appear in the missing sets
            self.assertNotIn("python", gap["basic_missing"])
            self.assertNotIn("sql", gap["basic_missing"])

    def test_recommend_jobs_with_empty_inputs(self):
        recommendations = self.recommender.recommend_jobs({}, {}, {}, top_k=2)
        self.assertEqual(len(recommendations), 2)
        for rec in recommendations:
            self.assertTrue(len(rec["job_profile"]) > 0)


if __name__ == "__main__":
    unittest.main()
