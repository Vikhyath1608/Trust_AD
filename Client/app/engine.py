"""
Main extraction engine - top-level orchestrator.
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from config.settings import SystemConfig
from classifiers.ml_filter import MLProductClassifier
from vectorstore.chroma_store import VectorDBStore
from datastore.user_data import ReadOnlyUserDataStore
from datastore.training_data import ReadOnlyTrainingDataStore
from classifiers.llm_classifier import LLMClassifierWithWriteBack
from extraction.url_extractor import URLQueryExtractor
from extraction.normalizer import QueryNormalizer
from scoring.engagement import EngagementScorer
from aggregation.aggregators import ProductAggregator
from app.pipeline import StreamingPipeline
from utils.logging import Logger
from utils.exceptions import (
    UserInterestExtractorError,
    MLClassifierError,
    UserNotFoundError
)


class ExtractionEngine:
    """
    Top-level extraction engine.
    
    Responsibilities:
    - Instantiate all dependencies
    - Wire components together
    - Run pipeline
    - Compute aggregations
    - Return final result
    """
    
    def __init__(self, config: SystemConfig):
        """
        Initialize extraction engine.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.logger = Logger(verbose=config.verbose)
        
        # Components (initialized lazily)
        self._ml_classifier: Optional[MLProductClassifier] = None
        self._embedding_model: Optional[SentenceTransformer] = None
        self._vectordb_store: Optional[VectorDBStore] = None
        self._user_data_store: Optional[ReadOnlyUserDataStore] = None
        self._training_data_store: Optional[ReadOnlyTrainingDataStore] = None
        self._llm_classifier: Optional[LLMClassifierWithWriteBack] = None
        self._pipeline: Optional[StreamingPipeline] = None
    
    def extract(self, user_id: str) -> Dict[str, Any]:
        """
        Extract user interest summary.
        
        Args:
            user_id: User identifier
        
        Returns:
            Complete result dictionary with top-N summaries and metadata
        """
        self.logger.section(f"Extracting Interest Summary for User: {user_id}")
        
        try:
            # Initialize components
            self._initialize_components()
            
            # Run pipeline
            product_queries, stats = self._pipeline.process_user_csv(
                user_id=user_id,
                data_dir=self.config.processing.data_dir
            )
            
            # Check if products found
            if not product_queries:
                self.logger.info("No products found - returning empty result\n")
                return self._build_empty_result(user_id, stats)
            
            # Compute aggregations
            self.logger.info(
                f"Computing aggregations from {len(product_queries)} products...\n"
            )
            result = self._compute_aggregations(
                user_id=user_id,
                product_queries=product_queries,
                stats=stats
            )
            
            # Print summary
            self._print_summary(result)
            
            return result
            
        except UserNotFoundError as e:
            self.logger.error(str(e))
            return {
                'error': str(e),
                'top_1_most_recent': None,
                'top_2_most_dominant_product': None,
                'top_3_dominant_category_subcategory': None,
                'top_4_dominant_category': None,
                'metadata': {'products_found': 0}
            }
        
        except MLClassifierError as e:
            self.logger.error(f"ML classifier error: {e}")
            return {
                'error': f'ML classifier load failed: {e}',
                'top_1_most_recent': None,
                'top_2_most_dominant_product': None,
                'top_3_dominant_category_subcategory': None,
                'top_4_dominant_category': None,
                'metadata': {}
            }
        
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'top_1_most_recent': None,
                'top_2_most_dominant_product': None,
                'top_3_dominant_category_subcategory': None,
                'top_4_dominant_category': None,
                'metadata': {}
            }
    
    def _initialize_components(self) -> None:
        """Initialize all system components."""
        # ML Classifier
        self._ml_classifier = MLProductClassifier(
            model_path=self.config.ml.model_path,
            embedding_model_name=self.config.ml.embedding_model_name,
            logger=self.logger
        )
        
        # Embedding Model
        self.logger.info("Loading embedding model for Vector DB...")
        try:
            self._embedding_model = SentenceTransformer(
                self.config.ml.embedding_model_name
            )
            self.logger.info("✓ Embedding model loaded\n")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            self._embedding_model = None
        
        # Vector DB Store
        self._vectordb_store = VectorDBStore(
            db_path=self.config.vectordb.db_path,
            collection_name=self.config.vectordb.collection_name,
            embedding_model=self._embedding_model,
            allow_reset=self.config.vectordb.allow_reset,
            anonymized_telemetry=self.config.vectordb.anonymized_telemetry,
            logger=self.logger
        )
        
        # User Data Store
        self._user_data_store = ReadOnlyUserDataStore(
            user_data_path=self.config.datastore.user_data_path,
            logger=self.logger
        )
        
        # Training Data Store
        self._training_data_store = ReadOnlyTrainingDataStore(
            training_data_path=self.config.datastore.training_data_path,
            logger=self.logger
        )
        
        # LLM Classifier
        self._llm_classifier = LLMClassifierWithWriteBack(
            vectordb_store=self._vectordb_store,
            embedding_model=self._embedding_model,
            logger=self.logger
        )
        
        # URL Extractor and Normalizer
        url_extractor = URLQueryExtractor()
        normalizer = QueryNormalizer()
        
        # Engagement Scorer
        engagement_scorer = EngagementScorer(
            alpha=self.config.processing.alpha,
            beta=self.config.processing.beta
        )
        
        # Pipeline
        self._pipeline = StreamingPipeline(
            ml_classifier=self._ml_classifier,
            vectordb_store=self._vectordb_store,
            user_data_store=self._user_data_store,
            training_data_store=self._training_data_store,
            llm_classifier=self._llm_classifier,
            url_extractor=url_extractor,
            normalizer=normalizer,
            engagement_scorer=engagement_scorer,
            chunk_size=self.config.processing.chunk_size,
            max_products=self.config.processing.max_products,
            semantic_threshold=self.config.vectordb.semantic_threshold,
            logger=self.logger
        )
        
        self.logger.info("")
    
    def _compute_aggregations(
        self,
        user_id: str,
        product_queries: list,
        stats: Any
    ) -> Dict[str, Any]:
        """
        Compute top-N aggregations.
        
        Args:
            user_id: User identifier
            product_queries: List of product query dicts
            stats: Processing statistics
        
        Returns:
            Complete result dictionary
        """
        aggregator = ProductAggregator()
        
        # Compute aggregations
        top_1 = aggregator.most_recent(product_queries)
        top_2 = aggregator.most_dominant_product(product_queries)
        top_3 = aggregator.dominant_category_subcategory(product_queries)
        top_4 = aggregator.dominant_category(product_queries)
        
        # Build metadata
        metadata = {
            'user_id': user_id,
            'products_found': stats.products_found,
            'total_rows': stats.total_rows,
            'queries_extracted': stats.queries_extracted,
            'ml_label_0': stats.ml_label_0,
            'ml_label_1': stats.ml_label_1,
            'vectordb_exact_hits': stats.vectordb_exact_hits,
            'vectordb_semantic_hits': stats.vectordb_semantic_hits,
            'user_data_hits': stats.user_data_hits,
            'training_data_hits': stats.training_data_hits,
            'llm_calls': stats.llm_calls,
            'llm_success': stats.llm_success,
            'llm_written_to_vectordb': stats.llm_written_to_vectordb,
            'non_products': stats.non_products,
            'alpha': self.config.processing.alpha,
            'beta': self.config.processing.beta,
            'max_products': self.config.processing.max_products,
            'semantic_threshold': self.config.vectordb.semantic_threshold,
            'extraction_date': datetime.now().isoformat()
        }
        
        return {
            'top_1_most_recent': top_1,
            'top_2_most_dominant_product': top_2,
            'top_3_dominant_category_subcategory': top_3,
            'top_4_dominant_category': top_4,
            'metadata': metadata
        }
    
    def _build_empty_result(
        self,
        user_id: str,
        stats: Any
    ) -> Dict[str, Any]:
        """Build empty result when no products found."""
        return {
            'top_1_most_recent': None,
            'top_2_most_dominant_product': None,
            'top_3_dominant_category_subcategory': None,
            'top_4_dominant_category': None,
            'metadata': {
                'user_id': user_id,
                'products_found': 0,
                'total_rows': stats.total_rows,
                'queries_extracted': stats.queries_extracted,
                'ml_label_0': stats.ml_label_0,
                'ml_label_1': stats.ml_label_1,
                'vectordb_exact_hits': stats.vectordb_exact_hits,
                'vectordb_semantic_hits': stats.vectordb_semantic_hits,
                'user_data_hits': stats.user_data_hits,
                'training_data_hits': stats.training_data_hits,
                'llm_calls': stats.llm_calls,
                'llm_success': stats.llm_success,
                'llm_written_to_vectordb': stats.llm_written_to_vectordb
            }
        }
    
    def _print_summary(self, result: Dict[str, Any]) -> None:
        """Print results summary."""
        top_1 = result['top_1_most_recent']
        top_2 = result['top_2_most_dominant_product']
        top_3 = result['top_3_dominant_category_subcategory']
        top_4 = result['top_4_dominant_category']
        
        self.logger.separator()
        self.logger.info("Results Summary")
        self.logger.separator()
        
        if top_1:
            self.logger.info("\nTOP 1 - Most Recent:")
            self.logger.info(f"  Query: {top_1['query']}")
            self.logger.info(
                f"  Product: {top_1['brand']} {top_1['product']} {top_1['model']}"
            )
            self.logger.info(f"  Category: {top_1['category']}")
            self.logger.info(f"  Timestamp: {top_1['timestamp']}")
            self.logger.info(f"  Source: {top_1['source']}")
        
        if top_2:
            self.logger.info("\nTOP 2 - Most Dominant Product:")
            self.logger.info(
                f"  Product: {top_2['brand']} {top_2['product']} {top_2['model']}"
            )
            self.logger.info(f"  Category: {top_2['category']}")
            self.logger.info(
                f"  Total Engagement: {top_2['total_engagement_score']:.2f}"
            )
            self.logger.info(f"  Search Count: {top_2['search_count']}")
        
        if top_3:
            self.logger.info("\nTOP 3 - Dominant Category-Subcategory:")
            self.logger.info(f"  Category: {top_3['category']}")
            self.logger.info(f"  Subcategory: {top_3['subcategory']}")
            self.logger.info(
                f"  Total Engagement: {top_3['total_engagement_score']:.2f}"
            )
            self.logger.info(f"  Search Count: {top_3['search_count']}")
        
        if top_4:
            self.logger.info("\nTOP 4 - Dominant Category:")
            self.logger.info(f"  Category: {top_4['category']}")
            self.logger.info(
                f"  Total Engagement: {top_4['total_engagement_score']:.2f}"
            )
            self.logger.info(f"  Search Count: {top_4['search_count']}")
        
        self.logger.info("\n")
        self.logger.separator()
        self.logger.info("")