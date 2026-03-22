"""
Custom exceptions for User Interest Extractor.
"""


class UserInterestExtractorError(Exception):
    """Base exception for all extractor errors."""
    pass


class MLClassifierError(UserInterestExtractorError):
    """ML classifier initialization or prediction error."""
    pass


class VectorDBError(UserInterestExtractorError):
    """Vector database operation error."""
    pass


class DataStoreError(UserInterestExtractorError):
    """Data store loading or access error."""
    pass


class CSVProcessingError(UserInterestExtractorError):
    """CSV file processing error."""
    pass


class LLMClassificationError(UserInterestExtractorError):
    """LLM classification error."""
    pass


class UserNotFoundError(UserInterestExtractorError):
    """User CSV file not found."""
    pass