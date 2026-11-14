"""Pre-fetch NASA POWER + MODIS data for the demo fields into data/samples (committed), so the demo runs offline.

Usage (from the repo root): PYTHONPATH=src python -m fieldshift.samples
Demo fields are listed in data/samples/locations.csv; elevation_m is filled in from the POWER response.
"""

from __future__ import annotations

import asyncio
import csv
import json

from . import db, modis, power


async def main() -> None:
    with db.LOCATIONS_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        lat, lon = round(float(row["lat"]), 2), round(float(row["lon"]), 2)
        daily, ndvi = await asyncio.gather(power.fetch_daily(lat, lon), modis.fetch_ndvi(lat, lon))
        for kind, payload in (("power", daily), ("modis", ndvi)):
            path = db.SAMPLES_DIR / f"{kind}_{lat:.2f}_{lon:.2f}.json"
            path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        row["elevation_m"] = daily["meta"]["elevation_m"]
        print(f"{row['slug']}: {len(daily['days'])} POWER days, {len(ndvi['points'])} NDVI composites")

    with db.LOCATIONS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    asyncio.run(main())
