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
Implemented in `src/fieldshift/rotations.py` (issue #10). All sub-scores are 0–100, **higher = better for the farmer**. Inputs: Shape 1 profile, crop traits from `data/crops.csv`, farmer inputs (rotation of 1–4 crops, priorities, irrigation yes/no, slope flat/moderate/steep). These are **team assumptions, indicative, not reviewed** by an agronomist yet.

**Crop season and rain coverage.** A crop occupies the months from `sow_month` to `harvest_month` (wrapping over New Year). *Rain coverage* = Σ `rain_mm` (I-01) over those months ÷ mean of `water_need_mm_min/max`, capped at 1. Fallow = 1.

| Score | Formula | Notes |
|---|---|---|
| `water` | 100 × mean rain coverage of the main crops; a cover crop counts with weight 0.5 | Rain-fed: how much of the crop's need rain provides. Irrigated: the rest must be irrigated, so a low score = more irrigation water |
| `soil` | nitrogen (25) + organic matter (25) + erosion (30) + pest break (20) | see below |
| ↳ nitrogen | 25 if a main crop has `n_fixing = yes`; 15 if only the cover crop does; else 0 | |
| ↳ organic matter | 25 × mean `residue_organic_matter` (low 0, medium 0.5, high 1); +5 with a cover crop (max 25) | |
| ↳ erosion | 30 × (1 − min(1, exposure × slope factor)). Exposure = share of the cycle's heavy-rain days (I-07) that fall in bare months (falls back to `rain_mm` if a site has no heavy-rain days). Slope factor: flat 0.5, moderate 0.75, steep 1 | Bare months over a cycle = for each year, the months outside the crop's window, minus the cover crop's months |
| ↳ pest break | 20 × (1 − share of consecutive years, cyclic, with the same botanical family); a 1-year rotation (monoculture) = 0 | |
| `income` | mean of `market_value_illustrative` (low 20, medium 50, high 80); fallow 0 | **Illustrative only** — must be labeled as such; real prices go under information gaps |
| `risk` | mean over years of 100 − penalties. Frost (I-05) / heat (I-06) days in the crop's season: low tolerance & > 1 day → −30; medium & > 5 days → −15. Rain-fed only, rain coverage < 50 %: drought tolerance low −30, medium −15, high −5 | Higher = lower climate risk |
| `overall` | weighted mean of the four scores; weights = farmer priorities 0–3 each (default 1; all 0 → equal) | Changes the order of alternatives, not the sub-scores |

**UI words:** ≥ 67 good · 34–66 neutral · < 34 poor (`rotations.label`).

**Candidates.** A crop can be proposed only if its penalties add up to < 30 (so, e.g., thirsty crops are excluded when rain-fed). Strategy kinds:
- `legume_break`: replace one year (or add one, up to 4 years) with a suitable legume.
- `cover_crop`: same main crops + a `type = cover` crop whose whole window fits between a harvest and the next sowing.
- `water_saving`: replace the crop with the highest water need by a suitable crop with `drought_tolerance = high` and a lower water need.
- `forage_diversification`: replace or add a forage crop from a family not in the current rotation.

The best variant of each kind is chosen by `overall`; the engine returns the current rotation + the 3 best kinds, never repeating a rotation. Alternatives are listed by score but never called "the best" in the UI.

