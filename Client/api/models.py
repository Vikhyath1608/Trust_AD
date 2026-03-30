"""
Pydantic models for API requests and responses.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    """Request model for user interest extraction."""
    user_id: str = Field(..., description="User identifier", min_length=1)
    max_products: Optional[int] = Field(100, description="Maximum products to extract", ge=1, le=1000)
    alpha: Optional[float] = Field(1.0, description="Weight for ClickCount", ge=0.0)
    beta: Optional[float] = Field(1.0, description="Weight for Frequency", ge=0.0)
    semantic_threshold: Optional[float] = Field(0.85, description="Semantic search threshold", ge=0.0, le=1.0)
    verbose: Optional[bool] = Field(False, description="Enable verbose logging")


class BrowserHistoryRequest(BaseModel):
    """Request model for exporting Chrome browser history to CSV."""
    user_id: str = Field(
        ...,
        description="User identifier — the exported CSV will be saved as <user_id>.csv",
        min_length=1
    )
    chrome_profile_path: str = Field(
        ...,
        description=(
            "Full path to the Chrome profile directory. "
            r"Example: C:\Users\name\AppData\Local\Google\Chrome\User Data\Profile 3"
        ),
        min_length=1
    )


class BrowserHistoryResponse(BaseModel):
    """Response model for browser history export."""
    success: bool = Field(..., description="Whether the export was successful")
    user_id: str = Field(..., description="User identifier")
    csv_path: Optional[str] = Field(None, description="Absolute path to the saved CSV file")
    rows_exported: Optional[int] = Field(None, description="Number of history rows written to CSV")
    overwritten: bool = Field(False, description="True if an existing CSV was overwritten")
    error: Optional[str] = Field(None, description="Error message if export failed")


class ProductInfo(BaseModel):
    """Product information model."""
    timestamp: Optional[str] = None
    query: Optional[str] = None
    category: Optional[str] = None
    product: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    engagement_score: Optional[float] = None
    total_engagement_score: Optional[float] = None
    search_count: Optional[int] = None
    source: Optional[str] = None


class CategoryInfo(BaseModel):
    """Category information model."""
    category: Optional[str] = None
    subcategory: Optional[str] = None
    total_engagement_score: Optional[float] = None
    search_count: Optional[int] = None


class ExtractionMetadata(BaseModel):
    """Extraction metadata model."""
    user_id: Optional[str] = None
    products_found: Optional[int] = None
    total_rows: Optional[int] = None
    queries_extracted: Optional[int] = None
    ml_label_0: Optional[int] = None
    ml_label_1: Optional[int] = None
    vectordb_exact_hits: Optional[int] = None
    vectordb_semantic_hits: Optional[int] = None
    user_data_hits: Optional[int] = None
    training_data_hits: Optional[int] = None
    llm_calls: Optional[int] = None
    llm_success: Optional[int] = None
    llm_written_to_vectordb: Optional[int] = None
    non_products: Optional[int] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    max_products: Optional[int] = None
    semantic_threshold: Optional[float] = None
    extraction_date: Optional[str] = None
    csv_format: Optional[str] = None


class ExtractionResponse(BaseModel):
    """Response model for user interest extraction."""
    success: bool = Field(..., description="Whether extraction was successful")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    top_1_most_recent: Optional[Dict[str, Any]] = Field(None, description="Most recent product search")
    top_2_most_dominant_product: Optional[Dict[str, Any]] = Field(None, description="Most dominant product by engagement")
    top_3_dominant_category_subcategory: Optional[Dict[str, Any]] = Field(None, description="Dominant category-subcategory")
    top_4_dominant_category: Optional[Dict[str, Any]] = Field(None, description="Dominant category")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extraction metadata and statistics")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    components: Dict[str, str]