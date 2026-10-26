import os
import sys
import json
import numpy as np
import whisper  # For Speech-to-Text
import parselmouth  # For audio prosody (nervousness, articulation)
import soundfile as sf  # To read audio files
from io import BytesIO
import time
from typing import Optional, Dict, Any

from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError

# Note: This file no longer contains the Colab-specific 'record_audio' function.
# That logic will now live in the HTML frontend.

class CommunicationAnalyzer:
    """
    Analyzes a voice recording for communication skills.

    Pipeline:
    1. Clean/Convert audio (Whisper)
    2. Transcribe audio to text (Whisper)
    3. Analyze text for vocabulary and fumbling (Gemini via google-genai)
    4. Analyze audio for nervousness and articulation (Parselmouth)
    5. Combine scores into a final rating.
    """

    def __init__(self, gemini_api_key=None):
        """
        Initializes the analyzer with the Gemini API key and loads the
        Whisper model.
        """
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        print("Loading Whisper STT model (base.en)... This may take a moment.")
        try:
            self.whisper_model = whisper.load_model("base.en")
            print("Whisper model loaded.")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            print("Please ensure you have an internet connection to download the model.")
            raise RuntimeError("Whisper model could not be loaded.") from e

        print("Initializing Gemini text analysis client...")
        try:
            self.client = genai.Client(api_key=self.api_key)
            print("Gemini client initialized.")
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
            raise RuntimeError(f"Gemini client initialization failed: {e}") from e

    def _clean_audio(self, audio_path):
        """
        Loads any audio format (e.g., .webm) using Whisper's robust loader
        and saves it as a 'clean' .wav file that Parselmouth can read.
        """
        print(f"Loading and converting {audio_path} to a clean WAV format...")
        try:
            # 1. Load audio using Whisper's robust FFmpeg-backed loader
            # This handles .webm, .mp4, .mp3, etc.
            audio = whisper.load_audio(audio_path)

            # 2. Get the base name
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            clean_wav_path = f"clean_{base_name}.wav"

            # 3. Resample to 16kHz (standard for STT) and save as 16-bit PCM WAV
            # whisper.audio.SAMPLE_RATE is 16000
            sf.write(clean_wav_path, audio, whisper.audio.SAMPLE_RATE, subtype='PCM_16')

            print(f"Clean audio saved to {clean_wav_path}")
            return clean_wav_path

        except Exception as e:
            print(f"Error during audio cleaning with ffmpeg/whisper: {e}")
            try:
                # Direct soundfile fallback for standard WAV files
                audio_data, sr = sf.read(audio_path)
                if len(audio_data.shape) > 1:
                    audio_data = audio_data.mean(axis=1)
                base_name = os.path.splitext(os.path.basename(audio_path))[0]
                clean_wav_path = f"clean_{base_name}.wav"
                sf.write(clean_wav_path, audio_data, sr, subtype='PCM_16')
                print(f"Clean audio saved via soundfile fallback to {clean_wav_path}")
                return clean_wav_path
            except Exception as sf_err:
                print(f"Soundfile fallback also failed: {sf_err}")
                return None

    def transcribe_audio(self, audio_path):
        """
        Transcribes the audio file to text using Whisper.

        --- FIX ---
        This function no longer uses soundfile.read() and only returns
        the transcribed text.

        Returns:
            str: The transcribed text.
        """
        print(f"Transcribing audio from: {audio_path}...")
        try:
            # Transcribe
            # Whisper's transcribe function can handle .webm files directly
            result = self.whisper_model.transcribe(audio_path)
            text = result["text"].strip()

            print("Transcription complete.")
            return text
        except Exception as e:
            print(f"Error during transcription: {e}")
            # This will include the "Format not recognised" error if sf.read was still here
            return None

    def analyze_text(self, text):
        """
        Analyzes the transcribed text for vocabulary and fumbling
        using the Gemini API via the official google-genai SDK.
        """
        print("Analyzing text for vocabulary and fumbling...")
        if not text or not text.strip():
            print("Warning: No text to analyze.")
            return {
                "vocabulary_rating": 0.0,
                "filler_words_count": 0,
                "filler_words_list": [],
                "feedback": "No speech detected in audio."
            }

        prompt = f"""
        You are a professional speech coach. Analyze the following text transcribed
        from a short speech. Evaluate it *only* for vocabulary and fumbling.

        - "vocabulary_rating": Rate the richness and appropriateness of the vocabulary on a scale of 1 to 10.
        - "filler_words_count": Count *all* instances of filler words (e.g., "um", "ah", "like", "you know", "basically", "actually").
        - "filler_words_list": Provide a list of the filler words you found.
        - "feedback": Give 1-2 sentences of constructive feedback.

        TEXT TO ANALYZE:
        ---
        {text}
        ---
        """

        json_schema = {
            "type": "OBJECT",
            "properties": {
                "vocabulary_rating": {
                    "type": "NUMBER",
                    "description": "A score from 1 (basic) to 10 (highly advanced) based on word choice."
                },
                "filler_words_count": {
                    "type": "NUMBER",
                    "description": "The total count of filler words like 'um', 'ah', 'like', 'you know', etc."
                },
                "filler_words_list": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "A list of the filler words found in the text."
                },
                "feedback": {
                    "type": "STRING",
                    "description": "A 1-2 sentence constructive feedback on the vocabulary and fumbling."
                }
            },
            "required": ["vocabulary_rating", "filler_words_count", "filler_words_list", "feedback"]
        }

        primary_model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        candidates = [primary_model, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3-flash-preview"]
        models_to_try = list(dict.fromkeys(candidates))

        last_error = None
        for model_name in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=json_schema,
                        temperature=0.2,
                    )
                )
                raw_text = response.text if hasattr(response, "text") and response.text else ""
                if not raw_text and hasattr(response, "parts") and response.parts:
                    raw_text = response.parts[0].text

                parsed = json.loads(raw_text)
                if not isinstance(parsed, dict):
                    raise ValueError("Model response was not a valid JSON object.")

                vocab = float(parsed.get("vocabulary_rating", 5.0))
                vocab = max(0.0, min(10.0, vocab))
                fumbles = int(parsed.get("filler_words_count", 0))
                fumbles = max(0, fumbles)
                filler_list = parsed.get("filler_words_list", [])
                if not isinstance(filler_list, list):
                    filler_list = []
                feedback = str(parsed.get("feedback", "")).strip() or "Constructive response recorded."

                print(f"Text analysis complete using model '{model_name}'.")
                return {
                    "vocabulary_rating": vocab,
                    "filler_words_count": fumbles,
                    "filler_words_list": filler_list,
                    "feedback": feedback
                }
            except (APIError, ClientError) as api_err:
                code = getattr(api_err, "code", 500)
                msg = getattr(api_err, "message", str(api_err))
                print(f"Gemini API error ({type(api_err).__name__}) with model '{model_name}': [{code}] {msg}")
                last_error = {
                    "error": f"Gemini API error ({code}): {msg}",
                    "status_code": code
                }
                # If rate limited (429) or high demand (503), attempt next model
                if (code in (429, 503) or "demand" in str(msg).lower()) and model_name != models_to_try[-1]:
                    print(f"Notice: Model '{model_name}' returned [{code}]. Attempting fallback model...")
                    continue
                return last_error
            except json.JSONDecodeError as json_err:
                print(f"Failed to parse Gemini response as JSON: {json_err}")
                return {
                    "error": f"Failed to parse Gemini response: {json_err}",
                    "status_code": 502
                }
            except Exception as err:
                print(f"Error during Gemini text analysis: {type(err).__name__}: {err}")
                return {
                    "error": f"Failed to analyze text with Gemini: {type(err).__name__} - {str(err)}",
                    "status_code": 500
                }

        return last_error or {"error": "Failed to analyze text with Gemini.", "status_code": 500}

    def analyze_prosody(self, audio_path, word_count):
        """
        Analyzes the audio file itself for nervousness and articulation
        using the Parselmouth library.
        """
        print("Analyzing audio prosody (nervousness, articulation)...")
        try:
            # Load sound file
            snd = parselmouth.Sound(audio_path)

            # 1. Articulation (Speaking Rate)
            duration = snd.get_total_duration()
            speaking_rate_wpm = 0
            if duration > 0 and word_count > 0:
                speaking_rate_wpm = (word_count / duration) * 60  # Words per minute

            # 2. Nervousness (Jitter and Pitch Variation)
            pitch = snd.to_pitch()

            # Get jitter (local, absolute)
            # This is a common point of failure if speech is not detected.
            jitter = parselmouth.praat.call(pitch, "Get jitter (local)", 0.0, 0.0, 0.0001, 0.02, 1.3) * 100  # As a percentage

            # Get standard deviation of pitch (a measure of monotone vs. varied speech)
            pitch_std_dev = parselmouth.praat.call(pitch, "Get standard deviation", 0, 0, "Hertz")

            print("Audio prosody analysis complete.")
            return {
                "speaking_rate_wpm": speaking_rate_wpm,
                "jitter_percent": jitter,
                "pitch_std_dev_hz": pitch_std_dev,
                "duration_sec": duration
            }

        except Exception as e:
            print(f"Error during prosody analysis: {e}")
            print(f"This can happen with very short or silent audio files. File used: {audio_path}")
            return {
                "speaking_rate_wpm": 0,
                "jitter_percent": 0,
                "pitch_std_dev_hz": 0,
                "duration_sec": 0
            }

    def get_final_analysis(self, audio_path):
        """
        Runs the full pipeline and returns a final, scored analysis.
        """
        print("-" * 50)
        print(f"Starting full analysis for: {audio_path}")

        # --- Step 1: Clean audio for Parselmouth ---
        clean_wav_path = self._clean_audio(audio_path)
        if clean_wav_path is None:
            return {
                "error": "Failed to clean or convert audio file. Ensure ffmpeg is installed or upload a valid audio format.",
                "status_code": 400
            }

        try:
            # --- Step 2: Transcribe ---
            transcribed_text = self.transcribe_audio(clean_wav_path)
            if transcribed_text is None:
                return {
                    "error": "Failed to transcribe audio. Please check microphone or file format.",
                    "status_code": 500
                }

            word_count = len(transcribed_text.split())

            # --- Step 3: Text Analysis ---
            text_analysis = self.analyze_text(transcribed_text)
            if isinstance(text_analysis, dict) and "error" in text_analysis:
                return text_analysis
            if text_analysis is None:
                return {"error": "Failed to analyze text with Gemini.", "status_code": 500}

            # --- Step 4: Audio Prosody Analysis ---
            prosody_analysis = self.analyze_prosody(clean_wav_path, word_count)

            # --- Step 5: Combine and Score ---
            final_report = self._generate_final_report(
                transcribed_text,
                text_analysis,
                prosody_analysis
            )

            print("Full analysis complete.")
            print("-" * 50)
            return final_report
        finally:
            # Clean up temporary clean WAV
            if clean_wav_path and os.path.exists(clean_wav_path):
                try:
                    os.remove(clean_wav_path)
                except Exception as cleanup_err:
                    print(f"Warning: Could not remove clean wav file: {cleanup_err}")

    def _generate_final_report(self, text, text_analysis, prosody):
        """Helper to combine all data into a final report."""

        # --- Scoring (Simple Example) ---
        # Scale all metrics to 0-10

        # 1. Vocabulary Score
        vocab_score = text_analysis.get("vocabulary_rating", 0)

        # 2. Fumbling Score (Inverse score: 0 fumbles = 10 points)
        fumble_count = text_analysis.get("filler_words_count", 0)
        fumble_score = max(0, 10 - (fumble_count * 2)) # 5 fumbles = 0 points

        # 3. Articulation Score (Ideal rate is ~140-160 wpm)
        rate = prosody.get("speaking_rate_wpm", 0)
        articulation_score = 0
        if rate > 0: # Only score if speech was detected
            if 130 <= rate <= 170:
                articulation_score = 10
            elif rate > 170: # Too fast
                articulation_score = max(0, 10 - (rate - 170) / 10)
            else: # Too slow
                articulation_score = max(0, 10 - (130 - rate) / 10)

        # 4. Nervousness Score (Ideal jitter is < 1%)
        jitter = prosody.get("jitter_percent", 0)
        nervousness_score = 0
        if jitter > 0: # Only score if jitter was measurable
            nervousness_score = max(0, 10 - (jitter * 10)) # 1% jitter = 0 points
        elif text and len(text.split()) > 10: # Spoke, but jitter was 0 (good!)
             nervousness_score = 10

        # --- Final Weighted Score ---
        # We'll weight vocabulary and fumbling higher
        final_score = (
            (vocab_score * 0.3) +
            (fumble_score * 0.3) +
            (articulation_score * 0.2) +
            (nervousness_score * 0.2)
        )

        return {
            "final_communication_score": f"{final_score:.1f} / 10.0",
            "transcribed_text": text,
            "detailed_scores": [
                {"metric": "Vocabulary", "score": f"{vocab_score:.1f}/10", "details": text_analysis.get("feedback")},
                {"metric": "Fumbling", "score": f"{fumble_score:.1f}/10", "details": f"Found {fumble_count} filler words: {text_analysis.get('filler_words_list')}"},
                {"metric": "Articulation (Pace)", "score": f"{articulation_score:.1f}/10", "details": f"Your pace was {rate:.0f} WPM. (Ideal: 130-170)"},
                {"metric": "Vocal Jitter (Nervousness)", "score": f"{nervousness_score:.1f}/10", "details": f"Jitter was {jitter:.4f}%. (Ideal: < 0.5%)"}
            ],
            "raw_data": {
                "text_analysis": text_analysis,
                "prosody_analysis": prosody
            }
        }
