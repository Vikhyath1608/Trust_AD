"""
ML-based first-level product filter.
"""
import numpy as np
from pathlib import Path
from typing import Optional
import joblib
from sentence_transformers import SentenceTransformer

from utils.exceptions import MLClassifierError
from utils.logging import Logger


class MLProductClassifier:
    """
    ML-based first-level filter using trained model.
    
    Predicts binary label:
        0: Non-product (skip all further processing)
        1: Product (continue to classification cascade)
    """
    
    def __init__(
        self, 
        model_path: str,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        logger: Optional[Logger] = None
    ):
        """
        Initialize ML classifier.
        
        Args:
            model_path: Path to trained model file
            embedding_model_name: Name of sentence transformer model
            logger: Optional logger instance
        
        Raises:
            MLClassifierError: If model cannot be loaded
        """
        self.logger = logger or Logger(verbose=False)
        self.model_path = Path(model_path)
        
        # Load embedding model
        try:
            self.embedder = SentenceTransformer(embedding_model_name)
        except Exception as e:
            raise MLClassifierError(f"Failed to load embedding model: {e}")
        
        # Load trained classifier
        if not self.model_path.exists():
            raise MLClassifierError(f"Model file not found: {model_path}")
        
        try:
            self.model = joblib.load(str(self.model_path))
            self.logger.info(f"✓ ML classifier loaded from {model_path}")
        except Exception as e:
            raise MLClassifierError(f"Failed to load ML model: {e}")
    
    def predict_label(self, query: str) -> int:
        """
        Predict if query is a product search.
        
        Args:
            query: Search query string
        
        Returns:
            0 for non-product (skip), 1 for product (continue)
            Returns 0 on any error (fail-closed behavior)
        """
        if not query or not query.strip():
            return 0
        
        try:
            # Generate embedding
            embedding = self.embedder.encode(
                query, 
                convert_to_numpy=True
            ).reshape(1, -1)
            
            # Predict label
            label = self.model.predict(embedding)[0]
            return int(label)
            
        except Exception as e:
            self.logger.warning(f"ML prediction error for '{query}': {e}")
            # Fail-closed: treat errors as non-product
            return 0