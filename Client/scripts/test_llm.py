"""
LLM Classifier Test Script
--------------------------
Pass any query directly to the LLM and see the raw JSON classification result.

Usage:
    python scripts/test_llm.py
    python scripts/test_llm.py "samsung galaxy s24"
    python scripts/test_llm.py "how to fix python error"
"""
import sys
import json
from pathlib import Path

# Project root on sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env
from api.dependencies import _load_dotenv
_load_dotenv()

from classifiers.llm_classifier import LLMClassifierWithWriteBack
from extraction.normalizer import QueryNormalizer
from utils.logging import Logger


def test_query(query: str) -> None:
    """Run a single query through the LLM classifier and print the result."""

    normalizer = QueryNormalizer()
    normalized = normalizer.normalize(query)

    print(f"\n{'='*60}")
    print(f"  Query      : {query}")
    print(f"  Normalized : {normalized}")
    print(f"{'='*60}")

    # Initialise classifier (no VectorDB or embedding model needed for raw testing)
    classifier = LLMClassifierWithWriteBack(
        vectordb_store=None,
        embedding_model=None,
        logger=Logger(verbose=True)
    )

    if not classifier.client:
        print("\n✗  LLM client not initialised.")
        print("   Check that HF_API_TOKEN is set correctly in your .env file.")
        return

    print("\nCalling LLM...\n")
    result = classifier.classify(query=query, normalized_query=normalized)

    if result is None:
        print("✗  LLM returned no result (classification failed).")
        print("   Check the warnings above for details.")
        return

    # Pretty print
    print("✓  Classification Result:")
    print(json.dumps(result, indent=2))

    # Summary line
    label = "PRODUCT" if result.get("is_product") else "NON-PRODUCT"
    cat   = result.get("category", "")
    prod  = result.get("product", "")
    brand = result.get("brand", "")
    model = result.get("model", "")
    conf  = result.get("confidence", 0.0)

    print(f"\n  → {label}  |  {brand} {prod} {model}  |  category: {cat}  |  confidence: {conf}")


def run_batch(queries: list) -> None:
    """Run multiple queries and print a summary table."""

    normalizer = QueryNormalizer()
    classifier = LLMClassifierWithWriteBack(
        vectordb_store=None,
        embedding_model=None,
        logger=Logger(verbose=True)
    )

    if not classifier.client:
        print("\n✗  LLM client not initialised. Check HF_API_TOKEN in .env")
        return

    # ── Quick connection test before batch ────────────────────────────────
    print("\nRunning connection test...")
    try:
        resp = classifier.client.chat_completion(
            messages=[{"role": "user", "content": 'Reply with exactly: {"ok": true}'}],
            max_tokens=20
        )
        test_text = resp.choices[0].message.content or ""
        print(f"✓  Connection OK — raw response: {test_text.strip()[:80]}\n")
    except Exception as e:
        print(f"✗  Connection FAILED: {type(e).__name__}: {e}")
        print("   Check HF_API_TOKEN, model name, and internet connection.\n")
        return

    if not classifier.client:
        print("\n✗  LLM client not initialised. Check HF_API_TOKEN in .env")
        return

    print(f"\n{'='*80}")
    print(f"  BATCH TEST — {len(queries)} queries")
    print(f"{'='*80}")
    print(f"  {'#':<4} {'Query':<45} {'Label':<12} {'Brand/Product':<25} {'Conf'}")
    print(f"  {'-'*4} {'-'*45} {'-'*12} {'-'*25} {'-'*6}")

    for i, query in enumerate(queries, 1):
        normalized = normalizer.normalize(query)

        # Temporarily enable verbose to catch the exact error
        classifier.logger.verbose = True
        result = classifier.classify(query=query, normalized_query=normalized)
        classifier.logger.verbose = False

        if result is None:
            print(f"  {i:<4} {query:<45} {'ERROR':<12}")
            continue

        label  = "PRODUCT" if result.get("is_product") else "non-product"
        brand  = result.get("brand", "")
        prod   = result.get("product", "")
        bp     = f"{brand} {prod}".strip()
        conf   = result.get("confidence", 0.0)

        print(f"  {i:<4} {query:<45} {label:<12} {bp:<25} {conf:.2f}")

    print(f"{'='*80}\n")


# ── Default test queries ───────────────────────────────────────────────────────
DEFAULT_QUERIES = [
    # Expected: PRODUCT
    "hero xpulse 210",
]


def main():
    args = sys.argv[1:]

    if args:
        # Single query passed as command-line argument
        query = " ".join(args)
        test_query(query)
    else:
        # No argument — run the default batch test
        print("\nNo query provided — running default batch test.")
        print("Tip: pass a query as argument:  python scripts/test_llm.py \"your query here\"\n")
        run_batch(DEFAULT_QUERIES)


if __name__ == "__main__":
    main()