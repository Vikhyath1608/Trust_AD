"""
Unit tests for processing pipeline.
"""
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, MagicMock
from pathlib import Path

from app.pipeline import StreamingPipeline, ProcessingStats
from utils.exceptions import UserNotFoundError, CSVProcessingError


class TestProcessingStats:
    """Test processing statistics."""
    
    def test_initialization(self):
        """Test stats initialization."""
        stats = ProcessingStats()
        
        assert stats.total_rows == 0
        assert stats.queries_extracted == 0
        assert stats.ml_label_0 == 0
        assert stats.ml_label_1 == 0
        assert stats.products_found == 0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = ProcessingStats()
        stats.total_rows = 10
        stats.products_found = 5
        
        result = stats.to_dict()
        
        assert isinstance(result, dict)
        assert result['total_rows'] == 10
        assert result['products_found'] == 5


class TestStreamingPipeline:
    """Test streaming pipeline."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components."""
        return {
            'ml_classifier': Mock(),
            'vectordb_store': Mock(),
            'user_data_store': Mock(),
            'training_data_store': Mock(),
            'llm_classifier': Mock(),
            'url_extractor': Mock(),
            'normalizer': Mock(),
            'engagement_scorer': Mock()
        }
    
    def test_initialization(self, mock_components):
        """Test pipeline initialization."""
        pipeline = StreamingPipeline(
            ml_classifier=mock_components['ml_classifier'],
            vectordb_store=mock_components['vectordb_store'],
            user_data_store=mock_components['user_data_store'],
            training_data_store=mock_components['training_data_store'],
            llm_classifier=mock_components['llm_classifier'],
            url_extractor=mock_components['url_extractor'],
            normalizer=mock_components['normalizer'],
            engagement_scorer=mock_components['engagement_scorer'],
            chunk_size=100,
            max_products=50
        )
        
        assert pipeline.chunk_size == 100
        assert pipeline.max_products == 50
        assert isinstance(pipeline.stats, ProcessingStats)
    
    def test_process_user_csv_not_found(self, mock_components, tmp_path):
        """Test processing with missing CSV."""
        pipeline = StreamingPipeline(
            ml_classifier=mock_components['ml_classifier'],
            vectordb_store=mock_components['vectordb_store'],
            user_data_store=mock_components['user_data_store'],
            training_data_store=mock_components['training_data_store'],
            llm_classifier=mock_components['llm_classifier'],
            url_extractor=mock_components['url_extractor'],
            normalizer=mock_components['normalizer'],
            engagement_scorer=mock_components['engagement_scorer']
        )
        
        with pytest.raises(UserNotFoundError):
            pipeline.process_user_csv(
                user_id="nonexistent_user",
                data_dir=str(tmp_path)
            )
    
    def test_add_timestamps(self, mock_components):
        """Test timestamp addition to chunk."""
        pipeline = StreamingPipeline(
            ml_classifier=mock_components['ml_classifier'],
            vectordb_store=mock_components['vectordb_store'],
            user_data_store=mock_components['user_data_store'],
            training_data_store=mock_components['training_data_store'],
            llm_classifier=mock_components['llm_classifier'],
            url_extractor=mock_components['url_extractor'],
            normalizer=mock_components['normalizer'],
            engagement_scorer=mock_components['engagement_scorer']
        )
        
        # Create test chunk
        chunk = pd.DataFrame({
            'Time1': [1609459200, 1609545600],  # Unix timestamps
            'Links': ['http://example.com', 'http://example2.com']
        })
        
        result = pipeline._add_timestamps(chunk)
        
        assert 'timestamp' in result.columns
        assert 'timestamp_unix' in result.columns
        assert len(result) == 2