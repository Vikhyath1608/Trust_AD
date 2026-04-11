"""
Ad Serving Platform — FastAPI application.

Run:
    cd Server
    uvicorn api.main:app --reload --port 8001
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.middleware import add_middleware
from api.routes import ads, analytics, serving
from core.config import get_settings
from db.session import init_db
from models.schemas import HealthResponse
from utils.logging import get_logger

logger = get_logger("api.main")
settings = get_settings()


# ─────────────────────────────────────────────────────────────────────────────
# App factory
# ─────────────────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Ad Serving Platform — Ad repository management, "
            "interest-driven ad matching, and analytics."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware
    add_middleware(app)

    # Routers
    app.include_router(ads.router)
    app.include_router(serving.router)
    app.include_router(analytics.router)

    # Serve uploaded images as static files
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/uploads",
        StaticFiles(directory=str(upload_dir.parent)),
        name="uploads",
    )

    # ── Lifecycle events ───────────────────────────────────────────────────

    @app.on_event("startup")
    def startup():
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"Database: {settings.DATABASE_URL}")
        init_db()
        logger.info("Database tables initialised.")

    @app.on_event("shutdown")
    def shutdown():
        logger.info("Shutting down.")

    # ── Health check ───────────────────────────────────────────────────────

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    def health():
        from db.session import engine
        db_ok = "ok"
        try:
            with engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        except Exception as exc:
            db_ok = f"error: {exc}"

        return HealthResponse(
            status="healthy" if db_ok == "ok" else "degraded",
            version=settings.APP_VERSION,
            database=settings.DATABASE_URL.split("://")[0],  # e.g. "sqlite"
            components={
                "database": db_ok,
                "ad_repository": "ok",
                "ad_matcher": "ok",
                "ad_analyzer": "ok",
            },
        )

    return app


app = create_app()