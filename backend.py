import os
import sys
import json
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
from typing import List, Dict, Any, Optional
import time
import threading
import certifi
from dotenv import load_dotenv

load_dotenv()
# EasyOCR downloads its model through Python's HTTPS stack. Use the bundled
# Mozilla CA certificates on macOS when the system trust store is unavailable.
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
AI_API_PORT = int(os.getenv("AI_API_PORT", "8001"))
ENABLE_NGROK = os.getenv("ENABLE_NGROK", "").lower() in {"1", "true", "yes"}

# --- Colab/Ngrok specific imports (loaded only when enabled) ---
ngrok = None
conf = None
if ENABLE_NGROK:
    try:
        from pyngrok import ngrok, conf
    except ImportError as e:
        raise RuntimeError("ENABLE_NGROK is set to true, but pyngrok is not installed. Install with: pip install pyngrok") from e

# --- Import AI/ML classes ---
try:
    from job_recommender import JobRecommender
except ImportError as e:
    JobRecommender = None
    print(f"Warning: job_recommender could not be imported: {e}")

try:
    from pypdf import PdfReader
except ImportError as e:
    PdfReader = None
    print(f"Warning: pypdf could not be imported: {e}")

try:
    import easyocr
    from pdf2image import convert_from_path
    import numpy as np
except ImportError as e:
    easyocr = None
    convert_from_path = None
    print(f"Notice: EasyOCR/pdf2image not available. Text-based PDF extraction via pypdf will be used: {e}")

try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError, ClientError
except ImportError as e:
    genai = None
    types = None
    APIError = None
    ClientError = None
    print(f"Warning: google.genai could not be imported: {e}")

try:
    from communication_analyzer import CommunicationAnalyzer
except ImportError as e:
    CommunicationAnalyzer = None
    print(f"Warning: communication_analyzer could not be imported: {e}")


#
# --- 1. API Key and Model Setup ---
#
# --- Read configuration from .env/environment ---
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")

# Configure Gemini Client
gemini_client = None
if GOOGLE_API_KEY and genai is not None:
    try:
        gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"WARNING: Failed to initialize Gemini client: {e}")
else:
    print("WARNING: GEMINI_API_KEY is not configured. Resume analysis will be unavailable.")

# Configure Ngrok only when explicitly enabled.
if ENABLE_NGROK:
   if not NGROK_AUTHTOKEN:
       raise RuntimeError("ENABLE_NGROK is enabled but NGROK_AUTHTOKEN is not configured.")
   conf.get_default().auth_token = NGROK_AUTHTOKEN

# --- Pre-load AI Models (Global State) ---
print("Server is starting... Loading AI models. This may take a moment.")
recommender = None
if JobRecommender is not None:
    try:
        recommender = JobRecommender()
        print("AI models loaded successfully - Job Recommender")
    except Exception as e:
        print(f"WARNING: Job Recommender failed to load: {e}")

ocr_reader = None

def get_ocr_reader():
    global ocr_reader
    if ocr_reader is None and easyocr is not None:
        try:
            print("Initializing EasyOCR... This may take a moment.")
            ocr_reader = easyocr.Reader(['en'])
            print("AI models loaded successfully - EasyOCR")
        except Exception as e:
            print(f"Notice: EasyOCR model initialization failed: {e}")
    return ocr_reader

analyzer = None
if CommunicationAnalyzer is not None and GOOGLE_API_KEY:
    try:
        analyzer = CommunicationAnalyzer(gemini_api_key=GOOGLE_API_KEY)
        print("AI models loaded successfully - Voice Analyzer")
    except Exception as e:
        print(f"WARNING: Voice analysis is unavailable: {e}")


#
# --- 2. Define AI Pipeline Functions (from Resume_OCR.py) ---
#

def detect_document_text(path: str, reader: Optional[Any] = None) -> str:
    """Extract selectable PDF text, falling back to EasyOCR for scanned PDFs."""
    if PdfReader is not None:
        try:
            extracted_pages = [
                page.extract_text() or "" for page in PdfReader(path).pages
            ]
            selectable_text = "\n\n--- END OF PAGE ---\n\n".join(extracted_pages).strip()
            if selectable_text:
                return selectable_text
        except Exception as e:
            print(f"Selectable PDF text extraction failed; trying OCR: {e}")

    active_reader = reader or get_ocr_reader()
    if convert_from_path is None or active_reader is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "This PDF contains no selectable text and OCR requires Poppler and EasyOCR. "
                "Install Poppler with 'brew install poppler' and ensure EasyOCR is installed, then restart backend.py."
            )
        )

    try:
        images = convert_from_path(path)
        if not images:
            raise Exception("PDF is empty or could not be read.")
    except Exception as e:
        print(f"Error converting scanned PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=(
                "This PDF contains no selectable text and OCR requires Poppler. "
                "Install it with 'brew install poppler', then restart backend.py."
            )
        ) from e

    full_text = []
    for i, img in enumerate(images):
        img_np = np.array(img)
        result = active_reader.readtext(img_np, detail=0, paragraph=True)
        full_text.append("\n".join(result))

    return "\n\n--- END OF PAGE ---\n\n".join(full_text)

def parse_resume_to_json(resume_text: str) -> dict:
    """Uses Gemini API to parse raw text into a structured JSON."""

    # --- UPDATED SCHEMA ---
    # This schema includes all the fields your new frontend expects.
    json_schema = {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING", "description": "The full name of the candidate."},
            "contact_info": {
                "type": "OBJECT",
                "properties": {
                    "email": {"type": "STRING"},
                    "phone": {"type": "STRING"},
                    "linkedin": {"type": "STRING", "description": "Full LinkedIn URL, if available."}
                }
            },
            "professional_summary": {"type": "STRING", "description": "A 2-4 sentence summary from the top of the resume."},
            "education": {
                "type": "OBJECT",
                "properties": {
                    "place": {"type": "STRING"},
                    "degree": {"type": "STRING"},
                    "field": {"type": "STRING"},
                    "year": {"type": "STRING"},
                    "cgpa": {"type": "STRING"},
                },
            },
            "skills": {
                "type": "OBJECT",
                "properties": {
                    "Languages": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "Backend": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "Databases": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "DevOps & Tools": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "Machine Learning": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "Generative AI": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "Other": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
            },
            "projects": {
                "type": "ARRAY",
                "description": "An array of project objects.",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Title of the project"},
                        "skills": {"type": "STRING", "description": "Comma-separated string of skills"},
                        "desc": {"type": "STRING", "description": "Description of the project"}
                    },
                    "required": ["title", "skills", "desc"]
                }
            },
            "achievements_and_awards": {
                "type": "ARRAY",
                "description": "A list of achievements, hackathon wins, or awards.",
                "items": {"type": "STRING"}
            },
            "positions_of_responsibility": {
                "type": "ARRAY",
                "description": "A list of positions held, like 'Club Lead' or 'Coordinator'.",
                "items": {"type": "STRING"}
            }
        },
    }

    if not GOOGLE_API_KEY or gemini_client is None:
        raise HTTPException(
            status_code=503,
            detail="Resume analysis is unavailable until GEMINI_API_KEY is configured."
        )

    prompt = f"""
    You are an expert resume parser. Read the following resume text, which was extracted by OCR,
    and parse it *exactly* into the provided JSON schema.

    - Extract all relevant fields.
    - If a field is not present, return a null or empty value for it.
    - Categorize skills into the correct categories. If a skill doesn't fit, place it in "Other".
    - Extract all projects into a JSON array.
    - Extract all achievements and positions of responsibility.
    - The text "--- END OF PAGE ---" indicates a page break in the original PDF.

    RESUME TEXT:
    ---
    {resume_text}
    ---
    """

    primary_model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
    candidates = [primary_model, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3-flash-preview"]
    models_to_try = list(dict.fromkeys(candidates))

    last_error = None
    last_code = 500
    for model_name in models_to_try:
        try:
            print(f"Parsing resume text with Gemini model '{model_name}'...")
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=json_schema,
                    temperature=0.1
                )
            )
            raw_text = response.text if hasattr(response, "text") and response.text else ""
            if not raw_text and hasattr(response, "parts") and response.parts:
                raw_text = response.parts[0].text
            
            parsed_json = json.loads(raw_text)
            print(f"Resume parsed successfully with '{model_name}'.")
            return parsed_json

        except (APIError, ClientError) as api_err:
            code = getattr(api_err, "code", 500)
            msg = getattr(api_err, "message", str(api_err))
            print(f"Gemini API error during resume parsing with '{model_name}': [{code}] {msg}")
            last_error = f"HTTP {code}: {msg}"
            last_code = code
            if model_name != models_to_try[-1] and (code in (429, 503) or "demand" in str(msg).lower()):
                print(f"Notice: Model '{model_name}' returned [{code}]. Attempting fallback model...")
                continue
            if code == 429:
                raise HTTPException(
                    status_code=429,
                    detail=f"Gemini API quota exceeded for resume parsing: {msg}"
                )
            if code == 503 and model_name == models_to_try[-1]:
                raise HTTPException(
                    status_code=503,
                    detail=f"Gemini service temporarily unavailable: {msg}"
                )
            raise HTTPException(
                status_code=code if 400 <= code <= 599 else 500,
                detail=f"Gemini API error during resume parsing: {msg}"
            )
        except json.JSONDecodeError as json_err:
            print(f"Failed to parse Gemini response as JSON: {json_err}")
            last_error = str(json_err)
            last_code = 502
            continue
        except Exception as e:
            print(f"Unexpected error during resume parsing with '{model_name}': {e}")
            last_error = str(e)
            last_code = 500
            continue

    print(f"Failed to parse resume after all models: {last_error}")
    raise HTTPException(status_code=last_code, detail=f"Failed to parse resume with Gemini: {last_error}")


def convert_gemini_to_recommender_format(gemini_data: dict) -> dict:
    """
    Converts the 'projects' array from Gemini into the
    object/dict format that the JobRecommender expects.
    """
    projects_object = {}
    if "projects" in gemini_data and isinstance(gemini_data["projects"], list):
        for i, proj in enumerate(gemini_data["projects"]):
            title = proj.get("title", f"Untitled Project {i+1}")
            if title in projects_object:
                title = f"{title}_{i}"
            projects_object[title] = {
                "skills": proj.get("skills", ""),
                "desc": proj.get("desc", "")
            }

    return {
        "education": gemini_data.get("education", {}),
        "skills": gemini_data.get("skills", {}),
        "projects": projects_object
    }

#
# --- 3. FastAPI App & Endpoints ---
#
app = FastAPI()

# --- Enable CORS ---
# This is the block that was likely causing the error.
# It should be at the top level (no indentation).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Define API Models ---
class SkillGap(BaseModel):
    basic_missing: List[str]
    intermediate_missing: List[str]
    advanced_missing: List[str]

class Recommendation(BaseModel):
    job_profile: str
    match_score: float
    skill_gap: SkillGap

# --- FIX: Renamed class to be unique ---
# This is the response model for the resume endpoint
class ResumeAnalysisResponse(BaseModel):
    message: str
    recommendations: List[Recommendation]
    parsed_data: Dict[str, Any]  # This will hold the full JSON from Gemini

# --- FIX: Renamed class to be unique ---
# This is the response model for the audio endpoint
class AudioAnalysisResponse(BaseModel):
    message: str
    report: Dict[str, Any]


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {
        "resume_analyzer_status": {
            "message": "Resume Analyzer API is running. POST to /analyze_resume/ to upload a PDF."
        },
        "communication_analyzer_status": {
            "message": "Communication Analyzer API is running. POST to /analyze_audio/ to upload an audio file."
        }
    }


# --- FIX: Updated response_model to use the new unique class ---
@app.post("/analyze_resume/", response_model=ResumeAnalysisResponse)
async def analyze_resume(file: UploadFile = File(...)):

    if not GOOGLE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Resume analysis is unavailable until GEMINI_API_KEY is configured."
        )

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    if recommender is None:
        raise HTTPException(
            status_code=503,
            detail="Job recommender is temporarily unavailable."
        )

    safe_name = os.path.basename(file.filename or "resume.pdf")
    temp_pdf_path = f"temp_{int(time.time()*1000)}_{safe_name}"
    try:
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save temporary file: {e}")
    finally:
        file.file.close()

    try:
        # --- Run the Full AI Pipeline ---
        print(f"Processing: {temp_pdf_path}")
        raw_text = detect_document_text(temp_pdf_path, ocr_reader)
        if not raw_text:
            raise HTTPException(status_code=500, detail="OCR failed to extract any text.")

        print("Parsing text with Gemini...")
        gemini_parsed_data = parse_resume_to_json(raw_text)
        if not gemini_parsed_data:
            raise HTTPException(status_code=500, detail="Gemini failed to parse the resume text.")

        # We need this converted data just for the recommender
        structured_data_for_recommender = convert_gemini_to_recommender_format(gemini_parsed_data)

        print("Getting job recommendations...")
        recommendations = recommender.recommend_jobs(
            structured_data_for_recommender["education"],
            structured_data_for_recommender["skills"],
            structured_data_for_recommender["projects"],
            top_k=3
        )

        print("Analysis complete.")

        # --- UPDATED Return ---
        # This return statement is the new, correct one.
        return {
            "message": "Analysis successful!",
            "recommendations": recommendations,
            "parsed_data": gemini_parsed_data  # Send the full, detailed JSON
        }

    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


# --- FIX: Updated response_model to use the new unique class ---
@app.post("/analyze_audio/", response_model=AudioAnalysisResponse)
async def analyze_audio(file: UploadFile = File(...)):

    if analyzer is None:
        raise HTTPException(
            status_code=503,
            detail="Voice analysis is unavailable. Resume analysis is still available."
        )

    # Check if the file is an audio file
    allowed_extensions = ('.wav', '.webm', '.mp3', '.m4a', '.ogg', '.flac')
    is_audio_content = bool(file.content_type and (
        file.content_type.startswith("audio/") or
        file.content_type in ("video/webm", "application/octet-stream")
    ))
    has_audio_ext = any(file.filename.lower().endswith(ext) for ext in allowed_extensions) if file.filename else False

    if not (is_audio_content or has_audio_ext):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file (e.g., .wav, .webm, .mp4).")

    # Save the audio to a temporary file
    safe_name = os.path.basename(file.filename or "response.webm")
    temp_audio_path = f"temp_{int(time.time()*1000)}_{safe_name}"
    try:
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save temporary file: {e}")
    finally:
        file.file.close()

    try:
        # --- Run the Full AI Pipeline ---
        print(f"Processing: {temp_audio_path}")
        report = analyzer.get_final_analysis(temp_audio_path)

        if "error" in report:
            status_code = int(report.get("status_code") or 500)
            raise HTTPException(status_code=status_code, detail=report["error"])

        print("Analysis complete.")
        return {
            "message": "Analysis successful!",
            "report": report
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception as cleanup_err:
                print(f"Warning: Could not remove temporary audio file: {cleanup_err}")

#
# --- 4. Colab/Ngrok Specific Launch Code ---
#
def run_with_ngrok(app):
    """
    Starts the FastAPI server (uvicorn) and creates a
    public URL for it using ngrok.
    """

    # Start ngrok
    print("Starting ngrok tunnel...")
    public_url = None # Initialize public_url
    try:
        public_url = ngrok.connect(AI_API_PORT)
        print("---")
        print(f"✅ Your backend is running at: {public_url}")
        print("---")
        print("Your frontend application (index.html) is configured to use an ngrok URL.")
        print("If the app stops working, you may need to update the URL in index.html to match the one above.")
        print(f"Resume Endpoint: {public_url}/analyze_resume/")
        print(f"Audio Endpoint:  {public_url}/analyze_audio/")
        print("---")

    except Exception as e:
        print(f"Error starting ngrok: {e}")
        print("This may be due to a missing or invalid Authtoken.")
        sys.exit(1)

    # Start uvicorn server in a new thread
    def run_uvicorn():
        uvicorn.run(app, host="127.0.0.1", port=AI_API_PORT, log_level="info")

    uvicorn_thread = threading.Thread(target=run_uvicorn)
    uvicorn_thread.start()

    # Keep the main thread alive (e.g., in Colab)
    try:
        # Keep the Colab cell running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        if public_url:
            ngrok.disconnect(public_url)
        print("Server shut down.")

def run_server():
    if ENABLE_NGROK:
        run_with_ngrok(app)
    else:
        print(f"AI service is running at http://127.0.0.1:{AI_API_PORT}")
        uvicorn.run(app, host="127.0.0.1", port=AI_API_PORT, log_level="info")


if __name__ == "__main__":
    run_server()