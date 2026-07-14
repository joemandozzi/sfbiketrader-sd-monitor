"""Tracks every distinct (brand, model) pair extracted so far, so each run
can re-search San Diego for the full historical set of frames -- not just
ones discovered in this run -- since a new San Diego listing can show up
for a frame model first seen weeks ago.
"""
import json
import os
from pathlib import Path
from typing import List, Set, Tuple

DEFAULT_KNOWN_FRAMES_FILE = str(Path(__file__).resolve().parent.parent / "data" / "known_frames.json")

Frame = Tuple[str, str]  # (brand, model)


def load_known_frames(path: str = DEFAULT_KNOWN_FRAMES_FILE) -> Set[Frame]:
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        pairs: List[List[str]] = json.load(f)
    return {(brand, model) for brand, model in pairs}


def add_known_frames(frames: Set[Frame], path: str = DEFAULT_KNOWN_FRAMES_FILE) -> None:
    existing = load_known_frames(path)
    combined = existing | frames
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(sorted(combined), f, indent=2)
