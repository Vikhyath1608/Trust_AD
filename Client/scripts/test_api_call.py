"""
Test script to call the User Interest Extractor API.
"""
import requests
import json
import sys
from typing import Optional


def call_extraction_api(
    user_id: str,
    base_url: str = "http://localhost:8000",
    max_products: int = 100,
    alpha: float = 1.0,
    beta: float = 1.0,
    semantic_threshold: float = 0.85,
    verbose: bool = False
) -> Optional[dict]:
    """
    Call the extraction API and return the result.
    
    Args:
        user_id: User identifier
        base_url: API base URL
        max_products: Maximum products to extract
        alpha: Weight for ClickCount
        beta: Weight for Frequency
        semantic_threshold: Semantic search threshold
        verbose: Enable verbose logging
    
    Returns:
        API response as dictionary or None if failed
    """
    endpoint = f"{base_url}/api/v1/extract"
    
    payload = {
        "user_id": user_id,
        "max_products": max_products,
        "alpha": alpha,
        "beta": beta,
        "semantic_threshold": semantic_threshold,
        "verbose": verbose
    }
    
    try:
        print(f"Calling API: {endpoint}")
        print(f"Payload: {json.dumps(payload, indent=2)}\n")
        
        response = requests.post(endpoint, json=payload, timeout=300)
        
        # Check HTTP status
        if response.status_code == 200:
            print("✓ API call successful!\n")
            return response.json()
        else:
            print(f"✗ API call failed with status code: {response.status_code}")
            print(f"Error: {response.text}\n")
            return None
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection Error: Is the API server running?")
        print("Start the server with: python scripts/run_api.py\n")
        return None
    except requests.exceptions.Timeout:
        print("✗ Request timed out (>300s)\n")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}\n")
        return None


def print_result(result: dict) -> None:
    """
    Pretty print the extraction result.
    
    Args:
        result: API response dictionary
    """
    print("="*80)
    print("EXTRACTION RESULT")
    print("="*80)
    
    # Print full JSON
    print("\nFull JSON Response:")
    print(json.dumps(result, indent=2, default=str))
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    # Check success
    if not result.get('success', False):
        print(f"\n✗ Extraction failed: {result.get('error', 'Unknown error')}")
        return
    
    # Print summaries
    print("\n✓ Extraction successful!")
    
    # Top 1: Most Recent
    top_1 = result.get('top_1_most_recent')
    if top_1:
        print("\n📌 TOP 1 - Most Recent Product:")
        print(f"   Query: {top_1.get('query')}")
        print(f"   Product: {top_1.get('brand')} {top_1.get('product')} {top_1.get('model')}")
        print(f"   Category: {top_1.get('category')}")
        print(f"   Timestamp: {top_1.get('timestamp')}")
        print(f"   Source: {top_1.get('source')}")
    
    # Top 2: Most Dominant Product
    top_2 = result.get('top_2_most_dominant_product')
    if top_2:
        print("\n🏆 TOP 2 - Most Dominant Product:")
        print(f"   Product: {top_2.get('brand')} {top_2.get('product')} {top_2.get('model')}")
        print(f"   Category: {top_2.get('category')}")
        print(f"   Total Engagement: {top_2.get('total_engagement_score'):.2f}")
        print(f"   Search Count: {top_2.get('search_count')}")
    
    # Top 3: Dominant Category-Subcategory
    top_3 = result.get('top_3_dominant_category_subcategory')
    if top_3:
        print("\n📊 TOP 3 - Dominant Category-Subcategory:")
        print(f"   Category: {top_3.get('category')}")
        print(f"   Subcategory: {top_3.get('subcategory')}")
        print(f"   Total Engagement: {top_3.get('total_engagement_score'):.2f}")
        print(f"   Search Count: {top_3.get('search_count')}")
    
    # Top 4: Dominant Category
    top_4 = result.get('top_4_dominant_category')
    if top_4:
        print("\n📂 TOP 4 - Dominant Category:")
        print(f"   Category: {top_4.get('category')}")
        print(f"   Total Engagement: {top_4.get('total_engagement_score'):.2f}")
        print(f"   Search Count: {top_4.get('search_count')}")
    
    # Metadata
    metadata = result.get('metadata', {})
    if metadata:
        print("\n📈 Metadata:")
        print(f"   Products Found: {metadata.get('products_found')}")
        print(f"   Total Rows Processed: {metadata.get('total_rows')}")
        print(f"   Queries Extracted: {metadata.get('queries_extracted')}")
        print(f"   ML Label=0 (skipped): {metadata.get('ml_label_0')}")
        print(f"   ML Label=1 (processed): {metadata.get('ml_label_1')}")
        print(f"   Vector DB Hits (exact): {metadata.get('vectordb_exact_hits')}")
        print(f"   Vector DB Hits (semantic): {metadata.get('vectordb_semantic_hits')}")
        print(f"   User Data Hits: {metadata.get('user_data_hits')}")
        print(f"   Training Data Hits: {metadata.get('training_data_hits')}")
        print(f"   LLM Calls: {metadata.get('llm_calls')}")
        print(f"   LLM Success: {metadata.get('llm_success')}")
        print(f"   LLM Written to Vector DB: {metadata.get('llm_written_to_vectordb')}")
    
    print("\n" + "="*80)


def main():
    """Main function."""
    # Configuration
    USER_ID = "user7"  
    BASE_URL = "http://localhost:8000"
    
    print("\n" + "="*80)
    print("USER INTEREST EXTRACTOR - API TEST")
    print("="*80 + "\n")
    
    # Call API
    result = call_extraction_api(
        user_id=USER_ID,
        base_url=BASE_URL,
        max_products=100,
        alpha=1.0,
        beta=1.0,
        semantic_threshold=0.85,
        verbose=True
    )
    
    # Print result
    if result:
        print_result(result)
    else:
        print("Failed to get result from API.")
        sys.exit(1)


if __name__ == "__main__":
    main()