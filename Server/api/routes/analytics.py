"""
Analytics routes.

GET /analytics/overview          — Platform-wide stats
GET /analytics/ads/{id}          — Per-ad stats
GET /analytics/keywords          — Keyword frequency distribution
GET /analytics/impressions/time  — Daily impression time-series
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_ad_analyzer
from db.session import get_db
from models.schemas import AdAnalytics, OverallAnalytics
from services.ad_analyzer import AdAnalyzer

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/overview",
    response_model=OverallAnalytics,
    summary="Platform-wide analytics overview",
)
def get_overview(
    top_n: int = Query(5, ge=1, le=20, description="Top N ads per ranked list"),
    db: Session = Depends(get_db),
    analyzer: AdAnalyzer = Depends(get_ad_analyzer),
):
    """
    Returns:
    - Total / active / inactive ad counts
    - Overall impressions, clicks, CTR
    - Top categories by impressions
    - Top ads by impressions and by CTR
    """
    return analyzer.get_overall_analytics(db, top_n=top_n)


@router.get(
    "/ads/{ad_id}",
    response_model=AdAnalytics,
    summary="Analytics for a single ad",
)
def get_ad_analytics(
    ad_id: int,
    db: Session = Depends(get_db),
    analyzer: AdAnalyzer = Depends(get_ad_analyzer),
):
    from core.exceptions import AdNotFoundError
    from fastapi import HTTPException, status

    try:
        return analyzer.get_ad_analytics(db, ad_id)
    except AdNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "AdNotFound", "ad_id": ad_id},
        )


@router.get(
    "/keywords",
    summary="Keyword frequency across all ads",
)
def get_keyword_distribution(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    analyzer: AdAnalyzer = Depends(get_ad_analyzer),
):
    return {"keywords": analyzer.keyword_distribution(db, limit=limit)}


@router.get(
    "/impressions/time",
    summary="Daily impression counts (time-series)",
)
def get_impressions_over_time(
    ad_id: Optional[int] = Query(None, description="Filter to a specific ad"),
    db: Session = Depends(get_db),
    analyzer: AdAnalyzer = Depends(get_ad_analyzer),
):
    return {"series": analyzer.impressions_over_time(db, ad_id=ad_id)}