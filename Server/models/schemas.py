"""
Pydantic v2 request/response schemas.

Naming convention:
    <Entity>Create   — POST body (inbound, no id)
    <Entity>Update   — PATCH body (all fields optional)
    <Entity>Out      — Response (includes id, timestamps)
    <Entity>Summary  — Lightweight response for list endpoints
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# Ad Keyword
# ─────────────────────────────────────────────────────────────────────────────

class AdKeywordOut(BaseModel):
    id: int
    keyword: str

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Ad CRUD
# ─────────────────────────────────────────────────────────────────────────────

class AdCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Ad headline")
    description: str = Field(..., min_length=10, description="Ad body copy")
    image_url: Optional[str] = Field(None, description="Creative image URL or upload path")
    destination_url: Optional[str] = Field(None, description="Click-through URL")

    category: str = Field(..., min_length=2, max_length=100, description="Targeting category (e.g. Electronics)")
    brand: Optional[str] = Field(None, max_length=100, description="Brand name for brand-match targeting")
    keywords: List[str] = Field(
        default_factory=list,
        description="Targeting keywords (max 20)",
    )

    budget: float = Field(0.0, ge=0.0, description="Total budget in USD")
    bid_cpm: float = Field(0.0, ge=0.0, description="Bid per 1000 impressions in USD")
    is_active: bool = Field(True, description="Whether the ad is eligible to be served")

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        if len(v) > 20:
            raise ValueError("Maximum 20 targeting keywords allowed.")
        cleaned = [kw.strip().lower() for kw in v if kw.strip()]
        return list(dict.fromkeys(cleaned))  # deduplicate, preserve order

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        return v.strip().title()

    @field_validator("brand")
    @classmethod
    def normalize_brand(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().title() if v else None


class AdUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    image_url: Optional[str] = None
    destination_url: Optional[str] = None
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    keywords: Optional[List[str]] = None
    budget: Optional[float] = Field(None, ge=0.0)
    bid_cpm: Optional[float] = Field(None, ge=0.0)
    is_active: Optional[bool] = None

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        if len(v) > 20:
            raise ValueError("Maximum 20 targeting keywords allowed.")
        return [kw.strip().lower() for kw in v if kw.strip()]

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().title() if v else None


class AdOut(BaseModel):
    id: int
    title: str
    description: str
    image_url: Optional[str]
    destination_url: Optional[str]
    category: str
    brand: Optional[str]
    keywords: List[str] = Field(default_factory=list)
    budget: float
    bid_cpm: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Aggregated analytics (populated separately)
    impression_count: Optional[int] = None
    click_count: Optional[int] = None
    ctr: Optional[float] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def extract_keywords(cls, data: Any) -> Any:
        # ORM object → flatten keyword_list into keywords
        if hasattr(data, "keyword_list"):
            data.__dict__["keywords"] = data.keyword_list
        return data


class AdSummary(BaseModel):
    id: int
    title: str
    category: str
    brand: Optional[str]
    is_active: bool
    impression_count: Optional[int] = None
    click_count: Optional[int] = None
    ctr: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Ad Serving
# ─────────────────────────────────────────────────────────────────────────────

class InterestSignals(BaseModel):
    """
    Mirrors the output from the Client-side ExtractionEngine.
    All top-N fields are optional so partial results still work.
    """
    user_id: str = Field(..., description="User identifier passed to Client API")

    # top_1: most recent product search
    top_1_most_recent: Optional[Dict[str, Any]] = None

    # top_2: most dominant product (highest cumulative engagement)
    top_2_most_dominant_product: Optional[Dict[str, Any]] = None

    # top_3: dominant category + subcategory
    top_3_dominant_category_subcategory: Optional[Dict[str, Any]] = None

    # top_4: dominant category
    top_4_dominant_category: Optional[Dict[str, Any]] = None

    # passthrough metadata from client
    client_metadata: Optional[Dict[str, Any]] = None


class ServeAdRequest(BaseModel):
    """Request body for the /serve endpoint."""
    user_id: str = Field(..., description="User identifier — server will call Client API internally")
    max_ads: int = Field(1, ge=1, le=10, description="Number of ads to return")
    record_impression: bool = Field(True, description="Whether to persist an impression record")


class ServeAdFromSignalsRequest(BaseModel):
    """
    Serve ads directly from pre-computed interest signals.
    Used by the demo UI after it has already fetched client data.
    """
    signals: InterestSignals
    max_ads: int = Field(1, ge=1, le=10)
    record_impression: bool = Field(True)


class ServedAd(BaseModel):
    """A single ad returned by the serving engine, with match metadata."""
    ad_id: int
    title: str
    description: str
    image_url: Optional[str]
    destination_url: Optional[str]
    category: str
    brand: Optional[str]
    keywords: List[str]

    # Match metadata
    relevance_score: float = Field(..., description="0.0 – 1.0 composite relevance score")
    match_rank: int = Field(..., description="1 = best match")
    matched_signals: Dict[str, Any] = Field(
        default_factory=dict,
        description="Which interest signals contributed to this match",
    )
    impression_id: Optional[int] = Field(None, description="DB impression record id (if recorded)")

    model_config = {"from_attributes": True}


class ServeAdResponse(BaseModel):
    user_id: str
    ads: List[ServedAd]
    total_candidates_evaluated: int
    signals_used: Dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────────────────────────────────

class AdAnalytics(BaseModel):
    """Per-ad analytics snapshot."""
    ad_id: int
    title: str
    category: str
    brand: Optional[str]
    impression_count: int
    click_count: int
    ctr: float
    budget: float
    bid_cpm: float
    is_active: bool
    created_at: datetime


class CategoryAnalytics(BaseModel):
    category: str
    ad_count: int
    total_impressions: int
    total_clicks: int
    avg_ctr: float


class OverallAnalytics(BaseModel):
    total_ads: int
    active_ads: int
    inactive_ads: int
    total_impressions: int
    total_clicks: int
    overall_ctr: float
    top_categories: List[CategoryAnalytics]
    top_ads_by_impressions: List[AdAnalytics]
    top_ads_by_ctr: List[AdAnalytics]


# ─────────────────────────────────────────────────────────────────────────────
# Shared
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    components: Dict[str, str]


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# ─────────────────────────────────────────────────────────────────────────────
# Ad Generation (LLM-assisted)
# ─────────────────────────────────────────────────────────────────────────────

class AdGenerateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Ad headline")
    description: str = Field(..., min_length=10, description="Ad body copy")
    brand: Optional[str] = Field(None, max_length=100, description="Brand name (optional)")
    destination_url: Optional[str] = Field(None, description="Click-through URL (optional)")


class AdGenerateResponse(BaseModel):
    category: str = Field(..., description="Suggested targeting category")
    keywords: List[str] = Field(..., description="Suggested targeting keywords")
    confidence: float = Field(..., description="LLM confidence score 0-1")
    llm_used: bool = Field(..., description="True if LLM was used, False if heuristic fallback")