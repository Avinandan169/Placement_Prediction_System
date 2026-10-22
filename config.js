// Centralized API Configuration for AI Placements Predictor
const API_CONFIG = {
    // Main FastAPI backend (main.py): authentication, profiles, quiz generator, chatbot, officer data
    MAIN_API_BASE_URL: 'http://127.0.0.1:8000',

    // AI Microservice (backend.py): resume parsing, job recommendation, audio/voice analysis.
    // Keep it separate from main.py, which uses port 8000. For Colab/ngrok,
    // replace this with the public URL printed by backend.py.
    AI_API_BASE_URL: 'http://127.0.0.1:8001'
};
