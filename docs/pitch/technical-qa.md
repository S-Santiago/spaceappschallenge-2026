# Technical Q&A notes (jury)

Short answers for the Málaga pitch Q&A (#44). Numbers are for the demo fields and come from our own runs on the committed NASA samples (`data/samples/`, 2026-11-14). **Status words:** *built* = in `main` and tested · *planned* = issue open, not built yet.

## Methods — "How does it work?"
- **Data in (built):** NASA POWER daily point API, 2005–2025: max/min temperature, corrected rain, root-zone soil wetness, solar radiation, dew point, wind. MODIS MOD13Q1 NDVI (250 m), 2024–2025, through the ORNL DAAC web service. Neither needs a login or an API key.
- **Climate profile (built, `climate.py`):** 11 indicators per calendar month (I-01…I-11 in `docs/indicators.md`): rain, reference evapotranspiration (ET₀), water balance, soil wetness, frost / heat / heavy-rain days, greenness, likely-bare months, and a decade comparison.
- **ET₀ (built):** FAO-56 Penman-Monteith from POWER radiation, humidity and wind. Hargreaves (temperature only) is used only for days missing those. Checked against FAO-56 worked examples 8 (Ra) and 18 (ET₀). Hargreaves alone gave ~755 mm/yr in Málaga city; Penman-Monteith gives ~1,264 mm/yr, in the range published for the coast.
- **Rotation engine (built, `rotations.py`):** takes the farmer's current rotation and builds alternatives (legume break, cover crop, water-saving swap, forage/diversification). Each strategy gets four 0–100 scores (water, soil, income, risk) and an overall score weighted by the farmer's priorities. Rules are simple and written down in `docs/indicators.md → Scoring`.
- **Predictions (built, `predictions.py`):** statistics over 21 years of NASA data, **no AI or machine learning**, always labelled "not a weather forecast". P-01: chance of rain in each week. P-02: chance of a heavy-rain day (≥ 20 mm) in each month, and the rain expected once every 2, 5 and 10 years (Gumbel distribution fitted by L-moments). P-03: last spring and first autumn frost dates (percentiles). P-07: alerts when heavy rain usually comes while the field is bare.
- **Example, Vega de Antequera:** last spring frost by 14 March in 19 of 21 years. Heavy rain expected once every 10 years: ~48 mm in a day; the largest day in 21 years was 52.7 mm (13 Nov 2024, the DANA storm), so the data catches real events. Wettest week for useful rain (≥ 10 mm): from 29 October, in 62 % of years.
- **"Why 20 mm for predictions but 30 mm in the climate calendar?"** P-02 uses the international ETCCDI "very heavy rain" index (R20mm) so its probabilities are comparable; the calendar's 30 mm (I-07) is a stricter team rule for erosive storms. Both are documented in `docs/indicators.md`.
- **Tests (built):** 128 pytest tests, including hand-checked values and the FAO-56 examples.

## Why these thresholds?
| Threshold | Why | Honest caveat |
|---|---|---|
| Frost: Tmin < 0 °C | Freezing point; same rule as the ETCCDI frost-day index | Area value; frost hollows get more |
| Heat: Tmax > 35 °C | Simple team rule for very hot days | Not crop-specific; wheat suffers at lower temperatures when it flowers |
| Heavy rain: ≥ 30 mm/day | Targets erosive Mediterranean storms (ETCCDI R20mm uses 20 mm) | Team assumption, indicative |
| Likely bare: NDVI < 0.25 | Bare soil ≈ 0.1–0.2, dense crops > 0.5 | Stubble and dry grass can confuse it |
| Effective rain 0.8, stored water 100 mm/m of roots | Simple FAO-56-style soil-water idea | Not calibrated to the plot's soil |

All of these are team assumptions, documented with sources in `docs/indicators.md`. An agronomist has not reviewed them yet; that is the first next step.

## What the data cannot tell (say it before they ask)
- **It is about the area, not the plot.** POWER is a model/reanalysis grid cell of about 55 km; it does not see valleys, slopes or sea breeze.
- **Soil wetness is a model value** (`GWETROOT`), not a satellite measurement.
- **Greenness covers only 2024–2025,** and a 250 m pixel can mix several plots.
- **Ten years against ten years is a change, not a proven climate trend.** Example: Vega de Antequera had 14.6 % less rain and 13 more days above 35 °C per year in 2016–2025 than in 2005–2014.
- **Income is illustrative:** a low/medium/high label, not real prices.
- **Not a forecast:** everything is "based on 21 years of NASA data (2005–2025), not a weather forecast".
- Every value and prediction has its own one-line limit, in English and Spanish (`docs/architecture.md`).

## Demo-field numbers (2005–2025 means)
| Field | Rain mm/yr | ET₀ mm/yr | Frost days/yr | Days > 35 °C/yr | Rain change | Heat-day change |
|---|---|---|---|---|---|---|
| Vega de Antequera (37.03, −4.64) | 442 | 1,385 | 4.0 | 21.9 | −14.6 % | +13.2 |
| Campillos (37.07, −4.87) | 493 | 1,411 | 8.5 | 38.5 | −9.3 % | +14.5 |
| Guadalhorce valley (36.72, −4.67) | 486 | 1,264 | 0 | 0 | −14.2 % | 0 |

Takeaway: the air asks for about three times more water than the rain gives. That is why water and drought tolerance weigh so much in the strategies.

## Why not other NASA data? ("Why not SMAP?")
SMAP soil moisture, GPM IMERG rain, ECOSTRESS and Landsat need an Earthdata login, big files or more processing than a 2-day build allows. Instead we use POWER `GWETROOT`, `PRECTOTCORR` and POWER-based Penman-Monteith ET₀. The full list with reasons is in `docs/nasa-data.md → Official resources not used`. A good next step is SMAP for a soil-moisture check.

## Security and privacy ("How do you handle data and keys?")
- The NASA APIs we use need **no keys**, so there are no secrets in the repository. Anything secret would go in `.env`, which git ignores.
- **No personal data.** An analysis stores only the field inputs (rotation, priorities, irrigation, slope) and coordinates rounded to 2 decimals (~1 km). No names, accounts or phone numbers.
- The API checks every input (Pydantic models): unknown crops or fields are rejected with 422/404.
- `/security-review` was run on the engine branch with no findings. It runs again before the demo goes public.
- Demo fields work offline: their NASA data is pre-loaded, so the demo does not depend on NASA being reachable.

## Science lens ("Is it sound? What is the resolution?")
- POWER meteorology: ½° × ⅝° (≈ 55 km at Málaga), MERRA-2 reanalysis, API v2.10.3. MODIS: 250 m, 16-day composites (MOD13Q1 v061).
- Methods follow FAO-56 (Allen et al., 1998). The threshold sources are in `docs/indicators.md`.
- What would make it stronger: an agronomist's review of the thresholds, a check against an AEMET or Junta de Andalucía station near Antequera, and real crop prices.

## Team lens ("How did you split the work? What did you learn?")
Work was split in Scrum sprints (`docs/sprint-plan.md`): PWA, API and data, data analysis, Scrum/UX/docs. AI use (Claude Code only, for code and documents, never inside the app) is declared in `docs/ai-usage.md`, and every AI output was checked by tests or by hand.
