"""
ML Product Classifier Test Script
----------------------------------
Test the ML model (ml_product_model.pkl) on any query.
Returns label 0 (non-product) or 1 (product) with confidence probability.

Usage:
    python scripts/test_ml.py
    python scripts/test_ml.py "samsung galaxy s24"
    python scripts/test_ml.py "how to fix python error"
"""
import sys
from pathlib import Path

# Project root on sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env
from api.dependencies import _load_dotenv
_load_dotenv()

from config.settings import SystemConfig
from classifiers.ml_filter import MLProductClassifier
from extraction.normalizer import QueryNormalizer
from utils.logging import Logger


def load_classifier() -> MLProductClassifier:
    """Load the ML classifier using settings from .env"""
    config = SystemConfig.default()
    return MLProductClassifier(
        model_path=config.ml.model_path,
        embedding_model_name=config.ml.embedding_model_name,
        logger=Logger(verbose=True)
    )


def test_query(classifier: MLProductClassifier, query: str) -> None:
    """Test a single query and print detailed result."""
    normalizer = QueryNormalizer()
    normalized = normalizer.normalize(query)

    print(f"\n{'='*60}")
    print(f"  Query      : {query}")
    print(f"  Normalized : {normalized}")
    print(f"{'='*60}")

    # Get label
    label = classifier.predict_label(normalized)

    # Try to get probability if model supports it
    confidence = None
    try:
        import numpy as np
        embedding = classifier.embedder.encode(normalized, convert_to_numpy=True).reshape(1, -1)
        proba = classifier.model.predict_proba(embedding)[0]
        confidence = proba[1]  # probability of label=1 (product)
    except AttributeError:
        pass  # model doesn't support predict_proba

    # Print result
    if label == 1:
        verdict = "✓  PRODUCT     (label=1) → passes to classification cascade"
        bar_fill = int((confidence or 1.0) * 30)
    else:
        verdict = "✗  NON-PRODUCT (label=0) → skipped"
        bar_fill = int((1 - (confidence or 0.0)) * 30)

    print(f"\n  Label      : {label}")
    if confidence is not None:
        bar = "█" * bar_fill + "░" * (30 - bar_fill)
        print(f"  Confidence : {confidence:.4f}  [{bar}]")
    print(f"\n  {verdict}\n")


def run_batch(classifier: MLProductClassifier, queries: list) -> None:
    """Run multiple queries and print a summary table."""
    normalizer = QueryNormalizer()

    print(f"\n{'='*80}")
    print(f"  ML BATCH TEST — {len(queries)} queries")
    print(f"{'='*80}")

    # Header
    has_proba = hasattr(classifier.model, "predict_proba")
    if has_proba:
        print(f"  {'#':<4} {'Query':<48} {'Label':<5} {'Conf':>6}  {'Verdict'}")
        print(f"  {'-'*4} {'-'*48} {'-'*5} {'-'*6}  {'-'*15}")
    else:
        print(f"  {'#':<4} {'Query':<48} {'Label':<5}  {'Verdict'}")
        print(f"  {'-'*4} {'-'*48} {'-'*5}  {'-'*15}")

    products = 0
    non_products = 0

    for i, query in enumerate(queries, 1):
        normalized = normalizer.normalize(query)
        label = classifier.predict_label(normalized)

        confidence_str = ""
        if has_proba:
            try:
                import numpy as np
                emb = classifier.embedder.encode(normalized, convert_to_numpy=True).reshape(1, -1)
                proba = classifier.model.predict_proba(emb)[0]
                confidence_str = f"{proba[1]:>6.4f}"
            except Exception:
                confidence_str = "  N/A "

        verdict = "PRODUCT" if label == 1 else "non-product"
        display_query = query if len(query) <= 48 else query[:45] + "..."

        if label == 1:
            products += 1
        else:
            non_products += 1

        if has_proba:
            print(f"  {i:<4} {display_query:<48} {label:<5} {confidence_str}  {verdict}")
        else:
            print(f"  {i:<4} {display_query:<48} {label:<5}  {verdict}")

    # Summary
    total = len(queries)
    print(f"\n{'='*80}")
    print(f"  SUMMARY:  {products}/{total} PRODUCT  |  {non_products}/{total} non-product")
    print(f"{'='*80}\n")


# ── Default test queries ───────────────────────────────────────────────────────
DEFAULT_QUERIES = [
    # Expected label=1 (product)
    "xpulse 210",
]


def main():
    print("\n" + "="*60)
    print("  ML PRODUCT CLASSIFIER TEST")
    print("="*60)

    # Load model
    try:
        classifier = load_classifier()
    except Exception as e:
        print(f"\n✗  Failed to load ML classifier: {e}")
        print("   Make sure ml_product_model.pkl exists in the project root.")
        sys.exit(1)

    args = sys.argv[1:]

    if args:
        # Single query from command line
        query = " ".join(args)
        test_query(classifier, query)
    else:
        # No argument → run default batch
        print("\nNo query provided — running default batch test.")
        print("Tip: python scripts/test_ml.py \"your query here\"\n")
        run_batch(classifier, DEFAULT_QUERIES)


if __name__ == "__main__":
    main()