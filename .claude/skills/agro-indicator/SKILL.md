---
name: agro-indicator
description: Compute an agroclimatic indicator (frost days, heat-stress days, growing degree days, reference evapotranspiration, water balance, dry spells, extreme rain days, anomalies vs a baseline, bare-field periods) from NASA data with a documented formula, unit, source and limits, and express the result in farmer-friendly words. Use whenever the tool needs a number derived from climate or satellite data.
---

# Agro indicator

Argument: indicator name (or a new one to define) and the input dataset (e.g. a NASA POWER cache in `data/samples/`).

## 1. Catalog first
Open `docs/indicators.md`. If the indicator exists, implement/reuse it **exactly as defined there**. If it is new, add it to the catalog first (all fields below) and only then implement it. Never use an undocumented formula.

Each catalog entry must have: **ID · name · plain-language meaning · formula · inputs (dataset + variables) · unit · time aggregation · thresholds and where they come from · source/reference · limits · farmer-friendly sentence template**.

## 2. Standard definitions (use these unless the team decides otherwise)
| ID | Indicator | Definition |
|---|---|---|
| I-01 | Frost days | Days with `T2M_MIN < 0 °C` (per month / season / year) |
| I-02 | Heat-stress days | Days with `T2M_MAX >` crop heat threshold from `data/crops.csv` |
| I-03 | Growing degree days | Σ max(0, (Tmax+Tmin)/2 − Tbase), Tbase from `data/crops.csv` |
| I-04 | Reference evapotranspiration (ET₀) | FAO-56 Penman-Monteith if all inputs exist; otherwise FAO-56 Hargreaves: 0.0023·(Tmean+17.8)·(Tmax−Tmin)^0.5·Ra (Ra in mm/day). State which one was used |
| I-05 | Climatic water balance | Precipitation − ET₀ (mm) per month/season |
| I-06 | Dry spells | Longest run of consecutive days with precipitation < 1 mm |
| I-07 | Extreme rain days | Days above the local 95th percentile of wet-day precipitation (erosion risk) |
| I-08 | Anomaly | Value − mean of the same calendar period over a baseline (default 1991–2020); say if the baseline is shorter |
| I-09 | Frost-free season | Days between last spring frost and first autumn frost |
| I-10 | Bare-field periods | Periods where a vegetation index (MODIS/Landsat NDVI) stays below a threshold; threshold is an assumption to state and justify |
| I-11 | Trend | Change per decade (e.g. linear fit / Sen's slope) with the period used; never extrapolate beyond the data |

## 3. Implementation rules
- Inputs come from `src/fieldshift/power.py` (`fetch_daily`) and `src/fieldshift/modis.py` (`fetch_ndvi`). Do not re-download data in this module.
- Code lives in `src/fieldshift/climate.py` (track A in `docs/work-plan.md`), one function per indicator, with a docstring citing the catalog ID.
- The module's public output must match **Shape 1 — climate profile** in `docs/work-plan.md` (`months[]` with `rain_mm`, `et0_mm`, `water_balance_mm`, `soil_wetness`, `frost_days`, `heat_days`, `heavy_rain_days`, `ndvi`, `likely_bare`; `trends`; `sources`). If a field changes, update the shape in `work-plan.md` and warn tracks B and C.
- Handle missing values explicitly (report how many days were missing; skip or flag periods with > 10 % missing).
- Add a tiny test with a hand-checkable example (e.g. 3 days of data → expected frost days).
- Output both the **number with unit** and the **farmer sentence**, e.g. "On average 12 frost days per year, mostly in January (NASA POWER, 1991–2025)".
- Always attach: data source, period, and resolution caveat (grid cell ≈ comarca, not the plot).

## 4. Validity check
For anything non-trivial (thresholds, ET₀ method, NDVI threshold) ask the `agro-domain-advisor` agent to review before showing it in the demo. Mark unreviewed indicators as "indicative".

Answer the team in Spanish; catalog and code in English.
