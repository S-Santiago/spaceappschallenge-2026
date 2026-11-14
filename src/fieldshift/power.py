"""NASA POWER (Prediction Of Worldwide Energy Resources) daily point data client.

API docs: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
No login or key required. Source data: MERRA-2 (meteorology), ~0.5° x 0.625° grid.
"""

from __future__ import annotations

import httpx

from . import cache

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "GWETROOT"]
START_YEAR = 2005
END_YEAR = 2025
FILL_VALUE = -999.0


async def fetch_daily(lat: float, lon: float) -> dict:
    """Return {"meta": {...}, "days": {"YYYYMMDD": {param: value}}} for START_YEAR..END_YEAR."""
    lat, lon = round(lat, 2), round(lon, 2)
    cached = cache.load("power", lat, lon)
    if cached:
        return cached

    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": f"{START_YEAR}0101",
        "end": f"{END_YEAR}1231",
        "format": "JSON",
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.get(POWER_URL, params=params)
        resp.raise_for_status()
        raw = resp.json()

    series = raw["properties"]["parameter"]
    days: dict[str, dict[str, float | None]] = {}
    for param, values in series.items():
        for day, value in values.items():
            days.setdefault(day, {})[param] = None if value == FILL_VALUE else value

    payload = {
        "meta": {
            "source": "NASA POWER daily point API (community=AG)",
            "api_version": raw["header"]["api"]["version"],
            "sources": raw["header"].get("sources", []),
            "elevation_m": raw["geometry"]["coordinates"][2],
            "period": f"{START_YEAR}-{END_YEAR}",
            "parameters": raw.get("parameters", {}),
        },
        "days": days,
    }
    cache.save("power", lat, lon, payload)
    return payload
