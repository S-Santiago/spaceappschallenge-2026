# Architecture

Stack: **Python 3.11+ · SQLite** engine ([0002](decisions/0002-tech-stack.md)) behind a **FastAPI** JSON API, and a **PWA in vanilla JS** with a hand-written service worker, served by the same service from `web/` ([0004](decisions/0004-mobile-pwa.md), [0005](decisions/0005-pwa-vanilla-js.md)). The early Streamlit test harness (`src/app.py`) was retired on 2026-11-14 once the PWA reached parity with real data (#14). Data contracts (Shape 1, Shape 2) and owners: [work-plan.md](work-plan.md).

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
| App (PWA) | HTML + CSS + vanilla JS modules, manifest, hand-written service worker, no build step | `web/` | @S-Santiago | ✅ #35 · #14 · #40 (real API, loading/error states, offline analyses and predictions; real-phone check pending) |
| ~~Internal test harness~~ | ~~Streamlit~~ | ~~`src/app.py`~~ | @S-Santiago | Retired 2026-11-14 (decision 0004) |
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

## Limits per value shown to the farmer (#44)
Every number in the UI gets one short sentence saying what it cannot tell. Texts live in code, in English and Spanish, so the PWA shows them next to the value (e.g. an "i" or a line under the number). Tests check that every value has both languages.

| ID | Value | Limit (English; Spanish in code) | Source in code / API |
|---|---|---|---|
| I-01 | `rain_mm` | Average for 2005-2025 over an area of about 50 km; a single year can be much wetter or drier. | `climate.FIELD_LIMITS` → profile `field_limits` |
| I-02 | `et0_mm` | Estimated from NASA sunshine, humidity and wind for the area; local wind or sea breeze can change it. | 〃 |
| I-03 | `water_balance_mm` | Rain minus the water the air asks for; irrigation, runoff and water stored in your soil are not counted. | 〃 |
| I-04 | `soil_wetness` | Model estimate for the area, not a measurement; use it to compare months, not to decide when to irrigate. | 〃 |
| I-05 | `frost_days` | Days below 0 °C for the area; valley bottoms and hollows can get more frost than shown. | 〃 |
| I-06 | `heat_days` | Days above 35 °C; some crops suffer at lower temperatures when they flower, so heat stress can be higher. | 〃 |
| I-07 | `heavy_rain_days` | Days with 30 mm or more for the area; a local storm can be stronger than the area average. | 〃 |
| I-08 | `ndvi` | Satellite greenness for 2024-2025 only, from a 250 m square that may include other plots. | 〃 |
| I-09 | `likely_bare` | A guess from greenness; stubble, dry grass or a mixed square can be counted wrongly. | 〃 |
| I-10 | `rain_change_pct` | Compares 2016-2025 with 2005-2014; ten years is short, so this is a change, not a proven trend. | 〃 |
| I-11 | `heat_days_change` | Same sentence as I-10. | 〃 |
| Score | `water` | Compares rain in the crop's months (plus some stored winter rain) with a typical need; your soil type and yields are not modelled. | `rotations.SCORE_LIMITS` → `/api/analyze` `score_limits` (in the request language) |
| Score | `soil` | Simple points for nitrogen, organic matter, erosion and pest break from general crop traits, not a soil test. | 〃 |
| Score | `income` | Illustrative only: a low/medium/high market label, not real prices, costs or subsidies. | 〃 |
| Score | `risk` | Frost, heat and dry seasons against general crop tolerances; pests, diseases and market risk are not included. | 〃 |
| Score | `overall` | Weighted by your priorities; it orders the options but does not say which one is best for you. | 〃 |

**Predictions.** P-01, P-02, P-03 and P-07 are in code: `predictions.PREDICTION_LIMITS` → `limits` in the predictions payload (`GET /api/predictions`), keyed like the payload, in English and Spanish. Wording follows the caveats in [indicators.md → Predictions](indicators.md#predictions-p-01p-07--statistics-over-nasa-history-not-ai). Every card also carries the `basis` line ("Not a weather forecast").

| ID | Key | Limit (English; Spanish in code) |
|---|---|---|
| P-01 | `rain_weeks` | Share of the past 21 years (2005-2025) with rain in that week; it does not forecast this year's weather. |
| P-02 | `heavy_rain` | Rain averaged over an area of about 50 km and only 21 years of data: local storms can be stronger, and storms rarer than once in 10 years are not estimated. |
| P-03 | `frost` | Air temperature for the area; ground frost and cold valley bottoms can freeze later in spring and harder than shown. |
| P-07 | `alerts` | Heavy-rain days often fall when the field is bare; this is a warning sign, not measured soil loss, and your field may be covered differently this year. |
| P-04 *(stretch, not built)* | — | Draft: a 20-year slope with its confidence interval; if the interval includes zero we cannot say the climate is changing. |
| P-05 *(stretch, not built)* | — | Draft: compares this season's rain with the last 20 years for the area; the most recent days of NASA data may be missing. |
| P-06 *(stretch, not built)* | — | Draft: combines rain and frost odds with general crop limits; soil condition and local advice decide the real sowing date. |

The general statements (`climate.LIMITS`, `rotations.DISCLAIMER`) stay as they are, at the end of the results.

## Heavy-rain warnings on this phone (#42) — privacy note
**Built (stretch, Sprint 3):** after a tap on "🔔 Warn me when this risk is near" in the P-07 alert card, the PWA shows **local notifications** with `registration.showNotification()` from the page. There is **no push server, no push subscription, no VAPID key**, and nothing about the farmer or the field is sent anywhere because of this feature. Code: `web/js/notify.js` (loaded on demand), `web/js/notify-format.js` (pure rules, tested in `tests/web/notify.test.mjs`), `notificationclick` in `web/sw.js`.

- **Permission** is asked only from that tap, with the reason next to the button ("Nothing is sent to us"); never on page load. Blocked, unsupported (e.g. iPhone Safari not added to the Home Screen, iOS < 16.4) and on/off states are explained in words. No consent record is needed beyond the browser's own permission, since there is no subscription.
- **Rule:** when FarmLens is opened (or What to expect loads, also from cached predictions offline), for each field with warnings on, if `alerts[]` has the current or the next month → one notification per field per alerted month. Text: P-07 wording, level as a word, year counts, "Based on NASA history, not a forecast". A tap opens What to expect for that field.
- **Limit:** a local notification can only be shown while FarmLens runs, so warnings come **when the farmer opens the app**, not at a set date. Reminders with the app closed would need Web Push (a push server and a subscription) or Periodic Background Sync (Chrome only, installed app, not guaranteed) — a possible next step, with explicit consent, not built.

**Stored on the phone only** (`localStorage`, key `farmlens-warnings-v1`; removed with "Turn off" or by clearing the site data):

| What | Why |
|---|---|
| Field key: demo field slug, or the map point rounded to 2 decimals (~1 km) | Identify the field the warning is for |
| Field label (demo field name or "your point (lat, lon)") | Notification title |
| The answers of that analysis (rotation, priorities, irrigation, slope) | Open the same results again when the notification is tapped |
| Alert months of P-07 (month, share of years, years, level) | Decide offline which months are near |
| Dedupe keys `<field key>\|YYYY-MM` of warnings already shown (pruned after ~13 months) | One notification per field per month |

No name, contact, account, device identifier or precise location beyond the point the farmer chose is stored. The same answers and point are already kept by the service worker for offline results (#14).

## Known limitations
- NASA POWER is modelled/derived data on a ~50 km grid: describes the area, not the plot.
- `GWETROOT` is model-based root-zone wetness, not satellite-measured soil moisture.
- MODIS NDVI: only 2024–2025, 250 m pixels may mix several plots.
- Market value of crops is illustrative.
- Hosted demo: disk resets on restart (DB rebuilt from seed; saved analyses lost).
- Thresholds are team assumptions documented in [indicators.md](indicators.md): frost Tmin < 0 °C, heat Tmax > 35 °C, heavy rain ≥ 30 mm/day, likely bare NDVI < 0.25. None is crop-specific.
- ET0 is FAO-56 Penman-Monteith from NASA POWER radiation, humidity and wind (Hargreaves only as a fallback for missing days); still a ~50 km cell value.
- Rotation scores use simple, documented rules ([indicators.md → Scoring](indicators.md#scoring-shape-2-scores)): rain in the crop's months vs its seasonal water need; stored soil water, yields and real prices are not modelled. `income` is illustrative.
- Uncertainty statements for the UI (English and Spanish): `climate.LIMITS`, returned in every profile as `limits`; one sentence per value in `field_limits` and `score_limits` (see above).
- Coastal grid cells (Málaga city, Cártama): no heat days and an urban MODIS pixel in the city; the demo field should be inland farmland (e.g. Vega de Antequera).
