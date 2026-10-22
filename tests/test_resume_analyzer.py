import os
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

import backend
from pypdf import PdfWriter


class TestResumeAnalyzerRegression(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend.app)

    def create_sample_pdf(self, text="Sample resume for John Doe. Skills: Python, SQL."):
        import io
        from pypdf import PdfWriter
        from pypdf.generic import NameObject, create_string_object, DictionaryObject, ArrayObject

        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        
        # Write PDF to bytes
        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)
        return pdf_bytes.getvalue()

    def test_analyze_resume_rejects_non_pdf(self):
        response = self.client.post(
            "/analyze_resume/",
            files={"file": ("profile.png", b"fake png data", "image/png")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid file type. Please upload a PDF.", response.json()["detail"])

    def test_analyze_resume_service_unavailable_without_api_key(self):
        original_key = backend.GOOGLE_API_KEY
        backend.GOOGLE_API_KEY = None
        try:
            response = self.client.post(
                "/analyze_resume/",
                files={"file": ("resume.pdf", b"%PDF-1.4 dummy", "application/pdf")}
            )
            self.assertEqual(response.status_code, 503)
            self.assertIn("unavailable until GEMINI_API_KEY is configured", response.json()["detail"])
        finally:
            backend.GOOGLE_API_KEY = original_key

    def test_convert_gemini_to_recommender_format(self):
        gemini_data = {
            "education": {"degree": "B.Tech", "field": "CS"},
            "skills": {"Languages": ["Python", "Java"]},
            "projects": [
                {
                    "title": "Placement Portal",
                    "skills": "FastAPI, PostgreSQL",
                    "desc": "Built complete web portal"
                },
                {
                    "title": "ML Model",
                    "skills": "PyTorch",
                    "desc": "Built classifier"
                }
            ]
        }

        converted = backend.convert_gemini_to_recommender_format(gemini_data)
        self.assertIn("education", converted)
        self.assertIn("skills", converted)
        self.assertIn("projects", converted)
        self.assertIn("Placement Portal", converted["projects"])
        self.assertIn("ML Model", converted["projects"])
        self.assertEqual(converted["projects"]["Placement Portal"]["skills"], "FastAPI, PostgreSQL")

    @patch("backend.parse_resume_to_json")
    @patch("backend.detect_document_text")
    def test_analyze_resume_successful_flow_preserves_harsh_response_schema(
        self, mock_detect, mock_parse
    ):
        mock_detect.return_value = "Candidate John Doe\nPython, Docker, PyTorch"
        mock_parse.return_value = {
            "name": "John Doe",
            "contact_info": {"email": "john@example.com", "phone": "1234567890"},
            "professional_summary": "Aspiring ML Engineer",
            "education": {"degree": "B.Tech", "field": "Computer Science"},
            "skills": {
                "Languages": ["Python"],
                "Machine Learning": ["PyTorch", "Scikit-Learn"]
            },
            "projects": [
                {
                    "title": "AI Assistant",
                    "skills": "Python, LLM",
                    "desc": "Built intelligent bot"
                }
            ],
            "achievements_and_awards": ["Winner at Hackathon 2025"],
            "positions_of_responsibility": ["Tech Lead"]
        }

        # Ensure API key is configured for test
        original_key = backend.GOOGLE_API_KEY
        backend.GOOGLE_API_KEY = "test_key"

        try:
            sample_pdf_bytes = b"%PDF-1.4 sample pdf content"
            response = self.client.post(
                "/analyze_resume/",
                files={"file": ("my_resume.pdf", sample_pdf_bytes, "application/pdf")}
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()

            # Confirm Harsh's schema keys
            self.assertEqual(data["message"], "Analysis successful!")
            self.assertIn("recommendations", data)
            self.assertIn("parsed_data", data)
            self.assertEqual(data["parsed_data"]["name"], "John Doe")
            self.assertIsInstance(data["recommendations"], list)
            self.assertTrue(len(data["recommendations"]) > 0)

            # Confirm recommendation structure
            rec0 = data["recommendations"][0]
            self.assertIn("job_profile", rec0)
            self.assertIn("match_score", rec0)
            self.assertIn("skill_gap", rec0)

            # Verify no temporary files remain
            leftover = [f for f in os.listdir(".") if f.startswith("temp_") and f.endswith(".pdf")]
            self.assertEqual(len(leftover), 0)

        finally:
            backend.GOOGLE_API_KEY = original_key


if __name__ == "__main__":
    unittest.main()
