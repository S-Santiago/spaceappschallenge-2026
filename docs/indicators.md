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
| P-01 | `rain_weeks[]` | How likely it is to rain in each week of the year | For each of 52 weeks (week 1 = 1–7 Jan; **week 52 has 8–9 days**, it absorbs 30–31 Dec — slight upward bias for that week) and each year: rainy if any day `PRECTOTCORR ≥ 1 mm`; useful rain if the weekly total ≥ 10 mm. `prob_rain`, `prob_useful_rain` = share of years; `mean_rain_mm` = mean weekly total. A week-year with any missing day is skipped | 0–1, mm | 1 mm = ETCCDI wet-day threshold (also filters reanalysis drizzle). 10 mm/week: **team assumption, indicative** — no published reference found; start-of-season rules elsewhere are stricter (e.g. ~20 mm in 3 days) | ✅ implemented · agro review: sound |
| P-02 | `heavy_rain` | How likely a storm is each month, and how often a very big one comes | `months[]`: share of years with ≥ 1 day ≥ **20 mm** in that month (ETCCDI R20mm; month-years with > 10 % missing skipped). `return_levels[]`: daily rain reached on average once every **2, 5, 10 years** — Gumbel fitted by **L-moments** on the annual maxima (years with ≤ 10 % missing), with `observed_years` = how many years reached it. `annual_max`: median, largest and its year | 0–1, mm, years | 21 annual maxima of cell-averaged rain (~50 km) **underestimate local storms**; Gumbel can underestimate Mediterranean extremes; no return period beyond 10 years. Check passed: the Oct–Nov 2024 DANA days appear (13 Nov 2024: 52.7 mm in the Antequera cell, its largest day in 21 years) | ✅ implemented |
| P-03 | `frost` | When frosts usually stop in spring and start in autumn | Per year: last day with `T2M_MIN < 0 °C` in Jan–Jun and first in Jul–Dec ("first frost before 31 Dec"). Years without frost count as "no frost" (earliest for spring, latest for autumn). **Nearest-rank** percentiles on observed dates, rounded to the safe side (no interpolation, which could blend a real date with a frost-free year): spring median and ~90th percentile of the last frost, autumn median and ~10th percentile of the first frost; `years_by_p90` / `years_from_p10` give the count ("19 of 21 years"); `safe_days` between them. Half-years with > 10 % missing Tmin are skipped | date (MM-DD), 0–1, days, count | Tmin < 0 °C = AEMET frost-day rule. About 9 in 10 years (19 of 21) = **team choice of risk level**. Air Tmin at 2 m for a ~50 km cell: ground (radiative) frost and cold-air pools in valley bottoms (e.g. Vega de Antequera) can be **later and harder** than shown | ✅ implemented · agro review: plausible with caveats (fixed) |
| P-04 *(stretch)* | `trends` | Is it getting hotter / drier, and how sure are we | Sen's slope per decade of annual rain and heat days, with a 95 % confidence interval (Mann-Kendall) | mm/decade, days/decade | Standard non-parametric trend method; 21 years is short → wide intervals | stretch |
| P-05 *(stretch)* | `dryness` | Is this season drier than usual | Rain accumulated since 1 September vs the same window in past years → percentile (SPI-style, empirical) | percentile | Empirical percentile instead of a fitted SPI because of the short record | stretch |
| P-06 *(stretch)* | `sowing_window` | Best weeks to sow each crop | Weeks after `last_frost_p90` (P-03) and with `prob_useful_rain` (P-01) ≥ 0.5 within the crop's sowing months (`data/crops.csv`) | weeks | Combines P-01, P-03 and the crop catalogue | stretch |
| P-07 | `alerts[]` | When heavy rain usually comes while the field is bare | Month alerted when P-02 `prob` ≥ 0.2 (≥ 1 year in 5) **and** the field is bare by at least one source, listed in `sources`: `satellite` = MODIS `likely_bare` (I-09, 2024–2025) · `crop_calendar` = no crop of the farmer's current rotation occupies that month in at least one year (`rotations.window`, `data/crops.csv`). `level`: high if `prob` ≥ 0.4, else medium; `raise_for_slope` lifts medium → high on steep fields. `null` when neither source is available | months, level | Supervisor request. Satellite alone gave **no alert** in the demo fields: NDVI < 0.25 only in Jul–Sep (no storms), while stubble/weeds keep October NDVI at 0.27–0.32 although the seedbed is bare → the crop calendar is needed. Daily totals are only a proxy for erosivity (RUSLE R): wording "heavy-rain days often fall when the field is bare", not measured erosion | ✅ implemented |

**Farmer sentences (UI, P-01 and P-03)** — use counts of years, not percentiles (21 years is a short record):
- P-01: "In the week of 26 Nov it rained in **16 of the last 21 years** (in 9 of them more than 10 mm)."
- P-03 spring: "In **19 of the last 21 years** the last frost came **on or before 14 March**." · No frost: "No frost in the last 21 years in this area."
- P-03 autumn: "In **19 of the last 21 years** the first frost came **on or after 3 December** (or not at all before the new year)."
- Frost caveat (always with P-03): "Frost near the ground and in valley bottoms can come later and be harder than shown. Check with local experience."
- P-02: "In November, a day with more than 20 mm of rain happened in **11 of the last 21 years**. About once every 5 years a single day brings **42 mm** or more."
- P-07 (alert card): "⚠️ **November · high**: your field is usually bare and heavy rain is common (11 of 21 years). Bare soil can wash away — a cover crop or leaving stubble helps." Show the source: "(crop calendar)" / "(satellite)".
- Always add: "Based on 21 years of NASA data for an area of about 50 km. Not a weather forecast."
- Variants used by the PWA "What to expect" tab (`web/js/expect-format.js`, approved by the frontend owner 2026-11-14): P-01 no rainy year → "In the week of 16 Jul it did not rain in any of the last 21 years."; no year over 10 mm → "(never more than 10 mm)". P-03 frost-free window (`safe_days`) → "That leaves about 264 days without frost in most years, between 14 March and 3 December."; spring/autumn date missing because frost came in fewer than ~1 year in 10 → "In 20 of the last 21 years there was no frost in spring / before the new year." P-02 month with no such day → "In July, no day with more than 20 mm of rain in the last 21 years." P-07 **medium** alert → "Your field is usually bare and heavy rain comes in some years (5 of 21 years)." (high keeps "heavy rain is common"). The tab header and every card say "Based on the last 20 years of NASA data — not a weather forecast."

**Real results P-02/P-07 (2005–2025):** months with a ≥ 20 mm day — November 52 % (Antequera), 62 % (Campillos), 67 % (Guadalhorce); July 0 % everywhere. 5-year daily rain: 42 / 45 / 46 mm. Alerts for the demo rotations (crop calendar): Antequera durum wheat–wheat–sunflower → Oct medium, **Nov high**, Dec–Feb medium (winter before sunflower); Guadalhorce maize–faba bean → **Feb, Mar, Nov high**, Oct and Dec medium.

**Agronomic review (2026-11-14, `agro-domain-advisor`):** P-01 sound; P-03 plausible with caveats → nearest-rank percentiles, year counts and frost caveat applied; P-02 and P-07 methods revised above before coding. Sources checked by the reviewer: AEMET frost-day definition; a third-party climate summary for Antequera (~7 frost days/yr, consistent). Next validation source: AEMET "Mapas de riesgo 2002–2012". Other references cited from memory are marked as such and still to verify.

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

