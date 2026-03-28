"""
URL query extraction utilities.

Supports two browser-history CSV formats:
  Type 1 (Legacy): URLs from search engines — query extracted from ?q= / ?p= params.
  Type 2 (New):    Title-only rows — page title is used directly as the query signal.
"""
from urllib.parse import urlparse, parse_qs, unquote
from typing import Optional


class URLQueryExtractor:
    """Extract search queries from browser history rows."""

    # Supported search engines and their query parameters
    SEARCH_ENGINES = {
        'google': 'q',
        'bing': 'q',
        'duckduckgo': 'q',
        'yahoo': 'p'
    }

    @staticmethod
    def extract(url: str) -> Optional[str]:
        """
        Extract search query from a Type-1 search-engine URL.

        Parses the URL and returns the value of the recognised search-engine
        query parameter (e.g. ?q=...).  Returns None for all non-search URLs
        so that the pipeline skips them.

        Args:
            url: Full URL string

        Returns:
            Extracted search query or None
        """
        if not url or not isinstance(url, str):
            return None

        try:
            url = unquote(url)
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            query_params = parse_qs(parsed.query)

            for engine, param_name in URLQueryExtractor.SEARCH_ENGINES.items():
                if engine in domain and param_name in query_params:
                    query = query_params[param_name][0].strip()
                    if query:
                        return query

            return None

        except Exception:
            return None

    @staticmethod
    def extract_from_title(title: str) -> Optional[str]:
        """
        Extract a query signal from a page title (Type-2 CSV rows).

        For Type-2 files the page title is the only textual signal available.
        Common site-name suffixes appended after ' - ' or ' | ' separators
        are stripped so only the content-describing portion is returned.

        Examples:
            "Samsung Galaxy S24 Ultra - Amazon"  →  "Samsung Galaxy S24 Ultra"
            "Nike Air Max 270 Shoes | Myntra"    →  "Nike Air Max 270 Shoes"
            "localhost"                           →  None  (too short / generic)

        Args:
            title: Raw page title string

        Returns:
            Cleaned title string to use as query, or None if unusable
        """
        if not title or not isinstance(title, str):
            return None

        title = title.strip()
        if not title:
            return None

        # Strip common site-name suffixes
        for sep in (' - ', ' | ', ' – ', ' — '):
            if sep in title:
                title = title.split(sep)[0].strip()
                break

        # Discard single-word generic titles (e.g. "localhost", "Gmail")
        if len(title.split()) < 2:
            return None

        return title if title else None