"""Pre-fetch NASA POWER + MODIS data into data/samples (committed), so the demo runs offline.

Usage (from the repo root):
  PYTHONPATH=src python -m fieldshift.samples           # demo fields of data/samples/locations.csv
  PYTHONPATH=src python -m fieldshift.samples --points  # map points of data/samples/prefetch_points.csv

Demo fields: elevation_m is filled in from the POWER response.
Map points (towns the PWA finds with "Town or area"): real NASA data cached under the exact key the PWA sends,
so they answer instantly; they are NOT demo fields. Files already present are kept, so a town whose download
failed (ORNL is often slow) can be retried by running the command again.
"""

from __future__ import annotations

import asyncio
import csv
import json
import sys

from . import db, modis, power

PREFETCH_CSV = db.SAMPLES_DIR / "prefetch_points.csv"
FETCHERS = {"power": power.fetch_daily, "modis": modis.fetch_ndvi}


def _path(kind: str, lat: float, lon: float):
    return db.SAMPLES_DIR / f"{kind}_{lat:.2f}_{lon:.2f}.json"


def _write(kind: str, lat: float, lon: float, payload: dict) -> None:
    _path(kind, lat, lon).write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")


async def demo_fields() -> None:
    with db.LOCATIONS_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        lat, lon = round(float(row["lat"]), 2), round(float(row["lon"]), 2)
        daily, ndvi = await asyncio.gather(power.fetch_daily(lat, lon), modis.fetch_ndvi(lat, lon))
        _write("power", lat, lon, daily)
        _write("modis", lat, lon, ndvi)
        row["elevation_m"] = daily["meta"]["elevation_m"]
        print(f"{row['slug']}: {len(daily['days'])} POWER days, {len(ndvi['points'])} NDVI composites")

    with db.LOCATIONS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


async def map_points() -> None:
    with PREFETCH_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    async def one(row: dict, kind: str) -> None:
        lat, lon = round(float(row["lat"]), 2), round(float(row["lon"]), 2)
        path = _path(kind, lat, lon)
        if path.exists():
            print(f"{row['slug']} {kind}: kept ({path.stat().st_size:,} B)")
            return
        try:
            _write(kind, lat, lon, await FETCHERS[kind](lat, lon))
            print(f"{row['slug']} {kind}: fetched ({path.stat().st_size:,} B)")
        except Exception as exc:  # e.g. ORNL 502/timeout after the client's own retries: run again later
            print(f"{row['slug']} {kind}: FAILED ({exc!r:.100}), run the command again later")

    await asyncio.gather(*(one(r, k) for r in rows for k in r["sources"].split(";")))
    total = sum(f.stat().st_size for f in db.SAMPLES_DIR.iterdir() if f.is_file())
    print(f"data/samples total: {total / 1024 / 1024:.2f} MiB")


if __name__ == "__main__":
    asyncio.run(map_points() if "--points" in sys.argv[1:] else demo_fields())
