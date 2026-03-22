"""
Configuration settings for User Interest Extractor.

All values are loaded from environment variables (populated from .env file).
Sensible defaults are provided for every setting except HF_API_TOKEN.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field


def _env(key: str, default: str = "") -> str:
    """Read a string env variable, stripping surrounding quotes if any."""
    return os.environ.get(key, default).strip().strip('"').strip("'")


def _env_float(key: str, default: float) -> float:
    try:
        return float(_env(key, str(default)))
    except ValueError:
        return default


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


def _env_bool(key: str, default: bool) -> bool:
    return _env(key, str(default)).lower() in ("1", "true", "yes")


@dataclass
class HFConfig:
    """Hugging Face Inference API configuration."""
    api_token: str = field(default_factory=lambda: _env("HF_API_TOKEN"))
    model: str = field(
        default_factory=lambda: _env(
            "HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3"
        )
    )


@dataclass
class MLConfig:
    """ML classifier configuration."""
    model_path: str = field(
        default_factory=lambda: _env("ML_MODEL_PATH", "./ml_product_model.pkl")
    )
    embedding_model_name: str = field(
        default_factory=lambda: _env("ML_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )


@dataclass
class VectorDBConfig:
    """Vector database configuration."""
    db_path: str = field(
        default_factory=lambda: _env("VECTORDB_PATH", "./chroma_db")
    )
    collection_name: str = field(
        default_factory=lambda: _env("VECTORDB_COLLECTION", "knowledge_base")
    )
    semantic_threshold: float = field(
        default_factory=lambda: _env_float("VECTORDB_SEMANTIC_THRESHOLD", 0.85)
    )
    allow_reset: bool = False
    anonymized_telemetry: bool = False


@dataclass
class DataStoreConfig:
    """Data store configuration."""
    user_data_path: str = field(
        default_factory=lambda: _env("USER_DATA_PATH", "./user_data.json")
    )
    training_data_path: str = field(
        default_factory=lambda: _env("TRAINING_DATA_PATH", "./training_data.json")
    )


@dataclass
class ProcessingConfig:
    """Processing configuration."""
    data_dir: str = field(
        default_factory=lambda: _env("BROWSER_HISTORY_DIR", "./browser_history")
    )
    chunk_size: int = field(
        default_factory=lambda: _env_int("CHUNK_SIZE", 100)
    )
    max_products: int = field(
        default_factory=lambda: _env_int("MAX_PRODUCTS", 100)
    )
    alpha: float = field(
        default_factory=lambda: _env_float("ENGAGEMENT_ALPHA", 1.0)
    )
    beta: float = field(
        default_factory=lambda: _env_float("ENGAGEMENT_BETA", 1.0)
    )


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = field(default_factory=lambda: _env("API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("API_PORT", 8000))
    verbose: bool = field(default_factory=lambda: _env_bool("API_VERBOSE", False))


@dataclass
class SystemConfig:
    """Complete system configuration — aggregates all sub-configs."""
    hf: HFConfig
    ml: MLConfig
    vectordb: VectorDBConfig
    datastore: DataStoreConfig
    processing: ProcessingConfig
    verbose: bool = True

    @classmethod
    def default(cls) -> "SystemConfig":
        """Create configuration loaded from environment / .env file."""
        return cls(
            hf=HFConfig(),
            ml=MLConfig(),
            vectordb=VectorDBConfig(),
            datastore=DataStoreConfig(),
            processing=ProcessingConfig(),
            verbose=_env_bool("API_VERBOSE", False),
        )