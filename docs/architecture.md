# Architecture

Stack: **Python 3.11+ · SQLite** engine ([0002](decisions/0002-tech-stack.md)) behind a **FastAPI** JSON API, and a **PWA in vanilla JS** with a hand-written service worker, served by the same service from `web/` ([0004](decisions/0004-mobile-pwa.md), [0005](decisions/0005-pwa-vanilla-js.md)). The Streamlit app (`src/app.py`) is only an internal test harness. Data contracts (Shape 1, Shape 2) and owners: [work-plan.md](work-plan.md).

## Design constraint: low-end phones
Primary users are farmers with at most a low/mid-range phone and poor mobile data. The UI is **mobile-first** (360 px, single column, light pages) and the demo path must not depend on live NASA calls. Details: [ux-guidelines.md](ux-guidelines.md#mobile-first-low-end-phones-primary-target).

## Components

| Component | Technology | Location | Owner | Status |
|---|---|---|---|---|
| NASA POWER client | Python, httpx (async) | `src/fieldshift/power.py` | @S-Santiago | ✅ built |
| MODIS NDVI client (ORNL DAAC) | Python, httpx (async) | `src/fieldshift/modis.py` | @S-Santiago | ✅ built |
| JSON cache (temporary) | files | `src/fieldshift/cache.py` | — | ✅ built · to be replaced by DB |
| Database | SQLite | `src/fieldshift/db.py`, schema + seed | @HectorLopGar-Dev | 🔴 #6 |
| Crop catalogue | CSV seed → `crops` table | `data/crops.csv` | @HectorLopGar-Dev | 🔴 #7 |
| Demo fields (offline) | committed seed | `data/samples/` | @HectorLopGar-Dev | 🔴 #8 |
| Climate indicators → Shape 1 | Python | `src/fieldshift/climate.py` | @HaoJunnnzhang | 🟡 #9 (built; DB hook pending #6) |
| Rotation engine → Shape 2 | Python | `src/fieldshift/rotations.py` | @HaoJunnnzhang | 🟡 #10 (built; needs real `crops.csv` from #7) |
| Tests | pytest | `tests/` | @HaoJunnnzhang | 🟡 #11 (26 tests) |
| API | FastAPI | `src/fieldshift/api.py` | @HectorLopGar-Dev | ✅ built (#36, PR #47) |
| App (PWA) | HTML + CSS + vanilla JS modules, manifest, hand-written service worker, no build step | `web/` | @S-Santiago | 🔴 #35 · #40 |
| Internal test harness (not the product) | Streamlit | `src/app.py` | @S-Santiago | ✅ built |
| Hosting | Free Python host (Render / HF Spaces / Fly.io) | — | @HectorLopGar-Dev | 🔴 #39 |

## Data flow
```
1. Farmer picks a demo field (or a point on the map), current rotation, priorities, irrigation, slope   [app.py]
2. db.get_profile(lat, lon) ── hit ──────────────────────────────────────────────┐
        │ miss                                                                    │
        ▼                                                                         │
   power.fetch_daily + modis.fetch_ndvi (NASA APIs) → climate.py → Shape 1 → db.save_profile
                                                                                  │
3. rotations.py(Shape 1, crops from db.get_crops(), farmer inputs) → Shape 2 ◄────┘
4. app.py renders: 12-month climate calendar · trends · 4 strategy cards (current + 3) · sources & limits
5. db.save_analysis(...)  (not persistent on the hosted demo)
```

## Indicators and scoring
Defined in [indicators.md](indicators.md). Thresholds and formulas must be documented there before implementation.

## Database (SQLite)
Module `src/fieldshift/db.py`, schema `src/fieldshift/schema.sql` (migrations tracked with `PRAGMA user_version`).
The DB file is **generated** and git-ignored (`FIELDSHIFT_DB`, default `data/processed/fieldshift.db`); it is rebuilt from committed seeds on start-up, so the app works offline. Rebuild by hand: `python -m fieldshift.db reset` (with `src` on `PYTHONPATH`).

| Table | Key | Content | Seeded from | Written by |
|---|---|---|---|---|
| `crops` | `crop` | Crop traits (columns in `docs/crop-traits.md`) | `data/crops.csv` (reloaded on every start) | — |
| `locations` | `slug` | Named fields; `is_demo=1` for the demo fields | `data/samples/locations.csv` | — |
| `nasa_raw` | `source, lat, lon` | Raw NASA POWER / MODIS payloads (replaces the old JSON file cache) | `data/samples/{power,modis}_<lat>_<lon>.json` | `power.py`, `modis.py` via `cache.py` |
| `climate_profiles` | `lat, lon` | Monthly profile, shape 1 in `docs/work-plan.md`, plus the `version` of the code that computed it | — | `climate.py` |
| `analyses` | `id` | Inputs (rotation, priorities, irrigation, slope) + resulting strategies (shape 2). No personal data | — | app |

Migration 2 adds `name`, `name_es`, `frost_tolerance`, `heat_tolerance` to `crops`. `get_engine_crops()` returns the catalogue in the format `rotations.py` expects (`crop_id`, `root_depth_m`, `market_value_illustrative`; perennials get a 12-month window). The HTTP API on top of these modules is documented in `docs/work-plan.md` ("API").

Coordinates are rounded to 2 decimals (~1 km) everywhere. Main functions: `get_crops()`, `get_crop()`, `get_locations()`, `get_location()`, `get_raw()`/`save_raw()`, `get_profile(lat, lon, version=None)`/`save_profile()`, `save_analysis()`/`get_analysis()`/`list_analyses()`.

## Known limitations
- NASA POWER is modelled/derived data on a ~50 km grid: describes the area, not the plot.
- `GWETROOT` is model-based root-zone wetness, not satellite-measured soil moisture.
- MODIS NDVI: only 2024–2025, 250 m pixels may mix several plots.
- Market value of crops is illustrative.
- Hosted demo: disk resets on restart (DB rebuilt from seed; saved analyses lost).
- Thresholds are team assumptions documented in [indicators.md](indicators.md): frost Tmin < 0 °C, heat Tmax > 35 °C, heavy rain ≥ 30 mm/day, likely bare NDVI < 0.25. None is crop-specific.
- ET0 is FAO-56 Penman-Monteith from NASA POWER radiation, humidity and wind (Hargreaves only as a fallback for missing days); still a ~50 km cell value.
- Rotation scores use simple, documented rules ([indicators.md → Scoring](indicators.md#scoring-shape-2-scores)): rain in the crop's months vs its seasonal water need; stored soil water, yields and real prices are not modelled. `income` is illustrative.
- Uncertainty statements for the UI (English and Spanish): `climate.LIMITS`, returned in every profile as `limits`.
- Coastal grid cells (Málaga city, Cártama): no heat days and an urban MODIS pixel in the city; the demo field should be inland farmland (e.g. Vega de Antequera).
