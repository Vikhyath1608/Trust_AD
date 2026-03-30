"""
API routes for User Interest Extractor.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from api.models import (
    ExtractionRequest, ExtractionResponse, HealthResponse,
    BrowserHistoryRequest, BrowserHistoryResponse
)
from api.dependencies import get_engine, get_default_config
from app.engine import ExtractionEngine
from config.settings import SystemConfig, ProcessingConfig
from utils.exceptions import UserNotFoundError, MLClassifierError
import traceback

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and component availability.
    """
    try:
        config = get_default_config()
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            components={
                "ml_model": "available",
                "vector_db": "available",
                "user_data": "available",
                "training_data": "available"
            }
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            version="1.0.0",
            components={
                "error": str(e)
            }
        )


@router.post("/extract", response_model=ExtractionResponse, tags=["Extraction"])
async def extract_user_interests(
    request: ExtractionRequest,
    engine: ExtractionEngine = Depends(get_engine)
):
    """
    Extract user interest summary from browser history.
    
    **Parameters:**
    - **user_id**: User identifier (must have corresponding CSV file)
    - **max_products**: Maximum number of products to extract (1-1000, default: 100)
    - **alpha**: Weight for ClickCount in engagement scoring (default: 1.0)
    - **beta**: Weight for Frequency in engagement scoring (default: 1.0)
    - **semantic_threshold**: Similarity threshold for Vector DB search (0.0-1.0, default: 0.85)
    - **verbose**: Enable verbose logging (default: false)
    
    **Returns:**
    - Top 4 aggregated interest summaries
    - Detailed metadata and statistics
    
    **Example Request:**
```json
    {
        "user_id": "user2",
        "max_products": 100,
        "alpha": 1.0,
        "beta": 1.0,
        "semantic_threshold": 0.85,
        "verbose": false
    }
```
    """
    try:
        # Override engine config with request parameters
        engine.config.processing.max_products = request.max_products
        engine.config.processing.alpha = request.alpha
        engine.config.processing.beta = request.beta
        engine.config.vectordb.semantic_threshold = request.semantic_threshold
        engine.config.verbose = request.verbose
        
        # Run extraction
        result = engine.extract(user_id=request.user_id)
        
        # Check for errors in result
        if 'error' in result and result['error']:
            return ExtractionResponse(
                success=False,
                error=result['error'],
                top_1_most_recent=result.get('top_1_most_recent'),
                top_2_most_dominant_product=result.get('top_2_most_dominant_product'),
                top_3_dominant_category_subcategory=result.get('top_3_dominant_category_subcategory'),
                top_4_dominant_category=result.get('top_4_dominant_category'),
                metadata=result.get('metadata')
            )
        
        # Success response
        return ExtractionResponse(
            success=True,
            error=None,
            top_1_most_recent=result.get('top_1_most_recent'),
            top_2_most_dominant_product=result.get('top_2_most_dominant_product'),
            top_3_dominant_category_subcategory=result.get('top_3_dominant_category_subcategory'),
            top_4_dominant_category=result.get('top_4_dominant_category'),
            metadata=result.get('metadata')
        )
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User not found",
                "message": str(e),
                "user_id": request.user_id
            }
        )
    
    except MLClassifierError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ML classifier error",
                "message": str(e)
            }
        )
    
    except Exception as e:
        # Log the full traceback
        error_trace = traceback.format_exc()
        print(f"Extraction error:\n{error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "type": type(e).__name__
            }
        )


@router.get("/users/{user_id}/exists", tags=["Users"])
async def check_user_exists(user_id: str):
    """
    Check if a user CSV file exists.
    
    **Parameters:**
    - **user_id**: User identifier
    
    **Returns:**
    - exists: Boolean indicating if user file exists
    - file_path: Path to user CSV file (if exists)
    """
    from pathlib import Path
    
    config = get_default_config()
    csv_path = Path(config.processing.data_dir) / f"{user_id}.csv"
    
    return {
        "user_id": user_id,
        "exists": csv_path.exists(),
        "file_path": str(csv_path) if csv_path.exists() else None
    }

@router.post("/browser-history/export", response_model=BrowserHistoryResponse, tags=["Browser History"])
async def export_browser_history(request: BrowserHistoryRequest):
    """
    Read Chrome browser history and save it as a CSV file.

    Reads the Chrome SQLite History database from the given profile path,
    converts it to the Type-2 CSV format (Title, Visit Count, Last Visit Time),
    and saves it as **<user_id>.csv** in the configured browser_history directory.

    If a CSV already exists for that user_id it will be **overwritten**.

    **Parameters:**
    - **user_id**: Identifier for the user — output file will be `<user_id>.csv`
    - **chrome_profile_path**: Full path to the Chrome profile directory

    **Finding your Chrome profile path:**
    - Open Chrome → address bar → `chrome://version`
    - Look for **Profile Path** (e.g. `C:\\...\\Chrome\\User Data\\Profile 3`)

    **Example Request:**
    ```json
    {
        "user_id": "user1",
        "chrome_profile_path": "C:\\\\Users\\\\name\\\\AppData\\\\Local\\\\Google\\\\Chrome\\\\User Data\\\\Profile 3"
    }
    ```
    """
    from browser_history.reader import export_history_to_csv

    config = get_default_config()
    output_dir = config.processing.data_dir
    csv_path = Path(output_dir) / f"{request.user_id}.csv"
    already_exists = csv_path.exists()

    try:
        saved_path, rows = export_history_to_csv(
            user_id=request.user_id,
            chrome_profile_path=request.chrome_profile_path,
            output_dir=output_dir
        )

        return BrowserHistoryResponse(
            success=True,
            user_id=request.user_id,
            csv_path=saved_path,
            rows_exported=rows,
            overwritten=already_exists,
            error=None
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Chrome profile or History database not found",
                "message": str(e),
                "user_id": request.user_id
            }
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to read or export browser history",
                "message": str(e),
                "user_id": request.user_id
            }
        )

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Browser history export error:\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "type": type(e).__name__
            }
        )