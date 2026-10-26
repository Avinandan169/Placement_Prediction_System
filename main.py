# import os
# import requests 
# import json     
# import time
# import psycopg
# from fastapi import FastAPI, Depends, HTTPException, status,Form
# from fastapi import File, UploadFile
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from dotenv import load_dotenv
# from urllib.parse import quote_plus 
# from pydantic import BaseModel, EmailStr
# from passlib.context import CryptContext
# from datetime import datetime, timedelta, timezone
# from jose import JWTError, jwt
# from typing import Annotated, List, Optional, Dict
# from fastapi.middleware.cors import CORSMiddleware

# # 1. Load variables
# load_dotenv()

# # 2. Create App & Add CORS
# app = FastAPI()

# # --- THIS IS THE FIX ---
# # I have added your port 5501 and a wildcard "*"
# origins = [
#     "http://localhost", "http://localhost:8080",
#     "http://127.0.0.1", "http://127.0.0.1:8080",
#     "http://127.0.0.1:5501", # Added your specific port
#     "null",
#     "*" # Added wildcard for easier development
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins, # Use the updated list
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# # ----------------------

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# # --- Pydantic Models ---
# class UserCreate(BaseModel):
#     email: EmailStr
#     password: str
#     role: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     email: str | None = None

# class StudentProfileCreate(BaseModel):
#     full_name: Optional[str] = None
#     course: Optional[str] = None
#     tenth_percentage: Optional[float] = None
#     twelfth_percentage: Optional[float] = None
#     current_year: Optional[int] = None
#     cgpa: Optional[float] = None
#     skills: Optional[List[str]] = None
#     projects: Optional[str] = None
#     achievements: Optional[str] = None
#     linkedin_url: Optional[str] = None

# class QuizSubmission(BaseModel):
#     answers: dict[str, str] 
#     time_spent: dict[str, float] 
#     quiz_data: dict 

# class StudentInfo(BaseModel):
#     id: int
#     full_name: Optional[str] = None
#     email: EmailStr
#     skills: Optional[List[str]] = None
#     star_level: Optional[int] = 0

# class OfficerStudentResponse(BaseModel):
#     students: List[StudentInfo]
#     all_skills: List[str]

# # --- Config and Helper Functions ---
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# db_user = os.getenv('DB_USER')
# db_pass_raw = os.getenv('DB_PASS')
# db_host = os.getenv('DB_HOST')
# db_port = os.getenv('DB_PORT')
# db_name = os.getenv('DB_NAME')
# db_pass_encoded = quote_plus(db_pass_raw)
# DB_URL = (
#     f"postgresql://{db_user}:{db_pass_encoded}"
#     f"@{db_host}:{db_port}/{db_name}"
# )
# print(f"DEBUG: Connecting with URL: {DB_URL}")
# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM")
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# LLM_API_URL = "https://router.huggingface.co/v1/chat/completions"
# LLM_HEADERS = {
#     "Authorization": f"Bearer {os.environ.get('HF_TOKEN')}",
#     "Content-Type": "application/json"
# }

# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.now(timezone.utc) + expires_delta
#     else:
#         expire = datetime.now(timezone.utc) + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# def verify_token(token: str, credentials_exception):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         if email is None:
#             raise credentials_exception
#         token_data = TokenData(email=email)
#         return token_data
#     except JWTError:
#         raise credentials_exception
    
# def get_db_connection():
#     try:
#         with psycopg.connect(DB_URL) as conn:
#             yield conn
#     except psycopg.OperationalError as e:
#         print(f"ERROR: Could not connect to database: {e}")
#         raise HTTPException(status_code=500, detail="Database connection error.")
    
# def get_current_user(
#     token: str = Depends(oauth2_scheme), 
#     db: psycopg.Connection = Depends(get_db_connection)
# ):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     token_data = verify_token(token, credentials_exception)
#     try:
#         with db.cursor() as cur:
#             cur.execute(
#                 "SELECT id, email, role FROM users WHERE email = %s",
#                 (token_data.email,)
#             )
#             user_record = cur.fetchone()
#             if user_record is None:
#                 raise credentials_exception
#             return {
#                 "id": user_record[0],
#                 "email": user_record[1],
#                 "role": user_record[2]
#             }
#     except Exception:
#         raise credentials_exception

# def query_llm_for_quiz(skills_dict: dict):
#     skills_list = []
#     if isinstance(skills_dict, dict):
#         for category, sk_list in skills_dict.items():
#             skills_list.extend(sk_list)
#     else:
#         skills_list = list(skills_dict) 
        
#     if not skills_list:
#         raise HTTPException(status_code=400, detail="No skills to generate quiz.")

#     skills_output = "{" + ", ".join([f'"{skill}"' for skill in skills_list]) + "}"
    
#     prompt = f"""You are an expert curriculum developer and quiz generator. Your sole task is to generate a set of 10 multiple-choice questions (MCQs) based *only* on the provided JSON data of skills.

# **STRICT Output Format Requirement:**
# 1.  **Your entire response must be a single, valid JSON object.**
# 2.  **DO NOT include any text, conversation, explanations, or commentary outside of the JSON object.**
# 3.  The JSON must strictly follow the provided `RESPONSE_JSON_SCHEMA`.

# **RESPONSE_JSON_SCHEMA (Required Output Structure):**
# ```json
# {{
#   "questions": [
#     {{
#       "question": "...",
#       "options": [
#         {{"A": "..."}},
#         {{"B": "..."}},
#         {{"C": "..."}},
#         {{"D": "..."}}
#       ],
#       "correct": "A|B|C|D",
#       "skill": "SkillName",
#       "difficulty": "easy|medium|hard",
#       "Explanation": "Detailed reasoning explaining why the correct option is right and the others are wrong." 
#     }}
#   ]
# }}
# ```
# **Question Requirements:**
# 1.  Generate exactly **10** unique MCQs.
# 2.  Each MCQ must be directly relevant to the content in the `SKILLS_JSON`.
# 3.  The difficulty distribution must be varied:
#     * **3** Easy Questions
#     * **4** Medium Questions
#     * **3** Hard Questions
# 4.  Each question must have exactly four answer options (A, B, C, D), with only one correct option.
# 5. These are the following skills for which you need to generate questions: {skills_output}""" 

#     payload = {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": [{"type": "text", "text": prompt}]
#             }
#         ],
#         "model": "meta-llama/Llama-4-Scout-17B-16E-Instruct:groq"
#     }
    
#     if not os.environ.get('HF_TOKEN'):
#          raise HTTPException(status_code=500, detail="HF_TOKEN environment variable is not set. Cannot call LLM API.")

#     try:
#         response = requests.post(LLM_API_URL, headers=LLM_HEADERS, json=payload, timeout=60)
#         response.raise_for_status() 
#         llm_response_content = response.json()["choices"][0]["message"]["content"]
#         json_string = llm_response_content.strip().replace('```json\n', '').replace('\n```', '')
#         return json.loads(json_string)
#     except Exception as e:
#         print(f"Error in LLM query: {e}")
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred during quiz generation: {e}")

# # --- Original Endpoints ---
# @app.get("/")
# def check_db_connection(db: psycopg.Connection = Depends(get_db_connection)):
#     try:
#         with db.cursor() as cur:
#             cur.execute("SELECT 1")
#             result = cur.fetchone()
#             if result == (1,):
#                 return {"status": "success", "message": "FastAPI is running and connected to PostgreSQL!"}
#             else:
#                 raise HTTPException(status_code=500, detail="Database connection test failed.")
#     except Exception as e:
#         print(f"Database query error: {e}")
#         raise HTTPException(status_code=500, detail=f"Database query error: {e}")

# @app.post("/register")
# def register_user(user_data: UserCreate, db: psycopg.Connection = Depends(get_db_connection)):
#     plain_password = user_data.password
#     if user_data.role not in ['student', 'officer']:
#         raise HTTPException(status_code=400, detail="Invalid role. Must be 'student' or 'officer'.")
#     try:
#         hashed_password = pwd_context.hash(plain_password)
#         with db.cursor() as cur:
#             cur.execute(
#                 "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)",
#                 (user_data.email, hashed_password, user_data.role)
#             )
#             db.commit()
#     except psycopg.IntegrityError:
#         db.rollback()
#         raise HTTPException(status_code=400, detail="Email already registered.")
#     except Exception as e:
#         db.rollback()
#         print(f"ERROR during registration: {e}")
#         raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
#     return {"status": "success", "message": f"User '{user_data.email}' created as a '{user_data.role}'."}

# @app.post("/login", response_model=Token)
# def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: psycopg.Connection = Depends(get_db_connection)):
#     email = form_data.username
#     password = form_data.password
#     try:
#         with db.cursor() as cur:
#             cur.execute(
#                 "SELECT email, password_hash, role FROM users WHERE email = %s",
#                 (email,)
#             )
#             user_record = cur.fetchone()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Database query error: {e}")
#     if not user_record or not pwd_context.verify(password, user_record[1]):
#         raise HTTPException(
#             status_code=401,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     user_email, user_hash, user_role = user_record
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user_email, "role": user_role}, 
#         expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.post("/profile/update")
# def update_student_profile(profile_data: StudentProfileCreate, current_user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db_connection)):
#     if current_user["role"] != 'student':
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can create a profile.")
    
#     user_id = current_user["id"]
#     update_data = profile_data.dict(exclude_unset=True)
#     if not update_data:
#         return {"status": "no_changes", "message": "No data provided to update."}

#     set_query_parts = [f"{key} = %s" for key in update_data.keys()]
#     set_query_string = ", ".join(set_query_parts)
#     sql_values = list(update_data.values())
#     set_query_string += ", last_updated = NOW()"
#     conflict_values = list(update_data.values())
    
#     sql_query = f"""
#     INSERT INTO student_profiles (user_id, {", ".join(update_data.keys())}, last_updated)
#     VALUES (%s, {", ".join(["%s"] * len(sql_values))}, NOW())
#     ON CONFLICT (user_id) DO UPDATE SET
#         {set_query_string};
#     """
    
#     final_sql_values = [user_id] + sql_values + conflict_values
#     try:
#         with db.cursor() as cur:
#             cur.execute(sql_query, final_sql_values)
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         print(f"Error updating profile: {e}")
#         raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
#     return {"status": "success", "message": "Profile updated successfully.", "user_id": user_id}

# @app.post("/generate-quiz")
# async def generate_quiz_endpoint(skills_data: Dict[str, List[str]], current_user: dict = Depends(get_current_user)):
#     if not skills_data:
#         raise HTTPException(status_code=400, detail="No skills data provided.")
#     quiz_data = query_llm_for_quiz(skills_data)
#     return quiz_data

# @app.post("/submit-quiz")
# async def submit_quiz(submission: QuizSubmission, current_user: dict = Depends(get_current_user)):
#     correct_answers = 0
#     total_questions = len(submission.quiz_data.get("questions", []))
#     graded_results = []
#     for i, q in enumerate(submission.quiz_data["questions"]):
#         q_index = str(i) 
#         user_answer = submission.answers.get(q_index)
#         is_correct = (user_answer == q["correct"])
        
#         if is_correct:
#             correct_answers += 1
            
#         graded_results.append({
#             "id": i + 1,
#             "question": q["question"],
#             "correct_answer": q["correct"],
#             "user_answer": user_answer if user_answer else "N/A",
#             "is_correct": is_correct,
#             "time_spent": float(submission.time_spent.get(q_index, 0.0))
#         })
#     final_stats = {
#         "score": f"{correct_answers}/{total_questions}",
#         "percentage": (correct_answers / total_questions) * 100 if total_questions else 0,
#         "total_time_seconds": sum(float(t) for t in submission.time_spent.values()),
#         "individual_results": graded_results
#     }
#     return final_stats

# @app.get("/officer/get-students", response_model=OfficerStudentResponse)
# def get_all_students(
#     current_user: dict = Depends(get_current_user),
#     db: psycopg.Connection = Depends(get_db_connection)
# ):
#     if current_user["role"] != 'officer':
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You do not have permission to access this resource."
#         )
#     students_list = []
#     all_skills = []
#     try:
#         with db.cursor() as cur:
#             cur.execute(
#                 """
#                 SELECT 
#                     u.id, 
#                     u.email, 
#                     sp.full_name, 
#                     sp.skills,
#                     sp.star_level
#                 FROM users u
#                 LEFT JOIN student_profiles sp ON u.id = sp.user_id
#                 WHERE u.role = 'student'
#                 ORDER BY sp.star_level DESC, sp.full_name;
#                 """
#             )
#             records = cur.fetchall()
#             for row in records:
#                 students_list.append(
#                     StudentInfo(
#                         id=row[0],
#                         email=row[1],
#                         full_name=row[2],
#                         skills=row[3],
#                         star_level=row[4]
#                     )
#                 )
            
#             cur.execute(
#                 """
#                 SELECT DISTINCT unnest(skills)
#                 FROM student_profiles
#                 WHERE skills IS NOT NULL;
#                 """
#             )
#             skill_records = cur.fetchall()
#             all_skills = sorted([row[0] for row in skill_records])
            
#     except Exception as e:
#         print(f"Error fetching students: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"An error occurred while fetching student data: {e}"
#         )
    
#     return OfficerStudentResponse(students=students_list, all_skills=all_skills)




import os
import requests 
import json     
import time
import threading
import psycopg
from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi import File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from urllib.parse import quote_plus 
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Annotated, List, Optional, Dict
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from google.genai.errors import APIError

# ML Pipeline and AI Soft Computing modules
from ml_pipeline.dataset_manager import DatasetManager
from ml_pipeline.eda import EDAService
from ml_pipeline.training import ModelTrainingService
from ml_pipeline.prediction import PredictionService
from ml_pipeline.explainability import ExplainabilityService
from ai_soft_computing.fuzzy_readiness import FuzzyPlacementReadinessSystem
from ai_soft_computing.astar_planner import AStarSkillPlanner

# 1. Load variables
load_dotenv()

# 2. Create App & Add CORS
app = FastAPI()
origins = [
    "http://localhost", "http://localhost:8080",
    "http://127.0.0.1", "http://127.0.0.1:8080", 
    "http://127.0.0.1:5501", 
    "null",
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# --- Pydantic Models ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class StudentProfileCreate(BaseModel):
    full_name: Optional[str] = None
    course: Optional[str] = None
    tenth_percentage: Optional[float] = None
    twelfth_percentage: Optional[float] = None
    current_year: Optional[int] = None
    cgpa: Optional[float] = None
    skills: Optional[List[str]] = None
    projects: Optional[str] = None
    achievements: Optional[str] = None
    linkedin_url: Optional[str] = None

class QuizSubmission(BaseModel):
    answers: dict[str, str] 
    time_spent: dict[str, float] 
    quiz_data: dict 

class StudentInfo(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: EmailStr
    skills: Optional[List[str]] = None
    star_level: Optional[int] = 0

class OfficerStudentResponse(BaseModel):
    students: List[StudentInfo]
    all_skills: List[str]

# --- NEW: Pydantic Model for Chat ---
class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

# --- Pydantic Models for Predictive Analytics & AI (CSE3141 / CSE3121) ---
class PredictionInput(BaseModel):
    CGPA: float
    Internships: int = 0
    Projects: int = 1
    Workshops: Optional[int] = None
    Workshops_Certifications: Optional[int] = None
    AptitudeTestScore: float = 75.0
    SoftSkillsRating: float = 4.0
    ExtracurricularActivities: str = "Yes"
    PlacementTraining: str = "Yes"
    SSC_Marks: float = 75.0
    HSC_Marks: float = 75.0
    student_name: Optional[str] = None

class FuzzyReadinessInput(BaseModel):
    cgpa: float
    aptitude: float
    soft_skills: float
    projects: int = 1
    internships: int = 0

class AStarPlanInput(BaseModel):
    target_role: str
    current_skills: List[str] = []

# --- Config and Helper Functions ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Validate required environment variables early
required_env_vars = [
    'DB_USER', 'DB_PASS', 'DB_HOST', 'DB_PORT', 'DB_NAME',
    'SECRET_KEY', 'ALGORITHM', 'ACCESS_TOKEN_EXPIRE_MINUTES'
]
missing_env = [var for var in required_env_vars if not os.getenv(var)]
if missing_env:
    raise RuntimeError(
        f"Missing required environment variable(s): {', '.join(missing_env)}. "
        f"Please configure them in your local .env file (see .env.example)."
    )

db_user = os.getenv('DB_USER')
db_pass_raw = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_pass_encoded = quote_plus(db_pass_raw) if db_pass_raw else ""
DB_URL = (
    f"postgresql://{db_user}:{db_pass_encoded}"
    f"@{db_host}:{db_port}/{db_name}"
)
# Redacted database target log to prevent password exposure
print(f"INFO: Database target configured for {db_user}@{db_host}:{db_port}/{db_name}")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
except ValueError:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be a valid integer.")

# Note: Legacy Hugging Face inference configuration has been removed.
# Quiz generation and career chat are now powered by Google Gemini API.

# --- Helper Functions (Original) ---
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
        return token_data
    except JWTError:
        raise credentials_exception
    
def get_db_connection():
    try:
        with psycopg.connect(DB_URL) as conn:
            yield conn
    except psycopg.OperationalError as e:
        print(f"ERROR: Could not connect to database: {e}")
        raise HTTPException(status_code=500, detail="Database connection error.")
    
def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: psycopg.Connection = Depends(get_db_connection)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token, credentials_exception)
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT id, email, role FROM users WHERE email = %s",
                (token_data.email,)
            )
            user_record = cur.fetchone()
            if user_record is None:
                raise credentials_exception
            return {
                "id": user_record[0],
                "email": user_record[1],
                "role": user_record[2]
            }
    except Exception:
        raise credentials_exception

def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional), 
    db: psycopg.Connection = Depends(get_db_connection)
) -> Optional[dict]:
    """Returns the authenticated user dict if valid token provided; None otherwise."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return None
        with db.cursor() as cur:
            cur.execute("SELECT id, email, role FROM users WHERE email = %s", (email,))
            user_record = cur.fetchone()
            if user_record:
                return {"id": user_record[0], "email": user_record[1], "role": user_record[2]}
    except Exception:
        return None
    return None

# --- LLM Helper Function (For Quiz using Google Gemini API) ---
def query_llm_for_quiz(skills_dict: dict):
    """Generates a technical quiz using Google Gemini API based on student's skills."""
    skills_list = []
    if isinstance(skills_dict, dict):
        for category, sk_list in skills_dict.items():
            if isinstance(sk_list, list):
                skills_list.extend(sk_list)
            elif isinstance(sk_list, str):
                skills_list.append(sk_list)
    elif isinstance(skills_dict, list):
        skills_list = list(skills_dict) 

    # Filter out empty or whitespace-only skills
    skills_list = [s.strip() for s in skills_list if isinstance(s, str) and s.strip()]
    if not skills_list:
        raise HTTPException(status_code=400, detail="No skills to generate quiz.")

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY environment variable is not set. Cannot call Gemini API."
        )

    skills_output = ", ".join(f'"{skill}"' for skill in skills_list)
    system_instruction = (
        "You are an expert curriculum developer and technical quiz generator. "
        "Your task is to generate a set of 10 multiple-choice questions (MCQs) "
        "strictly based on the user's provided technical skills. "
        "Always respond with a single valid JSON object matching the requested schema. "
        "Do not include Markdown code fences, conversational remarks, or text outside the JSON object."
    )

    prompt = f"""Generate a technical quiz of 10 multiple-choice questions based ONLY on these skills: [{skills_output}].

Requirements:
1. Generate exactly 10 unique MCQs.
2. Difficulty distribution: 3 easy questions, 4 medium questions, and 3 hard questions.
3. Every question must have exactly four options labeled A, B, C, and D, with only one correct option.
4. Output must strictly conform to this JSON schema:
{{
  "questions": [
    {{
      "question": "Question text here",
      "options": [
        {{"A": "First option text"}},
        {{"B": "Second option text"}},
        {{"C": "Third option text"}},
        {{"D": "Fourth option text"}}
      ],
      "correct": "A",
      "skill": "Relevant skill name",
      "difficulty": "easy",
      "Explanation": "Detailed explanation of why the correct option is right."
    }}
  ]
}}
"""

    try:
        client = genai.Client(api_key=gemini_api_key)
        max_retries = 2
        last_api_error = None
        data = None

        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.7,
                    )
                )
                if not response.text:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Empty response received from AI model."
                    )

                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

                data = json.loads(raw_text)
                break
            except APIError as e:
                last_api_error = e
                error_code = getattr(e, 'code', None)
                # Automatically retry transient capacity / rate limit issues
                if attempt < max_retries and (error_code in {429, 500, 503} or "RESOURCE_EXHAUSTED" in str(e) or "UNAVAILABLE" in str(e)):
                    time.sleep(1.0 * (attempt + 1))
                    continue
                
                if error_code == 429 or "RESOURCE_EXHAUSTED" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="AI service rate limit or quota exceeded. Please wait a moment and try again."
                    )
                print(f"Gemini API Error in quiz generation: {type(e).__name__} (code: {error_code})")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="An error occurred while communicating with the AI service for quiz generation."
                )

        if not isinstance(data, dict) or "questions" not in data or not isinstance(data["questions"], list):
            raise ValueError("Quiz response missing valid 'questions' array.")

        if len(data["questions"]) != 10:
            raise ValueError(f"Quiz must contain exactly 10 questions, received {len(data['questions'])}.")

        normalized_questions = []
        for idx, q in enumerate(data["questions"]):
            if not isinstance(q, dict):
                raise ValueError(f"Question at index {idx} must be a dictionary.")

            # 1. Validate question text
            question_text = q.get("question")
            if not isinstance(question_text, str) or not question_text.strip():
                raise ValueError(f"Question at index {idx} has missing or blank 'question' text.")

            # 2. Validate skill
            skill_text = q.get("skill")
            if not isinstance(skill_text, str) or not skill_text.strip():
                raise ValueError(f"Question at index {idx} has missing or blank 'skill'.")

            # 3. Validate Explanation
            explanation_text = q.get("Explanation")
            if not explanation_text:
                explanation_text = q.get("explanation")
            if not isinstance(explanation_text, str) or not explanation_text.strip():
                raise ValueError(f"Question at index {idx} has missing or blank 'Explanation'.")

            # 4. Validate and normalize difficulty (easy, medium, hard)
            raw_diff = q.get("difficulty")
            if not isinstance(raw_diff, str) or raw_diff.strip().lower() not in {"easy", "medium", "hard"}:
                raise ValueError(f"Question at index {idx} has invalid difficulty: '{raw_diff}'. Must be easy, medium, or hard.")
            normalized_difficulty = raw_diff.strip().lower()

            # 5. Validate options (must have exactly 4 non-empty options with keys A, B, C, D)
            raw_options = q.get("options")
            option_dict = {}

            if isinstance(raw_options, list):
                if len(raw_options) != 4:
                    raise ValueError(f"Question at index {idx} must have exactly 4 options, found {len(raw_options)}.")

                if all(isinstance(opt, dict) for opt in raw_options):
                    for opt in raw_options:
                        if len(opt) != 1:
                            raise ValueError(f"Question at index {idx} has malformed option entry: {opt}.")
                        k, v = next(iter(opt.items()))
                        k_upper = str(k).strip().upper()
                        if k_upper in option_dict:
                            raise ValueError(f"Question at index {idx} has duplicate option label '{k_upper}'.")
                        if not isinstance(v, str) or not v.strip():
                            raise ValueError(f"Question at index {idx} has blank text for option '{k_upper}'.")
                        option_dict[k_upper] = v.strip()
                elif all(isinstance(opt, str) for opt in raw_options):
                    keys = ["A", "B", "C", "D"]
                    for i, opt_text in enumerate(raw_options):
                        if not opt_text.strip():
                            raise ValueError(f"Question at index {idx} has blank text for option '{keys[i]}'.")
                        option_dict[keys[i]] = opt_text.strip()
                else:
                    raise ValueError(f"Invalid options format in question {idx}.")

            elif isinstance(raw_options, dict):
                if len(raw_options) != 4:
                    raise ValueError(f"Question at index {idx} must have exactly 4 options, found {len(raw_options)}.")
                for k, v in raw_options.items():
                    k_upper = str(k).strip().upper()
                    if not isinstance(v, str) or not v.strip():
                        raise ValueError(f"Question at index {idx} has blank text for option '{k_upper}'.")
                    option_dict[k_upper] = v.strip()
            else:
                raise ValueError(f"Options for question at index {idx} must be a list or dict.")

            if set(option_dict.keys()) != {"A", "B", "C", "D"}:
                raise ValueError(
                    f"Question at index {idx} options must have unique labels A, B, C, and D. Found: {sorted(list(option_dict.keys()))}."
                )

            normalized_options = [
                {"A": option_dict["A"]},
                {"B": option_dict["B"]},
                {"C": option_dict["C"]},
                {"D": option_dict["D"]}
            ]

            # 6. Validate correct answer (must match A, B, C, or D, or the full text of an option)
            raw_correct = q.get("correct")
            if not raw_correct or not isinstance(raw_correct, str):
                raise ValueError(f"Question at index {idx} is missing a valid 'correct' answer key.")

            correct_key = raw_correct.strip().upper()
            if correct_key in {"A", "B", "C", "D"}:
                validated_correct = correct_key
            else:
                # If model returned option text instead of label, resolve it
                matched_key = None
                for k in ["A", "B", "C", "D"]:
                    if option_dict[k].lower() == raw_correct.strip().lower():
                        matched_key = k
                        break
                if matched_key:
                    validated_correct = matched_key
                else:
                    raise ValueError(
                        f"Question at index {idx} has invalid correct answer '{raw_correct}' not matching any option."
                    )

            normalized_questions.append({
                "question": question_text.strip(),
                "options": normalized_options,
                "correct": validated_correct,
                "skill": skill_text.strip(),
                "difficulty": normalized_difficulty,
                "Explanation": explanation_text.strip()
            })

        return {"questions": normalized_questions}

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Failed to parse quiz response from AI: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned invalid or malformed quiz data. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in quiz generation: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during quiz generation."
        )


# --- NEW: LLM Helper Function (For Chatbot using Google Gemini API) ---
def query_llm_for_chat(user_message: str, chat_history: List, user_context: str):
    """Contacts Google Gemini API for a conversational career assistant response."""
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY environment variable is not set. Cannot call Gemini API."
        )

    system_prompt = f"""You are 'Placements AI', a helpful and encouraging career assistant.
You are talking to a student. Here is their profile information from our database:
---
{user_context}
---
Your rules:
1.  **Use the context:** If the user asks about themselves (e.g., "what are my skills?", "what projects do I have?"), answer using the profile information provided.
2.  **Be conversational:** Be friendly and supportive, not just a robot.
3.  **Answer general questions:** If the question is not about their profile (e.g., "what is Python?", "how do I prepare for an interview?"), answer it as a general expert.
4.  **Be concise:** Keep your answers helpful and to the point.
"""

    contents: List[types.Content] = []
    for msg in chat_history:
        # Map user to "user" and assistant to "model" for Gemini API
        role = "user" if msg.role == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.content)]
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)]
        )
    )

    try:
        client = genai.Client(api_key=gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            )
        )
        if not response.text:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Empty response received from AI model."
            )
        return response.text

    except APIError as e:
        error_code = getattr(e, 'code', None)
        if error_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service rate limit or quota exceeded. Please wait a moment and try again."
            )
        print(f"Gemini API Error: {type(e).__name__} (code: {error_code})")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="An error occurred while communicating with the AI service."
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in Gemini chat query: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during chat."
        )


# --- Original Endpoints ---
@app.get("/")
def check_db_connection(db: psycopg.Connection = Depends(get_db_connection)):
    try:
        with db.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            if result == (1,):
                return {"status": "success", "message": "FastAPI is running and connected to PostgreSQL!"}
            else:
                raise HTTPException(status_code=500, detail="Database connection test failed.")
    except Exception as e:
        print(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")

@app.post("/register")
def register_user(user_data: UserCreate, db: psycopg.Connection = Depends(get_db_connection)):
    plain_password = user_data.password
    if user_data.role not in ['student', 'officer']:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'student' or 'officer'.")
    try:
        hashed_password = pwd_context.hash(plain_password)
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)",
                (user_data.email, hashed_password, user_data.role)
            )
            db.commit()
    except psycopg.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered.")
    except Exception as e:
        db.rollback()
        print(f"ERROR during registration: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    return {"status": "success", "message": f"User '{user_data.email}' created as a '{user_data.role}'."}

@app.post("/login", response_model=Token)
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: psycopg.Connection = Depends(get_db_connection)):
    email = form_data.username
    password = form_data.password
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT email, password_hash, role FROM users WHERE email = %s",
                (email,)
            )
            user_record = cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    if not user_record or not pwd_context.verify(password, user_record[1]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_email, user_hash, user_role = user_record
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_email, "role": user_role}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile/me")
@app.get("/profile")
def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db_connection)
):
    """
    Fetches the profile of the currently authenticated user.
    Strictly scoped to current_user['id'] derived from the verified JWT.
    Client-supplied parameters or queries are never used to look up profiles.
    """
    user_id = current_user["id"]
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    sp.id,
                    u.id AS user_id,
                    u.email,
                    u.role,
                    sp.full_name,
                    sp.course,
                    sp.tenth_percentage,
                    sp.twelfth_percentage,
                    sp.current_year,
                    sp.cgpa,
                    sp.skills,
                    sp.projects,
                    sp.achievements,
                    sp.linkedin_url,
                    sp.star_level
                FROM users u
                LEFT JOIN student_profiles sp ON u.id = sp.user_id
                WHERE u.id = %s;
                """,
                (user_id,)
            )
            row = cur.fetchone()
            if not row or row[0] is None:
                # User exists in 'users' table, but has not completed student_profiles row yet
                return {
                    "id": None,
                    "user_id": user_id,
                    "email": current_user["email"],
                    "role": current_user.get("role", "student"),
                    "profile_completed": False,
                    "full_name": None,
                    "course": None,
                    "tenth_percentage": None,
                    "twelfth_percentage": None,
                    "current_year": None,
                    "cgpa": None,
                    "skills": None,
                    "projects": None,
                    "achievements": None,
                    "linkedin_url": None,
                    "star_level": 0
                }

            return {
                "id": row[0],
                "user_id": row[1],
                "email": row[2],
                "role": row[3],
                "profile_completed": True,
                "full_name": row[4],
                "course": row[5],
                "tenth_percentage": float(row[6]) if row[6] is not None else None,
                "twelfth_percentage": float(row[7]) if row[7] is not None else None,
                "current_year": row[8],
                "cgpa": float(row[9]) if row[9] is not None else None,
                "skills": row[10],
                "projects": row[11],
                "achievements": row[12],
                "linkedin_url": row[13],
                "star_level": row[14] or 0
            }
    except Exception as e:
        print(f"Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.post("/profile/update")
def update_student_profile(profile_data: StudentProfileCreate, current_user: dict = Depends(get_current_user), db: psycopg.Connection = Depends(get_db_connection)):
    if current_user["role"] != 'student':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can create a profile.")
    
    user_id = current_user["id"]
    update_data = profile_data.dict(exclude_unset=True)
    if not update_data:
        return {"status": "no_changes", "message": "No data provided to update."}

    set_query_parts = [f"{key} = %s" for key in update_data.keys()]
    set_query_string = ", ".join(set_query_parts)
    sql_values = list(update_data.values())
    set_query_string += ", last_updated = NOW()"
    conflict_values = list(update_data.values())
    
    sql_query = f"""
    INSERT INTO student_profiles (user_id, {", ".join(update_data.keys())}, last_updated)
    VALUES (%s, {", ".join(["%s"] * len(sql_values))}, NOW())
    ON CONFLICT (user_id) DO UPDATE SET
        {set_query_string};
    """
    
    final_sql_values = [user_id] + sql_values + conflict_values
    try:
        with db.cursor() as cur:
            cur.execute(sql_query, final_sql_values)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    return {"status": "success", "message": "Profile updated successfully.", "user_id": user_id}

@app.post("/generate-quiz")
async def generate_quiz_endpoint(skills_data: Dict[str, List[str]], current_user: dict = Depends(get_current_user)):
    if not skills_data:
        raise HTTPException(status_code=400, detail="No skills data provided.")
    quiz_data = query_llm_for_quiz(skills_data)
    return quiz_data

@app.post("/submit-quiz")
async def submit_quiz(submission: QuizSubmission, current_user: dict = Depends(get_current_user)):
    correct_answers = 0
    total_questions = len(submission.quiz_data.get("questions", []))
    graded_results = []
    for i, q in enumerate(submission.quiz_data["questions"]):
        q_index = str(i) 
        user_answer = submission.answers.get(q_index)
        is_correct = (user_answer == q["correct"])
        
        if is_correct:
            correct_answers += 1
            
        graded_results.append({
            "id": i + 1,
            "question": q["question"],
            "correct_answer": q["correct"],
            "user_answer": user_answer if user_answer else "N/A",
            "is_correct": is_correct,
            "time_spent": float(submission.time_spent.get(q_index, 0.0))
        })
    final_stats = {
        "score": f"{correct_answers}/{total_questions}",
        "percentage": (correct_answers / total_questions) * 100 if total_questions else 0,
        "total_time_seconds": sum(float(t) for t in submission.time_spent.values()),
        "individual_results": graded_results
    }
    return final_stats

@app.get("/officer/get-students", response_model=OfficerStudentResponse)
def get_all_students(
    current_user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db_connection)
):
    if current_user["role"] != 'officer':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    students_list = []
    all_skills = []
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    u.id, 
                    u.email, 
                    sp.full_name, 
                    sp.skills,
                    sp.star_level
                FROM users u
                LEFT JOIN student_profiles sp ON u.id = sp.user_id
                WHERE u.role = 'student'
                ORDER BY sp.star_level DESC, sp.full_name;
                """
            )
            records = cur.fetchall()
            for row in records:
                students_list.append(
                    StudentInfo(
                        id=row[0],
                        email=row[1],
                        full_name=row[2],
                        skills=row[3],
                        star_level=row[4]
                    )
                )
            
            cur.execute(
                """
                SELECT DISTINCT unnest(skills)
                FROM student_profiles
                WHERE skills IS NOT NULL;
                """
            )
            skill_records = cur.fetchall()
            all_skills = sorted([row[0] for row in skill_records])
            
    except Exception as e:
        print(f"Error fetching students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching student data: {e}"
        )
    
    return OfficerStudentResponse(students=students_list, all_skills=all_skills)


# --- NEW: Chatbot Endpoint ---
@app.post("/chat/ask")
async def chat_with_bot(
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db_connection)
):
    """
    Handles a chat request, fetches user context, 
    and returns a response from the LLM.
    """
    user_id = current_user["id"]
    user_context = "No profile data found for this user."

    # 1. Fetch user profile data from the database
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    u.email, 
                    sp.full_name, 
                    sp.course, 
                    sp.cgpa, 
                    sp.skills,
                    sp.projects,
                    sp.achievements
                FROM users u
                LEFT JOIN student_profiles sp ON u.id = sp.user_id
                WHERE u.id = %s;
                """,
                (user_id,)
            )
            profile_record = cur.fetchone()
            
            if profile_record:
                # Format the data into a clean string for the LLM
                user_context = f"""
                - Name: {profile_record[1]}
                - Email: {profile_record[0]}
                - Course: {profile_record[2]}
                - CGPA: {profile_record[3]}
                - Skills: {', '.join(profile_record[4] if profile_record[4] else [])}
                - Projects: {profile_record[5]}
                - Achievements: {profile_record[6]}
                """
    except Exception as e:
        print(f"Error fetching user context for chat: {e}")
        # We don't stop, we just proceed with no context.
    
    # 2. Call the LLM helper with the user's message and their data
    llm_response = query_llm_for_chat(
        user_message=chat_request.message,
        chat_history=chat_request.history,
        user_context=user_context
    )
    
    return {"response": llm_response}


# =====================================================================
# --- PREDICTIVE ANALYTICS & AI/SOFT COMPUTING EXTENSIONS ---
# (CSE3141: Predictive Analytics & CSE3121: AI & Soft Computing)
# =====================================================================

# Initialize Services
dataset_manager = DatasetManager()
eda_service = EDAService(dataset_manager)
training_service = ModelTrainingService(dataset_manager)
prediction_service = PredictionService()
explainability_service = ExplainabilityService(dataset_manager)
fuzzy_system = FuzzyPlacementReadinessSystem()
astar_planner = AStarSkillPlanner()


# --- 1. Dataset Management Endpoints ---
@app.get("/api/dataset/info")
async def get_dataset_info():
    """Returns metadata, data provenance, and schema of active placement dataset."""
    try:
        return dataset_manager.get_metadata()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dataset/preview")
async def get_dataset_preview(limit: int = 50):
    """Returns preview records and schema types for active placement dataset."""
    try:
        return dataset_manager.get_preview(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dataset/upload")
async def upload_dataset_csv(file: UploadFile = File(...)):
    """
    Accepts student placement CSV upload, validates required schema,
    stores immutable raw copy in data/raw/, and activates it for the ML pipeline.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only standard comma-separated (.csv) files are supported."
        )
    try:
        content = await file.read()
        metadata = dataset_manager.ingest_uploaded_csv(
            file_bytes=content,
            filename=file.filename,
            source_note="Uploaded via Web Workspace"
        )
        return {
            "message": "Dataset successfully uploaded, validated, and activated.",
            "metadata": metadata
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Dataset upload failed: {e}")


@app.post("/api/dataset/reset-default")
async def reset_to_default_dataset():
    """Resets active dataset back to the benchmark Krooz Campus Recruitment dataset."""
    try:
        metadata = dataset_manager.reset_to_default()
        return {
            "message": "Successfully reset active dataset to default Krooz Campus Recruitment benchmark.",
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 2. Exploratory Data Analysis (EDA) Endpoints ---
@app.get("/api/eda/summary")
async def get_eda_summary():
    """
    Returns complete exploratory data analysis for active dataset:
    descriptive statistics, missing values, duplicate detection,
    numeric histograms, categorical frequencies, and correlation matrix.
    """
    try:
        return eda_service.get_full_eda()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EDA calculation failed: {e}")


# --- 3. Model Training & Comparison Endpoints ---
@app.get("/api/model/status")
async def get_training_status():
    """Returns current model training status and progress percentage."""
    return training_service.get_status()


@app.get("/api/model/comparison")
async def get_model_comparison():
    """
    Returns evaluation metrics comparison across Dummy Classifier,
    Logistic Regression, Decision Tree, Random Forest, and Gradient Boosting.
    """
    try:
        return training_service.get_comparison_results()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/model/train")
async def train_models(background: bool = False):
    """
    Triggers model training, 5-fold cross-validation, hyperparameter tuning,
    and persistence across all 5 candidate classification pipelines.
    """
    if background:
        current_status = training_service.get_status()
        if current_status.get("state") == "running":
            return {"message": "Model training is already currently running.", "status": current_status}
        
        thread = threading.Thread(target=training_service.train_and_evaluate_all)
        thread.daemon = True
        thread.start()
        return {"message": "Model training started in background.", "status": training_service.get_status()}
    else:
        try:
            results = training_service.train_and_evaluate_all()
            return {"message": "Model training completed successfully.", "results": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Model training failed: {e}")


# --- 4. Prediction & Prediction History Endpoints ---
@app.post("/api/model/predict")
async def predict_placement(
    input_data: PredictionInput,
    current_user: Optional[dict] = Depends(get_optional_current_user),
    db: psycopg.Connection = Depends(get_db_connection)
):
    """
    Executes binary placement prediction and probability estimation.
    If authenticated, automatically persists prediction audit record to PostgreSQL.
    """
    try:
        # Resolve workshop field alias
        workshops_val = (
            input_data.Workshops
            if input_data.Workshops is not None
            else (input_data.Workshops_Certifications if input_data.Workshops_Certifications is not None else 0)
        )
        student_dict = {
            "CGPA": input_data.CGPA,
            "Internships": input_data.Internships,
            "Projects": input_data.Projects,
            "Workshops/Certifications": workshops_val,
            "AptitudeTestScore": input_data.AptitudeTestScore,
            "SoftSkillsRating": input_data.SoftSkillsRating,
            "ExtracurricularActivities": input_data.ExtracurricularActivities,
            "PlacementTraining": input_data.PlacementTraining,
            "SSC_Marks": input_data.SSC_Marks,
            "HSC_Marks": input_data.HSC_Marks,
        }

        prediction_result = prediction_service.predict(student_dict)

        # If user is authenticated, save record to prediction_history table
        history_id = None
        if current_user:
            try:
                with db.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO prediction_history (
                            user_id, student_name, cgpa, internships, projects, workshops,
                            aptitude_score, soft_skills_rating, extracurriculars, placement_training,
                            ssc_marks, hsc_marks, prediction_result, placement_probability,
                            model_version, feature_contributions
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                        """,
                        (
                            current_user["id"],
                            input_data.student_name or current_user.get("email", "Student"),
                            input_data.CGPA,
                            input_data.Internships,
                            input_data.Projects,
                            workshops_val,
                            input_data.AptitudeTestScore,
                            input_data.SoftSkillsRating,
                            input_data.ExtracurricularActivities,
                            input_data.PlacementTraining,
                            input_data.SSC_Marks,
                            input_data.HSC_Marks,
                            prediction_result["prediction"],
                            prediction_result["placement_probability"],
                            prediction_result["model_used"],
                            json.dumps(prediction_result["feature_contributions"])
                        )
                    )
                    db.commit()
                    row = cur.fetchone()
                    if row:
                        history_id = row[0]
            except Exception as dbe:
                print(f"Notice: Failed to persist prediction history: {dbe}")

        prediction_result["saved_history_id"] = history_id
        return prediction_result

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")


@app.get("/api/history/my")
async def get_my_prediction_history(
    current_user: dict = Depends(get_current_user),
    db: psycopg.Connection = Depends(get_db_connection)
):
    """Retrieves all past placement predictions saved for the authenticated student."""
    user_id = current_user["id"]
    try:
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT id, student_name, cgpa, internships, projects, workshops,
                       aptitude_score, soft_skills_rating, extracurriculars, placement_training,
                       ssc_marks, hsc_marks, prediction_result, placement_probability,
                       model_version, feature_contributions, created_at
                FROM prediction_history
                WHERE user_id = %s
                ORDER BY created_at DESC;
                """,
                (user_id,)
            )
            rows = cur.fetchall()
            history_list = []
            for r in rows:
                fc = r[15]
                if isinstance(fc, str):
                    try:
                        fc = json.loads(fc)
                    except Exception:
                        fc = []
                history_list.append({
                    "id": r[0],
                    "student_name": r[1],
                    "cgpa": float(r[2]) if r[2] is not None else None,
                    "internships": r[3],
                    "projects": r[4],
                    "workshops": r[5],
                    "aptitude_score": float(r[6]) if r[6] is not None else None,
                    "soft_skills_rating": float(r[7]) if r[7] is not None else None,
                    "extracurriculars": r[8],
                    "placement_training": r[9],
                    "ssc_marks": float(r[10]) if r[10] is not None else None,
                    "hsc_marks": float(r[11]) if r[11] is not None else None,
                    "prediction_result": r[12],
                    "placement_probability": float(r[13]) if r[13] is not None else None,
                    "model_version": r[14],
                    "feature_contributions": fc or [],
                    "created_at": r[16].isoformat() if r[16] else None
                })
            return {"history": history_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")


# --- 5. Feature Importance & Explainability Endpoints ---
@app.get("/api/model/explain")
async def get_model_explainability():
    """
    Returns global feature importance, permutation importance,
    and plain-language interpretability insights.
    """
    try:
        return explainability_service.get_global_explanations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 6. Fuzzy Placement Readiness Endpoints (CSE3121) ---
@app.post("/api/fuzzy/evaluate")
async def evaluate_fuzzy_readiness(input_data: FuzzyReadinessInput):
    """
    Mamdani Fuzzy Inference System for Placement Readiness:
    fuzzification, rule evaluation, aggregation, and centroid defuzzification.
    """
    try:
        result = fuzzy_system.evaluate(
            cgpa=input_data.cgpa,
            aptitude=input_data.aptitude,
            soft_skills=input_data.soft_skills,
            projects=input_data.projects,
            internships=input_data.internships
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fuzzy inference failed: {e}")


# --- 7. A* Skill Planner Endpoints (CSE3121) ---
@app.post("/api/astar/plan")
async def generate_astar_skill_plan(input_data: AStarPlanInput):
    """
    A* Heuristic Graph Search for optimal skill development trajectories.
    Uses admissible prerequisite closure heuristic to guarantee shortest learning path.
    """
    try:
        return astar_planner.plan_path(
            current_skills=input_data.current_skills,
            target_role=input_data.target_role
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"A* planning failed: {e}")


@app.get("/api/astar/roles")
async def get_astar_roles():
    """Returns available career roles and required competency sets for A* search."""
    return {"roles": astar_planner.get_available_roles()}


@app.get("/api/astar/all-skills")
async def get_astar_all_skills():
    """Returns all technical skills in the knowledge graph catalog."""
    return {"skills": astar_planner.get_all_skills()}
