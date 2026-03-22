"""
Logging utilities for User Interest Extractor.
"""
import sys
from typing import Optional


class Logger:
    """Simple logger with verbose control."""
    
    def __init__(self, verbose: bool = True, prefix: str = ""):
        self.verbose = verbose
        self.prefix = prefix
    
    def info(self, message: str) -> None:
        """Log info message."""
        if self.verbose:
            prefix_str = f"[{self.prefix}] " if self.prefix else ""
            print(f"{prefix_str}{message}", file=sys.stdout)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        if self.verbose:
            prefix_str = f"[{self.prefix}] " if self.prefix else ""
            print(f"{prefix_str}Warning: {message}", file=sys.stderr)
    
    def error(self, message: str) -> None:
        """Log error message."""
        prefix_str = f"[{self.prefix}] " if self.prefix else ""
        print(f"{prefix_str}Error: {message}", file=sys.stderr)
    
    def separator(self, char: str = "=", length: int = 80) -> None:
        """Print separator line."""
        if self.verbose:
            print(char * length)
    
    def section(self, title: str, char: str = "=", length: int = 80) -> None:
        """Print section header."""
        if self.verbose:
            self.separator(char, length)
            print(title)
            self.separator(char, length)
            print()