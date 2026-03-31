"""
Core configuration — driven by environment variables.
SQLite by default; switch to PostgreSQL by changing DATABASE_URL.
"""
from functools import lru_cache
from typing import Literal
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment / .env file.

    PostgreSQL migration:
        Set DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/adserver
        No other code changes required.
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────
    APP_NAME: str = "AdServing Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Database ───────────────────────────────────────────────────────────
    # SQLite (default — file lives next to the server package)
    DATABASE_URL: str = "sqlite:///./adserver.db"
    # Future PostgreSQL:
    # DATABASE_URL=postgresql+psycopg2://aduser:secret@localhost:5432/adserver
    DB_ECHO_SQL: bool = False          # Set True for SQL query logging
    DB_POOL_SIZE: int = 5              # Ignored for SQLite
    DB_MAX_OVERFLOW: int = 10          # Ignored for SQLite

    # ── Ad Serving ─────────────────────────────────────────────────────────
    # Weights for multi-signal ad scoring
    SCORE_WEIGHT_CATEGORY: float = 0.45
    SCORE_WEIGHT_KEYWORD: float = 0.35
    SCORE_WEIGHT_BRAND: float = 0.20

    # Minimum score threshold to serve an ad (0.0 – 1.0)
    MIN_SERVING_SCORE: float = 0.05

    # Maximum ads returned per serving request
    MAX_ADS_RETURNED: int = 5

    # ── Client API ─────────────────────────────────────────────────────────
    # URL of the running Client (interest extraction) service
    CLIENT_API_URL: str = "http://localhost:8000"
    CLIENT_API_TIMEOUT: int = 120      # seconds

    # ── File Upload ────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads/ad_creatives"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]

    # ── HuggingFace LLM (ad category/keyword generation) ──────────────────
    HF_API_TOKEN: str = ""
    HF_MODEL: str = "meta-llama/Llama-3.1-8B-Instruct"

    # ── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()