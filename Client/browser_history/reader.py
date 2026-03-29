"""
Chrome browser history reader.

Reads Chrome's SQLite History database and exports it as a CSV file
in the Type-2 format (Title, Visit Count, Last Visit Time) that the
processing pipeline already understands.
"""
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

import pandas as pd


# ── Chrome timestamp conversion ───────────────────────────────────────────────

def chrome_time_to_datetime(chrome_time: int) -> datetime | None:
    """
    Convert a Chrome timestamp to a Python datetime.

    Chrome stores time as microseconds since Jan 1, 1601 (UTC).

    Args:
        chrome_time: Raw integer from Chrome's SQLite database

    Returns:
        Python datetime or None if chrome_time is 0 / invalid
    """
    if not chrome_time:
        return None
    try:
        epoch_start = datetime(1601, 1, 1)
        return epoch_start + timedelta(microseconds=chrome_time)
    except (OverflowError, ValueError):
        return None


# ── Core reader ───────────────────────────────────────────────────────────────

def read_chrome_history(chrome_profile_path: str) -> pd.DataFrame:
    """
    Read Chrome browsing history from the profile's SQLite History database.

    Opens a temporary copy of the database to avoid the 'database is locked'
    error that occurs when Chrome is running.

    Args:
        chrome_profile_path: Full path to the Chrome profile directory
                             e.g. C:\\Users\\name\\AppData\\Local\\Google\\
                                  Chrome\\User Data\\Profile 3

    Returns:
        DataFrame with columns: Title, Visit Count, Last Visit Time

    Raises:
        FileNotFoundError: If the profile path or History DB does not exist
        RuntimeError:      If the database cannot be read
    """
    profile_path = Path(chrome_profile_path)
    if not profile_path.exists():
        raise FileNotFoundError(
            f"Chrome profile directory not found: {chrome_profile_path}"
        )

    history_db = profile_path / "History"
    if not history_db.exists():
        raise FileNotFoundError(
            f"Chrome History database not found at: {history_db}\n"
            "Make sure the profile path is correct and Chrome has been opened at least once."
        )

    # Copy DB to a temp file to avoid lock issues while Chrome is open
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db", prefix="chrome_history_")
    os.close(tmp_fd)

    try:
        shutil.copy2(str(history_db), tmp_path)

        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()

        # Group by title to get unique pages with max visit count
        cursor.execute("""
            SELECT
                title,
                MAX(visit_count)     AS visit_count,
                MAX(last_visit_time) AS last_visit_time
            FROM urls
            WHERE title IS NOT NULL AND title != ''
            GROUP BY title
            ORDER BY visit_count DESC
        """)
        rows = cursor.fetchall()
        conn.close()

    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to read Chrome History database: {e}")
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    # Build DataFrame
    records = []
    for title, visit_count, last_visit_time in rows:
        readable_time = chrome_time_to_datetime(last_visit_time)
        records.append({
            "Title":           title,
            "Visit Count":     visit_count,
            "Last Visit Time": readable_time
        })

    return pd.DataFrame(records)


# ── Export ────────────────────────────────────────────────────────────────────

def export_history_to_csv(
    user_id: str,
    chrome_profile_path: str,
    output_dir: str
) -> Tuple[str, int]:
    """
    Read Chrome history and save it as <user_id>.csv in output_dir.

    Overwrites any existing file for the same user_id.

    Args:
        user_id:             Identifier used as the output filename
        chrome_profile_path: Path to the Chrome profile directory
        output_dir:          Directory where the CSV will be saved
                             (created if it does not exist)

    Returns:
        Tuple of (absolute path to saved CSV, number of rows written)

    Raises:
        FileNotFoundError: If the Chrome profile / History DB is missing
        RuntimeError:      If the database cannot be read or CSV cannot be written
    """
    df = read_chrome_history(chrome_profile_path)

    if df.empty:
        raise RuntimeError(
            "Chrome History database is empty or contains no titled pages."
        )

    # Ensure output directory exists
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    csv_path = out_path / f"{user_id}.csv"

    try:
        # overwrite=True by default via mode='w'
        df.to_csv(str(csv_path), index=False)
    except OSError as e:
        raise RuntimeError(f"Failed to write CSV to {csv_path}: {e}")

    return str(csv_path.resolve()), len(df)