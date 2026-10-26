# Placement Prediction System: Predictive Analytics & Soft Computing Platform

An enterprise-grade, end-to-end Machine Learning, Fuzzy Logic, and Heuristic Search platform designed for campus placement readiness assessment and student career progression.

This system rigorously supports the curriculum and learning outcomes of two core academic courses:
1. **CSE3141 — Predictive Analytics**
2. **CSE3121 — Artificial Intelligence and Soft Computing**

---

## 1. System Architecture & End-to-End Workflow

```
[ Hugging Face (Krooz Recruitment) / Local CSV Upload ]
                           │
                           ▼
          [ Dataset Ingestion & Validation ]
       (SHA-256 Hash, Schema Audit, CC0-1.0 Provenance)
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
   [ Immutable Raw Data ]       [ Preprocessing Pipeline ]
       (data/raw/)          (Median Imputer, StandardScaler, OneHot)
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
       [ Exploratory Data Analysis ]             [ Stratified 5-Fold Cross-Validation ]
    (Histograms, Correlations, Outliers)           (Dummy, LogReg, DT, RF, GradBoost)
                                                                │
                                                                ▼
                                                   [ Model Selection & Tuning ]
                                                    (GridSearchCV on Train Split)
                                                                │
                                                                ▼
                                                  [ Evaluation & Persistence ]
                                                  (Accuracy, F1, ROC-AUC, CM)
                                                                │
                                                                ▼
    ┌───────────────────────────────────────────────────────────┴──────────────────────────────────────────┐
    ▼                                                           ▼                                          ▼
[ Placement Inference ]                         [ Explainable Fuzzy Readiness ]              [ A* Skill Development Planner ]
(Probabilities & Local Diagnostic Drivers)     (Mamdani FIS: \mu(x), Rules, Centroid)       (Heuristic Search: f(n) = g(n) + h(n))
    │                                                           │                                          │
    ▼                                                           ▼                                          ▼
[ PostgreSQL Prediction Audit ]                 [ Rule Firing & \alpha-Cut Tracing ]         [ Admissible Learning Roadmap ]
```

---

## 2. Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.11), Uvicorn, Pydantic V2 | High-performance asynchronous RESTful APIs, type validation |
| **Database** | PostgreSQL 16, Psycopg 3 | User authentication, profile persistence, prediction audit trail |
| **Machine Learning** | Scikit-Learn 1.9, NumPy 2.4, Pandas 3.1, Joblib | Classification pipelines, cross-validation, GridSearchCV, scaling, metrics |
| **AI & Soft Computing** | Custom Mamdani FIS Engine, A* Search Engine | Triangular/trapezoidal membership functions, centroid defuzzification, graph search |
| **NLP & Vectors** | Sentence-Transformers (`all-MiniLM-L6-v2`), PyPDF, EasyOCR | Vector embeddings, cosine similarity matching, resume parsing |
| **Speech & Audio** | OpenAI Whisper (`base.en`), Praat Parselmouth | Speech-to-text transcription, acoustic prosody and pitch analysis |
| **LLM Services** | Google Gemini API (`gemini-2.5-flash` / `gemini-3.5-flash`) | Technical quiz generation, resume entity extraction, chat assistance |
| **Frontend UI/UX** | Modern Semantic HTML5, CSS3 Design Tokens, Chart.js, Vanilla JS | Responsive SaaS analytics dashboard, accessible layouts, zero heavy bloat |

---

## 3. Academic Course Alignments

### CSE3141 — Predictive Analytics
* **Data Cleaning & Quality Assessment:** Ingestion pipeline validates data types, handles missing values via median imputation, and detects 72 duplicate records in the active dataset.
* **Exploratory Data Analysis (EDA):** Full statistical profiling (Mean, Std, Min, Q25, Median, Q75, Max, Skewness), Pearson correlation matrices, class balance inspection (58.03% unplaced : 41.97% placed), and Tukey IQR outlier identification.
* **Leakage-Free Preprocessing:** Data transformations (imputation, scaling, one-hot encoding) are encapsulated within `sklearn.pipeline.Pipeline` and fitted strictly on training folds.
* **Model Benchmarking:** Implements and compares 5 candidate classifiers:
  1. `DummyClassifier(strategy="most_frequent")` (Baseline)
  2. `LogisticRegression(max_iter=1000)`
  3. `DecisionTreeClassifier()`
  4. `RandomForestClassifier()`
  5. `GradientBoostingClassifier()`
* **Hyperparameter Tuning:** Conducted with `GridSearchCV` on the training partition.
* **Evaluation Metrics:** Held-out test accuracy, precision, recall, F1-score, ROC-AUC, and 5-fold cross-validation mean and standard deviation.
* **Model Explainability:** Global feature importance weights, permutation importance on test records, and local candidate contribution diagnostics.

### CSE3121 — Artificial Intelligence and Soft Computing
* **Mamdani Fuzzy Inference System (FIS):**
  - **Linguistic Input Variables:** `CGPA` (Low, Medium, High), `AptitudeScore` (Low, Medium, High), `SoftSkills` (Low, Medium, High), `PracticalExperience` (Low, Medium, High).
  - **Membership Functions:** Triangular (`trimf`) and Trapezoidal (`trapmf`) curves with defined linguistic intervals.
  - **Fuzzy Rule Base:** 16 expert rules capturing interactions across academic and behavioral domains.
  - **Inference Engine:** Conjunction via Mamdani minimum operator, consequence clipping via min implication, and rule union via maximum aggregation.
  - **Defuzzification:** Discretized **Centroid (Center of Gravity / Area) Method**:
    $$z^* = \frac{\sum z \cdot \mu(z)}{\sum \mu(z)}$$
  - **Explainability:** Full tracing of activated rules and $\alpha$-cuts.
* **A\* Heuristic Search Planner:**
  - **Graph Formulation:** Nodes represent technical milestones with prerequisites, directed dependency edges, and step costs representing effort in study hours ($g(n)$).
  - **Search State:** `frozenset` of acquired competencies managed via a priority queue (`heapq`).
  - **Admissible Heuristic $h(n)$:** Sum of minimum prerequisite effort hours remaining to satisfy all unsatisfied competencies for the target role. Because every missing skill must be learned and costs are positive, $h(n) \le h^*(n)$ (never overestimates), guaranteeing finding the optimal shortest path.

---

## 4. Dataset Provenance & Actual Measured Results

### Data Source
* **Dataset:** Krooz Campus Recruitment CSV
* **Source URL:** https://huggingface.co/datasets/Krooz/Campus_Recruitment_CSV
* **License:** CC0-1.0 (Public Domain)
* **Sample Count:** 10,000 total observations
* **Feature Schema:**
  - `CGPA` (Numeric float, 6.5 - 9.1)
  - `Internships` (Integer, 0 - 2)
  - `Projects` (Integer, 0 - 3)
  - `Workshops/Certifications` (Integer, 0 - 3)
  - `AptitudeTestScore` (Numeric integer, 60 - 90)
  - `SoftSkillsRating` (Numeric float, 3.0 - 5.0)
  - `ExtracurricularActivities` (Categorical: Yes/No)
  - `PlacementTraining` (Categorical: Yes/No)
  - `SSC_Marks` (Numeric integer, 55 - 90)
  - `HSC_Marks` (Numeric integer, 57 - 88)
  - `PlacementStatus` (Target: Placed / NotPlaced)
* **SHA-256 Checksum:** `a17403c05174f02ede5eb270c28cb5807d9da5cd076869a5bc70971fbbab2145`

### Actual Measured Model Evaluation Benchmark
Evaluated strictly on a 20% held-out test split (2,000 unseen student records):

| Model Algorithm | Accuracy | Precision | Recall | F1-Score | ROC-AUC | 5-Fold CV Accuracy | Training Time | Selection Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Dummy Baseline** | 58.05% | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 58.03% | 0.02s | Baseline |
| **Logistic Regression** | **80.65%** | **0.7756** | **0.7580** | **0.7667** | **0.8891** | **79.75% ± 0.009** | 0.28s | **Selected Production Model** |
| **Gradient Boosting** | 79.90% | 0.7762 | 0.7318 | 0.7534 | 0.8901 | 80.14% ± 0.008 | 1.84s | Candidate |
| **Random Forest** | 79.95% | 0.7779 | 0.7306 | 0.7535 | 0.8890 | 79.63% ± 0.010 | 1.42s | Candidate |
| **Decision Tree** | 77.90% | 0.7643 | 0.6841 | 0.7220 | 0.8668 | 78.09% ± 0.011 | 0.14s | Candidate |

**Model Selection Justification:** Logistic Regression achieved the highest held-out test F1-score (0.7667), high test accuracy (80.65%), strong discrimination (ROC-AUC 0.8891), and robust cross-validation stability, while providing direct interpretability via odds-ratio coefficients.

---

## 5. Local Installation & Execution Guide

### Prerequisites
* macOS / Linux / Windows WSL
* Python 3.11+
* PostgreSQL 15+ (`brew install postgresql@16`)

### Step 1: Clone and Set Up Virtual Environment
```bash
cd placements-predictor
python3.11 -m venv venv311
source venv311/bin/activate
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your database credentials and API key are configured:
```env
DB_USER=placement_user
DB_PASS=placement_secure_pass123
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=placement_db

SECRET_KEY=bc82ae2e962f00158ca189a7496fb033bbf4c03147270be6f18e07dd23d17284
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

GEMINI_API_KEY=your_gemini_api_key
```

### Step 3: Initialize Database Schema
```bash
psql -h 127.0.0.1 -U placement_user -d placement_db -f schema.sql
```

### Step 4: Launch the Services
Open 3 terminal tabs:

**Terminal 1 — Main Backend Service (Port 8000):**
```bash
source venv311/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 — AI Vector & Microservice (Port 8001):**
```bash
source venv311/bin/activate
AI_API_PORT=8001 python backend.py
```

**Terminal 3 — Frontend Static Server (Port 5500):**
```bash
python3 -m http.server 5500
```
Open `http://127.0.0.1:5500/dashboard.html` in your web browser.

---

## 6. Running the Test Suite
Execute the unit and integration test suites:
```bash
# Run all unit tests
./venv311/bin/python -m unittest discover tests

# Or run individual modules:
./venv311/bin/python -m unittest tests/test_predictive_analytics.py
./venv311/bin/python -m unittest tests/test_ai_soft_computing.py
./venv311/bin/python -m unittest tests/test_api_endpoints.py
```

---

## 7. REST API Documentation Summary

### Predictive Analytics (CSE3141)
* `GET /api/dataset/info`: Returns metadata, row/col count, licence, and SHA-256 hash.
* `GET /api/dataset/preview`: Returns preview records and schema types.
* `POST /api/dataset/upload`: Uploads and validates a student placement CSV.
* `POST /api/dataset/reset-default`: Resets to the benchmark Krooz dataset.
* `GET /api/eda/summary`: Returns summary statistics, histograms, outlier counts, and correlation matrix.
* `POST /api/model/train`: Trains candidate classifiers via 5-fold CV and GridSearchCV.
* `GET /api/model/status`: Returns training execution state and progress percentage.
* `GET /api/model/comparison`: Returns performance metrics comparison across all models.
* `POST /api/model/predict`: Runs classification inference, estimates probabilities, and logs to PostgreSQL.
* `GET /api/model/explain`: Returns global feature importance and permutation importance.
* `GET /api/history/my`: Fetches authenticated user's prediction history audit records.

### AI & Soft Computing (CSE3121)
* `POST /api/fuzzy/evaluate`: Evaluates student attributes using the Mamdani Fuzzy Inference System.
* `POST /api/astar/plan`: Generates the optimal milestone learning path via A* heuristic search.
* `GET /api/astar/roles`: Lists available career roles and target competencies.
* `GET /api/astar/all-skills`: Lists the complete skill catalog and dependency graph.
