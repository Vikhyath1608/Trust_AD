"""
Ad management routes.

POST   /ads/               — Create ad
GET    /ads/               — List ads (paginated, filterable)
GET    /ads/{id}           — Get single ad
PATCH  /ads/{id}           — Update ad
DELETE /ads/{id}           — Delete ad
PATCH  /ads/{id}/toggle    — Toggle active status
POST   /ads/upload-image   — Upload creative image → returns URL
"""
import math
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from api.dependencies import get_ad_repository, get_ad_generator
from core.exceptions import AdNotFoundError, AdValidationError, UploadError
from db.session import get_db
from models.schemas import (
    AdCreate,
    AdOut,
    AdSummary,
    AdUpdate,
    AdGenerateRequest,
    AdGenerateResponse,
    PaginatedResponse,
)
from services.ad_repository import AdRepository
from services.ad_generator import AdGeneratorService

router = APIRouter(prefix="/ads", tags=["Ad Management"])


def _ad_not_found(ad_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": "AdNotFound", "ad_id": ad_id},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Create
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=AdOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ad",
)
def create_ad(
    payload: AdCreate,
    db: Session = Depends(get_db),
    repo: AdRepository = Depends(get_ad_repository),
):
    """
    Upload a new ad creative to the repository.

    - **title**: Ad headline (3–255 chars)
    - **description**: Ad body copy
    - **category**: Primary targeting category (e.g. *Electronics*, *Fashion*)
    - **keywords**: Up to 20 targeting keywords
    - **budget**: Total budget in USD
    - **bid_cpm**: Bid per 1000 impressions
    """
    try:
        ad = repo.create_ad(db, payload)
        return _enrich_ad_out(ad)
    except AdValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# List
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="List ads with optional filters",
)
def list_ads(
    active_only: bool = Query(False, description="Return only active ads"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    repo: AdRepository = Depends(get_ad_repository),
):
    ads, total = repo.list_ads(
        db,
        active_only=active_only,
        category=category,
        brand=brand,
        page=page,
        page_size=page_size,
    )

    items = [_to_summary(ad) for ad in ads]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Get by ID
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{ad_id}", response_model=AdOut, summary="Get ad by ID")
def get_ad(
    ad_id: int,
    db: Session = Depends(get_db),
    repo: AdRepository = Depends(get_ad_repository),
):
    try:
        ad = repo.get_by_id(db, ad_id)
        return _enrich_ad_out(ad)
    except AdNotFoundError:
        raise _ad_not_found(ad_id)


# ─────────────────────────────────────────────────────────────────────────────
# Update
# ─────────────────────────────────────────────────────────────────────────────

@router.patch("/{ad_id}", response_model=AdOut, summary="Partially update an ad")
def update_ad(
    ad_id: int,
    payload: AdUpdate,
    db: Session = Depends(get_db),
    repo: AdRepository = Depends(get_ad_repository),
):
    try:
        ad = repo.update_ad(db, ad_id, payload)
        return _enrich_ad_out(ad)
    except AdNotFoundError:
        raise _ad_not_found(ad_id)


# ─────────────────────────────────────────────────────────────────────────────
# Toggle active
# ─────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/{ad_id}/toggle",
    response_model=AdOut,
    summary="Toggle ad active/inactive status",
)
def toggle_ad_active(
    ad_id: int,
    db: Session = Depends(get_db),
    repo: AdRepository = Depends(get_ad_repository),
):
    try:
        ad = repo.toggle_active(db, ad_id)
        return _enrich_ad_out(ad)
    except AdNotFoundError:
        raise _ad_not_found(ad_id)


# ─────────────────────────────────────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────────────────────────────────────

@router.delete(
    "/{ad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an ad",
)
def delete_ad(
    ad_id: int,
    db: Session = Depends(get_db),
    repo: AdRepository = Depends(get_ad_repository),
):
    try:
        repo.delete_ad(db, ad_id)
    except AdNotFoundError:
        raise _ad_not_found(ad_id)


# ─────────────────────────────────────────────────────────────────────────────
# Image upload
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# AI Generate category + keywords
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=AdGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="AI-generate category and keywords from ad creative",
)
def generate_ad_metadata(
    payload: AdGenerateRequest,
    generator: AdGeneratorService = Depends(get_ad_generator),
):
    """
    Calls the Hugging Face LLM (Llama-3.1-8B) to analyse the ad title,
    description, brand and landing URL, then returns a suggested targeting
    category and a list of relevant keywords.

    Falls back to a lightweight heuristic if the LLM is unavailable.
    """
    result = generator.generate(
        title=payload.title,
        description=payload.description,
        brand=payload.brand,
        destination_url=payload.destination_url,
    )
    return AdGenerateResponse(**result)


@router.post(
    "/upload-image",
    summary="Upload an ad creative image",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def upload_ad_image(
    file: UploadFile = File(..., description="JPEG, PNG, WebP or GIF image"),
    repo: AdRepository = Depends(get_ad_repository),
):
    """
    Upload a creative image.  Returns the URL to store in `image_url` when creating an ad.
    """
    try:
        file_bytes = await file.read()
        url = repo.save_uploaded_image(
            file_bytes=file_bytes,
            content_type=file.content_type or "image/jpeg",
            original_filename=file.filename or "upload.jpg",
        )
        return {"image_url": url, "filename": file.filename, "size_bytes": len(file_bytes)}
    except UploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _enrich_ad_out(ad) -> AdOut:
    """Build AdOut — include live analytics counts."""
    out = AdOut.model_validate(ad)
    out.impression_count = ad.impression_count
    out.click_count = ad.click_count
    out.ctr = ad.ctr
    return out


def _to_summary(ad) -> AdSummary:
    s = AdSummary.model_validate(ad)
    s.impression_count = ad.impression_count
    s.click_count = ad.click_count
    s.ctr = ad.ctr
    return s