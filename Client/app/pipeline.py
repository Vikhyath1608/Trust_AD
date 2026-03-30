"""
Main processing pipeline for streaming CSV and classification.

Supports two browser-history CSV formats detected automatically:
  Type 1 (Legacy):  Links, Time1, Time2, ClickCount, Frequency
  Type 2 (New):     url, title, visit_count, visit_time
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from classifiers.ml_filter import MLProductClassifier
from vectorstore.chroma_store import VectorDBStore
from datastore.user_data import ReadOnlyUserDataStore
from datastore.training_data import ReadOnlyTrainingDataStore
from classifiers.llm_classifier import LLMClassifierWithWriteBack
from extraction.url_extractor import URLQueryExtractor
from extraction.normalizer import QueryNormalizer
from extraction.csv_detector import CSVFormat, detect_csv_format, normalize_chunk
from scoring.engagement import EngagementScorer
from utils.exceptions import CSVProcessingError, UserNotFoundError
from utils.logging import Logger


class ProcessingStats:
    """Track processing statistics."""
    
    def __init__(self):
        self.total_rows = 0
        self.queries_extracted = 0
        self.ml_label_0 = 0
        self.ml_label_1 = 0
        self.vectordb_exact_hits = 0
        self.vectordb_semantic_hits = 0
        self.user_data_hits = 0
        self.training_data_hits = 0
        self.llm_calls = 0
        self.llm_success = 0
        self.llm_written_to_vectordb = 0
        self.products_found = 0
        self.non_products = 0
    
    def to_dict(self) -> Dict[str, int]:
        """Convert stats to dictionary."""
        return {
            'total_rows': self.total_rows,
            'queries_extracted': self.queries_extracted,
            'ml_label_0': self.ml_label_0,
            'ml_label_1': self.ml_label_1,
            'vectordb_exact_hits': self.vectordb_exact_hits,
            'vectordb_semantic_hits': self.vectordb_semantic_hits,
            'user_data_hits': self.user_data_hits,
            'training_data_hits': self.training_data_hits,
            'llm_calls': self.llm_calls,
            'llm_success': self.llm_success,
            'llm_written_to_vectordb': self.llm_written_to_vectordb,
            'products_found': self.products_found,
            'non_products': self.non_products
        }


class StreamingPipeline:
    """
    Streaming CSV processing pipeline with classification cascade.

    Automatically detects whether the CSV is Type-1 (Legacy) or Type-2 (New)
    and normalises every chunk to a unified internal schema before processing.

    Unified schema columns (produced by csv_detector normalizers):
        url, timestamp, click_count, frequency

    Pipeline flow:
        ML Filter (label 0 → skip, label 1 → continue)
            → Vector DB exact
            → Vector DB semantic
            → User Data
            → Training Data
            → LLM (with Vector DB write-back)
    """
    
    def __init__(
        self,
        ml_classifier: MLProductClassifier,
        vectordb_store: VectorDBStore,
        user_data_store: ReadOnlyUserDataStore,
        training_data_store: ReadOnlyTrainingDataStore,
        llm_classifier: LLMClassifierWithWriteBack,
        url_extractor: URLQueryExtractor,
        normalizer: QueryNormalizer,
        engagement_scorer: EngagementScorer,
        chunk_size: int = 100,
        max_products: int = 100,
        semantic_threshold: float = 0.85,
        logger: Optional[Logger] = None
    ):
        self.ml_classifier = ml_classifier
        self.vectordb_store = vectordb_store
        self.user_data_store = user_data_store
        self.training_data_store = training_data_store
        self.llm_classifier = llm_classifier
        self.url_extractor = url_extractor
        self.normalizer = normalizer
        self.engagement_scorer = engagement_scorer
        
        self.chunk_size = chunk_size
        self.max_products = max_products
        self.semantic_threshold = semantic_threshold
        
        self.logger = logger or Logger(verbose=False)
        self.stats = ProcessingStats()
    
    def process_user_csv(
        self,
        user_id: str,
        data_dir: str
    ) -> Tuple[List[Dict[str, Any]], ProcessingStats]:
        """
        Process user CSV file with streaming.

        Detects the CSV format automatically and delegates chunk processing
        to the appropriate path.

        Args:
            user_id: User identifier
            data_dir: Directory containing user CSV files

        Returns:
            Tuple of (product_queries list, processing stats)

        Raises:
            UserNotFoundError: If user CSV not found
            CSVProcessingError: If CSV processing fails
        """
        csv_path = Path(data_dir) / f"{user_id}.csv"
        if not csv_path.exists():
            raise UserNotFoundError(f"User CSV not found: {csv_path}")

        # ── Detect format ──────────────────────────────────────────────────
        csv_format = detect_csv_format(str(csv_path))
        format_label = csv_format.value

        if csv_format == CSVFormat.UNKNOWN:
            raise CSVProcessingError(
                f"Unrecognised CSV format for {csv_path}. "
                "Expected Type-1 (Links/Time1/ClickCount/Frequency) or "
                "Type-2 (url/title/visit_count/visit_time)."
            )

        self.logger.info(f"Streaming CSV: {csv_path}  [format: {format_label}]")
        self.logger.info(f"Target: {self.max_products} products\n")
        self.logger.info(
            "Processing with ML → Vector DB → User Data → "
            "Training Data → LLM (with write-back) flow...\n"
        )

        # ── Reset stats ────────────────────────────────────────────────────
        self.stats = ProcessingStats()
        product_queries: List[Dict[str, Any]] = []
        product_count = 0

        try:
            for chunk in pd.read_csv(
                csv_path,
                encoding='utf-8-sig',
                chunksize=self.chunk_size
            ):
                if product_count >= self.max_products:
                    break

                # Normalise to unified schema
                try:
                    norm_chunk = normalize_chunk(chunk, csv_format)
                except Exception as e:
                    self.logger.warning(f"Chunk normalisation failed: {e} — skipping chunk")
                    continue

                # Sort newest-first
                norm_chunk = norm_chunk.sort_values('timestamp', ascending=False)

                chunk_products = self._process_chunk(
                    norm_chunk, product_count, csv_format
                )
                product_queries.extend(chunk_products)
                product_count += len(chunk_products)

                if product_count >= self.max_products:
                    self.logger.info(
                        f"\n✓ Reached {self.max_products} products - stopping stream"
                    )
                    break

                if self.logger.verbose and product_count > 0 and product_count % 10 == 0:
                    self.logger.info(
                        f"  Progress: {product_count}/{self.max_products} products collected"
                    )

        except (UserNotFoundError, CSVProcessingError):
            raise
        except Exception as e:
            raise CSVProcessingError(f"Error processing CSV: {e}")

        self._print_stats(csv_format)
        return product_queries, self.stats

    # ──────────────────────────────────────────────────────────────────────
    # Chunk processing
    # ──────────────────────────────────────────────────────────────────────

    def _process_chunk(
        self,
        norm_chunk: pd.DataFrame,
        current_product_count: int,
        csv_format: CSVFormat,
        raw_chunk: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Process a single normalised CSV chunk.

        For Type-2 rows the page title (from the raw chunk) is used as the
        primary query signal because Type-2 URLs are not search-engine URLs.

        Args:
            norm_chunk:            Normalised DataFrame (unified schema)
            current_product_count: Running count of products already collected
            csv_format:            Detected format enum
            raw_chunk:             Original (pre-normalisation) chunk for title access

        Returns:
            List of product query dicts
        """
        products: List[Dict[str, Any]] = []

        # Align raw_chunk index with norm_chunk so we can read title by position
        raw_chunk = raw_chunk.copy()
        raw_chunk.columns = (
            raw_chunk.columns.str.replace('\ufeff', '', regex=False).str.strip()
        )
        raw_chunk.index = norm_chunk.index  # keep index aligned after sort

        for idx, row in norm_chunk.iterrows():
            if current_product_count + len(products) >= self.max_products:
                break

            self.stats.total_rows += 1

            url = row.get('url', '')

            # ── Query extraction (format-aware) ───────────────────────────
            if csv_format == CSVFormat.TYPE1_LEGACY:
                # Type-1: extract from search-engine URL
                search_query = self.url_extractor.extract(url)

            else:
                # Type-2: prefer page title, fallback to URL path
                raw_row = raw_chunk.loc[idx] if idx in raw_chunk.index else None
                title = ''
                if raw_row is not None:
                    title = str(raw_row.get('title', '') or '')

                search_query = (
                    self.url_extractor.extract_from_title(title)
                    or self.url_extractor.extract_from_url_path(url)
                )

            if not search_query:
                continue

            self.stats.queries_extracted += 1

            # ── Normalise ─────────────────────────────────────────────────
            normalized_query = self.normalizer.normalize(search_query)
            if not normalized_query:
                continue

            # ── Classification cascade ────────────────────────────────────
            product = self._process_query(
                search_query=search_query,
                normalized_query=normalized_query,
                row=row
            )

            if product:
                products.append(product)

        return products

    # ──────────────────────────────────────────────────────────────────────
    # Query processing (unchanged cascade logic)
    # ──────────────────────────────────────────────────────────────────────

    def _process_query(
        self,
        search_query: str,
        normalized_query: str,
        row: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Process single query through classification cascade.

        Args:
            search_query:    Original search query
            normalized_query: Normalized query
            row:             Unified-schema row (has click_count, frequency, timestamp)

        Returns:
            Product dict or None
        """
        # LEVEL 0: ML First-Level Filter
        ml_label = self.ml_classifier.predict_label(normalized_query)

        if ml_label == 0:
            self.stats.ml_label_0 += 1
            self.stats.non_products += 1
            return None

        self.stats.ml_label_1 += 1

        result, source = self._classify_query(search_query, normalized_query)

        if not result:
            return None

        is_product = result.get('is_product', False)

        if not is_product:
            self.stats.non_products += 1
            return None

        category  = (result.get('category') or '').strip()
        product   = (result.get('product')  or '').strip()
        brand     = (result.get('brand')    or '').strip()
        model     = (result.get('model')    or '').strip()

        engagement_score = self.engagement_scorer.calculate_score(row)

        self.stats.products_found += 1

        return {
            'timestamp':        row['timestamp'],
            'query':            normalized_query,
            'category':         category,
            'product':          product,
            'brand':            brand,
            'model':            model,
            'engagement_score': engagement_score,
            # Unified schema column names (fixes legacy bug where co_varnames was stored)
            'click_count':      float(row.get('click_count', 0)),
            'frequency':        float(row.get('frequency', 0)),
            'source':           source
        }

    def _classify_query(
        self,
        search_query: str,
        normalized_query: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Run classification cascade."""
        # LEVEL 1: Vector DB - Exact lookup
        vectordb_exact = self.vectordb_store.exact_lookup(normalized_query)
        if vectordb_exact:
            self.stats.vectordb_exact_hits += 1
            return vectordb_exact, 'vectordb_exact'

        # LEVEL 1b: Vector DB - Semantic search
        if self.vectordb_store.embedding_model:
            try:
                query_embedding = self.vectordb_store.embedding_model.encode(
                    normalized_query,
                    convert_to_numpy=True
                )
                vectordb_semantic = self.vectordb_store.semantic_search(
                    query_embedding,
                    threshold=self.semantic_threshold
                )
                if vectordb_semantic:
                    self.stats.vectordb_semantic_hits += 1
                    return vectordb_semantic, 'vectordb_semantic'
            except Exception as e:
                self.logger.warning(
                    f"Embedding error for '{normalized_query}': {e}"
                )

        # LEVEL 2: User Data lookup
        user_match = self.user_data_store.lookup(normalized_query)
        if user_match:
            self.stats.user_data_hits += 1
            return user_match, 'user_data'

        # LEVEL 3: Training Data lookup
        training_label = self.training_data_store.lookup(normalized_query)
        if training_label is not None:
            is_product = (training_label == 1)
            result = {
                'is_product': is_product,
                'category': '',
                'product': '',
                'brand': '',
                'model': '',
                'confidence': 0.0
            }
            self.stats.training_data_hits += 1
            return result, 'training_data'

        # LEVEL 4: LLM fallback with Vector DB write-back
        self.stats.llm_calls += 1
        llm_result = self.llm_classifier.classify(search_query, normalized_query)

        if llm_result:
            self.stats.llm_success += 1
            if llm_result.get('written_to_vectordb', False):
                self.stats.llm_written_to_vectordb += 1
            return llm_result, 'llm'

        return None, None

    # ──────────────────────────────────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────────────────────────────────

    def _print_stats(self, csv_format: Optional[CSVFormat] = None) -> None:
        """Print processing statistics."""
        self.logger.separator()
        self.logger.info("Collection Complete")
        self.logger.separator()
        if csv_format:
            self.logger.info(f"CSV Format: {csv_format.value}")
        self.logger.info(f"Total rows processed:     {self.stats.total_rows}")
        self.logger.info(f"Queries extracted:        {self.stats.queries_extracted}")
        self.logger.info(f"ML Label=0 (skipped):     {self.stats.ml_label_0}")
        self.logger.info(f"ML Label=1 (processed):   {self.stats.ml_label_1}")
        self.logger.info(f"Vector DB exact hits:     {self.stats.vectordb_exact_hits}")
        self.logger.info(f"Vector DB semantic hits:  {self.stats.vectordb_semantic_hits}")
        self.logger.info(f"User data hits:           {self.stats.user_data_hits}")
        self.logger.info(f"Training data hits:       {self.stats.training_data_hits}")
        self.logger.info(f"LLM calls:                {self.stats.llm_calls}")
        self.logger.info(f"LLM success:              {self.stats.llm_success}")
        self.logger.info(f"LLM written to Vector DB: {self.stats.llm_written_to_vectordb}")
        self.logger.info(f"Products collected:       {self.stats.products_found}")
        self.logger.info(f"Non-products found:       {self.stats.non_products}\n")



class ProcessingStats:
    """Track processing statistics."""
    
    def __init__(self):
        self.total_rows = 0
        self.queries_extracted = 0
        self.ml_label_0 = 0
        self.ml_label_1 = 0
        self.vectordb_exact_hits = 0
        self.vectordb_semantic_hits = 0
        self.user_data_hits = 0
        self.training_data_hits = 0
        self.llm_calls = 0
        self.llm_success = 0
        self.llm_written_to_vectordb = 0
        self.products_found = 0
        self.non_products = 0
    
    def to_dict(self) -> Dict[str, int]:
        """Convert stats to dictionary."""
        return {
            'total_rows': self.total_rows,
            'queries_extracted': self.queries_extracted,
            'ml_label_0': self.ml_label_0,
            'ml_label_1': self.ml_label_1,
            'vectordb_exact_hits': self.vectordb_exact_hits,
            'vectordb_semantic_hits': self.vectordb_semantic_hits,
            'user_data_hits': self.user_data_hits,
            'training_data_hits': self.training_data_hits,
            'llm_calls': self.llm_calls,
            'llm_success': self.llm_success,
            'llm_written_to_vectordb': self.llm_written_to_vectordb,
            'products_found': self.products_found,
            'non_products': self.non_products
        }




class StreamingPipeline:
    """
    Streaming CSV processing pipeline with classification cascade.

    Automatically detects whether the CSV is Type-1 (Legacy) or Type-2 (New)
    and normalises every chunk to a unified internal schema before processing.

    Unified schema columns (produced by csv_detector normalizers):
        url, timestamp, click_count, frequency

    Pipeline flow:
        ML Filter (label 0 → skip, label 1 → continue)
            → Vector DB exact
            → Vector DB semantic
            → User Data
            → Training Data
            → LLM (with Vector DB write-back)
    """

    def __init__(
        self,
        ml_classifier: MLProductClassifier,
        vectordb_store: VectorDBStore,
        user_data_store: ReadOnlyUserDataStore,
        training_data_store: ReadOnlyTrainingDataStore,
        llm_classifier: LLMClassifierWithWriteBack,
        url_extractor: URLQueryExtractor,
        normalizer: QueryNormalizer,
        engagement_scorer: EngagementScorer,
        chunk_size: int = 100,
        max_products: int = 100,
        semantic_threshold: float = 0.85,
        logger: Optional[Logger] = None
    ):
        self.ml_classifier = ml_classifier
        self.vectordb_store = vectordb_store
        self.user_data_store = user_data_store
        self.training_data_store = training_data_store
        self.llm_classifier = llm_classifier
        self.url_extractor = url_extractor
        self.normalizer = normalizer
        self.engagement_scorer = engagement_scorer

        self.chunk_size = chunk_size
        self.max_products = max_products
        self.semantic_threshold = semantic_threshold

        self.logger = logger or Logger(verbose=False)
        self.stats = ProcessingStats()

    def process_user_csv(
        self,
        user_id: str,
        data_dir: str
    ) -> Tuple[List[Dict[str, Any]], ProcessingStats]:
        """
        Process user CSV file with streaming.

        Detects the CSV format automatically and delegates chunk processing
        to the appropriate path.

        Args:
            user_id: User identifier
            data_dir: Directory containing user CSV files

        Returns:
            Tuple of (product_queries list, processing stats)

        Raises:
            UserNotFoundError: If user CSV not found
            CSVProcessingError: If CSV processing fails
        """
        csv_path = Path(data_dir) / f"{user_id}.csv"
        if not csv_path.exists():
            raise UserNotFoundError(f"User CSV not found: {csv_path}")

        # ── Detect format ──────────────────────────────────────────────────
        csv_format = detect_csv_format(str(csv_path))
        format_label = csv_format.value

        if csv_format == CSVFormat.UNKNOWN:
            raise CSVProcessingError(
                f"Unrecognised CSV format for {csv_path}. "
                "Expected Type-1 (Links/Time1/ClickCount/Frequency) or "
                "Type-2 (url/title/visit_count/visit_time)."
            )

        self.logger.info(f"Streaming CSV: {csv_path}  [format: {format_label}]")
        self.logger.info(f"Target: {self.max_products} products\n")
        self.logger.info(
            "Processing with ML → Vector DB → User Data → "
            "Training Data → LLM (with write-back) flow...\n"
        )

        # ── Reset stats ────────────────────────────────────────────────────
        self.stats = ProcessingStats()
        product_queries: List[Dict[str, Any]] = []
        product_count = 0

        try:
            reader = pd.read_csv(
                csv_path,
                encoding='utf-8-sig',
                chunksize=self.chunk_size
            )
            for chunk in reader:
                if product_count >= self.max_products:
                    break

                # Normalise to unified schema
                try:
                    norm_chunk = normalize_chunk(chunk, csv_format)
                except Exception as e:
                    self.logger.warning(f"Chunk normalisation failed: {e} — skipping chunk")
                    continue

                # Sort newest-first
                norm_chunk = norm_chunk.sort_values('timestamp', ascending=False)

                chunk_products = self._process_chunk(
                    norm_chunk, product_count, csv_format
                )
                product_queries.extend(chunk_products)
                product_count += len(chunk_products)

                if product_count >= self.max_products:
                    self.logger.info(
                        f"\n✓ Reached {self.max_products} products - stopping stream"
                    )
                    break

                if self.logger.verbose and product_count > 0 and product_count % 10 == 0:
                    self.logger.info(
                        f"  Progress: {product_count}/{self.max_products} products collected"
                    )

        except (UserNotFoundError, CSVProcessingError):
            raise
        except Exception as e:
            raise CSVProcessingError(f"Error processing CSV: {e}")

        self._print_stats(csv_format)
        return product_queries, self.stats

    # ──────────────────────────────────────────────────────────────────────
    # Chunk processing
    # ──────────────────────────────────────────────────────────────────────

    def _process_chunk(
        self,
        norm_chunk: pd.DataFrame,
        current_product_count: int,
        csv_format: CSVFormat,
    ) -> List[Dict[str, Any]]:
        """
        Process a single normalised CSV chunk.

        Both Type-1 and Type-2 rows arrive with the unified schema
        (url, title, timestamp, click_count, frequency).

        Type-1: query extracted from the 'url' column via search-engine param parsing.
        Type-2: query extracted from the 'title' column (page title is the only signal).

        Args:
            norm_chunk:            Normalised DataFrame (unified schema)
            current_product_count: Running count of products already collected
            csv_format:            Detected format enum

        Returns:
            List of product query dicts
        """
        products: List[Dict[str, Any]] = []

        for idx, row in norm_chunk.iterrows():
            if current_product_count + len(products) >= self.max_products:
                break

            self.stats.total_rows += 1

            # ── Query extraction (format-aware) ───────────────────────────
            if csv_format == CSVFormat.TYPE1_LEGACY:
                # Type-1: extract search query from URL
                url = str(row.get('url', '') or '')
                search_query = self.url_extractor.extract(url)
            else:
                # Type-2: title is the sole query signal (no URL column)
                title = str(row.get('title', '') or '')
                search_query = self.url_extractor.extract_from_title(title)

            if not search_query:
                continue

            self.stats.queries_extracted += 1

            # ── Normalise ─────────────────────────────────────────────────
            normalized_query = self.normalizer.normalize(search_query)
            if not normalized_query:
                continue

            # ── Classification cascade ────────────────────────────────────
            product = self._process_query(
                search_query=search_query,
                normalized_query=normalized_query,
                row=row
            )

            if product:
                products.append(product)

        return products

    # ──────────────────────────────────────────────────────────────────────
    # Query processing
    # ──────────────────────────────────────────────────────────────────────

    def _process_query(
        self,
        search_query: str,
        normalized_query: str,
        row: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Process single query through classification cascade.

        Args:
            search_query:     Original search query
            normalized_query: Normalized query
            row:              Unified-schema row (click_count, frequency, timestamp)

        Returns:
            Product dict or None
        """
        # LEVEL 0: ML First-Level Filter
        ml_label = self.ml_classifier.predict_label(normalized_query)

        if ml_label == 0:
            self.stats.ml_label_0 += 1
            self.stats.non_products += 1
            return None

        self.stats.ml_label_1 += 1

        result, source = self._classify_query(search_query, normalized_query)

        if not result:
            return None

        is_product = result.get('is_product', False)
        if not is_product:
            self.stats.non_products += 1
            return None

        category = (result.get('category') or '').strip()
        product  = (result.get('product')  or '').strip()
        brand    = (result.get('brand')    or '').strip()
        model    = (result.get('model')    or '').strip()

        engagement_score = self.engagement_scorer.calculate_score(row)

        self.stats.products_found += 1

        return {
            'timestamp':        row['timestamp'],
            'query':            normalized_query,
            'category':         category,
            'product':          product,
            'brand':            brand,
            'model':            model,
            'engagement_score': engagement_score,
            'click_count':      float(row.get('click_count', 0)),
            'frequency':        float(row.get('frequency', 0)),
            'source':           source
        }

    def _classify_query(
        self,
        search_query: str,
        normalized_query: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Run classification cascade."""
        # LEVEL 1: Vector DB - Exact lookup
        vectordb_exact = self.vectordb_store.exact_lookup(normalized_query)
        if vectordb_exact:
            self.stats.vectordb_exact_hits += 1
            return vectordb_exact, 'vectordb_exact'

        # LEVEL 1b: Vector DB - Semantic search
        if self.vectordb_store.embedding_model:
            try:
                query_embedding = self.vectordb_store.embedding_model.encode(
                    normalized_query, convert_to_numpy=True
                )
                vectordb_semantic = self.vectordb_store.semantic_search(
                    query_embedding, threshold=self.semantic_threshold
                )
                if vectordb_semantic:
                    self.stats.vectordb_semantic_hits += 1
                    return vectordb_semantic, 'vectordb_semantic'
            except Exception as e:
                self.logger.warning(f"Embedding error for '{normalized_query}': {e}")

        # LEVEL 2: User Data lookup
        user_match = self.user_data_store.lookup(normalized_query)
        if user_match:
            self.stats.user_data_hits += 1
            return user_match, 'user_data'

        # LEVEL 3: Training Data lookup
        training_label = self.training_data_store.lookup(normalized_query)
        if training_label is not None:
            is_product = (training_label == 1)
            result = {
                'is_product': is_product,
                'category': '', 'product': '',
                'brand': '', 'model': '', 'confidence': 0.0
            }
            self.stats.training_data_hits += 1
            return result, 'training_data'

        # LEVEL 4: LLM fallback with Vector DB write-back
        self.stats.llm_calls += 1
        llm_result = self.llm_classifier.classify(search_query, normalized_query)

        if llm_result:
            self.stats.llm_success += 1
            if llm_result.get('written_to_vectordb', False):
                self.stats.llm_written_to_vectordb += 1
            return llm_result, 'llm'

        return None, None

    # ──────────────────────────────────────────────────────────────────────
    # Stats
    # ──────────────────────────────────────────────────────────────────────

    def _print_stats(self, csv_format: Optional[CSVFormat] = None) -> None:
        """Print processing statistics."""
        self.logger.separator()
        self.logger.info("Collection Complete")
        self.logger.separator()
        if csv_format:
            self.logger.info(f"CSV Format:               {csv_format.value}")
        self.logger.info(f"Total rows processed:     {self.stats.total_rows}")
        self.logger.info(f"Queries extracted:        {self.stats.queries_extracted}")
        self.logger.info(f"ML Label=0 (skipped):     {self.stats.ml_label_0}")
        self.logger.info(f"ML Label=1 (processed):   {self.stats.ml_label_1}")
        self.logger.info(f"Vector DB exact hits:     {self.stats.vectordb_exact_hits}")
        self.logger.info(f"Vector DB semantic hits:  {self.stats.vectordb_semantic_hits}")
        self.logger.info(f"User data hits:           {self.stats.user_data_hits}")
        self.logger.info(f"Training data hits:       {self.stats.training_data_hits}")
        self.logger.info(f"LLM calls:                {self.stats.llm_calls}")
        self.logger.info(f"LLM success:              {self.stats.llm_success}")
        self.logger.info(f"LLM written to Vector DB: {self.stats.llm_written_to_vectordb}")
        self.logger.info(f"Products collected:       {self.stats.products_found}")
        self.logger.info(f"Non-products found:       {self.stats.non_products}\n")