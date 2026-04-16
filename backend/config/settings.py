"""
Central settings loaded from environment variables via python-dotenv.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/knightlife",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    CLASSIFIER_MODEL: str = os.getenv("CLASSIFIER_MODEL", "phi3")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_MAX_RETRIES: int = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
    GEMINI_RETRY_DELAY: float = float(os.getenv("GEMINI_RETRY_DELAY", "2.0"))

    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")
    INSTAGRAM_SESSION_FILE: str = os.getenv("INSTAGRAM_SESSION_FILE", "")
    APIFY_INSTAGRAM_TASK_ID: str = os.getenv(
        "APIFY_INSTAGRAM_TASK_ID",
        "simonocampo/instagram-post-scraper-task",
    )
    POST_LIMIT: int = int(os.getenv("POST_LIMIT", "20"))
    APIFY_API_TOKEN: str = os.getenv("APIFY_API_TOKEN", "")

    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "KnightLife")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes", "on"}

    RAW_POSTS_QUEUE: str = "raw_posts"

    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    MIN_CONFIDENCE: float = float(os.getenv("MIN_CONFIDENCE", "0.6"))
    ADMIN_SECRET_KEY: str = os.getenv("ADMIN_SECRET_KEY", "")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
