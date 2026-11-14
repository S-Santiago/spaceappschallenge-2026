# Work plan — team of 4

> **Agreed.** Stack: **Python 3.11+ · SQLite · FastAPI + PWA** — see [decisions/0002-tech-stack.md](decisions/0002-tech-stack.md), superseded for the UI by [0004](decisions/0004-mobile-pwa.md). Tasks and owners live in the GitHub issues (epic #16); this page is the summary.

## Product (MVP)
A mobile web app (PWA) where a farmer picks a field (demo field or map), enters the current rotation and their priorities (save water, soil health, income, low risk). The tool then shows:
1. **Field climate calendar** (12 months): rain, water deficit, soil moisture, frost and heat days, and months when the field is bare, all taken from NASA data.
2. **Long-term trends**: 2005–2014 vs 2016–2025 (rainfall, heat days).
3. **Rotation comparison**: the current rotation plus **3 alternatives** (legume break, cover crop in the bare window, water-saving swap, forage/diversification). Each one shows *why · evidence · benefits · information gaps · risks to review locally*.

> 📱 **Target user:** farmer with at most a low/mid-range phone and poor mobile data → mobile-first, lightweight, works at 360 px. See `docs/ux-guidelines.md`.

## Already built (on `main`)
| File | What it does | Status |
|---|---|---|
| `src/fieldshift/power.py` | NASA POWER daily point data 2005–2025 (Tmax, Tmin, precipitation, root-zone soil wetness) | ✅ built, tested on Málaga (7,670 days) |
| `src/fieldshift/modis.py` | MODIS MOD13Q1 NDVI 2024–2025 via ORNL DAAC (no login), parallel requests | ✅ built, tested (45 composites, ~25 s first call) |
| `src/fieldshift/cache.py` | JSON cache: `data/processed/cache` (ignored) → `data/samples` (committed demo data) — **to be replaced by `db.py`** (#6) | ✅ built |

## Work split (4 people, 4 independent tracks)
Each track owns its own files, so the four can work in parallel without conflicts. Interfaces between tracks are Shape 1, Shape 2 and the DB functions below.

| Track | Owner | Files | Issues |
|---|---|---|---|
| **App & integration** (full-stack) | @S-Santiago | `web/` (PWA), wiring, deployment | #12 · #13 · #14 · #15 |
| **Database** | @HectorLopGar-Dev | `src/fieldshift/db.py`, schema/seed SQL, `data/crops.csv`, demo-field seed in `data/samples/` | #6 · #7 · #8 |
| **Backend** (indicators + rotation engine) | @HaoJunnnzhang | `src/fieldshift/climate.py`, `src/fieldshift/rotations.py`, `tests/` | #9 · #10 · #11 |
| **General** (decisions, data registry, docs, demo, submission) | @sebasbarrabaja-cmyk | `README.md`, `docs/`, `docs/pitch/` | #1 · #3 · #4 · #5 |

**Reviews (#2, `.github/CODEOWNERS`):** code → @S-Santiago · visuals/UX, docs, README, pitch → @sebasbarrabaja-cmyk.

### Data flow
```
NASA POWER API ─┐                         data/crops.csv (seed)
                ├─ power.py / modis.py ─→ db.py (SQLite) ←──────────────┘
MODIS (ORNL) ───┘                           │      ▲
                                            ▼      │ save_profile / save_analysis
                              climate.py → Shape 1 → rotations.py → Shape 2
                                            │                         │
                                            └──→ api.py (FastAPI) → web/ (PWA) ←┘
```

### DB interface (proposal in #6 — owner @HectorLopGar-Dev)
Tables: `crops`, `locations`, `climate_profiles`, `analyses`. Functions: `get_crops()`, `get_profile(lat, lon)`, `save_profile(...)`, `save_analysis(...)`. The `.db` file is git-ignored and rebuilt at startup from the committed schema + seed (needed on free hosts whose disk is reset on restart).

### Shape 1 — climate profile (A → B, C)
```json
{
  "location": {"lat": 36.72, "lon": -4.42, "elevation_m": 144},
  "months": [{"month": 1, "rain_mm": 60, "et0_mm": 45, "water_balance_mm": 15,
              "soil_wetness": 0.6, "frost_days": 0.2, "heat_days": 0, "heavy_rain_days": 0.4,
              "ndvi": 0.15, "likely_bare": true}],
  "trends": {"rain_change_pct": -8, "heat_days_change": 3.1},
  "sources": ["NASA POWER 2005-2025", "MODIS MOD13Q1 2024-2025"],
  "limits": {"en": ["Climate values are NASA satellite and model estimates ..."], "es": ["Los datos de clima son ..."]},
  "field_limits": {"rain_mm": {"en": "Average for 2005-2025 over an area of about 50 km; ...", "es": "..."}, "...": {}}
}
```

### Shape 2 — strategies (B → C)
```json
[{"id": "current", "name": "Current rotation", "years": ["durum_wheat", "durum_wheat", "sunflower"],
  "cover_crop": null,
  "scores": {"water": 62, "soil": 40, "income": 70, "risk": 55, "overall": 57},
  "score_details": {"nitrogen": 0, "organic_matter": 12, "erosion": 24, "pest_break": 13, "bare_months_per_year": 4.7},
  "why": "...", "evidence": ["..."], "benefits": ["..."], "gaps": ["..."], "risks_to_review": ["..."]}]
```
`id` is `current` or a strategy kind (`legume_break`, `cover_crop`, `water_saving`, `forage_diversification`). `cover_crop` is `null` or `{"after_year": 2, "crop": "vetch_cover"}`. Call `rotations.compare(profile, current, crops, priorities, irrigated, slope, lang="en"|"es")`; use `rotations.label(score, lang)` for good/neutral/poor and `rotations.DISCLAIMER[lang]` at the end of the cards. Scope: Málaga province only; inland farmland such as Vega de Antequera (37.05, -4.60) gives a much more realistic profile than Málaga city, whose MODIS pixel is urban and whose NASA cell is coastal (no heat days).

## API (decision 0004 · #36 — owner @HectorLopGar-Dev)
`src/fieldshift/api.py` (FastAPI). Run from the repo root: `PYTHONPATH=src uvicorn fieldshift.api:app --reload` → interactive docs at `/docs`. The same service serves the PWA from `web/` (override with `FIELDSHIFT_WEB_DIR`), so there is no CORS. No logic in the API: data from `db.py`, profile from `climate.py`, strategies from `rotations.py`.

| Method & path | Returns |
|---|---|
| `GET /api/health` | `{"status": "ok"}` (use it to wake the free host before the pitch) |
| `GET /api/fields` | Demo fields: `[{"slug", "name", "lat", "lon", "elevation_m", "description"}]` |
| `GET /api/crops?lang=en\|es` | `[{"id", "name", "scientific_name", "type", "family", "n_fixing", "sow_month", "harvest_month", "confidence"}]` sorted by `name` in `lang` (accents ignored). **PWA crop field:** a text input with suggestions (`<datalist>`, no JS library); each suggestion reads "English name · Latin name", so the farmer can type either (accents and case ignored); the chosen `id` is sent in `rotation` |
| `POST /api/analyze` | Body below → `{"analysis_id", "profile": Shape 1, "strategies": Shape 2 + "labels", "pending", "disclaimer", "score_limits"}` (`score_limits`: one sentence per score, in the request language) |
| `GET /api/analyses/{id}` | A stored analysis: `{"id", "lat", "lon", "inputs", "strategies", "created_at"}` |
| `GET /api/predictions?field=<slug>` (or `lat`, `lon`) `&rotation=<id>&rotation=<id>…&slope=flat\|moderate\|steep` | Predictions shape below (P-01, P-02, P-03, P-07). Same POWER path and cache as `/api/analyze` (demo fields never call NASA; a new point waits for POWER, `503` if unreachable). MODIS is used only if already downloaded. `rotation` (1–4 crop ids of the **current** rotation, optional) enables the crop-calendar source of `alerts`; `slope` is applied with `raise_for_slope`. Without MODIS and without `rotation`, `alerts` is `null`. Errors: `404` unknown field, `422` missing/invalid location, unknown crop or slope. ~40 ms, ~7 KB for a demo field |

```json
POST /api/analyze
{"field": "antequera",                       // demo field slug, or "lat" + "lon" instead
 "rotation": ["durum_wheat", "durum_wheat", "sunflower"],   // 1-4 crop ids from /api/crops
 "priorities": {"water": 3, "soil": 1, "income": 1, "risk": 0},  // 0-3 each, default 1
 "irrigation": "none",                       // none | supplementary | full (anything but none = irrigated)
 "slope": "flat",                            // flat | moderate | steep
 "lang": "es"}                               // en | es: language of the card texts
```
Each strategy gets `"labels": {"water": "good", ..., "overall": "neutral"}` (`rotations.label`). Errors: `422` invalid input or unknown crop, `404` unknown field/analysis, `503` NASA unreachable for a non-demo point. Demo fields never call NASA (data pre-loaded); the climate profile is computed once and stored in `climate_profiles` (recomputed when `climate.py` changes). Every analysis is stored in `analyses` (no personal data).

**Points that are not demo fields.** NASA POWER answers in ~3 s, but the MODIS service (ORNL) can take minutes for a new point. The API waits for POWER (up to 60 s) and for MODIS only 3 s (`FIELDSHIFT_MODIS_WAIT_S`); if MODIS is not ready it answers anyway with `"pending": ["ndvi"]` and `likely_bare: null` in every month (bare-soil months unknown), while the MODIS download continues in the background. A retry joins that download instead of starting a new one; once it lands, the full profile is stored and `"pending": []`. **PWA:** show the results, say "satellite greenness still loading" when `pending` contains `ndvi`, and ask again after ~1 minute. Measured: new point ~6 s, same point afterwards < 0.3 s.

### Predictions shape (P-01, P-03 — #37; P-02, P-07 — #38)
`predictions.build_predictions(power_payload)` in `src/fieldshift/predictions.py` (pure function over the same POWER payload `climate.py` uses; no network). Served by `GET /api/predictions` (table above).

```json
{"period": "2005-2025",
 "basis": "Statistics of NASA POWER daily data for the field's ~50 km cell. Not a weather forecast.",
 "rain_weeks": [  // P-01: 52 weeks; week 1 = 1-7 Jan, week 52 includes 31 Dec
   {"week": 48, "start": "11-26", "prob_rain": 0.76, "prob_useful_rain": 0.43, "mean_rain_mm": 20.1, "years": 21}],
 "frost": {       // P-03: null dates = no frost in most years / never
   "spring": {"years": 21, "years_with_frost": 17, "probability": 0.81,
              "last_frost_median": "02-06", "last_frost_p90": "03-14", "years_by_p90": 19},
   "autumn": {"years": 21, "years_with_frost": 5, "probability": 0.24,
              "first_frost_median": null, "first_frost_p10": "12-03", "years_from_p10": 19},
   "safe_days": 264},
 "heavy_rain": {  // P-02
   "threshold_mm": 20,
   "months": [{"month": 11, "prob": 0.52, "years": 21}],
   "return_levels": [{"years": 2, "mm": 33, "observed_years": 11}, {"years": 5, "mm": 42, "observed_years": 4},
                     {"years": 10, "mm": 48, "observed_years": 3}],
   "annual_max": {"years": 21, "median_mm": 33.0, "max_mm": 52.7, "max_year": 2024},
   "method": "Gumbel fitted by L-moments on 21 annual maxima of cell-averaged daily rain"},
 "alerts": [      // P-07; null if neither MODIS nor a rotation was given
   {"month": 11, "prob": 0.52, "years": 21, "sources": ["crop_calendar"], "level": "high"}],
 "limits": {      // one sentence per card, en + es (predictions.PREDICTION_LIMITS, #44)
   "rain_weeks": {"en": "Share of the past 21 years (2005-2025) with rain in that week; ...", "es": "..."},
   "heavy_rain": {...}, "frost": {...}, "alerts": {...}}}
```
Call `build_predictions(power, modis, rotation)` with `rotation` = list of crop dicts of the farmer's **current** rotation (`[db.get_engine_crops()[c] for c in rotation_ids]`). The endpoint applies `predictions.raise_for_slope(level, slope)` with the farmer's slope, so the PWA shows `level` as it comes.
Values above are the real output for Vega de Antequera. UI wording (farmer sentences) in `docs/indicators.md` → Predictions.

## Suggested timeline (Europe/Madrid)
| When | Milestone |
|---|---|
| Sat by 13:30 (mentoring) | Interfaces agreed; persona + demo field chosen; stack decided |
| Sat 17:30 (review) | A and B return real JSON; C shows it end-to-end, even if ugly |
| Sun 13:00 | Feature freeze on content; polish UX and wording |
| Sun 15:00 | `main` frozen (CONTRIBUTING rule); demo recorded / slides done |
| Sun 16:30 | Technical pitch test |
| Sun before 23:59 | Submit for Judging, then re-check the confirmation |
