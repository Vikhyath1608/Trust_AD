"""
Domain-level exceptions for the Ad Serving Platform.
"""


class AdServerError(Exception):
    """Base exception."""


class AdNotFoundError(AdServerError):
    """Raised when an ad cannot be found by ID."""

    def __init__(self, ad_id: int):
        self.ad_id = ad_id
        super().__init__(f"Ad with id={ad_id} not found.")


class AdValidationError(AdServerError):
    """Raised when ad data fails business-rule validation."""


class NoAdsAvailableError(AdServerError):
    """Raised when no active ads exist in the repository."""


class ClientAPIError(AdServerError):
    """Raised when the Client (interest extraction) API call fails."""

    def __init__(self, detail: str):
        super().__init__(f"Client API error: {detail}")


class UploadError(AdServerError):
    """Raised when a file upload fails."""