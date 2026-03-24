"""
ChromaDB vector store with read/write capabilities.
"""
import hashlib
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from utils.exceptions import VectorDBError
from utils.logging import Logger


class VectorDBStore:
    """
    Vector database store with:
    - In-memory cache for exact lookups
    - Semantic similarity search
    - Write-back capability for LLM results
    """
    
    def __init__(
        self,
        db_path: str,
        collection_name: str = "knowledge_base",
        embedding_model: Optional[SentenceTransformer] = None,
        allow_reset: bool = False,
        anonymized_telemetry: bool = False,
        logger: Optional[Logger] = None
    ):
        """
        Initialize vector store.
        
        Args:
            db_path: Path to ChromaDB directory
            collection_name: Name of collection
            embedding_model: SentenceTransformer model for embeddings
            allow_reset: Allow database reset
            anonymized_telemetry: Enable telemetry
            logger: Optional logger instance
        
        Raises:
            VectorDBError: If database cannot be initialized
        """
        self.logger = logger or Logger(verbose=False)
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # In-memory cache for exact lookups
        self.query_to_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Create directory
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(
                    anonymized_telemetry=anonymized_telemetry,
                    allow_reset=allow_reset
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=collection_name)
                count = self.collection.count()
                self.logger.info(f"✓ Loaded Vector DB: {count} entries")
            except:
                self.collection = self.client.create_collection(name=collection_name)
                self.logger.info(f"✓ Created new Vector DB collection")
            
            # Build in-memory cache
            self._build_cache()
            
        except Exception as e:
            raise VectorDBError(f"Failed to initialize Vector DB: {e}")
    
    def _build_cache(self) -> None:
        """Build in-memory cache for fast exact lookups."""
        try:
            count = self.collection.count()
            if count == 0:
                return
            
            batch_size = 1000
            offset = 0
            
            while offset < count:
                results = self.collection.get(
                    limit=batch_size,
                    offset=offset
                )
                
                for doc, metadata in zip(results['documents'], results['metadatas']):
                    canonical_query = metadata.get('canonical_query', '').lower().strip()
                    if canonical_query:
                        self.query_to_metadata[canonical_query] = metadata
                
                offset += batch_size
            
            self.logger.info(f"✓ Built in-memory cache: {len(self.query_to_metadata)} entries")
            
        except Exception as e:
            self.logger.warning(f"Cache build error: {e}")
    
    def exact_lookup(self, normalized_query: str) -> Optional[Dict[str, Any]]:
        """
        Fast exact match lookup using in-memory cache.
        
        Args:
            normalized_query: Normalized query string
        
        Returns:
            Metadata dict or None
        """
        return self.query_to_metadata.get(normalized_query.lower().strip())
    
    def semantic_search(
        self, 
        query_embedding: np.ndarray, 
        threshold: float = 0.85
    ) -> Optional[Dict[str, Any]]:
        """
        Semantic similarity search.
        
        Args:
            query_embedding: Query embedding vector
            threshold: Similarity threshold (0.0 to 1.0)
        
        Returns:
            Best match metadata with similarity score or None
        """
        try:
            count = self.collection.count()
            if count == 0:
                return None
            
            # Query for nearest neighbor
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=1
            )
            
            if not results['distances'][0]:
                return None
            
            # Calculate similarity (ChromaDB returns distances)
            distance = results['distances'][0][0]
            similarity = 1 - distance
            
            if similarity >= threshold:
                metadata = results['metadatas'][0][0]
                
                return {
                    'canonical_query': metadata.get('canonical_query', ''),
                    'category': metadata.get('category', ''),
                    'product': metadata.get('product', ''),
                    'brand': metadata.get('brand', ''),
                    'model': metadata.get('model', ''),
                    'is_product': metadata.get('is_product', True),
                    'confidence': metadata.get('confidence', 0.8),
                    'similarity_score': float(similarity)
                }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Semantic search error: {e}")
            return None
    
    def add_entry(
        self,
        normalized_query: str,
        query_embedding: np.ndarray,
        classification_result: Dict[str, Any]
    ) -> bool:
        """
        Add LLM-classified entry to Vector DB.
        
        Args:
            normalized_query: Normalized query string
            query_embedding: Embedding vector
            classification_result: Classification metadata
        
        Returns:
            True if successfully added, False otherwise
        """
        if not self.embedding_model:
            return False
        
        try:
            # Create unique ID
            entry_id = hashlib.md5(normalized_query.encode('utf-8')).hexdigest()
            
            # Prepare metadata
            metadata = {
                'canonical_query': normalized_query,
                'category': str(classification_result.get('category', '')),
                'product': str(classification_result.get('product', '')),
                'brand': str(classification_result.get('brand', '')),
                'model': str(classification_result.get('model', '')),
                'is_product': bool(classification_result.get('is_product', False)),
                'confidence': float(classification_result.get('confidence', 0.0)),
                'source': 'llm',
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to collection
            self.collection.add(
                ids=[entry_id],
                embeddings=[query_embedding.tolist()],
                documents=[normalized_query],
                metadatas=[metadata]
            )
            
            # Update in-memory cache
            self.query_to_metadata[normalized_query] = metadata
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to add entry to Vector DB: {e}")
            return False