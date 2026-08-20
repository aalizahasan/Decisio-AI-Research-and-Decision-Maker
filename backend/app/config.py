import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve absolute directory paths for reliable .env loading
BASE_DIR = Path(__file__).resolve().parent.parent  # backend directory
ROOT_DIR = BASE_DIR.parent                        # project root directory

# Attempt to load .env from backend/ directory or root directory
if (BASE_DIR / ".env").exists():
    load_dotenv(BASE_DIR / ".env", override=True)
elif (ROOT_DIR / ".env").exists():
    load_dotenv(ROOT_DIR / ".env", override=True)
else:
    load_dotenv(override=True)


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "AI Research & Decision Platform API")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database configuration for PostgreSQL + pgvector
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_research_db")

    # RAG parameters
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

    @property
    def GEMINI_API_KEY(self) -> str:
        # Dynamically re-read environment variable or reload .env if empty
        key = os.getenv("GEMINI_API_KEY", "")
        if not key and (BASE_DIR / ".env").exists():
            load_dotenv(BASE_DIR / ".env", override=True)
            key = os.getenv("GEMINI_API_KEY", "")
        return key

    # Cross-Origin Resource Sharing (CORS) origins allowed to make requests
    raw_cors: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    CORS_ORIGINS: list[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

    # SMTP Real Email Delivery Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USER", "no-reply@decisio.ai"))
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() == "true"



settings = Settings()



