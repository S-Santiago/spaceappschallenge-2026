# Data registry & traceability

Every dataset, API or model output used in the project is registered here. This file feeds the **NASA Data** and **Other data & references** fields of the Project page.

> ⚠️ For Global Awards we must use **at least one NASA resource listed in the challenge** and explain its real role. Partner-agency or other open data may complement it but never replace it.

## 1. Datasets in use

_None yet. Use the `nasa-dataset-check` skill to add entries with the template in section 3._

| ID | Name | Provider | Role in the solution | Status |
|---|---|---|---|---|
| — | — | — | — | — |

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
_Add the recommended citation of each dataset used (many NASA DAACs provide a DOI-based citation)._
