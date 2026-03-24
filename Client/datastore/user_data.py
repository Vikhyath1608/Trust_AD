"""
Read-only user data store.
"""
import json
from pathlib import Path
from typing import Dict, Optional, Any

from utils.exceptions import DataStoreError
from utils.logging import Logger


class ReadOnlyUserDataStore:
    """
    Read-only accessor for user_data.json.
    
    Maintains in-memory index for fast exact lookups.
    """
    
    def __init__(
        self,
        user_data_path: str,
        logger: Optional[Logger] = None
    ):
        """
        Initialize user data store.
        
        Args:
            user_data_path: Path to user_data.json
            logger: Optional logger instance
        """
        self.logger = logger or Logger(verbose=False)
        self.user_data_path = Path(user_data_path)
        self.query_to_record: Dict[str, Dict[str, Any]] = {}
        
        self._load()
    
    def _load(self) -> None:
        """Load user_data.json into memory index."""
        if not self.user_data_path.exists():
            self.logger.info(
                f"Info: {self.user_data_path} not found - "
                "starting with empty user_data store"
            )
            return
        
        try:
            with open(self.user_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = data.get('records', [])
            else:
                self.logger.warning("Unexpected format in user_data.json")
                return
            
            loaded_count = 0
            for record in records:
                if not isinstance(record, dict):
                    continue
                
                normalized = record.get('normalized_query', '').lower().strip()
                if normalized and normalized not in self.query_to_record:
                    self.query_to_record[normalized] = record
                    loaded_count += 1
            
            self.logger.info(f"✓ Loaded user_data: {loaded_count} unique queries indexed")
            
        except Exception as e:
            raise DataStoreError(f"Could not load user_data.json: {e}")
    
    def lookup(self, normalized_query: str) -> Optional[Dict[str, Any]]:
        """
        Exact match lookup - READ-ONLY.
        
        Args:
            normalized_query: Normalized query string
        
        Returns:
            Record dict or None
        """
        return self.query_to_record.get(normalized_query.lower().strip())