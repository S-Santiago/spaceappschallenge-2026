# Indicator catalog

Every number the tool shows that is derived from data must be defined here **before** it is implemented (skill `/agro-indicator`). This is our evidence for the **Validity** criterion. Definitions agreed in issue #9 (owner @HaoJunnnzhang); implementation in `src/fieldshift/climate.py`; output = Shape 1 in `docs/work-plan.md`.

Common to all POWER-based indicators: source NASA POWER daily point API (`community=AG`), period 2005–2025, MERRA-2 reanalysis on a ~0.5° × 0.625° grid → describes the **area around the field (~50 km cell)**, not the plot itself.

| ID | Field | Plain meaning | Formula / rule | Unit | Threshold origin | Reviewed | Implemented |
|---|---|---|---|---|---|---|---|
| I-01 | `rain_mm` | How much it rains in a typical month | mean monthly Σ `PRECTOTCORR` | mm | — | no | ✅ `climate.py` |
| I-02 | `et0_mm` | How much water the air "asks" from the field | FAO-56 **Penman-Monteith** (eq. 6, G = 0) from POWER `T2M_MAX`, `T2M_MIN`, `ALLSKY_SFC_SW_DWN` (MJ m⁻² day⁻¹), `T2MDEW` (→ ea, eq. 14), `WS2M` (m/s), elevation of the POWER cell; Ra from latitude (eq. 21). Falls back to FAO-56 Hargreaves (eq. 52) on days missing radiation/humidity/wind; the count is in `quality.et0_method`. Checked against FAO-56 example 18 (3.9 mm/day) | mm | FAO-56 (Allen et al. 1998). Málaga city ≈ 1,264 mm/yr, Vega de Antequera ≈ 1,385 mm/yr | no | ✅ `climate.py` |
| I-03 | `water_balance_mm` | Is there spare water or a deficit? | `rain_mm − et0_mm` | mm | — | no | ✅ `climate.py` |
| I-04 | `soil_wetness` | How wet the root zone is (estimate) | mean `GWETROOT` | 0–1 | model output, not a measurement | no | ✅ `climate.py` |
| I-05 | `frost_days` | Days with frost | days `T2M_MIN < 0 °C` | days/month | Freezing point; same rule as the ETCCDI frost-day index (FD). A 50 km cell undercounts frost in valley bottoms | no | ✅ `climate.py` |
| I-06 | `heat_days` | Very hot days | days `T2M_MAX > 35 °C` | days/month | Team simplification, not crop-specific. Teixeira et al. 2013 (*Agric. For. Meteorol.* 170:206–215) use crop-specific critical Tmax during flowering (reportedly ~27 °C wheat, ~35 °C maize/soybean — **to verify in the paper**); 35 °C therefore underestimates heat stress for wheat in May–June | no | ✅ `climate.py` |
| I-07 | `heavy_rain_days` | Days with storms that wash soil away | days `PRECTOTCORR ≥ 30 mm` | days/month | Team assumption. ETCCDI's standard index R20mm uses ≥20 mm for "very heavy" rain days; we use 30 mm to target erosive events in Mediterranean storms. Indicative | no | ✅ `climate.py` |
| I-08 | `ndvi` | How green the field is | mean MOD13Q1 NDVI per month, 2024–2025, 250 m pixel | 0–1 | — | no | ✅ `climate.py` |
| I-09 | `likely_bare` | Is the field probably bare? | `ndvi < 0.25` | yes/no | Assumption: bare soil typically shows NDVI ≈ 0.1–0.2 and dense green crops > 0.5; 0.25 also flags stubble/very sparse cover. Indicative, to be checked against a known field | no | ✅ `climate.py` |
| I-10 | `trends.rain_change_pct` | Is it raining less than before? | mean annual rain 2016–2025 vs 2005–2014 | % | — | no | ✅ `climate.py` |
| I-11 | `trends.heat_days_change` | Are there more very hot days? | mean annual heat days 2016–2025 − 2005–2014 | days/year | — | no | ✅ `climate.py` |

## Implementation notes (`src/fieldshift/climate.py`)
- Monthly values: computed per month-year, then averaged over 2005–2025 for each calendar month.
- Missing data: a month-year is skipped for a variable when more than 10 % of its days are missing; with ≤ 10 % missing, sums and day counts are rescaled to the full month. `quality.missing_days` and `quality.skipped_month_years` are returned with the profile (extra field, not used by the UI).
- Ra (I-02) follows FAO-56 eqs. 21–25; checked against FAO-56 example 8 (20° S, 3 Sep → 32.2 MJ m⁻² day⁻¹). Penman-Monteith checked against FAO-56 example 18. Hargreaves (temperature only) gave ~755 mm/yr in Málaga city because the coastal cell has a small day–night range; Penman-Monteith with POWER radiation, humidity and wind fixes this.
- NDVI (I-08): each 16-day MODIS composite is assigned to the month of its start date.
- Trends (I-10, I-11): only complete years count; 2015 belongs to neither decade.
- If MODIS fails, the profile is still built with `ndvi` and `likely_bare` set to `null`.

## Limits to show in the UI
Farmer-friendly versions in English and Spanish are returned in the profile as `limits` = `{"en": [...], "es": [...]}` (`climate.LIMITS`). One sentence per indicator is returned as `field_limits` = `{"rain_mm": {"en": ..., "es": ...}, ...}` (`climate.FIELD_LIMITS`) and one per score as `score_limits` in `/api/analyze` (`rotations.SCORE_LIMITS`); full table in [architecture.md](architecture.md#limits-per-value-shown-to-the-farmer-44).
- ET0 uses POWER radiation, humidity and wind for a ~50 km cell; local wind and sea breeze are not captured.
- POWER: modelled/derived data for a ~50 km cell; local microclimate (valleys, slopes) is not captured.
- `soil_wetness`: model estimate (MERRA-2), not satellite-measured soil moisture.
- NDVI: only two years (2024–2025); a 250 m pixel can mix several plots.
- 10-year vs 10-year comparison shows a change, not a proven long-term climate trend.

## Predictions (P-01…P-07) — statistics over NASA history, not AI
Defined for issues #37/#38 (owner today @sebasbarrabaja-cmyk). Code: `src/fieldshift/predictions.py`; tests: `tests/test_predictions.py`. Input: NASA POWER daily data 2005–2025 for the field's cell (same payload as I-01…I-11), plus MODIS NDVI for P-07. **Always shown as "based on the last 20 years of NASA data", never as a weather forecast.** Must-have: P-01, P-02, P-03, P-07 · stretch: P-04, P-05, P-06.

| ID | Field | Plain meaning | Method | Unit | Threshold origin | Status |
|---|---|---|---|---|---|---|
| P-01 | `rain_weeks[]` | How likely it is to rain in each week of the year | For each of 52 weeks (week 1 = 1–7 Jan; days 365–366 in week 52) and each year: rainy if any day `PRECTOTCORR ≥ 1 mm`; useful rain if the weekly total ≥ 10 mm. `prob_rain`, `prob_useful_rain` = share of years; `mean_rain_mm` = mean weekly total. A week-year with any missing day is skipped | 0–1, mm | 1 mm = ETCCDI wet-day threshold. 10 mm/week: team assumption for rain that wets the topsoil enough for sowing/germination. Indicative | ✅ implemented |
| P-02 | `heavy_rain` | How likely a storm is each month, and how often a very big one comes | Monthly share of years with ≥ 1 day ≥ 30 mm (same threshold as I-07); return period of the yearly maximum daily rain from a Gumbel fit (method of moments) → "a storm of X mm comes about once every N years" | 0–1, mm, years | 30 mm as I-07. Gumbel = standard extreme-value method in hydrology; 21 years limits the reliability beyond ~10-year return periods | #38 |
| P-03 | `frost` | When frosts usually stop in spring and start in autumn | Per year: last day with `T2M_MIN < 0 °C` in Jan–Jun and first in Jul–Dec. Years without frost count as "no frost" (earliest for spring, latest for autumn). Spring: median and **90th percentile** of the last-frost date; autumn: median and **10th percentile** of the first-frost date; `safe_days` = days between them. Half-years with > 10 % missing Tmin are skipped | date (MM-DD), 0–1, days | Freezing point as I-05. 9-in-10 years = common agro-climatic planning risk level. Air Tmin at 2 m for a ~50 km cell: ground frost in valley bottoms can happen with Tmin above 0 °C → real risk is higher | ✅ implemented |
| P-04 *(stretch)* | `trends` | Is it getting hotter / drier, and how sure are we | Sen's slope per decade of annual rain and heat days, with a 95 % confidence interval (Mann-Kendall) | mm/decade, days/decade | Standard non-parametric trend method; 21 years is short → wide intervals | stretch |
| P-05 *(stretch)* | `dryness` | Is this season drier than usual | Rain accumulated since 1 September vs the same window in past years → percentile (SPI-style, empirical) | percentile | Empirical percentile instead of a fitted SPI because of the short record | stretch |
| P-06 *(stretch)* | `sowing_window` | Best weeks to sow each crop | Weeks after `last_frost_p90` (P-03) and with `prob_useful_rain` (P-01) ≥ 0.5 within the crop's sowing months (`data/crops.csv`) | weeks | Combines P-01, P-03 and the crop catalogue | stretch |
| P-07 | `alerts[]` | When heavy rain usually hits while the field is bare | Months with `likely_bare` (I-09) **and** P-02 monthly storm probability ≥ 0.2 → alert card "high erosion risk"; slope from the farmer increases the level | list of months + level | Supervisor request. 0.2 = at least 1 year in 5: team assumption | #38 |

**Farmer sentences (UI, P-01 and P-03):**
- P-01: "In the week of 26 Nov it rained in **76 %** of the last 21 years (**43 %** with more than 10 mm)."
- P-03 spring: "In **9 out of 10** years the last frost came **before 14 March**." · No frost: "No frost in the last 21 years at this place."
- P-03 autumn: "In **9 out of 10** years the first autumn frost came **after 3 December**."
- Always add: "Based on 21 years of NASA data for an area of about 50 km. Not a weather forecast."

**Real results (demo fields, 2005–2025):** Vega de Antequera — spring frost in 17/21 years, last frost before 14 Mar in 9/10 years; Campillos — same spring date, autumn frost in 15/21 years (first after 28 Nov in 9/10); Guadalhorce valley — no frost in 21 years. Late November: rain in 76 % (inland) to 90 % (Guadalhorce) of years; July: ≤ 5 %.

## Scoring (Shape 2 `scores`)
Implemented in `src/fieldshift/rotations.py` (issue #10). All sub-scores are 0–100, **higher = better for the farmer**. Inputs: Shape 1 profile, crop traits from `data/crops.csv`, farmer inputs (rotation of 1–4 crops, priorities, irrigation yes/no, slope flat/moderate/steep). These are **team assumptions, indicative, not reviewed** by an agronomist yet.

**Crop season and rain coverage.** A crop occupies the months from `sow_month` to `harvest_month` (wrapping over New Year).
- *Stored water* = min(0.5 × Σ `rain_mm` of the 3 months before sowing, 100 mm × `root_depth_m`) — about 100 mm of available water per metre of roots (typical loam); rain-fed spring crops in Andalusia live largely on stored winter rain. Team assumption based on the FAO-56 ch. 8 soil-water balance idea.
- *Rain coverage* = (0.8 × Σ `rain_mm` (I-01) over the crop's months + stored water) ÷ mean of `water_need_mm_min/max`, capped at 1. 0.8 is a simple effective-rainfall factor. Fallow = 1.

| Score | Formula | Notes |
|---|---|---|
| `water` | 100 × mean rain coverage of the main crops; a cover crop counts with weight 0.5. Crops with no sourced water need in `data/crops.csv` are left out of the mean (never counted as fully covered); if no crop has one, 50 (unknown). Only crops with a known need can be proposed as `water_saving` | Rain-fed: how much of the crop's need rain provides. Irrigated: the rest must be irrigated, so a low score = more irrigation water |
| `soil` | nitrogen (25) + organic matter (25) + erosion (30) + pest break (20) | see below |
| ↳ nitrogen | 25 if a forage or cover legume is a main crop (biomass stays on the farm); 15 if the only legumes are grain legumes (seed exports most of the fixed N) or a legume cover crop; else 0 | |
| ↳ organic matter | 25 × mean `residue_organic_matter` (low 0, medium 0.5, high 1); +5 with a cover crop (max 25) | |
| ↳ erosion | 30 × (1 − min(1, exposure × slope factor)). Exposure = share of the cycle's heavy-rain days (I-07) that fall in bare months (falls back to `rain_mm` if a site has no heavy-rain days). Slope factor: flat 0.5, moderate 0.75, steep 1 | Bare months over a cycle = for each year, the months outside the crop's window, minus the cover crop's months |
| ↳ pest break | 20 × (1 − share of consecutive years, cyclic, with the same botanical family); a 1-year rotation (monoculture) = 0 | |
| `income` | mean of `market_value_illustrative` (low 20, medium 50, high 80); fallow 0 | **Illustrative only** — must be labeled as such; real prices go under information gaps |
| `risk` | mean over years of 100 − penalties. Frost (I-05) / heat (I-06) days in the crop's season: low tolerance & > 1 day → −30; medium & > 5 days → −15. Rain-fed only, rain coverage < 50 %: drought tolerance low −30, medium −15, high −5 | Higher = lower climate risk |
| `overall` | weighted mean of the four scores; weights = farmer priorities 0–3 each (default 1; all 0 → equal) | Changes the order of alternatives, not the sub-scores |

**UI words:** ≥ 67 good · 34–66 neutral · < 34 poor (`rotations.label`).

**Candidates.** A crop can be proposed only if its penalties add up to < 30 (so, e.g., thirsty crops are excluded when rain-fed). Strategy kinds:
- `legume_break`: replace one year (or add one, up to 4 years) with a suitable legume.
- `cover_crop`: same main crops + a `type = cover` crop whose whole window fits between a harvest and the next sowing; rain-fed, only if its window gets ≥ 100 mm of rain (it competes for water with the next crop).
- `water_saving`: replace the crop with the highest water need by a suitable crop with `drought_tolerance = high` and a lower water need.
- `forage_diversification`: replace or add a forage crop from a family not in the current rotation.

Extra risk line (no score change): a legume that comes back in fewer than 3 years (soil diseases such as Ascochyta, Fusarium).

**Language.** `compare(..., lang="en"|"es")` returns all card texts in English or Spanish; numbers never depend on the language. Spanish crop names come from an optional `name_es` column in `data/crops.csv` (falls back to `name`).

The best variant of each kind is chosen by `overall`; the engine returns the current rotation + the 3 best kinds, never repeating a rotation. Alternatives are listed by score but never called "the best" in the UI.

