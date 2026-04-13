"""
Structured logger — thin wrapper around Python logging.
"""
import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Return a configured logger.

    Args:
        name: Logger name (usually __name__).
        level: Override log level (default: read from settings).
    """
    from core.config import get_settings
    settings = get_settings()

    log = logging.getLogger(name)

    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        log.addHandler(handler)

    log_level = level or settings.LOG_LEVEL
    log.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    return log