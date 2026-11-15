# Third-party components and licenses

Everything in (or used by) this project that the team did not create: libraries, frameworks, fonts, icons, images, map tiles, code snippets, datasets, models. Datasets are detailed in [nasa-data.md](nasa-data.md) but must also appear in section 3.

> Being accessible on the Internet does **not** mean it can be reused. Check the license *before* adding it. If unsure, ask the local lead before submitting.

## 1. Software dependencies

| Name | Version | Purpose | License | Link | Notes (attribution required?) |
|---|---|---|---|---|---|
| httpx | 0.28.1 | HTTP client for NASA POWER and ORNL MODIS APIs | BSD-3-Clause | https://www.python-httpx.org/ | No |
| GitHub Actions `actions/checkout`, `google-github-actions/auth`, `google-github-actions/setup-gcloud` — CI only, not shipped | v4 / v2 / v2 | Deploy workflow `.github/workflows/deploy-cloud-run.yml` (decision 0008) | MIT / Apache-2.0 / Apache-2.0 | https://github.com/actions/checkout · https://github.com/google-github-actions/auth · https://github.com/google-github-actions/setup-gcloud | No |
| SQLite (Python `sqlite3`) | bundled with Python | Local database (`src/fieldshift/db.py`) | Public domain | https://www.sqlite.org/copyright.html | No |
| pytest | 9.2.0 | Tests (dev only, `requirements-dev.txt`) | MIT | https://docs.pytest.org/ | No |
| Taste skill (`design-taste-frontend`) — dev tooling, not shipped in the app | 2.5.1 (commit f6b7657) | Claude Code skill: art direction (`.claude/skills/design-taste-frontend/`, see [ui-skills.md](ui-skills.md)) | MIT | https://github.com/Leonxlnx/taste-skill | Keep `LICENSE` in the folder. Its bundled photos/icons carry their own licenses (Unsplash License, CC0, CC BY 2.0/4.0, CC BY-SA 3.0/4.0, ISC, MIT; brand logos are trademarks), listed in the folder's `credits.json` / `icons-credits.json` / `photos.json` — not used in the app; any reuse must be registered in §2 with its credit line |
| Taste skill kit files (CSS/JS, unmodified copies) — shipped in the pitch page | 2.5.1 | `web/pitch/assets/` (system, cards, motion, layout, diagrams, counter-rolls moment) for the landing page `web/pitch/` | MIT | https://github.com/Leonxlnx/taste-skill | Keep the MIT notice with the files; no kit photos or icons are shipped |
| Frontend Design skill (`frontend-design`) — dev tooling, not shipped in the app | plugin 1.1.1 | Claude Code skill: UI implementation (`.claude/skills/frontend-design/`) | Apache-2.0 | https://github.com/anthropics/claude-plugins-official | Keep `LICENSE.txt` in the folder |
| Impeccable skill (`impeccable`) — dev tooling, not shipped in the app | 4.9.1 (commit 1995764), engine 0.1.24 | Claude Code skill: UI audit & refinement (`.claude/skills/impeccable/`) | Apache-2.0 | https://github.com/pbakaus/impeccable | Keep `LICENSE` and `NOTICE.md` in the folder. Engine binary downloaded at first run to `~/.impeccable/bin/` (not in the repo) |
| Leaflet (JS + CSS, vendored in `web/vendor/leaflet/`, unmodified) | 1.9.4 (from unpkg.com, npm package `leaflet`) | PWA "Another point on the map" (step 1); loaded only when that option is chosen | BSD-2-Clause | https://github.com/Leaflet/Leaflet | `LICENSE` kept next to the files; "Leaflet" link shown in the map corner |
| fastapi | 0.162.7 | HTTP JSON API for the PWA (`src/fieldshift/api.py`) | MIT | https://github.com/fastapi/fastapi | No |
| uvicorn | 0.54.0 | ASGI server that runs the API | BSD-3-Clause | https://github.com/encode/uvicorn | No |
| starlette (via fastapi) | 1.10.0 | Web toolkit under FastAPI; also serves the PWA static files | BSD-3-Clause | https://github.com/encode/starlette | No |
| pydantic (via fastapi) | 2.14.3 | Validates API request bodies | MIT | https://github.com/pydantic/pydantic | No |
| Docker image `python:3.12-slim` (public demo only, not in the repo) | 3.12.16 on Debian (tag `3.12-slim`, built 2026-11-05) | Base image of `Dockerfile` for the hosted demo on Cloud Run (decisions [0006](decisions/0006-public-demo-hosting.md), [0008](decisions/0008-public-demo-cloud-run.md)) | Python: PSF-2.0; image build files: MIT (docker-library/python); Debian base packages under their own licenses (mostly GPL/LGPL/BSD system tools, run as separate programs, not linked into our code) | https://hub.docker.com/_/python | No. Our code stays MIT; the image is built by the host, never committed |

> Removed on 2026-11-15 with the Hugging Face deploy workflow (decision 0008): huggingface_hub (`hf` CLI) and the GitHub Actions `actions/checkout` / `actions/setup-python` (CI only, never shipped).

> Removed on 2026-11-14 with the Streamlit test harness (decision 0004): streamlit, folium, streamlit-folium, altair, the CDN copy of Leaflet loaded by folium and the Material Symbols icon font. None of them ships with the app any more.

## 2. Assets (images, icons, fonts, audio, map tiles)

| Asset | Source / author | License | Where used | Attribution text |
|---|---|---|---|---|
| Familjen Grotesk and IBM Plex Mono (Google Fonts) | Google Fonts (Familjen Grotesk: Familjen Studio; IBM Plex Mono: IBM) | SIL Open Font License 1.1 | Landing page `web/pitch/` only (the app keeps system fonts) | None required on the page |
| OpenStreetMap standard map tiles | OpenStreetMap contributors (tile.openstreetmap.org) | Data: ODbL 1.0; tiles: OSM Tile Usage Policy (light use, valid User-Agent, attribution, no bulk download) | Step 1 map (`web/js/map.js`, only when the map option is chosen) | "© OpenStreetMap contributors" with a link to the copyright page — shown in the map corner |
| Málaga province outline (`web/js/malaga-area.js`) | OpenStreetMap contributors (relation 5275848), fetched once from Nominatim on 2026-11-14, simplified (threshold 0.003°) and rounded to 3 decimals | ODbL 1.0 (derived database: kept as a separate file with its source and license in the header) | PWA step 1: only points inside Málaga province can be chosen (map taps, phone location, place search); outline drawn on the map | "© OpenStreetMap contributors" — shown in the map corner and in the file header |
| OpenStreetMap Nominatim search service | OpenStreetMap Foundation (nominatim.openstreetmap.org) | Data: ODbL 1.0; service: Nominatim Usage Policy (max 1 request/s, no autocomplete while typing, no bulk geocoding, attribution) | PWA step 1 "Town or area" search (`web/js/api.js` `searchPlaces`, called only when the farmer taps Find) | "© OpenStreetMap contributors" — shown in the map corner |

> Map tiles: OpenStreetMap data requires "© OpenStreetMap contributors" attribution (ODbL). Many tile providers have their own usage policies — check them.

## 3. Data sources (summary)

| Dataset | Provider | Terms | Citation |
|---|---|---|---|
| NASA POWER Daily API v2.10.3 (D-01) | NASA LaRC POWER Project | No license stated; cite POWER's Reference + Data Reference; publication/redistribution notification requested | [nasa-data.md §4](nasa-data.md#4-citation-list) |
| MODIS MOD13Q1 v061 NDVI (D-02) via ORNL DAAC TESViS | NASA LP DAAC / ORNL DAAC | Openly shared without restriction (EOSDIS Data Use and Citation Guidance); citation required | [nasa-data.md §4](nasa-data.md#4-citation-list) |
| Crop traits from FAO-56 Tables 11 and 22 (`data/crops.csv`, R-01) | FAO | © FAO; values cited, no text reproduced | Allen et al. (1998), FAO Irrigation and Drainage Paper 56 |
| Crop water needs from FAO Training Manual 3 (`data/crops.csv`, R-02) | FAO | © FAO; values cited | Brouwer & Heibloem (1986), FAO Irrigation Water Management Training Manual 3 |
| Crop temperature parameters from FAO-66 (`data/crops.csv`, R-03) | FAO | © FAO; values cited | Steduto et al. (2012), FAO Irrigation and Drainage Paper 66 |

## 4. Code snippets copied or adapted

| Source (URL) | License | File(s) | What was adapted |
|---|---|---|---|
| _none yet_ | | | |

## 5. License compatibility notes
- Permissive licenses (MIT, BSD, Apache-2.0, ISC) are compatible with any project license we are considering.
- Copyleft licenses (GPL, AGPL) impose conditions on our project license — discuss with the team before adding.
- "Non-commercial" (CC BY-NC) or "no derivatives" (CC BY-ND) assets: avoid.
