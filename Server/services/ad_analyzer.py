"""
Ad Analytics Engine.

Provides:
  - Per-ad analytics (impressions, clicks, CTR)
  - Category-level aggregations
  - Overall platform analytics
  - Keyword frequency distribution
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.orm import Ad, AdClick, AdImpression
from models.schemas import AdAnalytics, CategoryAnalytics, OverallAnalytics
from utils.logging import get_logger

logger = get_logger(__name__)


def _ad_to_analytics(
    ad: Ad,
    imp_count: int,
    click_count: int,
) -> AdAnalytics:
    ctr = (click_count / imp_count) if imp_count > 0 else 0.0
    return AdAnalytics(
        ad_id=ad.id,
        title=ad.title,
        category=ad.category,
        brand=ad.brand,
        impression_count=imp_count,
        click_count=click_count,
        ctr=round(ctr, 6),
        budget=ad.budget,
        bid_cpm=ad.bid_cpm,
        is_active=ad.is_active,
        created_at=ad.created_at,
    )


class AdAnalyzer:
    """
    Computes analytics from the impressions / clicks event tables.
    All queries are read-only.
    """

    # ── Per-ad ────────────────────────────────────────────────────────────

    def get_ad_analytics(self, db: Session, ad_id: int) -> AdAnalytics:
        """Return impression/click counts for a single ad."""
        ad = db.get(Ad, ad_id)
        if ad is None:
            from core.exceptions import AdNotFoundError
            raise AdNotFoundError(ad_id)

        imp_count = db.scalar(
            select(func.count(AdImpression.id)).where(AdImpression.ad_id == ad_id)
        ) or 0
        click_count = db.scalar(
            select(func.count(AdClick.id)).where(AdClick.ad_id == ad_id)
        ) or 0

        return _ad_to_analytics(ad, imp_count, click_count)

    # ── Overall ───────────────────────────────────────────────────────────

    def get_overall_analytics(
        self,
        db: Session,
        top_n: int = 5,
    ) -> OverallAnalytics:
        """
        Compute platform-wide analytics.

        Args:
            db: DB session.
            top_n: How many top ads to include in each ranked list.

        Returns:
            OverallAnalytics schema.
        """
        # ── Counts ────────────────────────────────────────────────────────
        total_ads = db.scalar(select(func.count(Ad.id))) or 0
        active_ads = db.scalar(
            select(func.count(Ad.id)).where(Ad.is_active.is_(True))
        ) or 0
        total_impressions = db.scalar(select(func.count(AdImpression.id))) or 0
        total_clicks = db.scalar(select(func.count(AdClick.id))) or 0
        overall_ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0.0

        # ── Per-ad aggregations ────────────────────────────────────────────
        all_ads = list(db.scalars(select(Ad)).all())
        ad_analytics_list = self._bulk_analytics(db, all_ads)

        # ── Category aggregations ──────────────────────────────────────────
        cat_map: Dict[str, CategoryAnalytics] = {}
        for aa in ad_analytics_list:
            cat = aa.category
            if cat not in cat_map:
                cat_map[cat] = CategoryAnalytics(
                    category=cat,
                    ad_count=0,
                    total_impressions=0,
                    total_clicks=0,
                    avg_ctr=0.0,
                )
            cat_map[cat].ad_count += 1
            cat_map[cat].total_impressions += aa.impression_count
            cat_map[cat].total_clicks += aa.click_count

        # Recompute avg_ctr per category
        for cat_stat in cat_map.values():
            if cat_stat.total_impressions > 0:
                cat_stat.avg_ctr = round(
                    cat_stat.total_clicks / cat_stat.total_impressions, 6
                )

        top_categories = sorted(
            cat_map.values(),
            key=lambda c: c.total_impressions,
            reverse=True,
        )[:top_n]

        # ── Ranked ad lists ────────────────────────────────────────────────
        top_by_impressions = sorted(
            ad_analytics_list, key=lambda a: a.impression_count, reverse=True
        )[:top_n]

        top_by_ctr = sorted(
            [a for a in ad_analytics_list if a.impression_count >= 5],
            key=lambda a: a.ctr,
            reverse=True,
        )[:top_n]

        return OverallAnalytics(
            total_ads=total_ads,
            active_ads=active_ads,
            inactive_ads=total_ads - active_ads,
            total_impressions=total_impressions,
            total_clicks=total_clicks,
            overall_ctr=round(overall_ctr, 6),
            top_categories=top_categories,
            top_ads_by_impressions=top_by_impressions,
            top_ads_by_ctr=top_by_ctr,
        )

    # ── Keyword distribution ───────────────────────────────────────────────

    def keyword_distribution(self, db: Session, limit: int = 20) -> Dict[str, int]:
        """
        Return frequency of each targeting keyword across all ads.
        """
        from models.orm import AdKeyword
        rows = db.execute(
            select(AdKeyword.keyword, func.count(AdKeyword.id).label("cnt"))
            .group_by(AdKeyword.keyword)
            .order_by(func.count(AdKeyword.id).desc())
            .limit(limit)
        ).all()
        return {row.keyword: row.cnt for row in rows}

    # ── Impression time-series ─────────────────────────────────────────────

    def impressions_over_time(
        self, db: Session, ad_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Daily impression counts (last 30 days).
        Optionally filtered to a single ad.
        """
        from sqlalchemy import cast, Date
        stmt = (
            select(
                cast(AdImpression.served_at, Date).label("day"),
                func.count(AdImpression.id).label("impressions"),
            )
            .group_by("day")
            .order_by("day")
        )
        if ad_id is not None:
            stmt = stmt.where(AdImpression.ad_id == ad_id)

        rows = db.execute(stmt).all()
        return [{"day": str(row.day), "impressions": row.impressions} for row in rows]

    # ── Private helpers ────────────────────────────────────────────────────

    def _bulk_analytics(
        self, db: Session, ads: List[Ad]
    ) -> List[AdAnalytics]:
        """Efficiently compute analytics for a list of ads in 2 queries."""
        if not ads:
            return []

        ad_ids = [a.id for a in ads]

        # Impressions per ad
        imp_rows = db.execute(
            select(
                AdImpression.ad_id, func.count(AdImpression.id).label("cnt")
            )
            .where(AdImpression.ad_id.in_(ad_ids))
            .group_by(AdImpression.ad_id)
        ).all()
        imp_map = {row.ad_id: row.cnt for row in imp_rows}

        # Clicks per ad
        click_rows = db.execute(
            select(AdClick.ad_id, func.count(AdClick.id).label("cnt"))
            .where(AdClick.ad_id.in_(ad_ids))
            .group_by(AdClick.ad_id)
        ).all()
        click_map = {row.ad_id: row.cnt for row in click_rows}

        return [
            _ad_to_analytics(ad, imp_map.get(ad.id, 0), click_map.get(ad.id, 0))
            for ad in ads
        ]