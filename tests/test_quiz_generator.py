import os
import json
import unittest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from google.genai.errors import APIError

# Import target function from main.py
import main
from main import query_llm_for_quiz


class TestQuizGenerator(unittest.TestCase):
    """
    Focused automated unit tests for query_llm_for_quiz.
    All external calls to Gemini are strictly mocked to avoid quota usage.
    """

    def setUp(self):
        # Sample 10-question mock response payload matching expected schema
        self.sample_questions = [
            {
                "question": f"Question {i+1} on Python: What is feature {i+1}?",
                "options": [
                    {"A": f"Option A for {i+1}"},
                    {"B": f"Option B for {i+1}"},
                    {"C": f"Option C for {i+1}"},
                    {"D": f"Option D for {i+1}"}
                ],
                "correct": "A",
                "skill": "Python",
                "difficulty": "easy" if i < 3 else ("medium" if i < 7 else "hard"),
                "Explanation": f"Detailed explanation for question {i+1}."
            }
            for i in range(10)
        ]
        self.valid_gemini_json = json.dumps({"questions": self.sample_questions})
        self.sample_skills = {"Languages": ["Python", "JavaScript"]}

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_successful_quiz_generation(self, mock_client_cls):
        """Test successful generation and schema compliance of 10 MCQs."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = self.valid_gemini_json
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = query_llm_for_quiz(self.sample_skills)

        self.assertIn("questions", result)
        self.assertEqual(len(result["questions"]), 10)

        for q in result["questions"]:
            self.assertIn("question", q)
            self.assertIn("options", q)
            self.assertIn("correct", q)
            self.assertIn("skill", q)
            self.assertIn("difficulty", q)
            self.assertIn("Explanation", q)
            self.assertIsInstance(q["options"], list)
            self.assertEqual(len(q["options"]), 4)
            self.assertIn(q["difficulty"], {"easy", "medium", "hard"})
            self.assertIn(q["correct"], {"A", "B", "C", "D"})
            for opt in q["options"]:
                self.assertIsInstance(opt, dict)
                self.assertEqual(len(opt), 1)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_markdown_code_fence_cleaning(self, mock_client_cls):
        """Test that model responses wrapped in ```json ... ``` are cleanly parsed."""
        fenced_json = f"```json\n{self.valid_gemini_json}\n```"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = fenced_json
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = query_llm_for_quiz(self.sample_skills)
        self.assertEqual(len(result["questions"]), 10)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_malformed_model_output_invalid_json(self, mock_client_cls):
        """Test handling of non-JSON response from model."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Error: I cannot generate a quiz at this moment."
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)
        self.assertIn("invalid or malformed quiz data", ctx.exception.detail)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_malformed_model_output_missing_questions_key(self, mock_client_cls):
        """Test handling of JSON response missing top-level 'questions' key."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"wrong_key": []})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)
        self.assertIn("invalid or malformed quiz data", ctx.exception.detail)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_malformed_model_output_missing_question_fields(self, mock_client_cls):
        """Test handling when a question is missing required fields like 'correct'."""
        bad_questions = [dict(q) for q in self.sample_questions]
        del bad_questions[0]["correct"]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_wrong_question_count_fewer(self, mock_client_cls):
        """Test that fewer than 10 questions (e.g. 9) is rejected with HTTP 502."""
        fewer_questions = self.sample_questions[:9]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": fewer_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_wrong_question_count_more(self, mock_client_cls):
        """Test that more than 10 questions (e.g. 11) is rejected with HTTP 502."""
        more_questions = self.sample_questions + [self.sample_questions[0]]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": more_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_blank_question_text(self, mock_client_cls):
        """Test that blank question text is rejected with HTTP 502."""
        bad_questions = [dict(q) for q in self.sample_questions]
        bad_questions[0]["question"] = "   "
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_blank_skill(self, mock_client_cls):
        """Test that blank skill string is rejected with HTTP 502."""
        bad_questions = [dict(q) for q in self.sample_questions]
        bad_questions[0]["skill"] = ""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_blank_explanation(self, mock_client_cls):
        """Test that blank Explanation is rejected with HTTP 502."""
        bad_questions = [dict(q) for q in self.sample_questions]
        bad_questions[0]["Explanation"] = "   "
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_invalid_difficulty(self, mock_client_cls):
        """Test that difficulty outside easy/medium/hard is rejected with HTTP 502."""
        bad_questions = [dict(q) for q in self.sample_questions]
        bad_questions[0]["difficulty"] = "extreme"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_difficulty_case_insensitive_normalization(self, mock_client_cls):
        """Test that difficulty like 'EASY' and 'Medium' are normalized to lowercase."""
        questions = [dict(q) for q in self.sample_questions]
        questions[0]["difficulty"] = "EASY"
        questions[1]["difficulty"] = "Medium"
        questions[2]["difficulty"] = "HARD"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = query_llm_for_quiz(self.sample_skills)
        self.assertEqual(result["questions"][0]["difficulty"], "easy")
        self.assertEqual(result["questions"][1]["difficulty"], "medium")
        self.assertEqual(result["questions"][2]["difficulty"], "hard")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_duplicate_option_labels(self, mock_client_cls):
        """Test that duplicate option labels (e.g. two 'A' options) are rejected with HTTP 502."""
        bad_questions = [dict(q) for q in self.sample_questions]
        bad_questions[0]["options"] = [
            {"A": "First option"},
            {"A": "Duplicate A option"},
            {"C": "Third option"},
            {"D": "Fourth option"}
        ]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_missing_option_label(self, mock_client_cls):
        """Test that missing required option label (e.g. E instead of D) is rejected with HTTP 502."""
        bad_questions = [dict(q) for q in self.sample_questions]
        bad_questions[0]["options"] = [
            {"A": "Option A"},
            {"B": "Option B"},
            {"C": "Option C"},
            {"E": "Option E"}
        ]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_fewer_than_four_options(self, mock_client_cls):
        """Test that fewer than 4 options is rejected with HTTP 502."""
        bad_questions = [dict(q) for q in self.sample_questions]
        bad_questions[0]["options"] = [
            {"A": "Option A"},
            {"B": "Option B"},
            {"C": "Option C"}
        ]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_empty_option_text(self, mock_client_cls):
        """Test that blank text in an option is rejected with HTTP 502."""
        bad_questions = [dict(q) for q in self.sample_questions]
        bad_questions[0]["options"] = [
            {"A": "Option A"},
            {"B": "   "},
            {"C": "Option C"},
            {"D": "Option D"}
        ]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_invalid_correct_answer_key_no_fallback(self, mock_client_cls):
        """Test that invalid correct key (e.g. 'Z') raises HTTP 502 with no fallback to 'A'."""
        bad_questions = [dict(q) for q in self.sample_questions]
        bad_questions[0]["correct"] = "Z"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": bad_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_correct_answer_matches_option_text(self, mock_client_cls):
        """Test that if the model returns full option text for correct, it resolves to option letter."""
        questions = [dict(q) for q in self.sample_questions]
        questions[0]["correct"] = "Option B for 1"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = query_llm_for_quiz(self.sample_skills)
        self.assertEqual(result["questions"][0]["correct"], "B")

    @patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False)
    def test_missing_api_key(self):
        """Test that missing GEMINI_API_KEY raises HTTP 500 without leaking secrets."""
        with patch.object(os, "getenv", return_value=""):
            with self.assertRaises(HTTPException) as ctx:
                query_llm_for_quiz(self.sample_skills)
            self.assertEqual(ctx.exception.status_code, 500)
            self.assertIn("GEMINI_API_KEY environment variable is not set", ctx.exception.detail)

    def test_empty_skills_input(self):
        """Test that providing no skills raises HTTP 400."""
        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz({})
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("No skills", ctx.exception.detail)

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz({"Languages": ["   ", ""]})
        self.assertEqual(ctx.exception.status_code, 400)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_api_error_rate_limit_429(self, mock_client_cls):
        """Test rate limit / quota exhaustion triggers HTTP 429."""
        mock_client = MagicMock()
        err = APIError(429, {"error": {"message": "Resource has been exhausted (e.g. check quota)."}})
        mock_client.models.generate_content.side_effect = err
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("rate limit or quota exceeded", ctx.exception.detail)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_api_error_generic_502(self, mock_client_cls):
        """Test generic API communication error triggers HTTP 502."""
        mock_client = MagicMock()
        err = APIError(503, {"error": {"message": "Internal error encountered."}})
        mock_client.models.generate_content.side_effect = err
        mock_client_cls.return_value = mock_client

        with self.assertRaises(HTTPException) as ctx:
            query_llm_for_quiz(self.sample_skills)
        self.assertEqual(ctx.exception.status_code, 502)
        self.assertIn("communicating with the AI service", ctx.exception.detail)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_options_normalization_dict_format(self, mock_client_cls):
        """Test defensive normalization when options are provided as a single dict."""
        dict_options_payload = {
            "questions": [
                {
                    "question": "What is FastAPI?",
                    "options": {"A": "Web framework", "B": "Database", "C": "OS", "D": "Browser"},
                    "correct": "A",
                    "skill": "FastAPI",
                    "difficulty": "medium",
                    "Explanation": "FastAPI is a modern web framework."
                }
            ] + [dict(q) for q in self.sample_questions[1:]]
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(dict_options_payload)
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = query_llm_for_quiz(self.sample_skills)
        opts = result["questions"][0]["options"]
        self.assertIsInstance(opts, list)
        self.assertEqual(opts[0], {"A": "Web framework"})
        self.assertEqual(opts[1], {"B": "Database"})
        self.assertEqual(len(result["questions"]), 10)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_options_normalization_string_list_format(self, mock_client_cls):
        """Test defensive normalization when options are provided as a list of strings."""
        str_options_payload = {
            "questions": [
                {
                    "question": "What is Python?",
                    "options": ["Interpreted language", "Compiler only", "Hardware", "Database"],
                    "correct": "A",
                    "skill": "Python",
                    "difficulty": "easy",
                    "Explanation": "Python is an interpreted language."
                }
            ] + [dict(q) for q in self.sample_questions[1:]]
        }
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps(str_options_payload)
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = query_llm_for_quiz(self.sample_skills)
        opts = result["questions"][0]["options"]
        self.assertIsInstance(opts, list)
        self.assertEqual(opts[0], {"A": "Interpreted language"})
        self.assertEqual(opts[1], {"B": "Compiler only"})
        self.assertEqual(len(result["questions"]), 10)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_quiz_options_with_html_tags_and_special_chars(self, mock_client_cls):
        """Test questions containing HTML/JSX tags and special characters are preserved properly."""
        html_questions = [dict(q) for q in self.sample_questions]
        html_questions[0]["question"] = "Which header is required for <stdio.h> input & output functions?"
        html_questions[0]["options"] = [
            {"A": "<stdio.h>"},
            {"B": "<iostream>"},
            {"C": "<conio.h>"},
            {"D": "<stdlib.h>"}
        ]
        html_questions[0]["correct"] = "A"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": html_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = query_llm_for_quiz(self.sample_skills)
        q0 = result["questions"][0]
        self.assertEqual(q0["question"], "Which header is required for <stdio.h> input & output functions?")
        self.assertEqual(q0["options"][0], {"A": "<stdio.h>"})
        self.assertEqual(q0["options"][1], {"B": "<iostream>"})


class TestQuizEndpoint(unittest.TestCase):
    """
    Integration tests for the /generate-quiz FastAPI endpoint using TestClient.
    """

    def setUp(self):
        from fastapi.testclient import TestClient
        self.client = TestClient(main.app)

    def test_unauthenticated_request_returns_401(self):
        """Calling /generate-quiz without bearer token returns 401 Unauthorized."""
        response = self.client.post("/generate-quiz", json={"Languages": ["Python"]})
        self.assertEqual(response.status_code, 401)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key-12345"})
    @patch("main.genai.Client")
    def test_authenticated_generate_quiz_success(self, mock_client_cls):
        """Calling /generate-quiz with valid token and skills returns 200 and questions."""
        sample_questions = [
            {
                "question": f"Question {i+1}",
                "options": [{"A": "Opt1"}, {"B": "Opt2"}, {"C": "Opt3"}, {"D": "Opt4"}],
                "correct": "A",
                "skill": "Python",
                "difficulty": "easy",
                "Explanation": "Explanation text"
            }
            for i in range(10)
        ]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({"questions": sample_questions})
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 1, "email": "test@student.com", "role": "student"}
        try:
            response = self.client.post(
                "/generate-quiz",
                headers={"Authorization": "Bearer test-token"},
                json={"Languages": ["Python", "SQL"]}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("questions", data)
            self.assertEqual(len(data["questions"]), 10)
        finally:
            main.app.dependency_overrides.clear()

    def test_authenticated_generate_quiz_empty_payload(self):
        """Calling /generate-quiz with empty skills dict returns 400 Bad Request."""
        main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 1, "email": "test@student.com", "role": "student"}
        try:
            response = self.client.post(
                "/generate-quiz",
                headers={"Authorization": "Bearer test-token"},
                json={}
            )
            self.assertEqual(response.status_code, 400)
        finally:
            main.app.dependency_overrides.clear()

    def test_submit_quiz_unanswered_question_handling(self):
        """Verifies submitting a quiz with unanswered questions returns N/A and correct scoring."""
        sample_quiz_data = {
            "questions": [
                {
                    "question": f"Question {i+1}",
                    "options": [{"A": "Opt A"}, {"B": "Opt B"}, {"C": "Opt C"}, {"D": "Opt D"}],
                    "correct": "A"
                }
                for i in range(10)
            ]
        }
        # Question 0 is unanswered; Question 1 is answered correctly; Question 2 answered incorrectly
        submission_payload = {
            "answers": {
                "1": "A", # Q2 correct
                "2": "B", # Q3 incorrect
            },
            "time_spent": {str(i): 5.0 for i in range(10)},
            "quiz_data": sample_quiz_data
        }

        main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 1, "email": "test@student.com", "role": "student"}
        try:
            response = self.client.post(
                "/submit-quiz",
                headers={"Authorization": "Bearer test-token"},
                json=submission_payload
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["score"], "1/10")
            self.assertEqual(data["percentage"], 10.0)
            self.assertEqual(data["total_time_seconds"], 50.0)

            results = data["individual_results"]
            self.assertEqual(len(results), 10)

            # Check Q1 (unanswered)
            q1_res = results[0]
            self.assertEqual(q1_res["id"], 1)
            self.assertEqual(q1_res["user_answer"], "N/A")
            self.assertFalse(q1_res["is_correct"])
            self.assertEqual(q1_res["correct_answer"], "A")

            # Check Q2 (answered correctly)
            q2_res = results[1]
            self.assertEqual(q2_res["id"], 2)
            self.assertEqual(q2_res["user_answer"], "A")
            self.assertTrue(q2_res["is_correct"])

            # Check Q3 (answered incorrectly)
            q3_res = results[2]
            self.assertEqual(q3_res["id"], 3)
            self.assertEqual(q3_res["user_answer"], "B")
            self.assertFalse(q3_res["is_correct"])
        finally:
            main.app.dependency_overrides.clear()

    def test_submit_quiz_all_unanswered(self):
        """Verifies submitting a quiz with no answers returns 0/10 and all N/A."""
        sample_quiz_data = {
            "questions": [
                {
                    "question": f"Question {i+1}",
                    "options": [{"A": "Opt A"}, {"B": "Opt B"}, {"C": "Opt C"}, {"D": "Opt D"}],
                    "correct": "A"
                }
                for i in range(10)
            ]
        }
        submission_payload = {
            "answers": {},
            "time_spent": {str(i): 1.0 for i in range(10)},
            "quiz_data": sample_quiz_data
        }

        main.app.dependency_overrides[main.get_current_user] = lambda: {"id": 1, "email": "test@student.com", "role": "student"}
        try:
            response = self.client.post(
                "/submit-quiz",
                headers={"Authorization": "Bearer test-token"},
                json=submission_payload
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["score"], "0/10")
            self.assertEqual(data["percentage"], 0.0)
            for res in data["individual_results"]:
                self.assertEqual(res["user_answer"], "N/A")
                self.assertFalse(res["is_correct"])
        finally:
            main.app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
