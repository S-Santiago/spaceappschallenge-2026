# Indicator catalog

Every number the tool shows that is derived from data must be defined here **before** it is implemented (skill `/agro-indicator`). This is our evidence for the **Validity** criterion. Definitions agreed in issue #9 (owner @HaoJunnnzhang); implementation in `src/fieldshift/climate.py`; output = Shape 1 in `docs/work-plan.md`.

Common to all POWER-based indicators: source NASA POWER daily point API (`community=AG`), period 2005–2025, MERRA-2 reanalysis on a ~0.5° × 0.625° grid → describes the **area around the field (~50 km cell)**, not the plot itself.

| ID | Field | Plain meaning | Formula / rule | Unit | Threshold origin | Reviewed | Implemented |
|---|---|---|---|---|---|---|---|
| I-01 | `rain_mm` | How much it rains in a typical month | mean monthly Σ `PRECTOTCORR` | mm | — | no | pending |
| I-02 | `et0_mm` | How much water the air "asks" from the field | FAO-56 Hargreaves, Ra from latitude (FAO-56 eq. 21) | mm | FAO-56 | no | pending |
| I-03 | `water_balance_mm` | Is there spare water or a deficit? | `rain_mm − et0_mm` | mm | — | no | pending |
| I-04 | `soil_wetness` | How wet the root zone is (estimate) | mean `GWETROOT` | 0–1 | model output, not a measurement | no | pending |
| I-05 | `frost_days` | Days with frost | days `T2M_MIN < 0 °C` | days/month | freezing point | no | pending |
| I-06 | `heat_days` | Very hot days | days `T2M_MAX > 35 °C` | days/month | _TODO: cite source for 35 °C_ | no | pending |
| I-07 | `heavy_rain_days` | Days with storms that wash soil away | days `PRECTOTCORR ≥ 30 mm` | days/month | _TODO: cite source for 30 mm_ | no | pending |
| I-08 | `ndvi` | How green the field is | mean MOD13Q1 NDVI per month, 2024–2025, 250 m pixel | 0–1 | — | no | pending |
| I-09 | `likely_bare` | Is the field probably bare? | `ndvi < threshold` | yes/no | _TODO: threshold + justification_ | no | pending |
| I-10 | `trends.rain_change_pct` | Is it raining less than before? | mean annual rain 2016–2025 vs 2005–2014 | % | — | no | pending |
| I-11 | `trends.heat_days_change` | Are there more very hot days? | mean annual heat days 2016–2025 − 2005–2014 | days/year | — | no | pending |

## Limits to show in the UI
- POWER: modelled/derived data for a ~50 km cell; local microclimate (valleys, slopes) is not captured.
- `soil_wetness`: model estimate (MERRA-2), not satellite-measured soil moisture.
- NDVI: only two years (2024–2025); a 250 m pixel can mix several plots.
- 10-year vs 10-year comparison shows a change, not a proven long-term climate trend.

## Scoring (Shape 2 `scores`)
_TODO (issue #10/#11, @HaoJunnnzhang): define each sub-score (`water`, `soil`, `income`, `risk`) — inputs, formula, weights — and how farmer priorities change the `overall` weights. `income` relies on `market_value_illustrative` and must be labeled illustrative._
