# Data registry & traceability

Every dataset, API or model output used in the project is registered here. This file feeds the **NASA Data** and **Other data & references** fields of the Project page.

> ⚠️ For Global Awards we must use **at least one NASA resource listed in the challenge** and explain its real role. Partner-agency or other open data may complement it but never replace it.

## 1. Datasets in use

Both resources below are NASA resources named in the official challenge statement (NASA POWER, MODIS).

| ID | Name | Provider | Role in the solution | Status |
|---|---|---|---|---|
| D-01 | NASA POWER — Daily point API (Agroclimatology) | NASA Langley Research Center | Climate profile of the field: rain, ET₀, water balance, frost/heat/heavy-rain days, soil wetness, 2005–2025 trends (Shape 1 → rotation engine) | ✅ In use (`src/fieldshift/power.py`) |
| D-02 | MODIS/Terra MOD13Q1 v061 NDVI (via ORNL DAAC TESViS web service) | NASA LP DAAC (product) · ORNL DAAC (service) | Detects months when the field is likely bare → cover-crop / erosion suggestions | ✅ In use (`src/fieldshift/modis.py`) |

### D-01 · NASA POWER — Daily point API (Agroclimatology community)
| Field | Value |
|---|---|
| Provider | NASA Langley Research Center (LaRC), POWER Project |
| Official link | https://power.larc.nasa.gov/ · API docs https://power.larc.nasa.gov/docs/services/api/temporal/daily/ |
| Product & version | POWER Daily API **v2.10.3** (from the API response header, 2026-11-14), community `AG`, "Source Native Resolution Daily Data" |
| Access date | 2026-11-14 |
| Access method | REST API, no login/key — `src/fieldshift/power.py` (`fetch_daily`), JSON cache in `src/fieldshift/cache.py` (to be replaced by `db.py`, #6) |
| License / terms | No license stated on the official referencing page. Required: cite **POWER's Reference** and **POWER's Data Reference** (service name, version, date accessed). The project asks users to send a reference/link of any publication or presentation to larc-power-project@mail.nasa.gov and to notify it if data is passed on to others. See section 4. |
| Variables & units | `T2M_MAX` Temperature at 2 m maximum (°C) · `T2M_MIN` Temperature at 2 m minimum (°C) · `PRECTOTCORR` Precipitation corrected (mm/day) · `GWETROOT` Root zone soil wetness (dimensionless, 0–1). Units as returned by the API |
| Spatial coverage & resolution | Global. Meteorology: **½° latitude × ⅝° longitude** (≈ 55 × 55 km at Málaga) from MERRA-2 / GEOS assimilation models. Value for the grid cell containing the point; API returns cell elevation (e.g. 144.5 m for 36.72, −4.42) |
| Temporal coverage & resolution | Daily; we use **2005-01-01 → 2025-12-31** (local solar time, `time_standard: LST`) |
| Missing values / quality flags | Fill value **−999** → converted to missing (`None`) in `power.py` |
| Limits — what it does NOT allow us to conclude | Model/reanalysis estimates, **not measurements at the farm**; a ~55 km cell cannot capture valleys, slopes or plot-level microclimate. `GWETROOT` is model output, not satellite-measured soil moisture. 2005–2014 vs 2016–2025 shows a change between decades, not a proven long-term climate trend |
| Processing applied | Observation/model output (POWER) → transformation (monthly means, counts over thresholds, Hargreaves ET₀, decade comparison — catalog in `docs/indicators.md`) → inference (rotation suggestions in `rotations.py`) |
| Synthetic data? | No |
| Role in the solution | Core evidence for every rotation card (water balance, frost/heat risk, heavy-rain erosion risk, trends). Without it the tool cannot describe the field's climate or justify any suggestion |
| Small test done | Yes — Málaga (36.72, −4.42): 7,670 daily records 2005–2025 (team test); 3-day API check on 2026-11-14 confirmed version, units and fill value. Demo samples: `data/samples/` (#8) |

### D-02 · MODIS/Terra Vegetation Indices 16-Day L3 Global 250 m SIN Grid V061 (MOD13Q1)
| Field | Value |
|---|---|
| Provider | NASA Land Processes DAAC (product, author K. Didan) · ORNL DAAC TESViS web service (access) |
| Official link | Product: https://doi.org/10.5067/MODIS/MOD13Q1.061 · Service: https://modis.ornl.gov/data/modis_webservice.html (DOI https://doi.org/10.3334/ORNLDAAC/1600) |
| Product & version | MOD13Q1 **v061**, band `250m_16_days_NDVI` |
| Access date | 2026-11-14 |
| Access method | ORNL DAAC REST endpoint `/MOD13Q1/subset`, no login; max 10 composites per request → split and queried in parallel — `src/fieldshift/modis.py` (`fetch_ndvi`) |
| License / terms | "Openly shared, without restriction, in accordance with the EOSDIS Data Use and Citation Guidance" (Earthdata catalog page). Citation required for the product and, recommended, for the subsetting service. See section 4 |
| Variables & units | NDVI, int16 with **scale factor 0.0001** (→ −0.2 … 1.0), valid range −2000…10000, **fill value −3000** |
| Spatial coverage & resolution | Global; **250 m × 250 m** pixel containing the point (`kmAboveBelow=0`, `kmLeftRight=0`) |
| Temporal coverage & resolution | 16-day composites; product available since 2000-02-18; we use **2024–2025** |
| Missing values / quality flags | Fill value −3000 dropped in `modis.py`. Pixel reliability / QA layers are **not used yet** (clouds may lower some composites) |
| Limits — what it does NOT allow us to conclude | A 250 m pixel can mix several plots, roads or trees; two years only (no long-term trend); low NDVI = bare **or** senescent/stubble — "likely bare" is an inference with a documented threshold (`docs/indicators.md` I-09) |
| Processing applied | Observation (satellite composite) → transformation (scale, monthly mean) → inference (`likely_bare` flag) |
| Synthetic data? | No |
| Role in the solution | Identifies the bare-soil window of the current rotation → evidence for cover-crop and erosion-reduction strategies. Without it, bare periods would be assumed, not observed |
| Small test done | Yes — Málaga (36.72, −4.42): 45 composites for 2024–2025, ~25 s first call (team test). Demo path uses pre-loaded data (#8) |

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

**D-01 · NASA POWER** (official referencing guide: https://power.larc.nasa.gov/docs/referencing/)
- POWER's Reference: *"The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division."*
- POWER's Data Reference (adapted to the service we use): *"The data was obtained from the POWER Project's Daily API v2.10.3 on 2026/11/14."*
- Courtesy notice: after the hackathon, send the project link to larc-power-project@mail.nasa.gov (requested by the POWER Project).

**D-02 · MODIS MOD13Q1 v061**
- Product: *Didan, K. (2021). MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061 [Data set]. NASA Land Processes Distributed Active Archive Center. https://doi.org/10.5067/MODIS/MOD13Q1.061. Date accessed: 2026-11-14.*
- Access service: *ORNL DAAC. 2018. Terrestrial Ecology Subsetting & Visualization Services (TESViS) RESTful Web Service. https://doi.org/10.3334/ORNLDAAC/1600.*
