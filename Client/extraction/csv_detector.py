"""
CSV format detection for browser history files.

Supports two formats:
  Type 1 (Legacy):  Links, Time1, Time2, ClickCount, Frequency
  Type 2 (New):     Title, Visit Count, Last Visit Time
"""
import pandas as pd
from enum import Enum


class CSVFormat(Enum):
    TYPE1_LEGACY = "type1_legacy"   # Links, Time1, Time2, ClickCount, Frequency
    TYPE2_NEW    = "type2_new"      # Title, Visit Count, Last Visit Time
    UNKNOWN      = "unknown"


def _clean_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Strip BOM, whitespace from column names in-place and return df."""
    df.columns = df.columns.str.replace('\ufeff', '', regex=False).str.strip()
    return df


def detect_csv_format(csv_path: str) -> CSVFormat:
    """
    Detect the format of a browser history CSV file by inspecting its headers.

    Detection is case-insensitive and tolerant of leading/trailing whitespace.

    Args:
        csv_path: Path to the CSV file

    Returns:
        CSVFormat enum value
    """
    try:
        header_df = pd.read_csv(csv_path, nrows=0, encoding='utf-8-sig', sep=None, engine='python')
        cols = {c.strip().lower().replace('\ufeff', '') for c in header_df.columns}

        # Type 2: Title, Visit Count, Last Visit Time  (no URL column)
        if 'title' in cols and 'visit count' in cols and 'last visit time' in cols:
            return CSVFormat.TYPE2_NEW

        # Type 1: Links + at least one time/engagement column
        if 'links' in cols and (
            'time1' in cols or 'time2' in cols or
            'clickcount' in cols or 'frequency' in cols
        ):
            return CSVFormat.TYPE1_LEGACY

    except Exception:
        pass

    return CSVFormat.UNKNOWN


def normalize_columns_type1(chunk: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize a Type-1 chunk to the unified internal schema.

    Input columns:  Links, Time1, Time2, ClickCount, Frequency
    Output columns: title, timestamp, click_count, frequency

    'title' is set to an empty string — Type-1 has no page title; the
    pipeline uses URL-based search-query extraction for these rows.
    """
    chunk = _clean_cols(chunk.copy())

    # URL kept for query extraction in pipeline
    chunk = chunk.rename(columns={'Links': 'url'})

    # Resolve Unix timestamp: prefer Time1, fallback Time2
    if 'Time1' in chunk.columns:
        ts_raw = pd.to_numeric(chunk['Time1'], errors='coerce')
    elif 'Time2' in chunk.columns:
        ts_raw = pd.to_numeric(chunk['Time2'], errors='coerce')
    else:
        ts_raw = pd.Series(0, index=chunk.index)

    chunk['timestamp'] = pd.to_datetime(
        ts_raw, unit='s', errors='coerce'
    ).fillna(pd.Timestamp.now())

    chunk['click_count'] = pd.to_numeric(
        chunk.get('ClickCount', pd.Series(0, index=chunk.index)), errors='coerce'
    ).fillna(0)

    chunk['frequency'] = pd.to_numeric(
        chunk.get('Frequency', pd.Series(0, index=chunk.index)), errors='coerce'
    ).fillna(0)

    # No page title in Type-1
    chunk['title'] = ''

    return chunk[['url', 'title', 'timestamp', 'click_count', 'frequency']]


def normalize_columns_type2(chunk: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize a Type-2 chunk to the unified internal schema.

    Input columns:  Title, Visit Count, Last Visit Time
    Output columns: url, title, timestamp, click_count, frequency

    Type-2 has no URL column — title is the sole query signal.
    Type-2 has no Frequency column — defaults to 0.0.
    'Last Visit Time' is a human-readable datetime string.
    """
    chunk = _clean_cols(chunk.copy())

    # Rename to unified names (case-insensitive match)
    rename_map = {}
    for col in chunk.columns:
        lc = col.lower()
        if lc == 'title':
            rename_map[col] = 'title'
        elif lc == 'visit count':
            rename_map[col] = 'click_count'
        elif lc == 'last visit time':
            rename_map[col] = '_last_visit'
    chunk = chunk.rename(columns=rename_map)

    # Parse human-readable datetime  e.g. "2026-02-27 05:41:09.608887"
    chunk['timestamp'] = pd.to_datetime(
        chunk['_last_visit'], errors='coerce'
    ).fillna(pd.Timestamp.now())

    chunk['click_count'] = pd.to_numeric(
        chunk['click_count'], errors='coerce'
    ).fillna(0)

    # No Frequency in Type-2
    chunk['frequency'] = 0.0

    # No URL in Type-2
    chunk['url'] = ''

    return chunk[['url', 'title', 'timestamp', 'click_count', 'frequency']]


def normalize_chunk(chunk: pd.DataFrame, fmt: CSVFormat) -> pd.DataFrame:
    """
    Dispatch chunk normalisation based on detected format.

    Args:
        chunk: Raw DataFrame chunk
        fmt:   Detected CSVFormat

    Returns:
        Normalised DataFrame with unified schema:
            url, title, timestamp, click_count, frequency
    """
    if fmt == CSVFormat.TYPE1_LEGACY:
        return normalize_columns_type1(chunk)
    elif fmt == CSVFormat.TYPE2_NEW:
        return normalize_columns_type2(chunk)
    else:
        raise ValueError("Cannot normalise chunk: unknown CSV format")