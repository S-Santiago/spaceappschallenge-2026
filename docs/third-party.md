# Third-party components and licenses

Everything in (or used by) this project that the team did not create: libraries, frameworks, fonts, icons, images, map tiles, code snippets, datasets, models. Datasets are detailed in [nasa-data.md](nasa-data.md) but must also appear in section 3.

> Being accessible on the Internet does **not** mean it can be reused. Check the license *before* adding it. If unsure, ask the local lead before submitting.

## 1. Software dependencies

| Name | Version | Purpose | License | Link | Notes (attribution required?) |
|---|---|---|---|---|---|
| httpx | 0.28.1 | HTTP client for NASA POWER and ORNL MODIS APIs | BSD-3-Clause | https://www.python-httpx.org/ | No |
| SQLite (Python `sqlite3`) | bundled with Python | Local database (`src/fieldshift/db.py`) | Public domain | https://www.sqlite.org/copyright.html | No |
| pytest | 9.2.0 | Tests (dev only, `requirements-dev.txt`) | MIT | https://docs.pytest.org/ | No |
| streamlit | 1.67.0 | Web UI framework for the app (`src/app.py`) | Apache-2.0 | https://github.com/streamlit/streamlit | No (keep license notice if redistributed) |
| folium | 0.20.0 | Builds the Leaflet map for "Point on a map" (step 1) | MIT | https://github.com/python-visualization/folium | No |
| streamlit-folium | 0.27.4 | Embeds the folium map in Streamlit and returns the clicked point | MIT (from GitHub repo; PyPI metadata has no license field) | https://github.com/randyzwitch/streamlit-folium | No |
| Leaflet (JS, loaded by folium from a CDN) | 1.9.3 | Interactive map in the browser | BSD-2-Clause | https://github.com/Leaflet/Leaflet | "Leaflet" link shown in the map corner (kept by default) |

## 2. Assets (images, icons, fonts, audio, map tiles)

| Asset | Source / author | License | Where used | Attribution text |
|---|---|---|---|---|
| OpenStreetMap standard map tiles | OpenStreetMap contributors (tile.openstreetmap.org) | Data: ODbL 1.0; tiles: OSM Tile Usage Policy (light use, valid User-Agent, attribution, no bulk download) | Step 1 map (`src/app.py`, only when "Point on a map" is chosen) | "© OpenStreetMap contributors" — shown automatically in the map corner by folium |

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
