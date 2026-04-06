"""
Unit tests for ML classifier.
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
import joblib

from classifiers.ml_filter import MLProductClassifier
from utils.exceptions import MLClassifierError


class TestMLProductClassifier:
    """Test ML product classifier."""
    
    def test_initialization_success(self, tmp_path):
        """Test successful initialization."""
        # Create mock model file
        model_path = tmp_path / "test_model.pkl"
        mock_model = Mock()
        joblib.dump(mock_model, model_path)
        
        with patch('classifiers.ml_filter.SentenceTransformer') as mock_transformer:
            mock_transformer.return_value = Mock()
            
            classifier = MLProductClassifier(
                model_path=str(model_path),
                embedding_model_name="test-model"
            )
            
            assert classifier.model is not None
            assert classifier.embedder is not None
    
    def test_initialization_model_not_found(self):
        """Test initialization with missing model file."""
        with pytest.raises(MLClassifierError):
            MLProductClassifier(
                model_path="./nonexistent_model.pkl"
            )
    
    def test_predict_label_product(self, tmp_path):
        """Test prediction for product query."""
        # Create mock model
        model_path = tmp_path / "test_model.pkl"
        mock_model = Mock()
        mock_model.predict.return_value = np.array([1])
        joblib.dump(mock_model, model_path)
        
        with patch('classifiers.ml_filter.SentenceTransformer') as mock_transformer:
            mock_embedder = Mock()
            mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3])
            mock_transformer.return_value = mock_embedder
            
            classifier = MLProductClassifier(model_path=str(model_path))
            label = classifier.predict_label("samsung laptop")
            
            assert label == 1
    
    def test_predict_label_non_product(self, tmp_path):
        """Test prediction for non-product query."""
        model_path = tmp_path / "test_model.pkl"
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0])
        joblib.dump(mock_model, model_path)
        
        with patch('classifiers.ml_filter.SentenceTransformer') as mock_transformer:
            mock_embedder = Mock()
            mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3])
            mock_transformer.return_value = mock_embedder
            
            classifier = MLProductClassifier(model_path=str(model_path))
            label = classifier.predict_label("how to code")
            
            assert label == 0
    
    def test_predict_label_empty_query(self, tmp_path):
        """Test prediction with empty query."""
        model_path = tmp_path / "test_model.pkl"
        mock_model = Mock()
        joblib.dump(mock_model, model_path)
        
        with patch('classifiers.ml_filter.SentenceTransformer'):
            classifier = MLProductClassifier(model_path=str(model_path))
            
            assert classifier.predict_label("") == 0
            assert classifier.predict_label("   ") == 0
            assert classifier.predict_label(None) == 0
    
    def test_predict_label_error_handling(self, tmp_path):
        """Test error handling during prediction."""
        model_path = tmp_path / "test_model.pkl"
        mock_model = Mock()
        mock_model.predict.side_effect = Exception("Prediction error")
        joblib.dump(mock_model, model_path)
        
        with patch('classifiers.ml_filter.SentenceTransformer') as mock_transformer:
            mock_embedder = Mock()
            mock_embedder.encode.return_value = np.array([0.1, 0.2, 0.3])
            mock_transformer.return_value = mock_embedder
            
            classifier = MLProductClassifier(model_path=str(model_path))
            
            # Should return 0 (fail-closed) on error
            label = classifier.predict_label("test query")
            assert label == 0