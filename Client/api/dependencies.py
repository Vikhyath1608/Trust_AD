"""
Dependency injection for FastAPI.

Loads environment variables from .env file before building config,
so all settings (including HF_API_TOKEN) are available to every component.
"""
from functools import lru_cache
from pathlib import Path


def _load_dotenv() -> None:
    """
    Load .env into os.environ using python-dotenv if available,
    otherwise fall back to a simple manual parser.

    The .env file is expected at the project root (parent of api/).
    """
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=False)
    except ImportError:
        # Manual fallback — no python-dotenv needed
        import os
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value


# Load .env once at import time so all downstream code sees the variables
_load_dotenv()

from config.settings import SystemConfig
from app.engine import ExtractionEngine


@lru_cache()
def get_default_config() -> SystemConfig:
    """
    Return system configuration loaded from environment / .env (cached).
    """
    return SystemConfig.default()


@lru_cache()
def get_engine() -> ExtractionEngine:
    """
    Return a cached ExtractionEngine singleton.
    """
    return ExtractionEngine(get_default_config())