# Placement Prediction System

An AI-assisted student placement platform that helps students explore career opportunities, identify skill gaps, improve communication skills, and prepare for technical assessments. Placement officers can review student profiles through a role-based dashboard.

> **Project status:** This repository contains two separate FastAPI-oriented backend services and a static HTML/CSS frontend. Resume and communication-analysis features require additional dependencies and system tools beyond the current `requirements.txt`.

## Features

- Role-based authentication for students and placement officers
- JWT-based authentication and password hashing
- Student profile management
- Education, CGPA, skills, projects, achievements, and LinkedIn tracking
- AI-generated technical quizzes using Google Gemini
- Quiz submission, grading, score calculation, and time tracking
- Gemini-powered career assistant chat
- Resume parsing using OCR and Gemini
- Semantic job recommendations based on student profiles
- Basic, intermediate, and advanced skill-gap analysis
- Communication analysis using speech-to-text and audio-prosody metrics
- Placement officer dashboard for reviewing student data
- Static HTML/CSS/JavaScript frontend pages

## Architecture

The project contains two separate backend flows:

```text
                         ┌──────────────────────────┐
                         │ Static HTML/CSS frontend  │
                         └────────────┬─────────────┘
                                      │
              ┌───────────────────────┴────────────────────────┐
              │                                                │
              ▼                                                ▼
┌──────────────────────────────┐                 ┌──────────────────────────────┐
│ main.py                      │                 │ backend.py                   │
│ Account/profile service      │                 │ Resume/voice analysis service │
│                              │                 │                              │
│ - PostgreSQL                 │                 │ - EasyOCR + Poppler          │
│ - JWT authentication         │                 │ - Gemini resume parsing      │
│ - Student/officer roles      │                 │ - Sentence Transformers      │
│ - Technical quizzes          │                 │ - Whisper transcription      │
│ - Career assistant chat      │                 │ - Parselmouth prosody         │
└──────────────┬───────────────┘                 └──────────────────────────────┘
               │
               ▼
      ┌──────────────────────┐
      │ PostgreSQL database  │
      │ users                 │
      │ student_profiles      │
      └──────────────────────┘
```

`main.py` handles accounts, profiles, quizzes, officer access, and career chat.

`backend.py` is a separate service for resume and audio analysis. It has different dependencies and startup requirements.

## Technology Stack

- **Backend:** Python, FastAPI, Uvicorn
- **Database:** PostgreSQL
- **Authentication:** JWT, `python-jose`, Passlib, Bcrypt
- **Generative AI:** Google Gemini API
- **Semantic matching:** Sentence Transformers and cosine similarity
- **Resume processing:** EasyOCR and `pdf2image`
- **Speech processing:** Whisper, SoundFile, Parselmouth, and FFmpeg
- **Frontend:** HTML, CSS, and JavaScript

## Repository Structure

```text
.
├── main.py                    # Primary FastAPI service
├── backend.py                 # Resume and communication analysis service
├── job_recommender.py         # Job matching and skill-gap analysis
├── communication_analyzer.py  # Voice and communication analysis
├── schema.sql                 # PostgreSQL database schema
├── requirements.txt           # Python dependencies
├── .env.example               # Environment configuration template
├── LOCAL_SETUP.md              # macOS and PostgreSQL setup guide
├── config.js                  # Frontend configuration
├── style.css                  # Shared frontend styles
├── index.html                 # Main frontend page
├── login.html                 # Login page
├── register.html              # Registration page
├── dashboard.html             # Student dashboard
├── profile.html               # Student profile page
├── conversation.html          # Career assistant chat page
├── results.html               # Results page
├── officer-dashboard.html     # Officer dashboard
├── soft-skills.html           # Soft-skills page
├── test.html                  # Frontend testing page
└── tests/                     # Test files
```

## Prerequisites

For the primary backend service:

- Python 3.10 or later
- PostgreSQL
- Google Gemini API key
- Git
- Virtual environment support

For resume and audio analysis, you may also need:

- FFmpeg
- Poppler
- EasyOCR
- `pdf2image`
- Sentence Transformers
- Whisper
- Parselmouth
- SoundFile
- NumPy and other machine-learning dependencies
- Ngrok, if using the Colab/ngrok workflow in `backend.py`

> The current `requirements.txt` does not visibly include every package imported by `backend.py` and `communication_analyzer.py`. Install and verify the additional dependencies before using those features.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Avinandan169/Placement_Prediction_System.git
cd Placement_Prediction_System
```

### 2. Create a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file:

```bash
cp .env.example .env
```

Generate a strong JWT secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Update `.env` with your local configuration.

| Variable | Required | Description |
| --- | --- | --- |
| `DB_USER` | Yes | PostgreSQL username |
| `DB_PASS` | Yes | PostgreSQL password |
| `DB_HOST` | Yes | PostgreSQL host |
| `DB_PORT` | Yes | PostgreSQL port |
| `DB_NAME` | Yes | PostgreSQL database name |
| `SECRET_KEY` | Yes | JWT signing secret |
| `ALGORITHM` | Yes | JWT algorithm, usually `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | JWT token lifetime |
| `GEMINI_API_KEY` | Yes for AI features | Google Gemini API key |

Never commit `.env` or real API keys to the repository.

### 5. Create the PostgreSQL database

Create a dedicated development user and database:

```sql
CREATE USER placement_user WITH PASSWORD 'replace-with-a-strong-password';
CREATE DATABASE placement_db OWNER placement_user;
GRANT ALL PRIVILEGES ON DATABASE placement_db TO placement_user;
```

Initialize the database schema:

```bash
psql -h 127.0.0.1 -U placement_user -d placement_db -f schema.sql
```

The schema creates:

- `users`
- `student_profiles`
- Supporting indexes for email, roles, and profile lookups

For a macOS-specific setup guide, see [`LOCAL_SETUP.md`](LOCAL_SETUP.md).

### 6. Start the primary API

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
```

### 7. Serve the frontend

In another terminal:

```bash
python3 -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500/index.html
```

If the frontend cannot connect to the backend, review the API URL configured in `config.js`.

## Optional Resume and Communication Analysis Service

`backend.py` is separate from `main.py` and provides resume and audio-analysis functionality.

It includes endpoints for:

```text
GET  /
POST /analyze_resume/
POST /analyze_audio/
```

The service performs the following operations:

### Resume analysis

1. Accepts a PDF resume.
2. Converts PDF pages into images.
3. Extracts text using EasyOCR.
4. Uses Gemini to convert resume text into structured JSON.
5. Generates job recommendations.
6. Returns parsed resume information, recommendations, and skill gaps.

### Communication analysis

1. Accepts an audio recording.
2. Converts the audio into a clean WAV file.
3. Transcribes speech using Whisper.
4. Analyzes vocabulary and filler words with Gemini.
5. Measures speaking rate and vocal jitter using Parselmouth.
6. Produces a weighted communication score.

`backend.py` is currently designed around an interactive Colab/ngrok workflow. It asks for Gemini and Ngrok credentials and loads multiple AI models at startup. Review and adapt its launch behavior before using it as a conventional local service.

## API Overview

### Primary service: `main.py`

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `GET` | `/` | Checks API and PostgreSQL connectivity | Public |
| `POST` | `/register` | Creates a student or officer account | Public |
| `POST` | `/login` | Authenticates a user and returns a JWT | Public |
| `POST` | `/profile/update` | Creates or updates a student profile | Authenticated student |
| `POST` | `/generate-quiz` | Generates a technical quiz from submitted skills | Authenticated user |
| `POST` | `/submit-quiz` | Grades quiz responses and returns results | Authenticated user |
| `GET` | `/officer/get-students` | Returns student profiles and skills | Authenticated officer |
| `POST` | `/chat/ask` | Sends a message to the career assistant | Authenticated user |

## Example API Requests

### Register a user

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "use-a-strong-development-password",
    "role": "student"
  }'
```

### Log in

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=student@example.com&password=use-a-strong-development-password"
```

### Update a student profile

```bash
curl -X POST http://127.0.0.1:8000/profile/update \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Example Student",
    "course": "Computer Science",
    "cgpa": 8.5,
    "skills": [
      "Python",
      "FastAPI",
      "PostgreSQL"
    ]
  }'
```

## Testing and Verification

A `tests/` directory is included in the repository. Refer to the test files and project configuration for the appropriate test command.

Basic manual verification:

1. Start PostgreSQL.
2. Apply `schema.sql`.
3. Start the API with Uvicorn.
4. Visit `/` and verify the database health response.
5. Register a development user.
6. Log in and obtain an access token.
7. Update a student profile.
8. Serve the frontend and verify the configured API URL.

## Security Considerations

- Do not commit `.env` files or credentials.
- Replace all example database credentials.
- Generate a strong and unique `SECRET_KEY`.
- Use a least-privileged PostgreSQL user.
- Restrict CORS origins before production deployment.
- Use HTTPS in deployed environments.
- Protect Gemini and Ngrok credentials.
- Apply rate limiting around AI-powered endpoints.
- Treat resumes, profiles, and audio recordings as sensitive personal data.
- Define appropriate data retention and access policies.

## Known Limitations

- Gemini features depend on API availability, network connectivity, and quota.
- AI-generated quizzes, recommendations, and feedback may not always be accurate.
- Local AI models may download during the first run.
- Resume and audio analysis require additional Python packages and system tools.
- The job recommendation catalog is embedded in `job_recommender.py`.
- `main.py` and `backend.py` have different configuration and startup requirements.
- The current CORS settings are intended for development.
- No production deployment configuration is currently documented.

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature or bug-fix branch.
3. Make focused changes.
4. Add or update tests where applicable.
5. Verify the affected functionality locally.
6. Open a pull request with a clear description of the changes.

## License

No license is currently specified in this repository. Add a license file before distributing or reusing the project under defined terms.
