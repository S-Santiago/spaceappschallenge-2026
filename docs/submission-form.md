# Submission form — ready to paste

Text for the "Submit for Judging" form on spaceappschallenge.org. Copy each block as is. Sources: `README.md`, `docs/nasa-data.md`, `docs/third-party.md`, `docs/ai-usage.md`.

---

## Summary * (50–200 words)

FarmLens is a mobile-first web app that helps small farmers in Málaga, Spain, choose crop rotations that cope with hotter summers, drier springs and water restrictions. A farmer picks a field, enters the current rotation, irrigation, slope and priorities (save water, soil health, income, low risk). FarmLens turns 20 years of NASA POWER daily climate data (2005–2025) into a 12-month field calendar of rain, water deficit, frost, heat and heavy-rain days, and uses MODIS satellite vegetation data to find the months when the soil is left bare. It then compares the current rotation with three alternatives, such as adding a legume, sowing a cover crop in the bare window or switching to a less thirsty crop. For each option it explains why it is suggested, the evidence behind it, its benefits, what we do not know and which risks a local expert should check. It is designed for low-end phones with weak mobile data and works offline for the demo fields. FarmLens supports, and does not replace, farmers' judgment.

---

## Project Details *

🌾 **The problem**
Málaga's small farmers have cheap phones, weak coverage and little time. Every season they must pick the next crop while summers get hotter (about 40 °C in July inland), rain-fed fields get only 470–510 mm a year, irrigation faces restrictions and bare soil washes away in autumn storms. NASA data could help, but not in a form they can use.

📱 **What FarmLens does**
In four short steps the farmer chooses a field, enters the last 2–4 crops, sets priorities (water, soil, income, low risk) and adds irrigation and slope. They get:
- 📅 **Field calendar:** rain, water deficit, frost, heat, heavy-rain days and bare-soil months.
- 📈 **What is changing:** last 10 years vs the previous 10, plus risk levels. These are statistics over NASA history, not forecasts.
- 🔄 **Rotation comparison:** the current rotation plus 3 alternatives. Each card says why, evidence, benefits, information gaps and risks for a local expert to check.

🛰️ **NASA data**
- **NASA POWER** (2005–2025): temperature, rain, soil wetness, radiation, wind → water balance, frost, heat and trends.
- **MODIS NDVI** (2024–2025): shows when the soil is left bare → cover-crop and anti-erosion options.
- A sourced crop catalogue (FAO) and a rule-based engine. No machine learning: every number is traceable.

💚 **Benefits and impact**
Clear, honest options to protect soil and cope with heat and water scarcity, on the phone the farmer already has. It shows its uncertainty and supports, never replaces, the farmer's judgment.

⚡ **Made for low-end phones**
Installable PWA, under 200 KB of JavaScript, plain words, big buttons, works offline for demo fields, no accounts and no personal data.

🛠️ **Tools**
Python, FastAPI, SQLite, vanilla JavaScript PWA, Leaflet + OpenStreetMap, Docker on Google Cloud Run. Claude Code helped us code and document; the team reviewed and tested everything and the app has no AI model.

✨ **What is creative**
Two NASA datasets turned into a decision readable in one minute, with evidence and unknowns shown on every suggestion.

🚧 **Built vs next**
Built: data clients, indicators, rotation engine, PWA, offline demo, public demo. Next: Spanish UI, SMAP, GPM and Landsat data, local prices, soil tests.

🔗 Demo: https://farmlens-530581375456.europe-southwest1.run.app
🔗 Code (MIT): https://github.com/S-Santiago/spaceappschallenge-2026

---

## NASA Data * (Link Text → Link URL)

| Link Text | Link URL |
|---|---|
| NASA POWER (Prediction Of Worldwide Energy Resources) — Daily API, Agroclimatology | https://power.larc.nasa.gov/ |
| NASA POWER Daily API documentation (v2.10.3) | https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061 (MOD13Q1), NASA LP DAAC | https://doi.org/10.5067/MODIS/MOD13Q1.061 |
| ORNL DAAC MODIS/VIIRS Land Product Subsets web service (TESViS) | https://modis.ornl.gov/data/modis_webservice.html |

---

## Space Agency Partner & Other Data (Link Text → Link URL)

**Data and references**

| Link Text | Link URL |
|---|---|
| FAO Irrigation and Drainage Paper 56, Crop evapotranspiration (crop coefficients, ET₀ method) | https://www.fao.org/4/x0490e/x0490e00.htm |
| FAO Irrigation Water Management Training Manual 3, Irrigation water needs (crop water needs) | https://www.fao.org/3/s2022e/s2022e00.htm |
| FAO Irrigation and Drainage Paper 66, Crop yield response to water (crop temperature parameters) | https://www.fao.org/3/i2800e/i2800e.pdf |
| OpenStreetMap map tiles and data (© OpenStreetMap contributors, ODbL) | https://www.openstreetmap.org/copyright |
| OpenStreetMap Nominatim (place search and Málaga province outline) | https://nominatim.openstreetmap.org/ |

**Libraries and tools**

| Link Text | Link URL |
|---|---|
| Leaflet 1.9.4 (map library, BSD-2-Clause) | https://github.com/Leaflet/Leaflet |
| FastAPI (MIT) | https://github.com/fastapi/fastapi |
| Uvicorn (BSD-3-Clause) | https://github.com/encode/uvicorn |
| Starlette (BSD-3-Clause) | https://github.com/encode/starlette |
| Pydantic (MIT) | https://github.com/pydantic/pydantic |
| httpx (BSD-3-Clause) | https://github.com/encode/httpx |
| SQLite (public domain) | https://www.sqlite.org/ |
| pytest (MIT) | https://docs.pytest.org/ |
| Python 3.12 Docker image (base of the public demo) | https://hub.docker.com/_/python |
| Google Cloud Run (hosting of the public demo) | https://cloud.google.com/run |
| Claude Code, Anthropic (AI coding assistant, declared in docs/ai-usage.md) | https://www.anthropic.com/claude-code |
| Taste skill, design-taste-frontend (MIT, dev tooling) | https://github.com/Leonxlnx/taste-skill |
| Frontend Design skill (Apache-2.0, dev tooling) | https://github.com/anthropics/claude-plugins-official |
| Impeccable skill (Apache-2.0, dev tooling) | https://github.com/pbakaus/impeccable |

**Our own work**

| Link Text | Link URL |
|---|---|
| FarmLens source code, documentation and AI usage declaration (MIT) | https://github.com/S-Santiago/spaceappschallenge-2026 |

---

## Checkboxes

- Agree to Terms and Conditions: **tick it yourself** (you are accepting terms).
- Confirm All Work is Original: **tick it yourself**. Before ticking, check that every external resource is in the two tables above and that nothing copyrighted is in the demo (images, music, fonts).

## Before you press submit
- The GitHub repo must be **public** and the link open without login.
- Open the demo link on a phone and confirm it loads.
- Table row for the Taste skill: its bundled photos are not used in the app. If you prefer, drop the three skill rows (dev tooling only).
- Check FAO links open (they were not tested from here).
