# Local Setup Guide (macOS)

This guide walks you through setting up and running the **AI Placements Predictor** backend and database locally on macOS.

---

## 1. Install & Start PostgreSQL (macOS with Homebrew)

PostgreSQL is required to store user accounts and student profiles.

### Step 1.1: Install PostgreSQL via Homebrew
If you don't have PostgreSQL installed, run:
```bash
brew install postgresql@16
```

### Step 1.2: Start the PostgreSQL Service
```bash
brew services start postgresql@16
```

*(Optional) Ensure `psql` is in your PATH:*
```bash
brew link postgresql@16 --force
```

---

## 2. Configure Dedicated Database & User

Avoid running development applications as the `postgres` superuser. Create a dedicated database and user:

```bash
# 1. Open the PostgreSQL terminal as your default Mac user
psql postgres

# 2. Inside the psql prompt, run:
CREATE USER placement_user WITH PASSWORD 'placement_secure_pass123';
CREATE DATABASE placement_db OWNER placement_user;
GRANT ALL PRIVILEGES ON DATABASE placement_db TO placement_user;

# For PostgreSQL 15+, grant schema usage & privileges:
\c placement_db
GRANT ALL ON SCHEMA public TO placement_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO placement_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO placement_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO placement_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO placement_user;

# 3. Exit psql
\q
```

---

## 3. Initialize Database Tables (`schema.sql`)

Run the provided `schema.sql` script to create the `users`, `student_profiles`, and `prediction_history` tables:

```bash
psql -h 127.0.0.1 -U placement_user -d placement_db -f schema.sql
# Enter password: placement_secure_pass123
```

---

## 4. Environment Configuration (`.env`)

Create your local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Your `.env` file should look like this:
```env
# Database Credentials
DB_USER=placement_user
DB_PASS=placement_secure_pass123
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=placement_db

# JWT & Authentication
SECRET_KEY=bc82ae2e962f00158ca189a7496fb033bbf4c03147270be6f18e07dd23d17284
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI Integrations (Google Gemini API)
GEMINI_API_KEY=your_gemini_api_key
# Optional: customize model (defaults to gemini-2.5-flash with fallback to gemini-3.5-flash)
# GEMINI_MODEL=gemini-2.5-flash
```

### Required vs. Optional Variables:
| Variable | Status | Purpose |
| :--- | :--- | :--- |
| `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME` | **Required** | PostgreSQL connection |
| `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | **Required** | Password hashing & JWT generation |
| `GEMINI_API_KEY` | **Required** | Gemini chatbot, quiz generator, and communication analysis |
| `GEMINI_MODEL` | *Optional* | Gemini model override (e.g. `gemini-3.5-flash` or `gemini-2.5-flash`) |

---

## 5. System Dependencies (macOS with Homebrew)

For audio processing (Whisper speech-to-text) and scanned PDF OCR fallback:

```bash
# Required for Whisper audio transcription and WebM recording decoding:
brew install ffmpeg

# Required for scanned PDF conversion fallback (text-based PDFs work without it):
brew install poppler
```

---

## 6. Run the Backend Services

The application uses a coordinated dual-service architecture:

### Service 1: Main FastAPI Backend (Port 8000)
Handles authentication, student profiles, technical quizzes, Gemini chatbot, and placement officer data.

```bash
# 1. Activate virtual environment
source venv311/bin/activate

# 2. Start FastAPI with Uvicorn on Port 8000
uvicorn main:app --reload --port 8000
```

### Service 2: AI & ML Microservice (Port 8001)
Handles resume parsing, job recommendation vector search (`JobRecommender`), and audio communication analysis (`CommunicationAnalyzer`).

```bash
# 1. Open a second terminal and activate virtual environment
source venv311/bin/activate

# 2. Start AI microservice on Port 8001
AI_API_PORT=8001 python backend.py
```

*Note: For local development, `backend.py` runs natively on `http://127.0.0.1:8001`. If running via Colab/Ngrok, set `ENABLE_NGROK=true` and update `AI_API_BASE_URL` in `config.js` with the public ngrok URL.*

---

## 7. Run the Frontend

In a third terminal window, serve the frontend HTML files:

```bash
python3 -m http.server 5500
```
Open `http://127.0.0.1:5500/index.html` in your web browser.
