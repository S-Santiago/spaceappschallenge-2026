"""Rotation engine: Shape 1 climate profile + crop catalogue + farmer inputs -> Shape 2 strategies.

Scoring rules are documented in docs/indicators.md ("Scoring"). Every number used in the cards comes from
the climate profile (NASA) or from data/crops.csv (with its sources); nothing else is invented.
"""

from __future__ import annotations

import csv
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CROPS_CSV = ROOT / "data" / "crops.csv"

PRIORITIES = ("water", "soil", "income", "risk")
LEVEL = {"low": 0.0, "medium": 0.5, "high": 1.0}
MARKET = {"low": 20, "medium": 50, "high": 80}  # illustrative only
SLOPE_FACTOR = {"flat": 0.5, "moderate": 0.75, "steep": 1.0}
MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MIN_COVER_MONTHS = 3
SOURCE = "NASA POWER 2005-2025"
DISCLAIMER = "This tool supports, and does not replace, your judgment and local agricultural advice."

_INT = ("sow_month", "harvest_month")
_FLOAT = ("water_need_mm_min", "water_need_mm_max", "root_depth_m")


# ---------- crop catalogue ----------

def load_crops(path: Path = CROPS_CSV) -> dict[str, dict]:
    """Read data/crops.csv into {crop_id: traits}. Empty cells become None. Replaced by db.get_crops() (#6)."""
    crops = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            crop = {k: (v.strip() or None) if isinstance(v, str) else v for k, v in row.items()}
            for k in _INT:
                crop[k] = int(crop[k]) if crop.get(k) else None
            for k in _FLOAT:
                crop[k] = float(crop[k]) if crop.get(k) else None
            crops[crop["crop_id"]] = crop
    return crops


def is_fallow(crop: dict) -> bool:
    return crop.get("type") == "fallow" or crop.get("sow_month") is None


def window(crop: dict) -> list[int]:
    """Calendar months the crop occupies the field, sow to harvest inclusive (wraps over New Year)."""
    if is_fallow(crop):
        return []
    s, h = crop["sow_month"], crop["harvest_month"]
    return [(s - 1 + i) % 12 + 1 for i in range((h - s) % 12 + 1)]


def need_mm(crop: dict) -> float:
    lo, hi = crop.get("water_need_mm_min"), crop.get("water_need_mm_max")
    values = [v for v in (lo, hi) if v is not None]
    return sum(values) / len(values) if values else 0.0


# ---------- per-crop climate fit ----------

def _month(profile: dict, m: int) -> dict:
    return profile["months"][m - 1]


def season_sum(profile: dict, months: list[int], field: str) -> float:
    return sum(_month(profile, m).get(field) or 0 for m in months)


def rain_coverage(crop: dict, profile: dict) -> float:
    """Share of the crop's seasonal water need covered by rain in its growing months (0-1). Fallow = 1."""
    need = need_mm(crop)
    if is_fallow(crop) or need == 0:
        return 1.0
    return min(1.0, season_sum(profile, window(crop), "rain_mm") / need)


def climate_penalties(crop: dict, profile: dict, irrigated: bool) -> list[tuple[str, int]]:
    """(reason, penalty) pairs for frost, heat and drought in the crop's own season."""
    if is_fallow(crop):
        return []
    months = window(crop)
    frost, heat = season_sum(profile, months, "frost_days"), season_sum(profile, months, "heat_days")
    out = []
    for kind, days, tol in (("frost", frost, crop.get("frost_tolerance")), ("heat", heat, crop.get("heat_tolerance"))):
        if tol == "low" and days > 1:
            out.append((f"{kind}: {days:.1f} {kind} days in its season, low tolerance", 30))
        elif tol == "medium" and days > 5:
            out.append((f"{kind}: {days:.1f} {kind} days in its season, medium tolerance", 15))
    cov = rain_coverage(crop, profile)
    if not irrigated and cov < 0.5:
        p = {"low": 30, "medium": 15, "high": 5}.get(crop.get("drought_tolerance"), 15)
        out.append((f"drought: rain covers only {cov:.0%} of its water need, rain-fed", p))
    return out


def suitable(crop: dict, profile: dict, irrigated: bool) -> bool:
    """A crop can be proposed only if it is not heavily penalised by the local climate."""
    return sum(p for _, p in climate_penalties(crop, profile, irrigated)) < 30


# ---------- scoring (docs/indicators.md -> Scoring) ----------

def _bare_months(years: list[dict], cover: tuple[int, dict] | None) -> list[int]:
    """Calendar months with bare soil over the whole cycle (one entry per bare month per year).

    Over a full cycle the bare months are exactly the complement of each crop's window, year by year.
    """
    bare = Counter()
    for crop in years:
        bare.update(set(range(1, 13)) - set(window(crop)))
    if cover:
        bare.subtract(window(cover[1]))
    return sorted((+bare).elements())


def gap(years: list[dict], i: int) -> list[int]:
    """Bare months between the harvest of year i and the sowing of the next non-fallow crop (cyclic)."""
    if is_fallow(years[i]):
        return []
    n = len(years)
    nxt = next(years[(i + k) % n] for k in range(1, n + 1) if not is_fallow(years[(i + k) % n]))
    if any(is_fallow(years[(i + k) % n]) for k in range(1, n)):
        return list(range(1, 13))
    h, s = years[i]["harvest_month"], nxt["sow_month"]
    return [(h + k - 1) % 12 + 1 for k in range(1, (s - h - 1) % 12 + 1)] if s != h else []


def cover_fits(years: list[dict], i: int, cover: dict) -> bool:
    """A cover crop fits after year i when its whole window lies in that gap."""
    months = window(cover)
    return len(months) >= MIN_COVER_MONTHS and set(months) <= set(gap(years, i))


def score(years: list[dict], cover: tuple[int, dict] | None, profile: dict, irrigated: bool, slope: str) -> dict:
    n = len(years)
    cover_crop = cover[1] if cover else None

    # water: share of crop water need covered by rain; a cover crop counts as half a crop
    water_items = [(rain_coverage(c, profile), 1.0) for c in years]
    if cover_crop:
        water_items.append((rain_coverage(cover_crop, profile), 0.5))
    water = 100 * sum(v * w for v, w in water_items) / sum(w for _, w in water_items)

    # soil = nitrogen 25 + organic matter 25 + erosion 30 + pest break 20
    legume_main = any(c.get("n_fixing") == "yes" for c in years)
    legume_cover = bool(cover_crop and cover_crop.get("n_fixing") == "yes")
    nitrogen = 25 if legume_main else 15 if legume_cover else 0
    om = 25 * sum(LEVEL.get(c.get("residue_organic_matter"), 0) for c in years) / n
    if cover_crop:
        om = min(25, om + 5)
    bare = _bare_months(years, cover)
    weight_field = "heavy_rain_days" if season_sum(profile, list(range(1, 13)), "heavy_rain_days") > 0 else "rain_mm"
    total = season_sum(profile, list(range(1, 13)), weight_field) * n
    exposed = sum(_month(profile, m).get(weight_field) or 0 for m in bare) / total if total else len(bare) / (12 * n)
    erosion = 30 * (1 - min(1.0, exposed * SLOPE_FACTOR.get(slope, 0.5)))
    if n == 1:
        same = 1
    else:
        same = sum(years[i].get("family") == years[(i + 1) % n].get("family") and not is_fallow(years[i])
                   for i in range(n))
    pest = 20 * (1 - same / n)
    soil = nitrogen + om + erosion + pest

    # income (illustrative): mean market level; fallow earns nothing
    income = sum(0 if is_fallow(c) else MARKET.get(c.get("market_value_illustrative"), 0) for c in years) / n

    # risk: 100 minus climate penalties, averaged over the years (higher = lower risk)
    risk = sum(max(0, 100 - sum(p for _, p in climate_penalties(c, profile, irrigated))) for c in years) / n

    return {
        "water": round(water), "soil": round(soil), "income": round(income), "risk": round(risk),
        "_parts": {"nitrogen": nitrogen, "organic_matter": round(om), "erosion": round(erosion), "pest_break": round(pest),
                   "bare_months_per_year": round(len(bare) / n, 1)},
    }


def overall(scores: dict, priorities: dict) -> int:
    """Weighted mean of the four sub-scores; weights are the farmer's priorities (0-3, default 1 each)."""
    w = {k: max(0.0, float(priorities.get(k, 1))) for k in PRIORITIES}
    if sum(w.values()) == 0:
        w = dict.fromkeys(PRIORITIES, 1.0)
    return round(sum(scores[k] * w[k] for k in PRIORITIES) / sum(w.values()))


def label(value: int) -> str:
    """Words to show next to a score in the UI."""
    return "good" if value >= 67 else "neutral" if value >= 34 else "poor"


# ---------- candidate generation ----------

def _variants(current: list[str], pool: list[str], insert: bool) -> list[list[str]]:
    out = []
    for i, new in product(range(len(current)), pool):
        if current[i] != new:
            out.append(current[:i] + [new] + current[i + 1:])
    if insert and len(current) < 4:
        out += [current + [new] for new in pool]
    return out


def candidates(current: list[str], crops: dict, profile: dict, irrigated: bool) -> dict[str, list[dict]]:
    """Possible rotations per strategy kind: {kind: [{"years": [...], "cover": (index, crop_id) | None}]}."""
    ok = {cid: c for cid, c in crops.items()
          if not is_fallow(c) and c.get("type") != "cover" and suitable(c, profile, irrigated)}
    families = {crops[c].get("family") for c in current}
    legumes = [cid for cid, c in ok.items() if c.get("n_fixing") == "yes"]
    forage = [cid for cid, c in ok.items()
              if (c.get("type") == "forage" or c.get("forage_value") == "high") and c.get("family") not in families]
    thirstiest = max(range(len(current)), key=lambda i: need_mm(crops[current[i]]))
    savers = [cid for cid, c in ok.items()
              if c.get("drought_tolerance") == "high" and need_mm(c) < need_mm(crops[current[thirstiest]])]
    covers = [cid for cid, c in crops.items() if c.get("type") == "cover" and suitable(c, profile, irrigated)]
    years = [crops[c] for c in current]

    out = {
        "legume_break": [{"years": y, "cover": None} for y in _variants(current, legumes, insert=True)],
        "forage_diversification": [{"years": y, "cover": None} for y in _variants(current, forage, insert=True)],
        "water_saving": [{"years": current[:thirstiest] + [s] + current[thirstiest + 1:], "cover": None}
                         for s in savers],
        "cover_crop": [{"years": list(current), "cover": (i, cov)}
                       for i, cov in product(range(len(current)), covers)
                       if cover_fits(years, i, crops[cov])],
    }
    return out


# ---------- explanations ----------

def _name(crops: dict, cid: str) -> str:
    return crops[cid].get("name") or cid


def _span(months: list[int]) -> str:
    return f"{MONTH[months[0] - 1]}-{MONTH[months[-1] - 1]}" if months else "-"


def _crop_evidence(crop: dict, profile: dict) -> list[str]:
    if is_fallow(crop):
        return []
    months = window(crop)
    rain = season_sum(profile, months, "rain_mm")
    lo, hi = crop.get("water_need_mm_min"), crop.get("water_need_mm_max")
    need = f"{lo:.0f}-{hi:.0f} mm" if lo is not None and hi is not None else "unknown"
    src = crop.get("sources") or "no source"
    return [
        f"{crop.get('name')}: rain {_span(months)} averages {rain:.0f} mm ({SOURCE}, I-01) vs a water need of "
        f"{need} [{src}, confidence {crop.get('confidence') or 'unknown'}]",
    ]


def _climate_risks(years: list[dict], profile: dict, irrigated: bool) -> list[str]:
    risks = []
    for c in years:
        for reason, _ in climate_penalties(c, profile, irrigated):
            risks.append(f"{c.get('name')} - {reason} ({SOURCE}). Check with local experience.")
    return risks


def explain(kind: str, years: list[str], cover: tuple[int, str] | None, current: list[str], crops: dict,
            profile: dict, irrigated: bool, scores: dict, baseline: dict | None) -> dict:
    yc = [crops[c] for c in years]
    new = [c for c in years if c not in current]
    new_names = ", ".join(_name(crops, c) for c in dict.fromkeys(new))
    parts = scores["_parts"]
    evidence = [e for c in dict.fromkeys(years) for e in _crop_evidence(crops[c], profile)]
    trend = profile.get("trends", {})
    if trend.get("rain_change_pct") is not None:
        evidence.append(f"Rain 2016-2025 vs 2005-2014: {trend['rain_change_pct']:+.0f}% ({SOURCE}, I-10)")
    benefits, gaps = [], [
        "Local prices and costs: the income score is illustrative only",
        "Soil test (texture, organic matter, pH, nitrogen) for this field",
    ]
    risks = _climate_risks(yc, profile, irrigated)
    if not irrigated:
        gaps.append("Stored soil water at sowing (NASA soil wetness is a ~50 km model estimate, I-04)")

    if kind == "current":
        why = "Your current rotation, shown as the baseline to compare against."
        if parts["pest_break"] < 20:
            risks.append("Same crop family in consecutive years: pests and diseases can build up")
    elif kind == "legume_break":
        why = f"Adds {new_names}, a legume that takes nitrogen from the air and breaks the cereal/pest cycle."
        benefits += ["Less nitrogen fertiliser needed for the next crop", "Breaks pest and disease cycles"]
        gaps.append(f"Market or on-farm use for {new_names}")
        risks.append(f"Weed control and harvest machinery for {new_names}")
    elif kind == "forage_diversification":
        why = f"Adds {new_names}, a forage crop from a different family, to diversify income and the rotation."
        benefits += ["New crop family breaks pest cycles", "Forage for own livestock or local sale"]
        gaps.append(f"Is there a local buyer or livestock for {new_names}?")
        risks.append("Haymaking/silage machinery and labour")
    elif kind == "water_saving":
        old = [c for c in current if c not in years]
        why = (f"Swaps {', '.join(_name(crops, c) for c in old)} for {new_names}, which needs less water "
               f"and tolerates drought better.")
        benefits += ["Lower water need per season", "Less exposed to dry years"]
        gaps.append(f"Yield of {new_names} in this area in dry years")
    elif kind == "cover_crop":
        i, cid = cover
        cov = crops[cid]
        months = window(cov)
        why = (f"Keeps the same main crops but sows {_name(crops, cid)} as a cover crop after "
               f"{_name(crops, years[i])}, in months when the field is otherwise bare.")
        benefits += ["Protects bare soil from erosion", "Adds organic matter"]
        if cov.get("n_fixing") == "yes":
            benefits.append("Fixes nitrogen for the next crop")
        bare_ndvi = [m["month"] for m in profile["months"] if m.get("likely_bare")]
        if bare_ndvi:
            evidence.append(f"Satellite greenness suggests a bare field in {', '.join(MONTH[m - 1] for m in bare_ndvi)} "
                            f"(MODIS NDVI 2024-2025, I-09)")
        heavy = season_sum(profile, months, "heavy_rain_days")
        evidence.append(f"Cover crop period {_span(months)}: {heavy:.1f} heavy-rain days per year ({SOURCE}, I-07)")
        evidence += _crop_evidence(cov, profile)
        gaps.append("Seed cost of the cover crop and when to end it")
        risks.append("The cover crop uses soil water that the next crop may need; end it early in dry years")
    else:
        raise ValueError(kind)

    if baseline and parts["erosion"] > baseline["erosion"]:
        benefits.append("Less bare soil during heavy-rain months than your current rotation")
    risks.append("NASA data describe the area (~50 km), not your plot")
    return {"why": why, "evidence": evidence, "benefits": benefits, "gaps": gaps, "risks_to_review": risks}


# ---------- public entry point ----------

NAMES = {
    "current": "Current rotation",
    "legume_break": "Legume break",
    "cover_crop": "Cover crop in the bare window",
    "water_saving": "Water-saving swap",
    "forage_diversification": "Forage / diversification",
}


def _strategy(kind, years, cover, current, crops, profile, irrigated, slope, priorities, baseline=None) -> dict:
    cover_obj = (cover[0], crops[cover[1]]) if cover else None
    s = score([crops[c] for c in years], cover_obj, profile, irrigated, slope)
    scores = {k: s[k] for k in PRIORITIES}
    scores["overall"] = overall(scores, priorities)
    return {
        "id": kind,
        "name": NAMES[kind],
        "years": years,
        "cover_crop": {"after_year": cover[0] + 1, "crop": cover[1]} if cover else None,
        "scores": scores,
        "score_details": s["_parts"],
        **explain(kind, years, cover, current, crops, profile, irrigated, s, baseline),
    }


def compare(profile: dict, current: list[str], crops: dict, priorities: dict | None = None,
            irrigated: bool = False, slope: str = "flat", n_alternatives: int = 3) -> list[dict]:
    """Shape 2: the current rotation first, then the best variant of up to `n_alternatives` strategy kinds,
    ordered by overall score. Raises ValueError for unknown crops or a rotation outside 1-4 years."""
    if not 1 <= len(current) <= 4:
        raise ValueError("current rotation must have 1 to 4 years")
    unknown = [c for c in current if c not in crops]
    if unknown:
        raise ValueError(f"unknown crops: {unknown}")
    priorities = priorities or {}
    args = (current, crops, profile, irrigated, slope, priorities)

    baseline = _strategy("current", list(current), None, *args)
    scored = [_strategy(kind, o["years"], o["cover"], *args, baseline=baseline["score_details"])
              for kind, options in candidates(current, crops, profile, irrigated).items() for o in options]
    scored.sort(key=lambda s: s["scores"]["overall"], reverse=True)

    # Greedy pick: best remaining strategy of a kind not used yet, never repeating a rotation.
    picked, kinds, seen = [], set(), {(tuple(current), None)}
    for s in scored:
        key = (tuple(s["years"]), tuple(s["cover_crop"].values()) if s["cover_crop"] else None)
        if s["id"] in kinds or key in seen:
            continue
        picked.append(s)
        kinds.add(s["id"])
        seen.add(key)
        if len(picked) == n_alternatives:
            break
    return [baseline] + picked
