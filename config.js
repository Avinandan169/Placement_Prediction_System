// Centralized API Configuration for AI Placements Predictor
const API_CONFIG = {
    // Main FastAPI backend (main.py): authentication, profiles, quiz generator, chatbot, officer data
    MAIN_API_BASE_URL: 'http://127.0.0.1:8000',

    // AI Microservice (backend.py): resume parsing, job recommendation, audio/voice analysis
    // backend.py binds to port 8000 by default (or forwards via an Ngrok tunnel).
    // If running both services locally, run backend.py on an alternate port or configure the active tunnel URL here.
    AI_API_BASE_URL: 'http://127.0.0.1:8000'
};
