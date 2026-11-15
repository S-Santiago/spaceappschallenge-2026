# Technical Q&A notes (jury)

Short answers for the Málaga pitch Q&A (#44). Numbers are for the demo fields and come from our own runs on the committed NASA samples (`data/samples/`, rechecked 2026-11-15). **Status words:** *built* = in `main` and tested · *planned* = issue open, not built yet.

## Methods — "How does it work?"
- **Data in (built):** NASA POWER daily point API, 2005–2025: max/min temperature, corrected rain, root-zone soil wetness, solar radiation, dew point, wind. MODIS MOD13Q1 NDVI (250 m), 2024–2025, through the ORNL DAAC web service. Neither needs a login or an API key.
- **Climate profile (built, `climate.py`):** 11 indicators per calendar month (I-01…I-11 in `docs/indicators.md`): rain, reference evapotranspiration (ET₀), water balance, soil wetness, frost / heat / heavy-rain days, greenness, likely-bare months, and a decade comparison.
- **ET₀ (built):** FAO-56 Penman-Monteith from POWER radiation, humidity and wind. Hargreaves (temperature only) is used only for days missing those. Checked against FAO-56 worked examples 8 (Ra) and 18 (ET₀). Hargreaves alone gave ~755 mm/yr in Málaga city; Penman-Monteith gives ~1,264 mm/yr, in the range published for the coast.
- **Rotation engine (built, `rotations.py`):** takes the farmer's current rotation and builds alternatives (legume break, cover crop, water-saving swap, forage/diversification). Each strategy gets four 0–100 scores (water, soil, income, risk) and an overall score weighted by the farmer's priorities. Rules are simple and written down in `docs/indicators.md → Scoring`.
- **Predictions (built, `predictions.py`):** statistics over 21 years of NASA data, **no AI or machine learning**, always labelled "not a weather forecast". P-01: chance of rain in each week. P-02: chance of a heavy-rain day (≥ 20 mm) in each month, and the rain expected once every 2, 5 and 10 years (Gumbel distribution fitted by L-moments). P-03: last spring and first autumn frost dates (percentiles). P-07: alerts when heavy rain usually comes while the field is bare.
- **Example, Vega de Antequera:** last spring frost by 14 March in 19 of 21 years. Heavy rain expected once every 10 years: ~48 mm in a day; the largest day in 21 years was 52.7 mm (13 Nov 2024, the DANA storm), so the data catches real events. Wettest week for useful rain (≥ 10 mm): from 29 October, in 62 % of years.
- **"Why 20 mm for predictions but 30 mm in the climate calendar?"** P-02 uses the international ETCCDI "very heavy rain" index (R20mm) so its probabilities are comparable; the calendar's 30 mm (I-07) is a stricter team rule for erosive storms. Both are documented in `docs/indicators.md`.
- **Tests (built):** 112 pytest tests (engine, predictions, API, database) and 53 Node tests for the app, including hand-checked values and the FAO-56 examples.

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
- **Speed of a new point (say it honestly):** these towns were pre-fetched from NASA before the demo (Fuente de Piedra, Sierra de Yeguas, Teba and Villanueva del Rosario fully; Almargen, Mollina and Archidona satellite only); a brand-new point downloads live and the satellite photos take 1–3 minutes. Pre-fetching is caching real NASA data, not mock data (`data/README.md`).
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
- `/security-review` was run on the engine and the "limits" branches with no findings. Everything the app shows from the API is HTML-escaped.
- **Notifications stay on the phone.** Heavy-rain warnings are local notifications: no push server, no subscription, nothing leaves the phone. The app asks for permission only after the farmer taps "Warn me". Tested on a real Android phone. iPhone support for web notifications is limited.
- **Offline:** the app shell, the last analyses and the predictions are kept on the phone, so results open again without a connection. The demo fields' NASA data is pre-loaded on the server, so the demo does not depend on NASA being reachable.
- **Hosting:** public demo on Google Cloud Run in Madrid (`europe-southwest1`, HTTPS, Space Apps Google Cloud offer, #76), one instance always on, so there is no cold start. The disk is temporary, which is fine because the database is rebuilt from committed seeds at every start. Hugging Face Spaces (decision 0006) was dropped: Docker there is no longer free.

## Speed and quality on the public link ("Is it really light? Does it work on a cheap phone?")
Measured on 15 Nov 2026 (~11:30) on the public URL, `https://farmlens-530581375456.europe-southwest1.run.app`, revision with `main` at `bf3a43f`. Screenshots: `docs/pitch/lighthouse/`.

| What | Result | How it was measured |
|---|---|---|
| Lighthouse Performance · Accessibility · Best Practices | **100 · 100 · 100** | Lighthouse 13.6, mobile, simulated Slow 4G (150 ms, 1.6 Mbit/s) + CPU 4×, private window |
| First paint · main content · ready to tap | 0.9 s · 1.5 s · 1.5 s | Same run (FCP, LCP, Time to Interactive); total blocking time 30 ms, layout shift 0 |
| Page weight on first visit | **145 KB in 17 files, 97 KB of it JavaScript** | Same run (compressed transfer); project budget is < 200 KB of JS |
| First load to a usable form, empty cache | **4.4 s** | Headless Chrome, Pixel 5 screen, every request delayed as Slow 4G + CPU 4× (stricter than Lighthouse's estimate) |
| Demo field: tap "Analyze" → results | **0.3–0.8 s** (server answer 44–51 ms) | Same throttled browser, all 3 demo fields; "What to expect" tab 0.2–0.3 s |
| Pre-fetched town (Fuente de Piedra, #87) | **50–61 ms** server answer, satellite data already in | 3 calls to `POST /api/analyze` from a home connection in Spain |
| Brand-new map point | 3.8 s with satellite data in this run | One point east of Málaga; MODIS can still take 1–3 minutes when ORNL is busy, and the app says so |
| Installable | Yes, Chrome reports no installability problems | Chrome's own check (manifest + service worker); Lighthouse 12+ has no PWA score any more |
| Offline after one visit | App opens, "You're offline" banner, a saved demo field result opens | Same browser, network cut, page reloaded |
| Cold start | None: minimum instances = 1 | Cloud Run setting; it would only apply if min instances were set to 0 |

Lighthouse found nothing to fix (every weighted audit passes). These are numbers from one session, not an average: say "about".

## Science lens ("Is it sound? What is the resolution?")
- POWER meteorology: ½° × ⅝° (≈ 55 km at Málaga), MERRA-2 reanalysis, API v2.10.3. MODIS: 250 m, 16-day composites (MOD13Q1 v061).
- Methods follow FAO-56 (Allen et al., 1998). The threshold sources are in `docs/indicators.md`.
- What would make it stronger: an agronomist's review of the thresholds, a check against an AEMET or Junta de Andalucía station near Antequera, and real crop prices.

## Team lens ("How did you split the work? What did you learn?")
Work was split in Scrum sprints (`docs/sprint-plan.md`): PWA, API and data, data analysis, Scrum/UX/docs. AI use (Claude Code only, for code and documents, never inside the app) is declared in `docs/ai-usage.md`, and every AI output was checked by tests or by hand.
