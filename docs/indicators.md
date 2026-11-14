# Indicator catalog

Every number the tool shows that is derived from data must be defined here **before** it is implemented (skill `/agro-indicator`). This is our evidence for the **Validity** criterion. Definitions agreed in issue #9 (owner @HaoJunnnzhang); implementation in `src/fieldshift/climate.py`; output = Shape 1 in `docs/work-plan.md`.

Common to all POWER-based indicators: source NASA POWER daily point API (`community=AG`), period 2005–2025, MERRA-2 reanalysis on a ~0.5° × 0.625° grid → describes the **area around the field (~50 km cell)**, not the plot itself.

| ID | Field | Plain meaning | Formula / rule | Unit | Threshold origin | Reviewed | Implemented |
|---|---|---|---|---|---|---|---|
| I-01 | `rain_mm` | How much it rains in a typical month | mean monthly Σ `PRECTOTCORR` | mm | — | no | ✅ `climate.py` |
| I-02 | `et0_mm` | How much water the air "asks" from the field | FAO-56 Hargreaves, Ra from latitude (FAO-56 eq. 21) | mm | FAO-56 | no | ✅ `climate.py` |
| I-03 | `water_balance_mm` | Is there spare water or a deficit? | `rain_mm − et0_mm` | mm | — | no | ✅ `climate.py` |
| I-04 | `soil_wetness` | How wet the root zone is (estimate) | mean `GWETROOT` | 0–1 | model output, not a measurement | no | ✅ `climate.py` |
| I-05 | `frost_days` | Days with frost | days `T2M_MIN < 0 °C` | days/month | freezing point | no | ✅ `climate.py` |
| I-06 | `heat_days` | Very hot days | days `T2M_MAX > 35 °C` | days/month | Common crop heat-stress threshold: critical Tmax for most field crops lies around 32–38 °C (Teixeira et al. 2013, *Agric. For. Meteorol.* 170:206–215 — to be checked); 35 °C is a team simplification, not crop-specific | no | ✅ `climate.py` |
| I-07 | `heavy_rain_days` | Days with storms that wash soil away | days `PRECTOTCORR ≥ 30 mm` | days/month | Team assumption. ETCCDI's standard index R20mm uses ≥20 mm for "very heavy" rain days; we use 30 mm to target erosive events in Mediterranean storms. Indicative | no | ✅ `climate.py` |
| I-08 | `ndvi` | How green the field is | mean MOD13Q1 NDVI per month, 2024–2025, 250 m pixel | 0–1 | — | no | ✅ `climate.py` |
| I-09 | `likely_bare` | Is the field probably bare? | `ndvi < 0.25` | yes/no | Assumption: bare soil typically shows NDVI ≈ 0.1–0.2 and dense green crops > 0.5; 0.25 also flags stubble/very sparse cover. Indicative, to be checked against a known field | no | ✅ `climate.py` |
| I-10 | `trends.rain_change_pct` | Is it raining less than before? | mean annual rain 2016–2025 vs 2005–2014 | % | — | no | ✅ `climate.py` |
| I-11 | `trends.heat_days_change` | Are there more very hot days? | mean annual heat days 2016–2025 − 2005–2014 | days/year | — | no | ✅ `climate.py` |

## Implementation notes (`src/fieldshift/climate.py`)
- Monthly values: computed per month-year, then averaged over 2005–2025 for each calendar month.
- Missing data: a month-year is skipped for a variable when more than 10 % of its days are missing; with ≤ 10 % missing, sums and day counts are rescaled to the full month. `quality.missing_days` and `quality.skipped_month_years` are returned with the profile (extra field, not used by the UI).
- Ra (I-02) follows FAO-56 eqs. 21–25 and is converted to mm/day with ×0.408; checked against FAO-56 example 8 (20° S, 3 Sep → 32.2 MJ m⁻² day⁻¹).
- NDVI (I-08): each 16-day MODIS composite is assigned to the month of its start date.
- Trends (I-10, I-11): only complete years count; 2015 belongs to neither decade.
- If MODIS fails, the profile is still built with `ndvi` and `likely_bare` set to `null`.

## Limits to show in the UI
- POWER: modelled/derived data for a ~50 km cell; local microclimate (valleys, slopes) is not captured.
- `soil_wetness`: model estimate (MERRA-2), not satellite-measured soil moisture.
- NDVI: only two years (2024–2025); a 250 m pixel can mix several plots.
- 10-year vs 10-year comparison shows a change, not a proven long-term climate trend.
- Hargreaves ET0 depends on the day–night temperature range; on coastal grid cells (small range) it can underestimate ET0 (Málaga demo: ~755 mm/year).

## Scoring (Shape 2 `scores`)
_TODO (issue #10/#11, @HaoJunnnzhang): define each sub-score (`water`, `soil`, `income`, `risk`) — inputs, formula, weights — and how farmer priorities change the `overall` weights. `income` relies on `market_value_illustrative` and must be labeled illustrative._
