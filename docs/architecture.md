# Architecture

Stack decided in [decisions/0002-tech-stack.md](decisions/0002-tech-stack.md): **Python 3.11+ · Streamlit · SQLite**. Data contracts (Shape 1, Shape 2) and owners: [work-plan.md](work-plan.md).

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
| Climate indicators → Shape 1 | Python | `src/fieldshift/climate.py` | @HaoJunnnzhang | 🔴 #9 |
| Rotation engine → Shape 2 | Python | `src/fieldshift/rotations.py` | @HaoJunnnzhang | 🔴 #10 |
| Tests | pytest | `tests/` | @HaoJunnnzhang | 🔴 #11 |
| UI | Streamlit | `src/app.py` | @S-Santiago | 🔴 #12 · #13 |
| Hosting | Streamlit Community Cloud | — | @S-Santiago | 🔴 #15 |

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

## Known limitations
- NASA POWER is modelled/derived data on a ~50 km grid: describes the area, not the plot.
- `GWETROOT` is model-based root-zone wetness, not satellite-measured soil moisture.
- MODIS NDVI: only 2024–2025, 250 m pixels may mix several plots.
- Market value of crops is illustrative.
- Hosted demo: disk resets on restart (DB rebuilt from seed; saved analyses lost).
- _More from #11 (thresholds, uncertainty statements)._
