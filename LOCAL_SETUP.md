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

Run the provided `schema.sql` script to create the `users` and `student_profiles` tables:

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

# Optional Integrations
HF_TOKEN=your_huggingface_api_token
```

### Required vs. Optional Variables:
| Variable | Status | Purpose |
| :--- | :--- | :--- |
| `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME` | **Required** | PostgreSQL connection |
| `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | **Required** | Password hashing & JWT generation |
| `HF_TOKEN` | *Optional* | Required only when calling `/generate-quiz` or `/chat/ask` |

---

## 5. Run the Backend Server

Activate your existing virtual environment (`venv311`) and start the FastAPI server:

```bash
# 1. Activate virtual environment
source venv311/bin/activate

# 2. Start FastAPI with Uvicorn
uvicorn main:app --reload --port 8000
```

### Verify Server Health
Visit `http://127.0.0.1:8000/` in your browser. You should see:
```json
{
  "status": "success",
  "message": "FastAPI is running and connected to PostgreSQL!"
}
```

---

## 6. Run the Frontend

In a separate terminal window, serve the frontend HTML files:

```bash
python3 -m http.server 5500
```
Open `http://127.0.0.1:5500/index.html` in your web browser.
