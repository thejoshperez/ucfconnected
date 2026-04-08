"""
Central settings — loaded from environment variables via python-dotenv.
All secrets and environment-specific values live in .env (never committed).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Settings:
    # ── Postgres ──────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/knightlife",
    )

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ── Ollama ────────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    CLASSIFIER_MODEL: str = os.getenv("CLASSIFIER_MODEL", "phi3")
    EXTRACTOR_MODEL: str = os.getenv("EXTRACTOR_MODEL", "mistral")

    # ── Gemini ────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_MAX_RETRIES: int = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
    GEMINI_RETRY_DELAY: float = float(os.getenv("GEMINI_RETRY_DELAY", "2.0"))
    # ── Instagram ─────────────────────────────────────────────────────────
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")
    # Path to a saved session file created by login.py (supports 2FA accounts)
    INSTAGRAM_SESSION_FILE: str = os.getenv("INSTAGRAM_SESSION_FILE", "")
    # Comma-separated list of club Instagram usernames to scrape
    CLUB_ACCOUNTS: list[str] = [
        acc.strip()
        for acc in os.getenv(
            "CLUB_ACCOUNTS",
            "ucfknights,ucf_sga,ucf_engineering",
        ).split(",")
        if acc.strip()
    ]
    # How many posts to fetch per account per run
    POST_LIMIT: int = int(os.getenv("POST_LIMIT", "20"))

    # ── Image / OCR ───────────────────────────────────────────────────────
    IMAGE_DOWNLOAD_DIR: str = os.getenv("IMAGE_DOWNLOAD_DIR", "/tmp/knightlife_images")
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")

    # ── Queue ─────────────────────────────────────────────────────────────
    RAW_POSTS_QUEUE: str = "raw_posts"
    CLASSIFIED_QUEUE: str = "classified_posts"

    # ── API ───────────────────────────────────────────────────────────────
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]

    # ── LLM confidence threshold ──────────────────────────────────────────
    MIN_CONFIDENCE: float = float(os.getenv("MIN_CONFIDENCE", "0.6"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
