"""MODIS MOD13Q1 v061 NDVI (250 m, 16-day composites) via the ORNL DAAC MODIS/VIIRS web service.

API docs: https://modis.ornl.gov/data/modis_webservice.html — no login required.
The service returns at most 10 composites per request, so we split the period and query in parallel.
"""

from __future__ import annotations

import asyncio

import httpx

from . import cache

ORNL_URL = "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset"
BAND = "250m_16_days_NDVI"
SCALE = 0.0001
FILL = -3000
YEARS = (2024, 2025)
COMPOSITE_DOYS = list(range(1, 366, 16))  # 1, 17, ..., 353 (23 composites per year)


def _chunks() -> list[tuple[str, str]]:
    dates = [f"A{y}{d:03d}" for y in YEARS for d in COMPOSITE_DOYS]
    return [(dates[i], dates[min(i + 9, len(dates) - 1)]) for i in range(0, len(dates), 10)]


async def _fetch_chunk(client: httpx.AsyncClient, lat: float, lon: float, start: str, end: str) -> list:
    params = {
        "latitude": lat,
        "longitude": lon,
        "band": BAND,
        "startDate": start,
        "endDate": end,
        "kmAboveBelow": 0,
        "kmLeftRight": 0,
    }
    resp = await client.get(ORNL_URL, params=params, headers={"Accept": "application/json"})
    resp.raise_for_status()
    return resp.json().get("subset", [])


async def fetch_ndvi(lat: float, lon: float) -> dict:
    """Return {"meta": {...}, "points": [{"date": "YYYY-MM-DD", "ndvi": float}]}."""
    lat, lon = round(lat, 2), round(lon, 2)
    cached = cache.load("modis", lat, lon)
    if cached:
        return cached

    async with httpx.AsyncClient(timeout=120) as client:
        results = await asyncio.gather(*(_fetch_chunk(client, lat, lon, s, e) for s, e in _chunks()))

    points = []
    for chunk in results:
        for item in chunk:
            value = item["data"][0] if item.get("data") else FILL
            if value != FILL:
                points.append({"date": item["calendar_date"], "ndvi": round(value * SCALE, 3)})
    points.sort(key=lambda p: p["date"])

    payload = {
        "meta": {
            "source": "MODIS/Terra MOD13Q1 v061 via ORNL DAAC web service",
            "band": BAND,
            "pixel_size_m": 250,
            "period": f"{YEARS[0]}-{YEARS[-1]}",
        },
        "points": points,
    }
    cache.save("modis", lat, lon, payload)
    return payload
