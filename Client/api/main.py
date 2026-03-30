"""
FastAPI application for User Interest Extractor.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
import warnings

warnings.filterwarnings('ignore')

# Create FastAPI app
app = FastAPI(
    title="User Interest Extractor API",
    description="""
    Production-grade ML/Vector DB system for extracting user interest summaries from browser history.
    
    ## Features
    - ML-based first-level product filter
    - ChromaDB vector store with semantic search
    - LLM fallback with automatic knowledge base updates
    - Streaming CSV processing with early termination
    - Weighted engagement scoring
    - Top-N interest aggregations
    
    ## Architecture
```
    Query → ML Classifier (first-level gate)
             ├─ Label = 0 → SKIP (non-product)
             └─ Label = 1 → Continue
                             ├─ Vector DB (exact)
                             ├─ Vector DB (semantic)
                             ├─ User Data (READ-ONLY)
                             ├─ Training Data (READ-ONLY)
                             └─ LLM (fallback) → WRITE TO VECTOR DB
```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (configure as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "User Interest Extractor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "extract_endpoint": "/api/v1/extract"
    }