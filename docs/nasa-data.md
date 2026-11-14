# Data registry & traceability

Every dataset, API or model output used in the project is registered here. This file feeds the **NASA Data** and **Other data & references** fields of the Project page.

> ⚠️ For Global Awards we must use **at least one NASA resource listed in the challenge** and explain its real role. Partner-agency or other open data may complement it but never replace it.

## 1. Datasets in use

Both are listed in the official challenge Resources tab ("NASA POWER: Agroclimatology & Meteorological Data"; "Landsat and MODIS / VIIRS: Reflectance, NDVI, Vegetation Indices").

| ID | Name | Provider | Role in the solution | Status |
|---|---|---|---|---|
| D-01 | NASA POWER daily point data (Agroclimatology, `community=AG`) | NASA LaRC | Field climate calendar, crop water need vs rain, frost/heat/heavy-rain risk, decade trends (I-01..I-07, I-10, I-11); drives every rotation score | ✅ in use (`power.py`, `climate.py`) |
| D-02 | MODIS/Terra MOD13Q1 v061 NDVI | NASA LP DAAC, served by ORNL DAAC | Field greenness and months when the field is likely bare (I-08, I-09) → cover-crop evidence | ✅ in use (`modis.py`, `climate.py`) |

### D-01 · NASA POWER daily point data
| Field | Value |
|---|---|
| Provider | NASA Langley Research Center (LaRC) POWER Project |
| Official link | https://power.larc.nasa.gov/ · API docs https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| Product & version | POWER daily point API; version reported in the response header (`meta.api_version` in our cache) |
| Access date | 2026-11-14 |
| Access method | REST API, no login (`src/fieldshift/power.py`), cached as JSON |
| License / terms | NASA open data, no restrictions. Requested acknowledgement: "These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program." |
| Variables & units | `T2M_MAX`, `T2M_MIN`, `T2MDEW` (°C); `PRECTOTCORR` (mm/day); `GWETROOT` (0–1); `ALLSKY_SFC_SW_DWN` (MJ m⁻² day⁻¹); `WS2M` (m/s) |
| Spatial coverage & resolution | Global; meteorology from MERRA-2 at ~0.5° × 0.625° (≈ 50 km), solar ~1° |
| Temporal coverage & resolution | Daily, 2005-01-01 → 2025-12-31 (7,670 days) |
| Missing values / quality flags | Fill value −999 → `null`; month-years with > 10 % missing days are skipped (`climate.py`) |
| Limits | Model/reanalysis values for a ~50 km cell, not plot measurements; local microclimate, valley frost and sea breeze are not captured; `GWETROOT` is a model estimate, not measured soil moisture |
| Processing applied | daily values → monthly sums/counts per year → mean of each calendar month 2005–2025; ET0 by FAO-56 Penman-Monteith; decade comparison 2005–2014 vs 2016–2025 |
| Synthetic data? | No (tests use small hand-made series, clearly separated in `tests/`) |
| Role in the solution | Core: without it there is no climate calendar, no water score and no climate risk |
| Small test done | Yes: Málaga city (36.72, −4.42) and Vega de Antequera (37.05, −4.60) |

### D-02 · MODIS MOD13Q1 v061 NDVI
| Field | Value |
|---|---|
| Provider | NASA LP DAAC (product); subset served by the ORNL DAAC MODIS/VIIRS web service |
| Official link | https://lpdaac.usgs.gov/products/mod13q1v061/ · https://modis.ornl.gov/data/modis_webservice.html |
| Product & version | MOD13Q1 v061, band `250m_16_days_NDVI` |
| Access date | 2026-11-14 |
| Access method | ORNL REST API, no login (`src/fieldshift/modis.py`), cached as JSON |
| License / terms | NASA open data, no restrictions on reuse. Citation: Didan, K. (2021). MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061. NASA EOSDIS LP DAAC. doi:10.5067/MODIS/MOD13Q1.061 |
| Variables & units | NDVI, unitless (scale 0.0001; fill −3000 removed) |
| Spatial coverage & resolution | One 250 m pixel at the field point |
| Temporal coverage & resolution | 16-day composites, 2024–2025 (45 composites in the test) |
| Missing values / quality flags | Fill values dropped; pixel reliability flag not yet used |
| Limits | Only 2 years; a 250 m pixel can mix several plots, trees or buildings (Málaga city pixel is urban) |
| Processing applied | composites → mean per calendar month → `likely_bare` if NDVI < 0.25 |
| Synthetic data? | No |
| Role in the solution | Evidence for bare-field months and the cover-crop strategy |
| Small test done | Yes: same two points as D-01 |

### Official resources not used (and why)
| Resource | Why not (yet) | What we use instead |
|---|---|---|
| SMAP soil moisture | Earthdata Login + 9–36 km grid; little time | POWER `GWETROOT` (model root-zone wetness) |
| GPM IMERG precipitation | Earthdata Login, large files | POWER `PRECTOTCORR` |
| SRTM elevation | Needs login or an API key | Slope entered by the farmer |
| ECOSTRESS | Irregular revisit, AppEEARS login | POWER-based Penman-Monteith ET0 |
| Landsat / VIIRS | More processing than MODIS for a 2-day build | MODIS NDVI |
| GRACE / GRACE-FO, GEDI | ~300 km / forest-oriented | — (future) |
| USDA / USGS partner datasets (WSS, CDL, PRISM, SSURGO, NAIP, NLCD, NWIS, OpenET, LANDFIRE, CoCoRaHS, AMS, NASS) | U.S. only; our scope is Málaga | — |
| FAO GAEZ | Global, possible future check of crop suitability | — |

## 2. Candidate datasets (to evaluate — NOT yet verified)

Shortlist relevant to agriculture & climate adaptation. Each one must be checked against the official challenge Resources list and its own data-use terms before use.

| Candidate | What it gives | Typical resolution | Access | Why it may help |
|---|---|---|---|---|
| **NASA POWER** (Agroclimatology) | Daily temperature, precipitation, solar radiation, humidity, wind, evapotranspiration-related variables | ~0.5° (meteo), 1° (solar); daily since 1981 | REST API, no login | Easiest entry point: point-based climate series for any farm |
| **SMAP** soil moisture (L3/L4) | Surface / root-zone soil moisture | 9–36 km; daily / 3-hourly | NSIDC, Earthdata Login | Drought stress & irrigation timing |
| **MODIS** vegetation indices (MOD13Q1 NDVI/EVI) | Vegetation health | 250 m; 16-day | LP DAAC / AppEEARS, Earthdata Login | Crop condition over time |
| **GPM IMERG** precipitation | Global precipitation | 0.1°; 30-min / daily / monthly | GES DISC, Earthdata Login | Rainfall anomalies |
| **ECOSTRESS** | Land surface temperature, evapotranspiration, water stress | ~70 m; irregular revisit | LP DAAC / AppEEARS | Field-scale water stress |
| **Landsat** (NASA/USGS) | Multispectral imagery | 30 m; 8–16 days | USGS EarthExplorer / cloud | Field-level indices, bare-soil periods |
| **GRACE / GRACE-FO** | Terrestrial water storage anomalies (incl. groundwater trends) | ~300 km effective; monthly since 2002 | PO.DAAC / GES DISC, Earthdata Login | Long-term regional water trends |
| **SRTM** / NASADEM (elevation) | Elevation, slope | 30 m | LP DAAC / OpenTopography | Slope → erosion risk, frost-prone low areas |
| **GEDI** | Canopy height, aboveground biomass | ~25 m footprints (sampled) | LP DAAC / ORNL DAAC | Biomass context (mentioned in the challenge) |
| **AppEEARS** (tool) | Subset & extract time series for points/areas | — | Web + API, Earthdata Login | Avoids downloading full granules |
| **Earthdata Search / Worldview / Giovanni** (tools) | Discovery, visualization, quick analysis | — | Web | Exploration & validation |

All of the above except AppEEARS/Earthdata tools are named in the official statement (SMAP, ECOSTRESS, GPM, Landsat, MODIS, NASA POWER, GRACE/GRACE-FO, SRTM, GEDI) — confirm against the Resources tab.

### Non-NASA complements (local information required by the challenge)
| Candidate | What it gives | Notes |
|---|---|---|
| Soil properties (e.g. SoilGrids, ESDAC/LUCAS for Europe, national soil maps) | Texture, organic carbon, pH, depth | Check each license/terms before use |
| Crop characteristics (e.g. FAO-56 crop coefficients, FAO EcoCrop) | Water needs, season length, temperature limits, N-fixation | Cite the source of every crop parameter |
| Farmer priorities | Entered by the user in the tool | No personal data stored |

## 3. Entry template (copy for each dataset)

```markdown
### D-XX · <Dataset name>
| Field | Value |
|---|---|
| Provider | NASA / partner agency / other |
| Official link | <landing page / DOI> |
| Product & version | e.g. MOD13Q1 v061 |
| Access date | YYYY-MM-DD |
| Access method | API / download / AppEEARS / ... (script: `src/...`) |
| License / terms | <exact terms + link>. Citation required: <yes/no + text> |
| Variables & units | e.g. NDVI (unitless, scale 0.0001) |
| Spatial coverage & resolution | |
| Temporal coverage & resolution | |
| Missing values / quality flags | |
| Limits — what it does NOT allow us to conclude | |
| Processing applied | observation → transformation → inference (describe each step) |
| Synthetic data? | yes/no — explain |
| Role in the solution | What the product does with it; what would break if removed |
| Small test done | yes/no — sample in `data/samples/...` |
```

## 4. Citation list
- NASA POWER: "These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program."
- MODIS: Didan, K. (2021). *MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061*. NASA EOSDIS Land Processes DAAC. https://doi.org/10.5067/MODIS/MOD13Q1.061 — subset via ORNL DAAC MODIS/VIIRS Web Service.
- Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). *Crop evapotranspiration — FAO Irrigation and Drainage Paper 56*. FAO, Rome.
