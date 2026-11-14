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
| altair | 6.3.0 | Charts in the results view (`src/fieldshift/ui_results.py`); already installed as a Streamlit dependency, pinned because we import it directly. Rendered by the Vega/Vega-Lite JS bundled in Streamlit (BSD-3-Clause) | BSD-3-Clause | https://github.com/vega/altair | No |
| Taste skill (`design-taste-frontend`) — dev tooling, not shipped in the app | 2.5.1 (commit f6b7657) | Claude Code skill: art direction (`.claude/skills/design-taste-frontend/`, see [ui-skills.md](ui-skills.md)) | MIT | https://github.com/Leonxlnx/taste-skill | Keep `LICENSE` in the folder. Its bundled photos/icons carry their own licenses (Unsplash License, CC0, CC BY 2.0/4.0, CC BY-SA 3.0/4.0, ISC, MIT; brand logos are trademarks), listed in the folder's `credits.json` / `icons-credits.json` / `photos.json` — not used in the app; any reuse must be registered in §2 with its credit line |
| Frontend Design skill (`frontend-design`) — dev tooling, not shipped in the app | plugin 1.1.1 | Claude Code skill: UI implementation (`.claude/skills/frontend-design/`) | Apache-2.0 | https://github.com/anthropics/claude-plugins-official | Keep `LICENSE.txt` in the folder |
| Impeccable skill (`impeccable`) — dev tooling, not shipped in the app | 4.9.1 (commit 1995764), engine 0.1.24 | Claude Code skill: UI audit & refinement (`.claude/skills/impeccable/`) | Apache-2.0 | https://github.com/pbakaus/impeccable | Keep `LICENSE` and `NOTICE.md` in the folder. Engine binary downloaded at first run to `~/.impeccable/bin/` (not in the repo) |
| Leaflet (JS, loaded by folium from a CDN) | 1.9.3 | Interactive map in the browser | BSD-2-Clause | https://github.com/Leaflet/Leaflet | "Leaflet" link shown in the map corner (kept by default) |

## 2. Assets (images, icons, fonts, audio, map tiles)

| Asset | Source / author | License | Where used | Attribution text |
|---|---|---|---|---|
| Material Symbols (icon font, bundled inside Streamlit, no extra download) | Google | Apache-2.0 | Interface icons via `:material/…:` in `src/app.py` and `src/fieldshift/ui_results.py` (buttons, alerts, expanders) | None required (keep the license notice if the font is redistributed outside Streamlit) |
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
