"""Cache for raw NASA API payloads so repeated demo queries are instant and NASA APIs are not hammered.

Backed by the `nasa_raw` table of the SQLite database (see db.py). The committed samples in data/samples
(pre-fetched for the demo fields) are loaded into that table on start-up, so the app works offline.
"""

from __future__ import annotations

from typing import Any

from . import db


def load(kind: str, lat: float, lon: float) -> Any | None:
    return db.get_raw(kind, lat, lon)


def save(kind: str, lat: float, lon: float, payload: Any) -> None:
    db.save_raw(kind, lat, lon, payload)
