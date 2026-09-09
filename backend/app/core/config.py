import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file if available
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "IntentGuard AI")
    TAGLINE: str = "Ask. Search. Decide. Pay Safely."
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./intent_guard.db")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    LLAMA_MODEL: str = os.getenv("LLAMA_MODEL", "llama3")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_mock_12345")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "rzp_test_secret_67890")
    SECONDARY_AGENT_VPA: str = os.getenv("SECONDARY_AGENT_VPA", "agent.antigravity@psp")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "intentguard_jwt_secret_key_2026_super_secure")

settings = Settings()
