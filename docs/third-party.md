# Third-party components and licenses

Everything in (or used by) this project that the team did not create: libraries, frameworks, fonts, icons, images, map tiles, code snippets, datasets, models. Datasets are detailed in [nasa-data.md](nasa-data.md) but must also appear in section 3.

> Being accessible on the Internet does **not** mean it can be reused. Check the license *before* adding it. If unsure, ask the local lead before submitting.

## 1. Software dependencies

| Name | Version | Purpose | License | Link | Notes (attribution required?) |
|---|---|---|---|---|---|
| httpx | 0.28.1 | HTTP client for NASA POWER and ORNL MODIS APIs | BSD-3-Clause | https://www.python-httpx.org/ | No |
| pytest | 9.2.0 | Unit tests (`tests/`) | MIT | https://pytest.org/ | No |

## 2. Assets (images, icons, fonts, audio, map tiles)

| Asset | Source / author | License | Where used | Attribution text |
|---|---|---|---|---|
| _none yet_ | | | | |

> Map tiles: OpenStreetMap data requires "© OpenStreetMap contributors" attribution (ODbL). Many tile providers have their own usage policies — check them.

## 3. Data sources (summary)

| Dataset | Provider | Terms | Citation |
|---|---|---|---|
| NASA POWER daily point data | NASA LaRC | NASA open data | See `docs/nasa-data.md` D-01 |
| MODIS MOD13Q1 v061 NDVI (via ORNL DAAC web service) | NASA LP DAAC / ORNL DAAC | NASA open data | doi:10.5067/MODIS/MOD13Q1.061 (D-02) |

## 4. Code snippets copied or adapted

| Source (URL) | License | File(s) | What was adapted |
|---|---|---|---|
| _none yet_ | | | |

## 5. License compatibility notes
- Permissive licenses (MIT, BSD, Apache-2.0, ISC) are compatible with any project license we are considering.
- Copyleft licenses (GPL, AGPL) impose conditions on our project license — discuss with the team before adding.
- "Non-commercial" (CC BY-NC) or "no derivatives" (CC BY-ND) assets: avoid.
