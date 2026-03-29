"""
Engagement scoring utilities.
"""
from typing import Any
import pandas as pd


class EngagementScorer:
    """Calculate engagement scores from row data."""
    
    def __init__(self, alpha: float = 1.0, beta: float = 1.0):
        """
        Initialize engagement scorer.
        
        Args:
            alpha: Weight for ClickCount
            beta: Weight for Frequency
        """
        self.alpha = alpha
        self.beta = beta
    
    def calculate_score(self, row: Any) -> float:
        """
        Calculate engagement score for a row.

        Accepts the unified internal schema produced by csv_detector normalizers:
            click_count  — mapped from ClickCount (Type-1) or visit_count (Type-2)
            frequency    — mapped from Frequency (Type-1) or 0.0 (Type-2)

        Legacy column names (ClickCount / Frequency) are also accepted as a
        fallback so that any code paths that bypass the normalizer continue to
        work correctly.

        Args:
            row: DataFrame row or dict-like object

        Returns:
            Weighted engagement score
        """
        # Prefer unified schema names; fall back to legacy names
        click_count = row.get('click_count', row.get('ClickCount', 0))
        frequency   = row.get('frequency',   row.get('Frequency',   0))

        try:
            click_count = float(click_count) if pd.notna(click_count) else 0.0
            frequency   = float(frequency)   if pd.notna(frequency)   else 0.0
        except Exception:
            click_count = 0.0
            frequency   = 0.0

        return (click_count * self.alpha) + (frequency * self.beta)