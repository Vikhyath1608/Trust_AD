"""
Middleware: CORS + structured request/response logging.
"""
import time
import uuid

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_settings
from utils.logging import get_logger

logger = get_logger("api.access")
settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path, status code, and latency for every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        response: Response = await call_next(request)

        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"→ {response.status_code} ({latency_ms:.1f}ms)"
        )
        response.headers["X-Request-ID"] = request_id
        return response


def add_middleware(app) -> None:
    """Attach all middleware to the FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)