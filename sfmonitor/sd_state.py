"""Tracks which San Diego listing IDs have already been recorded in the
sheet, so re-runs only append genuinely new matches.

Ported from joemandozzi/bike-scraper's bikescraper/storage.py.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "seen_sd_listings.db"


def _connect(db_path=DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_listings (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            first_seen_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    return conn


def filter_unseen(listings, db_path=DB_PATH):
    """Return only the listings whose id hasn't been recorded before."""
    conn = _connect(db_path)
    try:
        seen_ids = {row[0] for row in conn.execute("SELECT id FROM seen_listings")}
        return [item for item in listings if item["id"] not in seen_ids]
    finally:
        conn.close()


def mark_seen(listings, db_path=DB_PATH):
    conn = _connect(db_path)
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO seen_listings (id, source) VALUES (?, ?)",
            [(item["id"], item["source"]) for item in listings],
        )
        conn.commit()
    finally:
        conn.close()
