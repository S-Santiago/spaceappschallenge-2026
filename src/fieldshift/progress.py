"""Live progress of the NASA downloads for a point, for GET /api/progress (docs/work-plan.md, "Live progress").

In memory only, per rounded point (0.01°), counters only: which source is downloading, how many MODIS batches
arrived and which try the slowest batch is on. It never changes the data results. Entries older than KEEP_S are
dropped. Single event loop (asyncio), so plain dict updates are safe.
"""

from __future__ import annotations

import time
from contextvars import ContextVar

KEEP_S = 900  # longer than api.MODIS_FAIL_MEMORY_S, so a remembered failure still shows as failed

# Set by api._fetch around the MODIS download task (tasks copy the context when created), read by modis.py.
# None outside a tracked download, so modis.fetch_ndvi keeps working on its own (tests, scripts).
current: ContextVar[dict | None] = ContextVar("fieldshift_progress", default=None)

_points: dict[tuple[float, float], dict[str, dict]] = {}


def _key(lat: float, lon: float) -> tuple[float, float]:
    return round(lat, 2), round(lon, 2)


def _prune(now: float) -> None:
    for key in [k for k, p in _points.items() if now - max(s["updated"] for s in p.values()) > KEEP_S]:
        del _points[key]


def start(source: str, lat: float, lon: float) -> dict:
    """A download of `source` ("power" | "modis") starts for the point: a fresh progress entry, returned."""
    now = time.monotonic()
    _prune(now)
    entry = {"state": "running", "started": now, "updated": now}
    if source == "modis":
        entry.update(batches_done=0, batches_total=0, tries={})
    _points.setdefault(_key(lat, lon), {})[source] = entry
    return entry


def finish(entry: dict, ok: bool) -> None:
    entry["state"] = "done" if ok else "failed"
    entry["updated"] = entry["ended"] = time.monotonic()


# Hooks for modis.py (no-ops when the download is not tracked).

def batches(total: int) -> None:
    if (entry := current.get()) is not None:
        entry.update(batches_total=total, batches_done=0, tries={}, updated=time.monotonic())


def batch_try(index: int, attempt: int) -> None:
    """Batch `index` starts try number `attempt` (1 = first)."""
    if (entry := current.get()) is not None:
        entry["tries"][index] = attempt
        entry["updated"] = time.monotonic()


def batch_done(index: int) -> None:
    if (entry := current.get()) is not None:
        entry["tries"].pop(index, None)
        entry["batches_done"] += 1
        entry["updated"] = time.monotonic()


def snapshot(lat: float, lon: float, stored: dict[str, bool], tries_max: int) -> dict:
    """Public JSON: {"power": {...}, "modis": {...}}. `stored[source]`: its data is already in the DB."""
    now = time.monotonic()
    found = _points.get(_key(lat, lon), {})
    out = {}
    for source in ("power", "modis"):
        entry = found.get(source)
        if entry is None:
            item = {"state": "done" if stored.get(source) else "idle", "elapsed_s": 0}
        else:
            item = {"state": entry["state"], "elapsed_s": round(entry.get("ended", now) - entry["started"])}
        if source == "modis":
            tries = (entry or {}).get("tries", {})
            item.update(batches_done=(entry or {}).get("batches_done", 0),
                        batches_total=(entry or {}).get("batches_total", 0),
                        attempt=max(tries.values(), default=1) if item["state"] == "running" else 1,
                        attempts_max=tries_max)
        out[source] = item
    return out
