"""Statistical predictions from NASA historical data (docs/indicators.md P-01..P-07). No AI/ML.

Every function is a pure function over the daily NASA POWER payload returned by power.fetch_daily
({"meta": {...}, "days": {"YYYYMMDD": {param: value}}}). Results describe what happened in the
last ~20 years at the field's POWER cell and must be shown as "based on the last 20 years of
NASA data", never as a weather forecast.

Implemented: P-01 weekly rain probability, P-02 heavy rain (monthly probability + Gumbel return
levels), P-03 frost dates, P-07 bare-soil x heavy-rain alerts. Stretch P-04..P-06 not implemented.
"""

from __future__ import annotations

import calendar
import math
from collections import defaultdict
from datetime import date, timedelta

WET_DAY_MM = 1.0  # P-01: a day with >= 1 mm counts as rainy (ETCCDI wet-day threshold)
USEFUL_WEEK_MM = 10.0  # P-01: a week with >= 10 mm of rain in total
FROST_C = 0.0  # P-03: same frost rule as climate.FROST_C (I-05)
MAX_MISSING = 0.10  # skip a week / half-year when more than 10 % of its days are missing
WEEKS = 52  # 52 weeks of 7 days; the last 1-2 days of the year are added to week 52
REF_YEAR = 2001  # non-leap year used to turn day-of-year into a calendar date (MM-DD)
HEAVY_DAY_MM = 20.0  # P-02/P-07: ETCCDI R20mm "very heavy precipitation day" (cell-averaged rain)
RETURN_PERIODS = (2, 5, 10)  # P-02: only up to 10 years with ~21 annual maxima (agro review)
EULER_GAMMA = 0.5772156649
ALERT_PROB = 0.2  # P-07: a >= 20 mm day in that month in at least 1 year in 5
HIGH_PROB = 0.4  # P-07: ... in at least 2 years in 5 -> "high"
LEVELS = ("medium", "high")

# One short limits sentence per prediction (#44), keyed like the build_predictions output. Shown on each card.
PREDICTION_LIMITS = {
    "rain_weeks": {  # P-01
        "en": "Share of the past 21 years (2005-2025) with rain in that week; it does not forecast this year's weather.",
        "es": "Parte de los 21 años pasados (2005-2025) con lluvia esa semana; no predice el tiempo de este año.",
    },
    "heavy_rain": {  # P-02
        "en": "Rain averaged over an area of about 50 km and only 21 years of data: local storms can be stronger, "
              "and storms rarer than once in 10 years are not estimated.",
        "es": "Lluvia media de una zona de unos 50 km y solo 21 años de datos: las tormentas locales pueden ser más "
              "fuertes, y no se estiman las que llegan menos de una vez cada 10 años.",
    },
    "frost": {  # P-03
        "en": "Air temperature for the area; ground frost and cold valley bottoms can freeze later in spring "
              "and harder than shown.",
        "es": "Temperatura del aire de la zona; la helada en el suelo y los fondos de valle fríos pueden helar más "
              "tarde en primavera y más fuerte de lo que se ve.",
    },
    "alerts": {  # P-07
        "en": "Heavy-rain days often fall when the field is bare; this is a warning sign, not measured soil loss, "
              "and your field may be covered differently this year.",
        "es": "Los días de lluvia fuerte suelen caer con la parcela desnuda; es una señal de aviso, no una medida "
              "de pérdida de suelo, y este año tu parcela puede estar cubierta de otra forma.",
    },
}


def _parse(days: dict) -> dict[int, dict[date, dict]]:
    """{year: {date: values}} from the POWER 'days' mapping."""
    by_year: dict[int, dict[date, dict]] = defaultdict(dict)
    for key, values in days.items():
        d = date(int(key[:4]), int(key[4:6]), int(key[6:8]))
        by_year[d.year][d] = values
    return by_year


def week_of_year(d: date) -> int:
    """1..52. Week 1 = 1-7 January; days 365-366 belong to week 52."""
    return min((d.timetuple().tm_yday - 1) // 7 + 1, WEEKS)


def week_start(week: int) -> str:
    """Calendar start of a week as 'MM-DD' (reference non-leap year)."""
    return (date(REF_YEAR, 1, 1) + timedelta(days=7 * (week - 1))).strftime("%m-%d")


def _doy_to_mmdd(doy: float) -> str:
    """Day of year (1..365, may be fractional) -> 'MM-DD' in a non-leap year."""
    return (date(REF_YEAR, 1, 1) + timedelta(days=round(doy) - 1)).strftime("%m-%d")


def _doy(d: date) -> int:
    """Day of year on a non-leap calendar, so 1 March is always day 60."""
    return date(REF_YEAR, d.month, min(d.day, 28) if d.month == 2 else d.day).timetuple().tm_yday


def rank_value(values: list[int], q: float, upper: bool) -> int | None:
    """Nearest-rank percentile (q in 0..100) that always returns an observed value.

    No interpolation, so a real frost date is never blended with the 0 / 366 "no frost" markers
    into a date that never happened. `upper=True` rounds the rank up (later date: the safe side
    for the last spring frost); `upper=False` rounds it down (earlier date: safe side for the
    first autumn frost).
    """
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * q / 100
    return s[math.ceil(k)] if upper else s[math.floor(k)]


# ------------------------------------------------------------------ P-01 weekly rain probability

def rain_weeks(days: dict) -> list[dict]:
    """P-01. For each of the 52 weeks of the year, over all years with enough data:

    - prob_rain: share of years with at least one day >= WET_DAY_MM in that week
    - prob_useful_rain: share of years with a weekly total >= USEFUL_WEEK_MM
    - mean_rain_mm: mean weekly total
    - years: number of years used
    A week-year is skipped when more than 10 % of its days are missing (i.e. any day of a 7-day week);
    days absent from the payload count as missing.
    """
    per_week: dict[int, list[tuple[bool, bool, float]]] = defaultdict(list)
    for year, items in _parse(days).items():
        groups: dict[int, list[float]] = defaultdict(list)
        for d, values in items.items():
            if values.get("PRECTOTCORR") is not None:
                groups[week_of_year(d)].append(values["PRECTOTCORR"])
        for week in range(1, WEEKS + 1):
            valid = groups.get(week, [])
            expected = 7 if week < WEEKS else (366 if calendar.isleap(year) else 365) - 7 * (WEEKS - 1)
            if not valid or (expected - len(valid)) / expected > MAX_MISSING:
                continue
            total = sum(valid) * expected / len(valid)
            per_week[week].append((any(r >= WET_DAY_MM for r in valid), total >= USEFUL_WEEK_MM, total))
    out = []
    for week in range(1, WEEKS + 1):
        rows = per_week.get(week, [])
        n = len(rows)
        out.append({
            "week": week,
            "start": week_start(week),
            "prob_rain": round(sum(r[0] for r in rows) / n, 2) if n else None,
            "prob_useful_rain": round(sum(r[1] for r in rows) / n, 2) if n else None,
            "mean_rain_mm": round(sum(r[2] for r in rows) / n, 1) if n else None,
            "years": n,
        })
    return out


# ------------------------------------------------------------------ P-03 frost dates

def _half_ok(year: int, items: dict[date, dict], months: range) -> bool:
    """True when at most 10 % of the days of those months have no Tmin."""
    expected = sum(calendar.monthrange(year, m)[1] for m in months)
    valid = sum(1 for d, v in items.items() if d.month in months and v.get("T2M_MIN") is not None)
    return (expected - valid) / expected <= MAX_MISSING


def frost_dates(days: dict) -> dict:
    """P-03. Last spring frost (Jan-Jun) and first autumn frost (Jul-Dec), Tmin < FROST_C.

    Years without a frost in a half count as "no frost" (earliest possible for spring, latest for
    autumn), so percentiles stay meaningful when frost is rare. Percentiles are nearest-rank
    observed dates, rounded to the safe side (see rank_value). Returns:
    - spring: probability of any frost, median and ~90th-percentile date of the last frost, and
      `years_by_p90` = how many years had their last frost on or before that date
    - autumn ("first frost before 31 Dec"): probability, median and ~10th-percentile date of the
      first frost, and `years_from_p10` = how many years had their first frost on or after it
    - safe_days: days between the spring and autumn dates above
    Dates are 'MM-DD'; None when no year had frost. Air Tmin at 2 m for a ~50 km cell: ground
    frost and frost in valley bottoms can be later and harder than shown.
    """
    spring_doys, autumn_doys = [], []
    spring_with = autumn_with = 0
    for year, items in _parse(days).items():
        frosts = sorted(d for d, v in items.items() if v.get("T2M_MIN") is not None and v["T2M_MIN"] < FROST_C)
        if _half_ok(year, items, range(1, 7)):
            spring = [d for d in frosts if d.month <= 6]
            spring_doys.append(_doy(spring[-1]) if spring else 0)
            spring_with += bool(spring)
        if _half_ok(year, items, range(7, 13)):
            autumn = [d for d in frosts if d.month >= 7]
            autumn_doys.append(_doy(autumn[0]) if autumn else 366)
            autumn_with += bool(autumn)

    def _date(doy: int | None, none_value: int) -> str | None:
        return None if doy is None or doy == none_value else _doy_to_mmdd(doy)

    last_p50, last_p90 = rank_value(spring_doys, 50, upper=True), rank_value(spring_doys, 90, upper=True)
    first_p50, first_p10 = rank_value(autumn_doys, 50, upper=False), rank_value(autumn_doys, 10, upper=False)
    safe = None
    if last_p90 is not None and first_p10 is not None:
        safe = min(first_p10, 365) - max(last_p90, 0)
    return {
        "spring": {
            "years": len(spring_doys),
            "years_with_frost": spring_with,
            "probability": round(spring_with / len(spring_doys), 2) if spring_doys else None,
            "last_frost_median": _date(last_p50, 0),
            "last_frost_p90": _date(last_p90, 0),
            # "In N of the last Y years the last frost came on or before last_frost_p90" (UI counts, not %)
            "years_by_p90": sum(d <= last_p90 for d in spring_doys) if last_p90 is not None else None,
        },
        "autumn": {
            "years": len(autumn_doys),
            "years_with_frost": autumn_with,
            "probability": round(autumn_with / len(autumn_doys), 2) if autumn_doys else None,
            "first_frost_median": _date(first_p50, 366),
            "first_frost_p10": _date(first_p10, 366),
            # "In N of the last Y years the first frost came on or after first_frost_p10"
            "years_from_p10": sum(d >= first_p10 for d in autumn_doys) if first_p10 is not None else None,
        },
        "safe_days": safe,
    }


# ------------------------------------------------------------------ P-02 heavy rain

def gumbel_lmoments(sample: list[float]) -> tuple[float, float] | None:
    """Gumbel (EV1) location xi and scale alpha fitted by L-moments (Hosking & Wallis 1997).

    l1 = b0, l2 = 2*b1 - b0 with b1 = mean((i-1)/(n-1) * x_(i)) over the sorted sample;
    alpha = l2 / ln 2, xi = l1 - 0.5772 * alpha. Needs at least 5 values.
    """
    n = len(sample)
    if n < 5:
        return None
    x = sorted(sample)
    b0 = sum(x) / n
    b1 = sum(i / (n - 1) * v for i, v in enumerate(x)) / n
    l2 = 2 * b1 - b0
    if l2 <= 0:
        return None
    alpha = l2 / math.log(2)
    return b0 - EULER_GAMMA * alpha, alpha


def gumbel_return_level(xi: float, alpha: float, years: float) -> float:
    """Value exceeded on average once every `years` years: xi - alpha * ln(-ln(1 - 1/T))."""
    return xi - alpha * math.log(-math.log(1 - 1 / years))


def heavy_rain(days: dict) -> dict:
    """P-02. Heavy-rain risk from daily NASA POWER rain (cell average, ~50 km).

    - months[m]: share of years with at least one day >= HEAVY_DAY_MM in that calendar month
      (a month-year with > 10 % missing rain is skipped), plus the count of years
    - return_levels: daily rain reached on average once every 2, 5, 10 years (Gumbel, L-moments
      on the annual maxima of years with <= 10 % missing days); `observed_years` = how many years
      actually reached it (a quick check of the fit)
    - annual_max: median and largest yearly maximum, and the year of the largest
    """
    by_month: dict[int, list[bool]] = defaultdict(list)
    maxima: dict[int, float] = {}
    for year, items in _parse(days).items():
        rain_by_month: dict[int, list[float]] = defaultdict(list)
        for d, v in items.items():
            if v.get("PRECTOTCORR") is not None:
                rain_by_month[d.month].append(v["PRECTOTCORR"])
        for m in range(1, 13):
            expected = calendar.monthrange(year, m)[1]
            rain = rain_by_month.get(m, [])
            if rain and (expected - len(rain)) / expected <= MAX_MISSING:
                by_month[m].append(any(r >= HEAVY_DAY_MM for r in rain))
        n_valid = sum(len(r) for r in rain_by_month.values())
        if n_valid and ((366 if calendar.isleap(year) else 365) - n_valid) / 365 <= MAX_MISSING:
            maxima[year] = max(r for rs in rain_by_month.values() for r in rs)

    fit = gumbel_lmoments(list(maxima.values()))
    levels = []
    if fit:
        for t in RETURN_PERIODS:
            mm = gumbel_return_level(*fit, t)
            levels.append({"years": t, "mm": round(mm), "observed_years": sum(v >= mm for v in maxima.values())})
    wettest = max(maxima, key=maxima.get) if maxima else None
    return {
        "threshold_mm": HEAVY_DAY_MM,
        "months": [{"month": m, "prob": round(sum(by_month[m]) / len(by_month[m]), 2) if by_month[m] else None,
                    "years": len(by_month[m])} for m in range(1, 13)],
        "return_levels": levels,
        "annual_max": {
            "years": len(maxima),
            "median_mm": round(percentile_median(list(maxima.values())), 1) if maxima else None,
            "max_mm": round(maxima[wettest], 1) if wettest else None,
            "max_year": wettest,
        },
        "method": f"Gumbel fitted by L-moments on {len(maxima)} annual maxima of cell-averaged daily rain",
    }


def percentile_median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


# ------------------------------------------------------------------ P-07 bare soil x heavy rain

def bare_months(modis_points: list[dict]) -> dict[int, bool]:
    """I-08/I-09 reused: {month: likely bare} from the MODIS NDVI points (2024-2025)."""
    from .climate import likely_bare, monthly_ndvi  # local import: climate imports the network clients

    return {m: bool(likely_bare(v)) for m, v in monthly_ndvi(modis_points).items()}


def rotation_bare_months(rotation: list[dict]) -> set[int]:
    """Calendar months with no crop in at least one year of the rotation (crop calendar from
    data/crops.csv, same window() as the rotation engine). Fallow years leave every month bare."""
    from .rotations import window

    bare: set[int] = set()
    for crop in rotation:
        bare |= set(range(1, 13)) - set(window(crop))
    return bare


def soil_alerts(heavy: dict, observed_bare: dict[int, bool] | None = None,
                planned_bare: set[int] | None = None) -> list[dict]:
    """P-07. Months when the field is bare and a >= 20 mm day happened in at least ALERT_PROB of the
    years (P-02). Bare comes from two sources, reported in `sources`:
    - "satellite": MODIS NDVI says likely bare (2024-2025, I-09) — observed but only two years and a
      fixed NDVI threshold (stubble, weeds and early emergence can hide a bare seedbed);
    - "crop_calendar": no crop of the farmer's rotation occupies that month (planned).
    Level "high" from HIGH_PROB, else "medium"; before the farmer's slope (see raise_for_slope).
    Wording: heavy-rain days often fall when the field is bare — a proxy, not measured erosion."""
    observed_bare = observed_bare or {}
    planned_bare = planned_bare or set()
    alerts = []
    for row in heavy["months"]:
        m, prob = row["month"], row["prob"]
        sources = [name for name, hit in (("satellite", observed_bare.get(m)), ("crop_calendar", m in planned_bare))
                   if hit]
        if prob is not None and prob >= ALERT_PROB and sources:
            alerts.append({"month": m, "prob": prob, "years": row["years"], "sources": sources,
                           "level": "high" if prob >= HIGH_PROB else "medium"})
    return alerts


def raise_for_slope(level: str, slope: str) -> str:
    """P-07: a steep field raises an alert one level (medium -> high); other slopes keep it."""
    if slope == "steep" and level in LEVELS:
        return LEVELS[min(LEVELS.index(level) + 1, len(LEVELS) - 1)]
    return level


# ------------------------------------------------------------------ bundle

def build_predictions(power_data: dict, modis_data: dict | None = None,
                      rotation: list[dict] | None = None) -> dict:
    """Predictions payload for one field (shape documented in docs/work-plan.md).

    `modis_data` (MODIS payload) and `rotation` (crop dicts of the farmer's current rotation, from
    db.get_crops / rotations.load_crops) are both optional. With neither, `alerts` is None (bare
    months unknown), never an empty list.
    """
    days = power_data["days"]
    years = sorted({int(k[:4]) for k in days})
    heavy = heavy_rain(days)
    alerts = None
    if modis_data or rotation:
        alerts = soil_alerts(heavy,
                             bare_months(modis_data["points"]) if modis_data else None,
                             rotation_bare_months(rotation) if rotation else None)
    return {
        "period": f"{years[0]}-{years[-1]}" if years else None,
        "basis": "Statistics of NASA POWER daily data for the field's ~50 km cell. Not a weather forecast.",
        "rain_weeks": rain_weeks(days),
        "heavy_rain": heavy,
        "frost": frost_dates(days),
        "alerts": alerts,
        "limits": PREDICTION_LIMITS,
    }
