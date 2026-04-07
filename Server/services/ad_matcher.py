"""
Ad Matching / Serving Engine.

Multi-signal scoring pipeline:

    1. Category Match     (weight: SCORE_WEIGHT_CATEGORY)
       - Exact category match → 1.0
       - Partial / substring match → 0.5

    2. Keyword Overlap    (weight: SCORE_WEIGHT_KEYWORD)
       - Jaccard-like overlap between ad keywords and interest tokens
       - Covers: top_1 query, top_2 product/brand, top_3 subcategory, top_4 category

    3. Brand Match        (weight: SCORE_WEIGHT_BRAND)
       - Exact brand match → 1.0
       - Brand substring in any signal → 0.5

Final score = weighted sum, normalised to [0, 1].
Ads below MIN_SERVING_SCORE are discarded.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from core.config import get_settings
from core.exceptions import NoAdsAvailableError
from models.orm import Ad, AdImpression
from models.schemas import InterestSignals, ServedAd, ServeAdResponse
from services.ad_repository import AdRepository
from utils.logging import get_logger
from utils.text import tokenize

logger = get_logger(__name__)
settings = get_settings()
ad_repo = AdRepository()


# ─────────────────────────────────────────────────────────────────────────────
# Internal data class
# ─────────────────────────────────────────────────────────────────────────────

class _ScoredAd:
    __slots__ = ("ad", "score", "matched_signals", "matched_keywords")

    def __init__(
        self,
        ad: Ad,
        score: float,
        matched_signals: Dict[str, Any],
        matched_keywords: List[str],
    ):
        self.ad = ad
        self.score = score
        self.matched_signals = matched_signals
        self.matched_keywords = matched_keywords


# ─────────────────────────────────────────────────────────────────────────────
# Signal extraction helpers
# ─────────────────────────────────────────────────────────────────────────────

def _extract_categories(signals: InterestSignals) -> List[str]:
    """Collect all category strings from the 4 top-N signals."""
    categories: List[str] = []

    if signals.top_4_dominant_category:
        cat = signals.top_4_dominant_category.get("category", "")
        if cat:
            categories.append(cat.lower())

    if signals.top_3_dominant_category_subcategory:
        cat = signals.top_3_dominant_category_subcategory.get("category", "")
        if cat:
            categories.append(cat.lower())

    if signals.top_2_most_dominant_product:
        cat = signals.top_2_most_dominant_product.get("category", "")
        if cat:
            categories.append(cat.lower())

    if signals.top_1_most_recent:
        cat = signals.top_1_most_recent.get("category", "")
        if cat:
            categories.append(cat.lower())

    return list(dict.fromkeys(categories))  # deduplicate, preserve priority


def _extract_brands(signals: InterestSignals) -> List[str]:
    """Collect brand mentions from the interest signals."""
    brands: List[str] = []

    for top in [
        signals.top_1_most_recent,
        signals.top_2_most_dominant_product,
    ]:
        if top:
            b = top.get("brand", "")
            if b:
                brands.append(b.lower())

    return list(dict.fromkeys(brands))


def _extract_interest_tokens(signals: InterestSignals) -> List[str]:
    """
    Build a flat token list from all interest signals.
    Used for keyword overlap scoring.
    """
    raw_parts: List[str] = []

    # top_1: query, product, brand, model, category
    if signals.top_1_most_recent:
        for field in ("query", "product", "brand", "model", "category"):
            v = signals.top_1_most_recent.get(field, "")
            if v:
                raw_parts.append(str(v))

    # top_2: product, brand, model, category
    if signals.top_2_most_dominant_product:
        for field in ("product", "brand", "model", "category"):
            v = signals.top_2_most_dominant_product.get(field, "")
            if v:
                raw_parts.append(str(v))

    # top_3: category, subcategory
    if signals.top_3_dominant_category_subcategory:
        for field in ("category", "subcategory"):
            v = signals.top_3_dominant_category_subcategory.get(field, "")
            if v:
                raw_parts.append(str(v))

    # top_4: category
    if signals.top_4_dominant_category:
        v = signals.top_4_dominant_category.get("category", "")
        if v:
            raw_parts.append(str(v))

    # Tokenize everything
    tokens: List[str] = []
    for part in raw_parts:
        tokens.extend(tokenize(part))

    return list(dict.fromkeys(tokens))


# ─────────────────────────────────────────────────────────────────────────────
# Scoring functions
# ─────────────────────────────────────────────────────────────────────────────

def _score_category(ad_category: str, signal_categories: List[str]) -> float:
    """Score category alignment."""
    ad_cat_lower = ad_category.lower()
    for sig_cat in signal_categories:
        if ad_cat_lower == sig_cat:
            return 1.0
        if ad_cat_lower in sig_cat or sig_cat in ad_cat_lower:
            return 0.6
    return 0.0


def _score_keywords(
    ad_keywords: List[str],
    interest_tokens: List[str],
) -> Tuple[float, List[str]]:
    """
    Keyword overlap score + which ad keywords matched.

    Returns:
        (score 0-1, list of matched keywords)
    """
    if not ad_keywords or not interest_tokens:
        return 0.0, []

    interest_set = set(interest_tokens)
    ad_kw_set = set(ad_keywords)

    matched = ad_kw_set & interest_set

    # Also check substring matches (e.g. "laptop" matches "gaming laptop")
    for kw in ad_kw_set - matched:
        for token in interest_tokens:
            if kw in token or token in kw:
                matched.add(kw)
                break

    if not matched:
        return 0.0, []

    # Jaccard-like: |intersection| / |ad keywords|  (penalises huge keyword sets less)
    score = len(matched) / max(len(ad_kw_set), 1)
    return min(score, 1.0), sorted(matched)


def _score_brand(
    ad_brand: Optional[str],
    signal_brands: List[str],
    interest_tokens: List[str],
) -> float:
    """Score brand alignment."""
    if not ad_brand:
        return 0.0

    ad_brand_lower = ad_brand.lower()

    for sb in signal_brands:
        if ad_brand_lower == sb:
            return 1.0
        if ad_brand_lower in sb or sb in ad_brand_lower:
            return 0.5

    # Fallback: brand token present anywhere in interest tokens
    for token in interest_tokens:
        if ad_brand_lower == token:
            return 0.3

    return 0.0


def _extract_top1_product_tokens(signals: InterestSignals) -> List[str]:
    """
    Extract specific product-level tokens from top_1 signal only.
    These are used for high-priority product matching (motorcycle, xpulse, hero, etc.)
    separate from the broad category match.
    """
    if not signals.top_1_most_recent:
        return []
    tokens: List[str] = []
    for field in ("product", "brand", "model", "query"):
        v = signals.top_1_most_recent.get(field, "")
        if v:
            tokens.extend(tokenize(str(v)))
    return list(dict.fromkeys(tokens))


def _compute_score(
    ad: Ad,
    signal_categories: List[str],
    signal_brands: List[str],
    interest_tokens: List[str],
    top1_product_tokens: List[str],
    top1_category: Optional[str],
) -> _ScoredAd:
    """
    Compute composite relevance score for a single ad.

    Scoring layers:
    1. top_1 product match  — specific product/brand/model tokens from most recent search
                              (highest priority: overrides broad category when matched)
    2. Category match       — broad category alignment across all signals
    3. Keyword overlap      — token overlap across all signals
    4. Brand match          — brand name alignment
    """
    w_cat = settings.SCORE_WEIGHT_CATEGORY
    w_kw = settings.SCORE_WEIGHT_KEYWORD
    w_brand = settings.SCORE_WEIGHT_BRAND

    # ── Layer 1: top_1 specific product match ────────────────────────────
    # Score how well this ad matches the specific product the user most recently searched.
    # Uses ad keywords + ad category vs the product/brand/query tokens from top_1.
    top1_kw_score, top1_matched = _score_keywords(ad.keyword_list, top1_product_tokens)

    # Also check if the ad's category directly matches top_1's product or model
    # (e.g. ad category "Motorcycle" matches top_1 product "motorcycle")
    top1_cat_score = 0.0
    if top1_category:
        top1_cat_score = _score_category(ad.category, [top1_category])
    # Check ad category against product tokens too (e.g. "Automotive" in ["motorcycle"])
    for token in top1_product_tokens:
        if token in ad.category.lower() or ad.category.lower() in token:
            top1_cat_score = max(top1_cat_score, 0.8)
            break

    top1_score = max(top1_kw_score, top1_cat_score)

    # ── Layer 2-4: standard scoring across all signals ───────────────────
    cat_score = _score_category(ad.category, signal_categories)
    kw_score, matched_kws = _score_keywords(ad.keyword_list, interest_tokens)
    brand_score = _score_brand(ad.brand, signal_brands, interest_tokens)

    standard_score = (
        cat_score * w_cat
        + kw_score * w_kw
        + brand_score * w_brand
    )

    # ── Final composite ──────────────────────────────────────────────────
    # If top_1 product has a strong match, it dominates the final score.
    # This ensures a motorcycle ad beats a phone ad when user searched for motorcycle.
    if top1_score >= 0.5:
        # Strong top_1 product match: weight it heavily (70%) over standard (30%)
        composite = top1_score * 0.70 + standard_score * 0.30
    elif top1_score > 0:
        # Weak top_1 match: blend with standard
        composite = top1_score * 0.40 + standard_score * 0.60
    else:
        # No top_1 match at all: pure standard scoring
        composite = standard_score

    all_matched_kws = list(dict.fromkeys(top1_matched + matched_kws))

    matched_signals = {
        "category_score": round(cat_score, 4),
        "keyword_score": round(kw_score, 4),
        "brand_score": round(brand_score, 4),
        "top1_product_score": round(top1_score, 4),
        "composite_score": round(composite, 4),
    }

    return _ScoredAd(
        ad=ad,
        score=composite,
        matched_signals=matched_signals,
        matched_keywords=all_matched_kws,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────────────────────

class AdMatcher:
    """
    Matches user interest signals to ads in the repository.

    Usage:
        matcher = AdMatcher()
        response = matcher.serve(db, signals, max_ads=1, record_impression=True)
    """

    def serve(
        self,
        db: Session,
        signals: InterestSignals,
        max_ads: int = 1,
        record_impression: bool = True,
    ) -> ServeAdResponse:
        """
        Score all active ads against user interest signals and return top N.

        Args:
            db: Active DB session.
            signals: InterestSignals extracted from Client API.
            max_ads: Number of ads to return (1–10).
            record_impression: Whether to persist impression records.

        Returns:
            ServeAdResponse with ranked ads and match metadata.

        Raises:
            NoAdsAvailableError: If no active ads exist in DB.
        """
        # Load all active ads
        active_ads = ad_repo.get_active_ads(db)
        if not active_ads:
            raise NoAdsAvailableError("No active ads in repository.")

        total_candidates = len(active_ads)
        logger.debug(f"Scoring {total_candidates} active ads for user={signals.user_id}")

        # Extract signals
        signal_categories = _extract_categories(signals)
        signal_brands = _extract_brands(signals)
        interest_tokens = _extract_interest_tokens(signals)

        logger.debug(
            f"Signal categories={signal_categories} brands={signal_brands} "
            f"tokens={interest_tokens[:10]}..."
        )

        # Extract top_1 specific product tokens (motorcycle, hero, xpulse, etc.)
        top1_product_tokens = _extract_top1_product_tokens(signals)
        top1_category = (
            signals.top_1_most_recent.get("category", "").lower()
            if signals.top_1_most_recent else None
        )
        logger.debug(f"top_1 product tokens={top1_product_tokens} category={top1_category}")

        # Score every ad
        scored: List[_ScoredAd] = [
            _compute_score(ad, signal_categories, signal_brands, interest_tokens,
                           top1_product_tokens, top1_category)
            for ad in active_ads
        ]

        # Filter by minimum threshold
        min_score = settings.MIN_SERVING_SCORE
        scored = [s for s in scored if s.score >= min_score]

        if not scored:
            # Fallback: return highest-scoring ad regardless of threshold
            scored = [max(
                [_compute_score(ad, signal_categories, signal_brands, interest_tokens,
                                top1_product_tokens, top1_category)
                 for ad in active_ads],
                key=lambda s: s.score,
            )]
            logger.info("All ads below min threshold; returning fallback best match.")

        # Sort descending by score, take top N
        scored.sort(key=lambda s: s.score, reverse=True)
        top_scored = scored[:max_ads]

        # Build response
        served_ads: List[ServedAd] = []
        for rank, s in enumerate(top_scored, start=1):
            impression_id = None
            if record_impression:
                impression_id = self._record_impression(
                    db=db,
                    ad=s.ad,
                    user_id=signals.user_id,
                    matched_category=signal_categories[0] if signal_categories else None,
                    matched_keywords=s.matched_keywords,
                    relevance_score=s.score,
                    match_rank=rank,
                )

            served_ads.append(
                ServedAd(
                    ad_id=s.ad.id,
                    title=s.ad.title,
                    description=s.ad.description,
                    image_url=s.ad.image_url,
                    destination_url=s.ad.destination_url,
                    category=s.ad.category,
                    brand=s.ad.brand,
                    keywords=s.ad.keyword_list,
                    relevance_score=round(s.score, 4),
                    match_rank=rank,
                    matched_signals=s.matched_signals,
                    impression_id=impression_id,
                )
            )

        signals_used = {
            "categories": signal_categories,
            "brands": signal_brands,
            "interest_tokens": interest_tokens[:20],
        }

        logger.info(
            f"Served {len(served_ads)} ad(s) for user={signals.user_id} "
            f"top_score={top_scored[0].score:.4f}"
        )

        return ServeAdResponse(
            user_id=signals.user_id,
            ads=served_ads,
            total_candidates_evaluated=total_candidates,
            signals_used=signals_used,
        )

    # ── Private ───────────────────────────────────────────────────────────

    def _record_impression(
        self,
        db: Session,
        ad: Ad,
        user_id: str,
        matched_category: Optional[str],
        matched_keywords: List[str],
        relevance_score: float,
        match_rank: int,
    ) -> int:
        """Persist an AdImpression row and return its id."""
        imp = AdImpression(
            ad_id=ad.id,
            user_id=user_id,
            matched_category=matched_category,
            relevance_score=relevance_score,
            match_rank=match_rank,
        )
        imp.set_matched_keywords(matched_keywords)
        db.add(imp)
        db.commit()
        db.refresh(imp)
        return imp.id