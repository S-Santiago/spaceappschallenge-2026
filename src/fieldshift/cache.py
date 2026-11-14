"""Tiny JSON file cache so repeated demo queries are instant and NASA APIs are not hammered.

Lookup order: data/processed/cache (git-ignored, written at runtime) then data/samples
(committed, pre-fetched for the demo locations so the app works offline).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "data" / "processed" / "cache"
SAMPLES_DIR = ROOT / "data" / "samples"


def _name(kind: str, lat: float, lon: float) -> str:
    return f"{kind}_{lat:.2f}_{lon:.2f}.json"


def load(kind: str, lat: float, lon: float) -> Any | None:
    for folder in (CACHE_DIR, SAMPLES_DIR):
        path = folder / _name(kind, lat, lon)
        if path.exists():
            return json.loads(path.read_text())
    return None


def save(kind: str, lat: float, lon: float, payload: Any) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / _name(kind, lat, lon)).write_text(json.dumps(payload))
