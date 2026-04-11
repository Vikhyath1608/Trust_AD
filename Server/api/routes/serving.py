"""
Ad Serving routes.

POST /serve                  — Serve ad by user_id (server calls Client API internally)
POST /serve/from-signals     — Serve ad from pre-computed interest signals (used by demo UI)
POST /ads/{id}/click         — Record a click event
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_ad_matcher
from core.exceptions import NoAdsAvailableError
from db.session import get_db
from models.orm import AdClick
from models.schemas import (
    ServeAdFromSignalsRequest,
    ServeAdRequest,
    ServeAdResponse,
)
from services.ad_matcher import AdMatcher
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Ad Serving"])


# ─────────────────────────────────────────────────────────────────────────────
# Serve by user_id  (server fetches interests from Client API)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/serve",
    response_model=ServeAdResponse,
    summary="Serve ads — server calls Client API internally",
)
def serve_ad(
    request: ServeAdRequest,
    db: Session = Depends(get_db),
    matcher: AdMatcher = Depends(get_ad_matcher),
):
    """
    Full pipeline:

    1. Server calls Client API `/extract` with `user_id`
    2. Extracts top-4 interest signals
    3. Runs ad matching against DB
    4. Returns ranked ads

    Use this when you want the server to own the full flow.
    """
    from core.config import get_settings
    import httpx

    settings = get_settings()

    # ── Call Client API ────────────────────────────────────────────────────
    try:
        client_url = f"{settings.CLIENT_API_URL}/extract"
        payload = {
            "user_id": request.user_id,
            "max_products": 100,
            "verbose": False,
        }
        with httpx.Client(timeout=settings.CLIENT_API_TIMEOUT) as client:
            resp = client.post(client_url, json=payload)
            resp.raise_for_status()
            client_data = resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "ClientAPIError",
                "message": f"Client API returned {exc.response.status_code}",
                "user_id": request.user_id,
            },
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ClientAPIUnreachable",
                "message": str(exc),
                "hint": "Ensure Client API is running and CLIENT_API_URL is correct.",
            },
        )

    # ── Build signals ──────────────────────────────────────────────────────
    from models.schemas import InterestSignals

    signals = InterestSignals(
        user_id=request.user_id,
        top_1_most_recent=client_data.get("top_1_most_recent"),
        top_2_most_dominant_product=client_data.get("top_2_most_dominant_product"),
        top_3_dominant_category_subcategory=client_data.get(
            "top_3_dominant_category_subcategory"
        ),
        top_4_dominant_category=client_data.get("top_4_dominant_category"),
        client_metadata=client_data.get("metadata"),
    )

    # ── Match ads ──────────────────────────────────────────────────────────
    try:
        return matcher.serve(
            db=db,
            signals=signals,
            max_ads=request.max_ads,
            record_impression=request.record_impression,
        )
    except NoAdsAvailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NoAdsAvailable", "message": str(exc)},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Serve from pre-computed signals  (demo UI uses this)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/serve/from-signals",
    response_model=ServeAdResponse,
    summary="Serve ads from pre-computed interest signals",
)
def serve_ad_from_signals(
    request: ServeAdFromSignalsRequest,
    db: Session = Depends(get_db),
    matcher: AdMatcher = Depends(get_ad_matcher),
):
    """
    Serve ads using interest signals already extracted by the caller.

    The demo UI calls Client API → receives signals → passes them here.
    This avoids a second round-trip to the Client service.
    """
    try:
        return matcher.serve(
            db=db,
            signals=request.signals,
            max_ads=request.max_ads,
            record_impression=request.record_impression,
        )
    except NoAdsAvailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NoAdsAvailable", "message": str(exc)},
        )


# ─────────────────────────────────────────────────────────────────────────────
# Click recording
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/ads/{ad_id}/click",
    status_code=status.HTTP_200_OK,
    summary="Record a click event for an ad",
)
def record_click(
    ad_id: int,
    impression_id: int | None = None,
    user_id: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Record that a user clicked an ad.
    Called from the demo UI when the user clicks the served creative.
    """
    click = AdClick(
        ad_id=ad_id,
        impression_id=impression_id,
        user_id=user_id,
    )
    db.add(click)
    db.commit()
    db.refresh(click)
    return {"click_id": click.id, "ad_id": ad_id, "recorded": True}