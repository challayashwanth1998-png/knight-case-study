"""
Knight Insurance AI Underwriting System — Configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Knight Insurance AI Underwriting"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./knight_insurance.db"
    # For RDS PostgreSQL: "postgresql://user:pass@host:5432/knight_insurance"

    # Google Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_EMAILS: str = "knight-insurance-emails"
    S3_BUCKET_DOCUMENTS: str = "knight-insurance-documents"

    # Email (IMAP)
    IMAP_HOST: Optional[str] = None
    IMAP_PORT: int = 993
    IMAP_USERNAME: Optional[str] = None
    IMAP_PASSWORD: Optional[str] = None

    # Email (SMTP) — defaults to IMAP credentials if not set
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Storage
    LOCAL_STORAGE_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
