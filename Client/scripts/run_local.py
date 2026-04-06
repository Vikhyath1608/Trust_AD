"""
Local execution script for user interest extraction.

Loads .env from the project root so that HF_API_TOKEN and all other
settings are available before any component is initialised.
"""
import json
import sys
from pathlib import Path

# Project root on sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env ─────────────────────────────────────────────────────────────────
from api.dependencies import _load_dotenv
_load_dotenv()

from config.settings import SystemConfig
from app.engine import ExtractionEngine


def main():
    """Run extraction for a single user."""
    config = SystemConfig.default()
    config.verbose = True          # verbose output for local runs

    engine = ExtractionEngine(config)

    user_id = "user7"              # change to the user you want to test
    result = engine.extract(user_id)

    print("\nFinal Result (JSON):")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()