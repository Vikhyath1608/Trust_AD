"""
Database session factory.

SQLite (default):
    DATABASE_URL = sqlite:///./adserver.db

PostgreSQL (production):
    DATABASE_URL = postgresql+psycopg2://user:pass@host:5432/adserver

No application code needs to change — only the DATABASE_URL env var.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from core.config import get_settings
from db.base import Base


def _build_engine():
    settings = get_settings()
    url = settings.DATABASE_URL

    kwargs: dict = {
        "echo": settings.DB_ECHO_SQL,
    }

    if url.startswith("sqlite"):
        # SQLite-specific: same-thread off, static pool for compatibility
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    else:
        # PostgreSQL / other: connection pool settings apply
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

    engine = create_engine(url, **kwargs)

    # Enable WAL mode for SQLite (better concurrent reads)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_wal(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # Safe for background tasks
)


def init_db() -> None:
    """Create all tables if they do not exist (idempotent)."""
    # Import models so SQLAlchemy registers them before create_all
    import models.orm  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a DB session and closes it after request.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context-manager version for use outside FastAPI (scripts, tests).
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()