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

# Plain-language uncertainty statements for the UI, English and Spanish
# (docs/indicators.md -> Limits to show in the UI).
LIMITS = {
    "en": [
        "Climate values are NASA satellite and model estimates for an area of about 50 km, not measurements on your plot.",
        "Soil wetness is a model estimate, not a measurement.",
        "Field greenness (NDVI) covers only 2024-2025 and a 250 m square that may include other plots.",
        "Comparing two 10-year periods shows a change, not a proven long-term climate trend.",
        "Frost, heat, heavy-rain and bare-field thresholds are general rules, not specific to your crop.",
    ],
    "es": [
        "Los datos de clima son estimaciones de satélite y modelos de NASA para una zona de unos 50 km, "
        "no medidas en tu parcela.",
        "La humedad del suelo es una estimación de un modelo, no una medida.",
        "El verdor de la parcela (NDVI) solo cubre 2024-2025 y un cuadrado de 250 m que puede incluir otras parcelas.",
        "Comparar dos periodos de 10 años muestra un cambio, no una tendencia climática demostrada.",
        "Los umbrales de helada, calor, lluvia fuerte y suelo desnudo son reglas generales, no propias de tu cultivo.",
    ],
}

# One short limits sentence per indicator (#44), keyed by the profile field. Shown next to each value in the UI.
FIELD_LIMITS = {
    "rain_mm": {  # I-01
        "en": "Average for 2005-2025 over an area of about 50 km; a single year can be much wetter or drier.",
        "es": "Media de 2005-2025 para una zona de unos 50 km; un año concreto puede ser mucho más húmedo o seco.",
    },
    "et0_mm": {  # I-02
        "en": "Estimated from NASA sunshine, humidity and wind for the area; local wind or sea breeze can change it.",
        "es": "Estimado con datos de NASA de sol, humedad y viento de la zona; el viento local o la brisa del mar "
              "pueden cambiarlo.",
    },
    "water_balance_mm": {  # I-03
        "en": "Rain minus the water the air asks for; irrigation, runoff and water stored in your soil are not counted.",
        "es": "Lluvia menos el agua que pide el aire; no cuenta el riego, la escorrentía ni el agua guardada en tu suelo.",
    },
    "soil_wetness": {  # I-04
        "en": "Model estimate for the area, not a measurement; use it to compare months, not to decide when to irrigate.",
        "es": "Estimación de un modelo para la zona, no una medida; sirve para comparar meses, no para decidir cuándo regar.",
    },
    "frost_days": {  # I-05
        "en": "Days below 0 °C for the area; valley bottoms and hollows can get more frost than shown.",
        "es": "Días bajo 0 °C en la zona; los fondos de valle y las hondonadas pueden tener más heladas.",
    },
    "heat_days": {  # I-06
        "en": "Days above 35 °C; some crops suffer at lower temperatures when they flower, so heat stress can be higher.",
        "es": "Días por encima de 35 °C; algunos cultivos sufren con menos calor en la floración, así que el estrés "
              "puede ser mayor.",
    },
    "heavy_rain_days": {  # I-07
        "en": "Days with 30 mm or more for the area; a local storm can be stronger than the area average.",
        "es": "Días con 30 mm o más en la zona; una tormenta local puede ser más fuerte que la media de la zona.",
    },
    "ndvi": {  # I-08
        "en": "Satellite greenness for 2024-2025 only, from a 250 m square that may include other plots.",
        "es": "Verdor visto por satélite solo en 2024-2025, en un cuadrado de 250 m que puede incluir otras parcelas.",
    },
    "likely_bare": {  # I-09
        "en": "A guess from greenness; stubble, dry grass or a mixed square can be counted wrongly.",
        "es": "Una estimación a partir del verdor; el rastrojo, la hierba seca o un cuadrado mixto pueden confundirla.",
    },
    "rain_change_pct": {  # I-10
        "en": "Compares 2016-2025 with 2005-2014; ten years is short, so this is a change, not a proven trend.",
        "es": "Compara 2016-2025 con 2005-2014; diez años es poco, así que es un cambio, no una tendencia demostrada.",
    },
    "heat_days_change": {  # I-11
        "en": "Compares 2016-2025 with 2005-2014; ten years is short, so this is a change, not a proven trend.",
        "es": "Compara 2016-2025 con 2005-2014; diez años es poco, así que es un cambio, no una tendencia demostrada.",
    },
}

GSC = 0.0820  # solar constant, MJ m-2 min-1 (FAO-56)
MJ_TO_MM = 0.408  # MJ m-2 day-1 -> mm day-1 equivalent evaporation (FAO-56)
SIGMA = 4.903e-9  # Stefan-Boltzmann constant, MJ K-4 m-2 day-1
PM_PARAMS = ("T2M_MAX", "T2M_MIN", "ALLSKY_SFC_SW_DWN", "T2MDEW", "WS2M")


def extraterrestrial_radiation_mj(lat: float, doy: int) -> float:
    """Ra in MJ m-2 day-1 for a latitude (deg) and day of year (FAO-56 eq. 21-25). Used by I-02."""
    phi = math.radians(lat)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    delta = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    return (24 * 60 / math.pi) * GSC * dr * (
        ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws)
    )


def extraterrestrial_radiation_mm(lat: float, doy: int) -> float:
    """Ra in mm/day equivalent evaporation."""
    return MJ_TO_MM * extraterrestrial_radiation_mj(lat, doy)


def sat_vapour_pressure(t: float) -> float:
    """e°(T) in kPa (FAO-56 eq. 11)."""
    return 0.6108 * math.exp(17.27 * t / (t + 237.3))


def penman_monteith_et0(tmax: float, tmin: float, rs: float, ea: float, u2: float, elevation_m: float,
                        ra_mj: float) -> float:
    """Daily grass-reference ET0 in mm, FAO-56 Penman-Monteith (eq. 6) with G = 0. I-02.

    rs: incoming shortwave radiation (MJ m-2 day-1), ea: actual vapour pressure (kPa), u2: wind at 2 m (m/s).
    """
    tmean = (tmax + tmin) / 2
    pressure = 101.3 * ((293 - 0.0065 * elevation_m) / 293) ** 5.26  # eq. 7
    gamma = 0.000665 * pressure  # eq. 8
    es = (sat_vapour_pressure(tmax) + sat_vapour_pressure(tmin)) / 2  # eq. 12
    slope = 4098 * sat_vapour_pressure(tmean) / (tmean + 237.3) ** 2  # eq. 13
    rso = (0.75 + 2e-5 * elevation_m) * ra_mj  # eq. 37
    rns = 0.77 * rs  # eq. 38, albedo 0.23
    rnl = (SIGMA * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * math.sqrt(max(ea, 0.0)))
           * (1.35 * min(rs / rso, 1.0) - 0.35)) if rso > 0 else 0.0  # eq. 39
    rn = rns - rnl
    et0 = (0.408 * slope * rn + gamma * 900 / (tmean + 273) * u2 * (es - ea)) / (slope + gamma * (1 + 0.34 * u2))
    return max(et0, 0.0)


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


def daily_et0(values: dict, lat: float, doy: int, elevation_m: float) -> tuple[float | None, str | None]:
    """ET0 for one day: Penman-Monteith when POWER radiation, dew point and wind exist, else Hargreaves."""
    if values.get("T2M_MAX") is None or values.get("T2M_MIN") is None:
        return None, None
    ra = extraterrestrial_radiation_mj(lat, doy)
    if all(values.get(k) is not None for k in PM_PARAMS):
        ea = sat_vapour_pressure(values["T2MDEW"])  # eq. 14
        return penman_monteith_et0(values["T2M_MAX"], values["T2M_MIN"], values["ALLSKY_SFC_SW_DWN"], ea,
                                   values["WS2M"], elevation_m, ra), "penman_monteith"
    return hargreaves_et0(values["T2M_MAX"], values["T2M_MIN"], MJ_TO_MM * ra), "hargreaves"


def month_year_stats(days: dict, lat: float, elevation_m: float = 0.0) -> dict[tuple[int, int], dict]:
    """Per (year, month): rain, ET0, soil wetness and day counts. None where data are too incomplete."""
    stats = {}
    for (year, month), items in _group_days(days).items():
        n = len(items)
        rain = [v["PRECTOTCORR"] for _, v in items if v.get("PRECTOTCORR") is not None]
        tmin = [v["T2M_MIN"] for _, v in items if v.get("T2M_MIN") is not None]
        tmax = [v["T2M_MAX"] for _, v in items if v.get("T2M_MAX") is not None]
        gwet = [v["GWETROOT"] for _, v in items if v.get("GWETROOT") is not None]
        daily = [daily_et0(v, lat, d.timetuple().tm_yday, elevation_m) for d, v in items]
        et0 = [e for e, _ in daily if e is not None]
        # Sums and counts are rescaled to the full month so a few missing days do not bias them low.
        stats[(year, month)] = {
            "rain_mm": sum(rain) * n / len(rain) if _ok(len(rain), n) else None,
            "et0_mm": sum(et0) * n / len(et0) if _ok(len(et0), n) else None,
            "soil_wetness": sum(gwet) / len(gwet) if _ok(len(gwet), n) else None,
            "frost_days": sum(t < FROST_C for t in tmin) * n / len(tmin) if _ok(len(tmin), n) else None,
            "heat_days": sum(t > HEAT_C for t in tmax) * n / len(tmax) if _ok(len(tmax), n) else None,
            "heavy_rain_days": sum(r >= HEAVY_RAIN_MM for r in rain) * n / len(rain) if _ok(len(rain), n) else None,
            "missing_days": n - min(len(rain), len(tmin), len(tmax), len(gwet)),
            "hargreaves_days": sum(m == "hargreaves" for _, m in daily),
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
    elevation = power_data["meta"].get("elevation_m") or 0.0
    stats = month_year_stats(power_data["days"], lat, elevation)
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
        "limits": LIMITS,
        "field_limits": FIELD_LIMITS,
        "quality": {
            "missing_days": sum(s["missing_days"] for s in stats.values()),
            "skipped_month_years": sum(any(v is None for v in s.values()) for s in stats.values()),
            "et0_method": "FAO-56 Penman-Monteith (Hargreaves on {} days without radiation/humidity/wind)".format(
                sum(s["hargreaves_days"] for s in stats.values())),
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
