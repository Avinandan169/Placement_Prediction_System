-- Schema initialization for AI Placements Predictor

-- 1. Users table (Students & Placement Officers)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('student', 'officer')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Student Profiles table
CREATE TABLE IF NOT EXISTS student_profiles (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255),
    course VARCHAR(255),
    tenth_percentage NUMERIC(5, 2),
    twelfth_percentage NUMERIC(5, 2),
    current_year INT,
    cgpa NUMERIC(4, 2),
    skills TEXT[],
    projects TEXT,
    achievements TEXT,
    linkedin_url TEXT,
    star_level INT DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Prediction History table (CSE3141 Predictive Analytics)
CREATE TABLE IF NOT EXISTS prediction_history (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    student_name VARCHAR(255),
    cgpa NUMERIC(4, 2),
    internships INT,
    projects INT,
    workshops INT,
    aptitude_score NUMERIC(5, 2),
    soft_skills_rating NUMERIC(4, 2),
    extracurriculars VARCHAR(10),
    placement_training VARCHAR(10),
    ssc_marks NUMERIC(5, 2),
    hsc_marks NUMERIC(5, 2),
    prediction_result VARCHAR(50),
    placement_probability NUMERIC(5, 2),
    model_version VARCHAR(100),
    feature_contributions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_prediction_history_user_id ON prediction_history(user_id);
