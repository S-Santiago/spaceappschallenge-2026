---
name: agro-indicator
description: Compute an agroclimatic indicator (frost days, heat-stress days, growing degree days, reference evapotranspiration, water balance, dry spells, extreme rain days, anomalies vs a baseline, bare-field periods) from NASA data with a documented formula, unit, source and limits, and express the result in farmer-friendly words. Use whenever the tool needs a number derived from climate or satellite data.
---

# Agro indicator

Argument: indicator name (or a new one to define) and the input dataset (e.g. a NASA POWER cache in `data/samples/`).

## 1. Catalog first
Open `docs/indicators.md`. If the indicator exists, implement/reuse it **exactly as defined there**. If it is new, add it to the catalog first (all fields below) and only then implement it. Never use an undocumented formula.

Each catalog entry must have: **ID · name · plain-language meaning · formula · inputs (dataset + variables) · unit · time aggregation · thresholds and where they come from · source/reference · limits · farmer-friendly sentence template**.

## 2. Team definitions (issue #9 — these are the agreed ones)
Monthly values are the **2005–2025 mean** of each calendar month (NASA POWER); NDVI uses 2024–2025 (MODIS).

| ID | Shape 1 field | Definition |
|---|---|---|
| I-01 | `rain_mm` | Mean monthly sum of `PRECTOTCORR` (mm) |
| I-02 | `et0_mm` | Reference evapotranspiration, FAO-56 **Hargreaves**: 0.0023·(Tmean+17.8)·(Tmax−Tmin)^0.5·Ra, with Ra (extraterrestrial radiation, mm/day equivalent) computed from latitude and day of year (FAO-56 eq. 21); Tmean = (Tmax+Tmin)/2. Monthly sum (mm) |
| I-03 | `water_balance_mm` | `rain_mm − et0_mm` (negative = deficit) |
| I-04 | `soil_wetness` | Mean `GWETROOT` (0–1, **model-based root-zone wetness**, not a satellite measurement) |
| I-05 | `frost_days` | Mean number of days per month with `T2M_MIN < 0 °C` |
| I-06 | `heat_days` | Mean number of days per month with `T2M_MAX > 35 °C` |
| I-07 | `heavy_rain_days` | Mean number of days per month with `PRECTOTCORR ≥ 30 mm` (erosion risk) |
| I-08 | `ndvi` | Mean MODIS MOD13Q1 NDVI of the composites falling in that month (2024–2025) |
| I-09 | `likely_bare` | `ndvi` below a documented threshold (assumption — justify the value in the catalog) |
| I-10 | `trends.rain_change_pct` | Annual rain, mean 2016–2025 vs mean 2005–2014, in % |
| I-11 | `trends.heat_days_change` | Annual heat days, mean 2016–2025 minus mean 2005–2014 |

Optional later (only if time): crop-specific heat thresholds, growing degree days, dry spells, frost-free season. Add them to the catalog first.

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
