"""Dedup state: tracks which Instagram post IDs have already been processed.

Flat JSON file is plenty at this volume (one account, low post frequency) --
no need for a database.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Set

DEFAULT_STATE_FILE = str(Path(__file__).resolve().parent.parent / "data" / "seen_posts.json")


def load_seen(path: str = DEFAULT_STATE_FILE) -> Set[str]:
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        data: Dict[str, str] = json.load(f)
    return set(data.keys())


def mark_seen(post_ids, path: str = DEFAULT_STATE_FILE) -> None:
    data: Dict[str, str] = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    for post_id in post_ids:
        data[post_id] = now
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
