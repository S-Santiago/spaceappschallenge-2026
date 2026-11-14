"""Climate indicators (docs/indicators.md I-01..I-11) -> Shape 1 climate profile (docs/work-plan.md).

Pure functions over the payloads returned by power.fetch_daily and modis.fetch_ndvi; this module
never downloads data itself except through `get_profile`, which calls those two clients.
"""

from __future__ import annotations

import asyncio
import math
from collections import defaultdict
from datetime import date

from . import modis, power

FROST_C = 0.0  # I-05
HEAT_C = 35.0  # I-06
HEAVY_RAIN_MM = 30.0  # I-07
BARE_NDVI = 0.25  # I-09
MAX_MISSING = 0.10  # skip a month-year when more than 10 % of its days are missing
BASELINE = (2005, 2014)  # I-10, I-11
RECENT = (2016, 2025)

GSC = 0.0820  # solar constant, MJ m-2 min-1 (FAO-56)
MJ_TO_MM = 0.408  # MJ m-2 day-1 -> mm day-1 equivalent evaporation (FAO-56)


def extraterrestrial_radiation_mm(lat: float, doy: int) -> float:
    """Ra in mm/day for a latitude (deg) and day of year (FAO-56 eq. 21-25). Used by I-02."""
    phi = math.radians(lat)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    delta = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    ra_mj = (24 * 60 / math.pi) * GSC * dr * (
        ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws)
    )
    return MJ_TO_MM * ra_mj


def hargreaves_et0(tmax: float, tmin: float, ra_mm: float) -> float:
    """Daily ET0 in mm, FAO-56 Hargreaves (eq. 52). I-02."""
    tmean = (tmax + tmin) / 2
    return 0.0023 * (tmean + 17.8) * math.sqrt(max(tmax - tmin, 0.0)) * ra_mm


def _group_days(days: dict) -> dict[tuple[int, int], list[tuple[date, dict]]]:
    groups: dict[tuple[int, int], list[tuple[date, dict]]] = defaultdict(list)
    for key, values in days.items():
        d = date(int(key[:4]), int(key[4:6]), int(key[6:8]))
        groups[(d.year, d.month)].append((d, values))
    return groups


def _ok(n_valid: int, n_days: int) -> bool:
    return n_days > 0 and (n_days - n_valid) / n_days <= MAX_MISSING


def month_year_stats(days: dict, lat: float) -> dict[tuple[int, int], dict]:
    """Per (year, month): rain, ET0, soil wetness and day counts. None where data are too incomplete."""
    stats = {}
    for (year, month), items in _group_days(days).items():
        n = len(items)
        rain = [v["PRECTOTCORR"] for _, v in items if v.get("PRECTOTCORR") is not None]
        tmin = [v["T2M_MIN"] for _, v in items if v.get("T2M_MIN") is not None]
        tmax = [v["T2M_MAX"] for _, v in items if v.get("T2M_MAX") is not None]
        gwet = [v["GWETROOT"] for _, v in items if v.get("GWETROOT") is not None]
        et0 = [
            hargreaves_et0(v["T2M_MAX"], v["T2M_MIN"], extraterrestrial_radiation_mm(lat, d.timetuple().tm_yday))
            for d, v in items
            if v.get("T2M_MAX") is not None and v.get("T2M_MIN") is not None
        ]
        # Sums and counts are rescaled to the full month so a few missing days do not bias them low.
        stats[(year, month)] = {
            "rain_mm": sum(rain) * n / len(rain) if _ok(len(rain), n) else None,
            "et0_mm": sum(et0) * n / len(et0) if _ok(len(et0), n) else None,
            "soil_wetness": sum(gwet) / len(gwet) if _ok(len(gwet), n) else None,
            "frost_days": sum(t < FROST_C for t in tmin) * n / len(tmin) if _ok(len(tmin), n) else None,
            "heat_days": sum(t > HEAT_C for t in tmax) * n / len(tmax) if _ok(len(tmax), n) else None,
            "heavy_rain_days": sum(r >= HEAVY_RAIN_MM for r in rain) * n / len(rain) if _ok(len(rain), n) else None,
            "missing_days": n - min(len(rain), len(tmin), len(tmax), len(gwet)),
        }
    return stats


def _mean(values: list) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def monthly_climate(stats: dict) -> list[dict]:
    """12 calendar months, each the mean over all years (I-01..I-07)."""
    fields = ["rain_mm", "et0_mm", "soil_wetness", "frost_days", "heat_days", "heavy_rain_days"]
    months = []
    for m in range(1, 13):
        rows = [s for (_, month), s in stats.items() if month == m]
        row = {"month": m, **{f: _mean([r[f] for r in rows]) for f in fields}}
        row["water_balance_mm"] = (
            row["rain_mm"] - row["et0_mm"] if row["rain_mm"] is not None and row["et0_mm"] is not None else None
        )
        months.append(row)
    return months


def monthly_ndvi(points: list[dict]) -> dict[int, float]:
    """I-08: mean NDVI of the MODIS composites starting in each calendar month."""
    by_month: dict[int, list[float]] = defaultdict(list)
    for p in points:
        by_month[int(p["date"][5:7])].append(p["ndvi"])
    return {m: sum(v) / len(v) for m, v in by_month.items()}


def likely_bare(ndvi: float | None) -> bool | None:
    """I-09: field probably bare (soil, stubble or fallow) when NDVI is below BARE_NDVI."""
    return None if ndvi is None else ndvi < BARE_NDVI


def _annual(stats: dict, field: str, years: tuple[int, int]) -> float | None:
    totals = []
    for y in range(years[0], years[1] + 1):
        values = [stats.get((y, m), {}).get(field) for m in range(1, 13)]
        if all(v is not None for v in values):
            totals.append(sum(values))
    return _mean(totals)


def trends(stats: dict) -> dict:
    """I-10 and I-11: recent decade vs baseline decade (complete years only)."""
    rain_old, rain_new = _annual(stats, "rain_mm", BASELINE), _annual(stats, "rain_mm", RECENT)
    heat_old, heat_new = _annual(stats, "heat_days", BASELINE), _annual(stats, "heat_days", RECENT)
    return {
        "rain_change_pct": round(100 * (rain_new - rain_old) / rain_old, 1) if rain_old and rain_new is not None else None,
        "heat_days_change": round(heat_new - heat_old, 1) if heat_old is not None and heat_new is not None else None,
        "baseline": f"{BASELINE[0]}-{BASELINE[1]}",
        "recent": f"{RECENT[0]}-{RECENT[1]}",
    }


def _round(value: float | None, digits: int) -> float | None:
    return None if value is None else round(value, digits)


def build_profile(lat: float, lon: float, power_data: dict, modis_data: dict | None) -> dict:
    """Shape 1 climate profile from the raw POWER and MODIS payloads."""
    stats = month_year_stats(power_data["days"], lat)
    ndvi = monthly_ndvi(modis_data["points"]) if modis_data else {}
    months = []
    for row in monthly_climate(stats):
        m = row["month"]
        months.append({
            "month": m,
            "rain_mm": _round(row["rain_mm"], 1),
            "et0_mm": _round(row["et0_mm"], 1),
            "water_balance_mm": _round(row["water_balance_mm"], 1),
            "soil_wetness": _round(row["soil_wetness"], 2),
            "frost_days": _round(row["frost_days"], 1),
            "heat_days": _round(row["heat_days"], 1),
            "heavy_rain_days": _round(row["heavy_rain_days"], 1),
            "ndvi": _round(ndvi.get(m), 2),
            "likely_bare": likely_bare(ndvi.get(m)),
        })
    sources = [f"NASA POWER {power_data['meta'].get('period', '')} (MERRA-2, ~50 km grid)".replace("  ", " ")]
    if modis_data:
        sources.append(f"MODIS MOD13Q1 {modis_data['meta'].get('period', '')} (NDVI, 250 m)")
    return {
        "location": {"lat": round(lat, 2), "lon": round(lon, 2), "elevation_m": power_data["meta"].get("elevation_m")},
        "months": months,
        "trends": trends(stats),
        "sources": sources,
        "quality": {
            "missing_days": sum(s["missing_days"] for s in stats.values()),
            "skipped_month_years": sum(any(v is None for v in s.values()) for s in stats.values()),
        },
    }


async def get_profile(lat: float, lon: float) -> dict:
    """Fetch POWER and MODIS in parallel and build the Shape 1 profile. NDVI is optional if MODIS fails."""
    power_data, modis_data = await asyncio.gather(
        power.fetch_daily(lat, lon), modis.fetch_ndvi(lat, lon), return_exceptions=True
    )
    if isinstance(power_data, BaseException):
        raise power_data
    if isinstance(modis_data, BaseException):
        modis_data = None
    return build_profile(lat, lon, power_data, modis_data)
