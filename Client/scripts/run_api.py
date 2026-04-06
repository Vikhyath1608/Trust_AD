"""
API server startup script.

Loads .env from the project root before starting uvicorn so that
HF_API_TOKEN and all other settings are available to every component.
"""
import sys
from pathlib import Path

# Project root on sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env ─────────────────────────────────────────────────────────────────
from api.dependencies import _load_dotenv
_load_dotenv()

# Read server settings from environment (with defaults)
import os
HOST = os.environ.get("API_HOST", "0.0.0.0").strip()
PORT = int(os.environ.get("API_PORT", "8000").strip())

import uvicorn


def main():
    """Start the FastAPI server."""
    print(f"Starting API server on http://{HOST}:{PORT}")
    print(f"Docs available at http://{HOST}:{PORT}/docs\n")
    uvicorn.run(
        "api.main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()