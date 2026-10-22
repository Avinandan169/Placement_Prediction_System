import os
import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO
from fastapi.testclient import TestClient

import backend
from communication_analyzer import CommunicationAnalyzer


class TestVoiceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(backend.app)

    def test_analyze_audio_rejects_non_audio_file(self):
        response = self.client.post(
            "/analyze_audio/",
            files={"file": ("notes.txt", b"Hello world this is not audio", "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid file type", response.json()["detail"])

    def test_analyze_audio_service_unavailable_when_analyzer_none(self):
        original_analyzer = backend.analyzer
        backend.analyzer = None
        try:
            response = self.client.post(
                "/analyze_audio/",
                files={"file": ("speech.wav", b"RIFF dummy audio data", "audio/wav")}
            )
            self.assertEqual(response.status_code, 503)
            self.assertIn("Voice analysis is unavailable", response.json()["detail"])
        finally:
            backend.analyzer = original_analyzer

    def test_analyze_audio_successful_pipeline_and_cleanup(self):
        mock_report = {
            "final_communication_score": "8.5 / 10.0",
            "transcribed_text": "I worked effectively with cross functional teams.",
            "detailed_scores": [
                {"metric": "Vocabulary", "score": "8.0/10", "details": "Good word choice."},
                {"metric": "Fumbling", "score": "9.0/10", "details": "Found 0 filler words."},
                {"metric": "Articulation (Pace)", "score": "8.5/10", "details": "Pace was 145 WPM."},
                {"metric": "Vocal Jitter (Nervousness)", "score": "8.5/10", "details": "Jitter was 0.2%."}
            ],
            "raw_data": {}
        }

        mock_analyzer = MagicMock()
        mock_analyzer.get_final_analysis.return_value = mock_report

        original_analyzer = backend.analyzer
        backend.analyzer = mock_analyzer

        try:
            # Send webm audio file
            response = self.client.post(
                "/analyze_audio/",
                files={"file": ("test_response.webm", b"\x1aE\xdf\xa3webm_dummy", "audio/webm")}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["message"], "Analysis successful!")
            self.assertEqual(data["report"]["final_communication_score"], "8.5 / 10.0")
            self.assertEqual(data["report"]["transcribed_text"], "I worked effectively with cross functional teams.")

            # Verify no leftover temp audio files
            leftover_temp = [f for f in os.listdir(".") if f.startswith("temp_") and f.endswith(".webm")]
            self.assertEqual(len(leftover_temp), 0)

        finally:
            backend.analyzer = original_analyzer

    def test_analyze_audio_transcription_failure_handling(self):
        mock_analyzer = MagicMock()
        mock_analyzer.get_final_analysis.return_value = {"error": "Failed to transcribe audio."}

        original_analyzer = backend.analyzer
        backend.analyzer = mock_analyzer

        try:
            response = self.client.post(
                "/analyze_audio/",
                files={"file": ("corrupt.wav", b"fake audio", "audio/wav")}
            )
            self.assertEqual(response.status_code, 500)
            self.assertIn("Failed to transcribe audio.", response.json()["detail"])

            # Verify temporary file cleanup on failure
            leftover_temp = [f for f in os.listdir(".") if f.startswith("temp_") and f.endswith(".wav")]
            self.assertEqual(len(leftover_temp), 0)

        finally:
            backend.analyzer = original_analyzer

    def test_communication_analyzer_scoring_formula(self):
        # Test the scoring weights in _generate_final_report without calling network APIs
        with patch.object(CommunicationAnalyzer, '__init__', lambda self, gemini_api_key: None):
            analyzer = CommunicationAnalyzer(gemini_api_key="fake_key")
            
            text = "I developed machine learning systems with scalable infrastructure."
            text_analysis = {
                "vocabulary_rating": 8.0,
                "filler_words_count": 1, # fumble_score = 10 - (1*2) = 8.0
                "filler_words_list": ["um"],
                "feedback": "Articulate response."
            }
            prosody = {
                "speaking_rate_wpm": 150, # optimal 130-170 -> 10.0
                "jitter_percent": 0.2 # 10 - (0.2*10) = 8.0
            }

            # Expected: (8*0.3) + (8*0.3) + (10*0.2) + (8*0.2) = 2.4 + 2.4 + 2.0 + 1.6 = 8.4
            report = analyzer._generate_final_report(text, text_analysis, prosody)

            self.assertEqual(report["final_communication_score"], "8.4 / 10.0")
            self.assertEqual(report["transcribed_text"], text)
            metrics = {m["metric"]: m["score"] for m in report["detailed_scores"]}
            self.assertEqual(metrics["Vocabulary"], "8.0/10")
            self.assertEqual(metrics["Fumbling"], "8.0/10")
            self.assertEqual(metrics["Articulation (Pace)"], "10.0/10")
            self.assertEqual(metrics["Vocal Jitter (Nervousness)"], "8.0/10")


if __name__ == "__main__":
    unittest.main()
