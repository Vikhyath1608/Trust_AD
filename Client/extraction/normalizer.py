"""
Query normalization utilities.
"""
import re
from typing import Optional


class QueryNormalizer:
    """Normalize search queries to canonical form."""
    
    @staticmethod
    def normalize(query: str) -> str:
        """
        Normalize query string.
        
        Args:
            query: Raw search query
        
        Returns:
            Normalized query string (lowercase, cleaned)
        """
        if not query:
            return ""
        
        # Convert to lowercase
        query = query.lower().strip()
        
        # Remove special characters (keep alphanumeric and spaces)
        query = re.sub(r'[^\w\s]', ' ', query)
        
        # Collapse multiple spaces
        query = re.sub(r'\s+', ' ', query)
        
        return query.strip()