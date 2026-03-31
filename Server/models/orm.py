"""
SQLAlchemy ORM models.

Tables:
    ads             — Ad creative repository
    ad_keywords     — Targeting keywords per ad (many-to-one)
    ad_impressions  — Every time an ad was served
    ad_clicks       — Every time an ad was clicked (future hook)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# Ads
# ─────────────────────────────────────────────────────────────────────────────

class Ad(Base):
    """Core ad creative with targeting metadata."""

    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Creative content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    destination_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Targeting
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Budget / pacing
    budget: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    bid_cpm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # Cost per 1000 impressions

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, server_default=func.now()
    )

    # Relationships
    keywords: Mapped[List["AdKeyword"]] = relationship(
        "AdKeyword", back_populates="ad", cascade="all, delete-orphan", lazy="selectin"
    )
    impressions: Mapped[List["AdImpression"]] = relationship(
        "AdImpression", back_populates="ad", cascade="all, delete-orphan", lazy="dynamic"
    )
    clicks: Mapped[List["AdClick"]] = relationship(
        "AdClick", back_populates="ad", cascade="all, delete-orphan", lazy="dynamic"
    )

    # ── Convenience helpers ────────────────────────────────────────────────

    @property
    def keyword_list(self) -> List[str]:
        return [kw.keyword for kw in self.keywords]

    @property
    def impression_count(self) -> int:
        return self.impressions.count()

    @property
    def click_count(self) -> int:
        return self.clicks.count()

    @property
    def ctr(self) -> float:
        imp = self.impression_count
        return (self.click_count / imp) if imp > 0 else 0.0

    def __repr__(self) -> str:
        return f"<Ad id={self.id} title={self.title!r} category={self.category!r}>"


class AdKeyword(Base):
    """Targeting keyword associated with an ad."""

    __tablename__ = "ad_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)

    ad: Mapped["Ad"] = relationship("Ad", back_populates="keywords")

    __table_args__ = (
        Index("ix_ad_keywords_ad_keyword", "ad_id", "keyword", unique=True),
    )

    def __repr__(self) -> str:
        return f"<AdKeyword ad_id={self.ad_id} keyword={self.keyword!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Impressions & Clicks  (event tables)
# ─────────────────────────────────────────────────────────────────────────────

class AdImpression(Base):
    """
    Recorded every time an ad is returned by the serving engine.
    Captures which interest signals triggered the match.
    """

    __tablename__ = "ad_impressions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Signals used for matching
    matched_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    matched_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    match_rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1 = best match

    served_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), index=True
    )

    ad: Mapped["Ad"] = relationship("Ad", back_populates="impressions")

    def set_matched_keywords(self, keywords: List[str]) -> None:
        self.matched_keywords = json.dumps(keywords)

    def get_matched_keywords(self) -> List[str]:
        if self.matched_keywords:
            return json.loads(self.matched_keywords)
        return []

    def __repr__(self) -> str:
        return f"<AdImpression id={self.id} ad_id={self.ad_id} user={self.user_id}>"


class AdClick(Base):
    """
    Recorded when a user clicks an ad (future hook — called from demo UI).
    """

    __tablename__ = "ad_clicks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    impression_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("ad_impressions.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    ad: Mapped["Ad"] = relationship("Ad", back_populates="clicks")

    def __repr__(self) -> str:
        return f"<AdClick id={self.id} ad_id={self.ad_id}>"