"""
Text utilities shared across services.
"""
import re
from typing import List

# Common English stop-words (compact set — expand as needed)
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "in", "on", "at", "to",
    "of", "with", "by", "from", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it",
    "they", "them", "their", "this", "that", "these", "those",
    "what", "which", "who", "how", "when", "where", "buy", "price",
    "best", "review", "cheap", "vs", "top", "new", "latest",
}


def tokenize(text: str) -> List[str]:
    """
    Lowercase, strip punctuation, remove stop-words, return meaningful tokens.

    >>> tokenize("Apple iPhone 15 Pro review")
    ['apple', 'iphone', '15', 'pro']
    """
    if not text:
        return []

    text = text.lower()
    # Split on non-alphanumeric (keep digits)
    tokens = re.findall(r"[a-z0-9]+", text)
    # Remove stop-words and very short tokens
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


def normalize_category(cat: str) -> str:
    """Title-case a category string."""
    return cat.strip().title() if cat else ""