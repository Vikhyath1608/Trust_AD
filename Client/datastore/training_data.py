"""
Read-only training data store.
"""
import json
from pathlib import Path
from typing import Dict, Optional

from utils.exceptions import DataStoreError
from utils.logging import Logger


class ReadOnlyTrainingDataStore:
    """
    Read-only accessor for training_data.json.
    
    Maintains in-memory index for fast exact lookups.
    """
    
    def __init__(
        self,
        training_data_path: str,
        logger: Optional[Logger] = None
    ):
        """
        Initialize training data store.
        
        Args:
            training_data_path: Path to training_data.json
            logger: Optional logger instance
        """
        self.logger = logger or Logger(verbose=False)
        self.training_data_path = Path(training_data_path)
        self.query_to_label: Dict[str, int] = {}
        
        self._load()
    
    def _load(self) -> None:
        """Load training_data.json into memory index."""
        if not self.training_data_path.exists():
            self.logger.info(
                f"Info: {self.training_data_path} not found - "
                "starting with empty training_data store"
            )
            return
        
        try:
            with open(self.training_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(data, list):
                entries = data
            elif isinstance(data, dict):
                entries = data.get('entries', [])
            else:
                self.logger.warning("Unexpected format in training_data.json")
                return
            
            loaded_count = 0
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                
                normalized = entry.get('query', '').lower().strip()
                if normalized:
                    self.query_to_label[normalized] = entry.get('label', 0)
                    loaded_count += 1
            
            self.logger.info(f"✓ Loaded training_data: {loaded_count} entries indexed")
            
        except Exception as e:
            raise DataStoreError(f"Could not load training_data.json: {e}")
    
    def lookup(self, normalized_query: str) -> Optional[int]:
        """
        Exact match lookup - READ-ONLY.
        
        Args:
            normalized_query: Normalized query string
        
        Returns:
            Label (0 or 1) or None
        """
        return self.query_to_label.get(normalized_query.lower().strip())