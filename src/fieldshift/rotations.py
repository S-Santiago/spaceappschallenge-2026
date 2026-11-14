"""Rotation engine: Shape 1 climate profile + crop catalogue + farmer inputs -> Shape 2 strategies.

Scoring rules are documented in docs/indicators.md ("Scoring"). Every number used in the cards comes from
the climate profile (NASA) or from data/crops.csv (with its sources); nothing else is invented.
Card texts are available in English ("en") and Spanish ("es").
"""

from __future__ import annotations

import csv
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CROPS_CSV = ROOT / "data" / "crops.csv"

PRIORITIES = ("water", "soil", "income", "risk")
LANGS = ("en", "es")
LEVEL = {"low": 0.0, "medium": 0.5, "high": 1.0}
MARKET = {"low": 20, "medium": 50, "high": 80}  # illustrative only
SLOPE_FACTOR = {"flat": 0.5, "moderate": 0.75, "steep": 1.0}
MIN_COVER_MONTHS = 3
EFFECTIVE_RAIN = 0.8  # share of in-season rain the crop can use
STORED_FRACTION = 0.5  # share of the rain of the months before sowing still stored in the soil
PRE_SOWING_MONTHS = 3
AWC_MM_PER_M = 100  # available soil water per metre of roots (typical loam)
DEFAULT_ROOT_M = 1.0
MIN_COVER_RAIN_MM = 100  # rain-fed cover crops are not proposed below this rain in their window
LEGUME_RETURN_YEARS = 3  # minimum years between two crops of the same legume

_INT = ("sow_month", "harvest_month")
_FLOAT = ("water_need_mm_min", "water_need_mm_max", "root_depth_m")

MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
}
DISCLAIMER = {
    "en": "This tool supports, and does not replace, your judgment and local agricultural advice.",
    "es": "Esta herramienta te ayuda a decidir, pero no sustituye tu criterio ni el consejo agronómico local.",
}
LABELS = {
    "en": {"good": "good", "neutral": "neutral", "poor": "poor"},
    "es": {"good": "bueno", "neutral": "regular", "poor": "malo"},
}
NAMES = {
    "en": {"current": "Current rotation", "legume_break": "Legume break",
           "cover_crop": "Cover crop in the bare window", "water_saving": "Water-saving swap",
           "forage_diversification": "Forage / diversification"},
    "es": {"current": "Rotación actual", "legume_break": "Descanso con leguminosa",
           "cover_crop": "Cubierta vegetal en el periodo sin cultivo", "water_saving": "Cambio para ahorrar agua",
           "forage_diversification": "Forraje / diversificación"},
}
SOURCE = {"en": "NASA POWER 2005-2025", "es": "NASA POWER 2005-2025"}
TOLERANCE = {"en": {"low": "low", "medium": "medium", "high": "high"},
             "es": {"low": "baja", "medium": "media", "high": "alta"}}

# Card texts. Placeholders are filled in explain(); keep both languages in sync.
T = {
    "en": {
        "evidence_crop": "{crop}: rain {span} averages {rain:.0f} mm ({src}, I-01), plus about {stored:.0f} mm stored "
                         "in the soil from earlier rain, vs a water need of {need} [{sources}, confidence {conf}]",
        "unknown": "unknown", "no_source": "no source",
        "trend": "Rain 2016-2025 vs 2005-2014: {pct:+.0f}% ({src}, I-10)",
        "gap_prices": "Local prices and costs: the income score is illustrative only",
        "gap_soil": "Soil test (texture, organic matter, pH, nitrogen) for this field",
        "gap_stored": "Real soil water at sowing (stored water is estimated; NASA soil wetness is a ~50 km model, I-04)",
        "frost": "{crop} - about {days:.1f} frost days in its season and {tol} frost tolerance ({src}). "
                 "Check with local experience.",
        "heat": "{crop} - about {days:.1f} days above 35 °C in its season and {tol} heat tolerance ({src}). "
                "Check with local experience.",
        "drought": "{crop} - rain-fed, rain covers only about {cov:.0%} of its water need ({src}). "
                   "Check with local experience.",
        "same_family": "Same crop family in consecutive years: pests and diseases can build up",
        "legume_return": "{crop} comes back in fewer than {n} years: risk of soil diseases (e.g. Ascochyta, Fusarium)",
        "why_current": "Your current rotation, shown as the baseline to compare against.",
        "why_legume": "Adds {crops}, a legume that takes nitrogen from the air and can help break the cereal pest cycle.",
        "ben_legume_n": "Can reduce nitrogen fertiliser for the next crop (depends on nodulation and how much residue stays)",
        "ben_pests": "Can help break cereal pest and disease cycles",
        "gap_market": "Market or on-farm use for {crops}",
        "risk_machinery": "Weed control and harvest machinery for {crops}",
        "why_forage": "Adds {crops}, a forage crop from a different family, to diversify income and the rotation.",
        "ben_family": "A new crop family can help break pest cycles",
        "ben_forage": "Forage for own livestock or local sale",
        "gap_buyer": "Is there a local buyer or livestock for {crops}?",
        "risk_hay": "Haymaking/silage machinery and labour",
        "why_water": "Swaps {old} for {crops}, which needs less water and is rated as more drought-tolerant "
                     "(crop table).",
        "ben_water_need": "Lower water need per season",
        "ben_dry_years": "Less exposed to dry years",
        "gap_yield": "Yield of {crops} in this area in dry years",
        "why_cover": "Keeps the same main crops but sows {cover} as a cover crop after {crop}, in months when the "
                     "field is otherwise bare.",
        "ben_erosion": "Protects bare soil from erosion",
        "ben_om": "Adds some organic matter over several years",
        "ben_cover_n": "May add some nitrogen if the cover crop establishes well",
        "ev_bare": "Satellite greenness suggests a bare field in {months} (MODIS NDVI 2024-2025, I-09)",
        "ev_cover": "Cover crop period {span}: {rain:.0f} mm of rain and {heavy:.1f} heavy-rain days per year "
                    "({src}, I-01, I-07)",
        "gap_seed": "Seed cost of the cover crop and when to end it",
        "risk_cover_water": "The cover crop uses soil water that the next crop may need; end it early in dry years",
        "ben_less_bare": "Less bare soil during heavy-rain months than your current rotation",
        "risk_area": "NASA data describe the area (~50 km), not your plot",
    },
    "es": {
        "evidence_crop": "{crop}: la lluvia de {span} es de {rain:.0f} mm de media ({src}, I-01), más unos {stored:.0f} mm "
                         "guardados en el suelo de lluvias anteriores, frente a una necesidad de agua de {need} "
                         "[{sources}, confianza {conf}]",
        "unknown": "desconocida", "no_source": "sin fuente",
        "trend": "Lluvia 2016-2025 frente a 2005-2014: {pct:+.0f}% ({src}, I-10)",
        "gap_prices": "Precios y costes locales: la puntuación de ingresos es solo orientativa",
        "gap_soil": "Análisis de suelo (textura, materia orgánica, pH, nitrógeno) de esta parcela",
        "gap_stored": "Agua real del suelo en la siembra (el agua guardada es una estimación; la humedad del suelo "
                      "de NASA es un modelo de ~50 km, I-04)",
        "frost": "{crop}: unos {days:.1f} días de helada en su ciclo y tolerancia a la helada {tol} ({src}). "
                 "Compruébalo con la experiencia local.",
        "heat": "{crop}: unos {days:.1f} días por encima de 35 °C en su ciclo y tolerancia al calor {tol} ({src}). "
                "Compruébalo con la experiencia local.",
        "drought": "{crop}: en secano, la lluvia solo cubre cerca del {cov:.0%} de su necesidad de agua ({src}). "
                   "Compruébalo con la experiencia local.",
        "same_family": "Misma familia de cultivo en años seguidos: pueden acumularse plagas y enfermedades",
        "legume_return": "{crop} vuelve en menos de {n} años: riesgo de enfermedades del suelo "
                         "(p. ej. rabia/Ascochyta, Fusarium)",
        "why_current": "Tu rotación actual, como punto de partida para comparar.",
        "why_legume": "Añade {crops}, una leguminosa que toma nitrógeno del aire y puede ayudar a cortar el ciclo "
                      "de plagas del cereal.",
        "ben_legume_n": "Puede reducir el abono nitrogenado del cultivo siguiente (depende de la nodulación y de "
                        "cuánto rastrojo quede)",
        "ben_pests": "Puede ayudar a cortar ciclos de plagas y enfermedades del cereal",
        "gap_market": "Venta o uso en la finca de {crops}",
        "risk_machinery": "Control de malas hierbas y maquinaria de cosecha para {crops}",
        "why_forage": "Añade {crops}, un forraje de otra familia, para diversificar ingresos y la rotación.",
        "ben_family": "Una familia de cultivo nueva puede ayudar a cortar ciclos de plagas",
        "ben_forage": "Forraje para el ganado propio o para vender en la zona",
        "gap_buyer": "¿Hay comprador local o ganado para {crops}?",
        "risk_hay": "Maquinaria y mano de obra para henificar o ensilar",
        "why_water": "Cambia {old} por {crops}, que necesita menos agua y figura como más tolerante a la sequía "
                     "(tabla de cultivos).",
        "ben_water_need": "Menos necesidad de agua por campaña",
        "ben_dry_years": "Menos expuesto a los años secos",
        "gap_yield": "Rendimiento de {crops} en esta zona en años secos",
        "why_cover": "Mantiene los mismos cultivos principales, pero siembra {cover} como cubierta después de {crop}, "
                     "en los meses en que la parcela queda sin cultivo.",
        "ben_erosion": "Protege el suelo desnudo de la erosión",
        "ben_om": "Aporta algo de materia orgánica a lo largo de varios años",
        "ben_cover_n": "Puede aportar algo de nitrógeno si la cubierta se implanta bien",
        "ev_bare": "El verdor por satélite indica parcela sin cultivo en {months} (MODIS NDVI 2024-2025, I-09)",
        "ev_cover": "Periodo de la cubierta {span}: {rain:.0f} mm de lluvia y {heavy:.1f} días de lluvia fuerte "
                    "al año ({src}, I-01, I-07)",
        "gap_seed": "Coste de la semilla de la cubierta y cuándo eliminarla",
        "risk_cover_water": "La cubierta gasta agua del suelo que puede necesitar el cultivo siguiente; "
                            "elimínala antes en años secos",
        "ben_less_bare": "Menos suelo desnudo en los meses de lluvias fuertes que con tu rotación actual",
        "risk_area": "Los datos de NASA describen la comarca (~50 km), no tu parcela",
    },
}


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


def crop_name(crop: dict, lang: str = "en") -> str:
    """Spanish name from an optional `name_es` column, falling back to `name`."""
    return (lang == "es" and crop.get("name_es")) or crop.get("name") or crop.get("crop_id")


# ---------- per-crop climate fit ----------

def _month(profile: dict, m: int) -> dict:
    return profile["months"][m - 1]


def season_sum(profile: dict, months: list[int], field: str) -> float:
    return sum(_month(profile, m).get(field) or 0 for m in months)


def stored_water(crop: dict, profile: dict) -> float:
    """Rain of the months before sowing still in the root zone (mm), capped by what the roots can reach."""
    if is_fallow(crop):
        return 0.0
    pre = [(crop["sow_month"] - k - 1) % 12 + 1 for k in range(1, PRE_SOWING_MONTHS + 1)]
    cap = AWC_MM_PER_M * (crop.get("root_depth_m") or DEFAULT_ROOT_M)
    return min(STORED_FRACTION * season_sum(profile, pre, "rain_mm"), cap)


def rain_coverage(crop: dict, profile: dict) -> float:
    """Share of the crop's seasonal water need covered by effective in-season rain plus stored soil water (0-1).
    Fallow = 1."""
    need = need_mm(crop)
    if is_fallow(crop) or need == 0:
        return 1.0
    supply = EFFECTIVE_RAIN * season_sum(profile, window(crop), "rain_mm") + stored_water(crop, profile)
    return min(1.0, supply / need)


def climate_penalties(crop: dict, profile: dict, irrigated: bool) -> list[dict]:
    """Frost, heat and drought problems in the crop's own season: [{"kind", "value", "tolerance", "penalty"}]."""
    if is_fallow(crop):
        return []
    months = window(crop)
    out = []
    for kind, field in (("frost", "frost_days"), ("heat", "heat_days")):
        days, tol = season_sum(profile, months, field), crop.get(f"{kind}_tolerance")
        if tol == "low" and days > 1:
            out.append({"kind": kind, "value": days, "tolerance": tol, "penalty": 30})
        elif tol == "medium" and days > 5:
            out.append({"kind": kind, "value": days, "tolerance": tol, "penalty": 15})
    cov = rain_coverage(crop, profile)
    if not irrigated and cov < 0.5:
        tol = crop.get("drought_tolerance")
        out.append({"kind": "drought", "value": cov, "tolerance": tol,
                    "penalty": {"low": 30, "medium": 15, "high": 5}.get(tol, 15)})
    return out


def suitable(crop: dict, profile: dict, irrigated: bool) -> bool:
    """A crop can be proposed only if it is not heavily penalised by the local climate."""
    return sum(p["penalty"] for p in climate_penalties(crop, profile, irrigated)) < 30


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


def cover_fits(years: list[dict], i: int, cover: dict, profile: dict, irrigated: bool) -> bool:
    """A cover crop fits after year i when its whole window lies in that gap and, if rain-fed,
    enough rain falls in that window."""
    months = window(cover)
    if len(months) < MIN_COVER_MONTHS or not set(months) <= set(gap(years, i)):
        return False
    return irrigated or season_sum(profile, months, "rain_mm") >= MIN_COVER_RAIN_MM


def legume_repeats(years: list[dict]) -> list[dict]:
    """Legumes that come back in fewer than LEGUME_RETURN_YEARS years (cyclic rotation)."""
    n = len(years)
    out = []
    for i, c in enumerate(years):
        if c.get("n_fixing") != "yes" or c in out:
            continue
        if any(years[(i + k) % n] is c or years[(i + k) % n].get("crop_id") == c.get("crop_id")
               for k in range(1, min(LEGUME_RETURN_YEARS, n + 1))):
            out.append(c)
    return out


def score(years: list[dict], cover: tuple[int, dict] | None, profile: dict, irrigated: bool, slope: str) -> dict:
    n = len(years)
    cover_crop = cover[1] if cover else None

    # water: share of crop water need covered by rain; a cover crop counts as half a crop
    water_items = [(rain_coverage(c, profile), 1.0) for c in years]
    if cover_crop:
        water_items.append((rain_coverage(cover_crop, profile), 0.5))
    water = 100 * sum(v * w for v, w in water_items) / sum(w for _, w in water_items)

    # soil = nitrogen 25 + organic matter 25 + erosion 30 + pest break 20
    legumes = [c for c in years if c.get("n_fixing") == "yes"]
    if any(c.get("type") in ("forage", "cover") for c in legumes):
        nitrogen = 25  # biomass largely stays on the farm
    elif legumes or (cover_crop and cover_crop.get("n_fixing") == "yes"):
        nitrogen = 15  # grain legume exports most of the fixed N; or legume cover only
    else:
        nitrogen = 0
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
    risk = sum(max(0, 100 - sum(p["penalty"] for p in climate_penalties(c, profile, irrigated))) for c in years) / n

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


def label(value: int, lang: str = "en") -> str:
    """Words to show next to a score in the UI."""
    return LABELS[lang]["good" if value >= 67 else "neutral" if value >= 34 else "poor"]


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

    return {
        "legume_break": [{"years": y, "cover": None} for y in _variants(current, legumes, insert=True)],
        "forage_diversification": [{"years": y, "cover": None} for y in _variants(current, forage, insert=True)],
        "water_saving": [{"years": current[:thirstiest] + [s] + current[thirstiest + 1:], "cover": None}
                         for s in savers],
        "cover_crop": [{"years": list(current), "cover": (i, cov)}
                       for i, cov in product(range(len(current)), covers)
                       if cover_fits(years, i, crops[cov], profile, irrigated)],
    }


# ---------- explanations ----------

def _span(months: list[int], lang: str) -> str:
    return f"{MONTHS[lang][months[0] - 1]}-{MONTHS[lang][months[-1] - 1]}" if months else "-"


def _crop_evidence(crop: dict, profile: dict, lang: str) -> list[str]:
    if is_fallow(crop):
        return []
    t = T[lang]
    lo, hi = crop.get("water_need_mm_min"), crop.get("water_need_mm_max")
    return [t["evidence_crop"].format(
        crop=crop_name(crop, lang), span=_span(window(crop), lang), rain=season_sum(profile, window(crop), "rain_mm"),
        stored=stored_water(crop, profile), src=SOURCE[lang],
        need=f"{lo:.0f}-{hi:.0f} mm" if lo is not None and hi is not None else t["unknown"],
        sources=crop.get("sources") or t["no_source"],
        conf=crop.get("confidence") or t["unknown"],
    )]


def _climate_risks(years: list[dict], profile: dict, irrigated: bool, lang: str) -> list[str]:
    t, risks = T[lang], []
    for c in years:
        for p in climate_penalties(c, profile, irrigated):
            risks.append(t[p["kind"]].format(crop=crop_name(c, lang), days=p["value"], cov=p["value"],
                                             tol=TOLERANCE[lang].get(p["tolerance"], "?"), src=SOURCE[lang]))
    return risks


def explain(kind: str, years: list[str], cover: tuple[int, str] | None, current: list[str], crops: dict,
            profile: dict, irrigated: bool, scores: dict, baseline: dict | None, lang: str = "en") -> dict:
    t = T[lang]
    yc = [crops[c] for c in years]
    new = [c for c in years if c not in current]
    names = ", ".join(crop_name(crops[c], lang) for c in dict.fromkeys(new))
    parts = scores["_parts"]
    evidence = [e for c in dict.fromkeys(years) for e in _crop_evidence(crops[c], profile, lang)]
    trend = profile.get("trends", {})
    if trend.get("rain_change_pct") is not None:
        evidence.append(t["trend"].format(pct=trend["rain_change_pct"], src=SOURCE[lang]))
    benefits, gaps = [], [t["gap_prices"], t["gap_soil"]]
    risks = _climate_risks(yc, profile, irrigated, lang)
    if not irrigated:
        gaps.append(t["gap_stored"])
    if parts["pest_break"] < 20:
        risks.append(t["same_family"])
    risks += [t["legume_return"].format(crop=crop_name(c, lang), n=LEGUME_RETURN_YEARS) for c in legume_repeats(yc)]

    if kind == "current":
        why = t["why_current"]
    elif kind == "legume_break":
        why = t["why_legume"].format(crops=names)
        benefits += [t["ben_legume_n"], t["ben_pests"]]
        gaps.append(t["gap_market"].format(crops=names))
        risks.append(t["risk_machinery"].format(crops=names))
    elif kind == "forage_diversification":
        why = t["why_forage"].format(crops=names)
        benefits += [t["ben_family"], t["ben_forage"]]
        gaps.append(t["gap_buyer"].format(crops=names))
        risks.append(t["risk_hay"])
    elif kind == "water_saving":
        old = ", ".join(crop_name(crops[c], lang) for c in current if c not in years)
        why = t["why_water"].format(old=old, crops=names)
        benefits += [t["ben_water_need"], t["ben_dry_years"]]
        gaps.append(t["gap_yield"].format(crops=names))
    elif kind == "cover_crop":
        i, cid = cover
        cov = crops[cid]
        months = window(cov)
        why = t["why_cover"].format(cover=crop_name(cov, lang), crop=crop_name(yc[i], lang))
        benefits += [t["ben_erosion"], t["ben_om"]]
        if cov.get("n_fixing") == "yes":
            benefits.append(t["ben_cover_n"])
        bare_ndvi = [m["month"] for m in profile["months"] if m.get("likely_bare")]
        if bare_ndvi:
            evidence.append(t["ev_bare"].format(months=", ".join(MONTHS[lang][m - 1] for m in bare_ndvi)))
        evidence.append(t["ev_cover"].format(span=_span(months, lang), rain=season_sum(profile, months, "rain_mm"),
                                             heavy=season_sum(profile, months, "heavy_rain_days"), src=SOURCE[lang]))
        evidence += _crop_evidence(cov, profile, lang)
        gaps.append(t["gap_seed"])
        risks.append(t["risk_cover_water"])
    else:
        raise ValueError(kind)

    if baseline and parts["erosion"] > baseline["erosion"]:
        benefits.append(t["ben_less_bare"])
    risks.append(t["risk_area"])
    return {"why": why, "evidence": evidence, "benefits": benefits, "gaps": gaps, "risks_to_review": risks}


# ---------- public entry point ----------

def _strategy(kind, years, cover, current, crops, profile, irrigated, slope, priorities, lang, baseline=None) -> dict:
    cover_obj = (cover[0], crops[cover[1]]) if cover else None
    s = score([crops[c] for c in years], cover_obj, profile, irrigated, slope)
    scores = {k: s[k] for k in PRIORITIES}
    scores["overall"] = overall(scores, priorities)
    return {
        "id": kind,
        "name": NAMES[lang][kind],
        "years": years,
        "cover_crop": {"after_year": cover[0] + 1, "crop": cover[1]} if cover else None,
        "scores": scores,
        "score_details": s["_parts"],
        **explain(kind, years, cover, current, crops, profile, irrigated, s, baseline, lang),
    }


def compare(profile: dict, current: list[str], crops: dict, priorities: dict | None = None,
            irrigated: bool = False, slope: str = "flat", n_alternatives: int = 3, lang: str = "en") -> list[dict]:
    """Shape 2: the current rotation first, then the best variant of up to `n_alternatives` strategy kinds,
    ordered by overall score. Texts in `lang` ("en" or "es").
    Raises ValueError for unknown crops, a rotation outside 1-4 years or an unknown language."""
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}")
    if not 1 <= len(current) <= 4:
        raise ValueError("current rotation must have 1 to 4 years")
    unknown = [c for c in current if c not in crops]
    if unknown:
        raise ValueError(f"unknown crops: {unknown}")
    priorities = priorities or {}
    args = (current, crops, profile, irrigated, slope, priorities, lang)

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
