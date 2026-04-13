"""
Launch the Ad Serving Platform API.

Usage:
    cd Server
    python scripts/run_server.py
    # or
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )