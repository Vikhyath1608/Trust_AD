"""
Ad Repository Service.

Handles all CRUD operations for ads and their targeting keywords.
File upload is handled separately (returns a URL string stored in ad.image_url).
"""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.config import get_settings
from core.exceptions import AdNotFoundError, AdValidationError, UploadError
from models.orm import Ad, AdKeyword
from models.schemas import AdCreate, AdUpdate
from utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AdRepository:
    """
    Manages the Ad creative repository.

    All methods receive a SQLAlchemy Session injected via FastAPI dependency.
    """

    # ── Create ────────────────────────────────────────────────────────────

    def create_ad(self, db: Session, payload: AdCreate) -> Ad:
        """
        Persist a new Ad plus its targeting keywords.

        Args:
            db: Active DB session.
            payload: Validated AdCreate schema.

        Returns:
            Persisted Ad ORM instance (with id populated).
        """
        ad = Ad(
            title=payload.title,
            description=payload.description,
            image_url=payload.image_url,
            destination_url=payload.destination_url,
            category=payload.category,
            brand=payload.brand,
            budget=payload.budget,
            bid_cpm=payload.bid_cpm,
            is_active=payload.is_active,
        )
        db.add(ad)
        db.flush()  # get ad.id without committing

        # Attach keywords
        self._sync_keywords(db, ad, payload.keywords)

        db.commit()
        db.refresh(ad)
        logger.info(f"Created Ad id={ad.id} title={ad.title!r}")
        return ad

    # ── Read ──────────────────────────────────────────────────────────────

    def get_by_id(self, db: Session, ad_id: int) -> Ad:
        """
        Fetch a single Ad by primary key.

        Raises:
            AdNotFoundError: if not found.
        """
        ad = db.get(Ad, ad_id)
        if ad is None:
            raise AdNotFoundError(ad_id)
        return ad

    def list_ads(
        self,
        db: Session,
        active_only: bool = False,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Ad], int]:
        """
        List ads with optional filters and pagination.

        Returns:
            (list of Ad, total count)
        """
        stmt = select(Ad)

        if active_only:
            stmt = stmt.where(Ad.is_active.is_(True))
        if category:
            stmt = stmt.where(func.lower(Ad.category) == category.lower())
        if brand:
            stmt = stmt.where(func.lower(Ad.brand) == brand.lower())

        total: int = db.scalar(select(func.count()).select_from(stmt.subquery()))

        stmt = stmt.order_by(Ad.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        ads = list(db.scalars(stmt).all())
        return ads, total

    def get_active_ads(self, db: Session) -> List[Ad]:
        """
        Return ALL active ads (used by the matching engine).
        """
        stmt = select(Ad).where(Ad.is_active.is_(True)).order_by(Ad.created_at.desc())
        return list(db.scalars(stmt).all())

    # ── Update ────────────────────────────────────────────────────────────

    def update_ad(self, db: Session, ad_id: int, payload: AdUpdate) -> Ad:
        """
        Partially update an Ad.

        Raises:
            AdNotFoundError: if not found.
        """
        ad = self.get_by_id(db, ad_id)

        update_data = payload.model_dump(exclude_unset=True)

        # Keywords are handled separately
        new_keywords = update_data.pop("keywords", None)

        for field, value in update_data.items():
            setattr(ad, field, value)

        if new_keywords is not None:
            self._sync_keywords(db, ad, new_keywords)

        db.commit()
        db.refresh(ad)
        logger.info(f"Updated Ad id={ad.id}")
        return ad

    def toggle_active(self, db: Session, ad_id: int) -> Ad:
        """Toggle is_active flag."""
        ad = self.get_by_id(db, ad_id)
        ad.is_active = not ad.is_active
        db.commit()
        db.refresh(ad)
        logger.info(f"Ad id={ad.id} is_active → {ad.is_active}")
        return ad

    # ── Delete ────────────────────────────────────────────────────────────

    def delete_ad(self, db: Session, ad_id: int) -> None:
        """
        Hard-delete an Ad and cascade to keywords/impressions/clicks.

        Raises:
            AdNotFoundError: if not found.
        """
        ad = self.get_by_id(db, ad_id)

        # Remove uploaded image file if stored locally
        if ad.image_url and ad.image_url.startswith("/uploads/"):
            self._delete_file(ad.image_url)

        db.delete(ad)
        db.commit()
        logger.info(f"Deleted Ad id={ad_id}")

    # ── File Upload ───────────────────────────────────────────────────────

    def save_uploaded_image(
        self,
        file_bytes: bytes,
        content_type: str,
        original_filename: str,
    ) -> str:
        """
        Save an uploaded image to UPLOAD_DIR.

        Returns:
            Relative URL string (e.g. "/uploads/ad_creatives/abc123.jpg")

        Raises:
            UploadError: on size or type violation.
        """
        # Validate type
        allowed = settings.ALLOWED_IMAGE_TYPES
        if content_type not in allowed:
            raise UploadError(
                f"File type '{content_type}' not allowed. Allowed: {allowed}"
            )

        # Validate size
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise UploadError(
                f"File size {len(file_bytes)} bytes exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit."
            )

        # Build path
        ext = Path(original_filename).suffix.lower() or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / filename

        dest.write_bytes(file_bytes)
        logger.info(f"Saved ad creative: {dest}")

        return f"/uploads/ad_creatives/{filename}"

    # ── Private helpers ───────────────────────────────────────────────────

    def _sync_keywords(
        self, db: Session, ad: Ad, new_keywords: List[str]
    ) -> None:
        """Replace the keyword set for an Ad (delete old, insert new)."""
        # Remove existing
        for kw in ad.keywords:
            db.delete(kw)
        db.flush()

        # Insert new
        for kw_text in new_keywords:
            db.add(AdKeyword(ad_id=ad.id, keyword=kw_text))

    def _delete_file(self, url_path: str) -> None:
        """Best-effort removal of a locally stored file."""
        try:
            # Strip leading /
            rel = url_path.lstrip("/")
            full = Path(rel)
            if full.exists():
                full.unlink()
                logger.debug(f"Removed file: {full}")
        except Exception as exc:
            logger.warning(f"Could not remove file {url_path}: {exc}")