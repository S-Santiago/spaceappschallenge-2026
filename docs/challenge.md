# Challenge 06 — Adapting farms with NASA data (crop rotation decision support)

| | |
|---|---|
| **Official title** | **Field Shift: Adapting Farms with NASA Data** (Spanish page: "Cambio de campo: adaptación de las granjas a los datos de la NASA") |
| **Event** | NASA Space Apps Challenge 2026 |
| **Difficulty** | Intermediate · Advanced |
| **Subjects** | Arts & multimedia · Earth science · Software |
| **Official link** | https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/ (read 2026-11-14) |
| **Resources tab** | See section 6 (copied 2026-11-14). More resources may be added before the hackathon. |

> The text below is the team's English working rendering of the official statement (the copy we received was a Spanish machine translation, where "SI" means AI). The official English page prevails.

## 1. Summary
Farmers worldwide face shifting temperatures, changing rainfall patterns, water scarcity, extreme weather and declining soil health. These pressures make it hard to choose **crop rotations** that protect fields, conserve water and support long-term resilience.

**The challenge:** build a **decision-support tool** that uses **NASA Earth observations** together with **local soil information, crop characteristics and farmer priorities** to help farmers **explore rotation strategies** that could strengthen soil health and adapt their farms to changing conditions.

## 2. Background
- Decisions are getting harder: rising temperatures, less predictable rainfall, worsening soil health, water scarcity, erosion, nutrient depletion, extreme events.
- Choosing a new crop for a rotation is difficult: a crop that improves soil in one place may use too much water, introduce disease, clash with local markets or fall outside the expected growing season elsewhere.
- Inspired in part by multi-generational farming experience.
- NASA's long-term environmental datasets help understand local growing conditions; **AI techniques** can translate that data into practical, farmer-friendly insights.

## 3. Objectives
Combine NASA Earth observations with local agricultural information into an **app, model, interactive map or other decision-support tool** that helps farmers explore crop-rotation options that may improve soil health and strengthen resilience to changing climate and water conditions.

**Suggested NASA datasets:** SMAP, ECOSTRESS, GPM, Landsat, MODIS, NASA POWER, GRACE & GRACE-FO, SRTM or other NASA elevation products (GEDI biomass is also mentioned in the considerations).

**Things to analyze:** temperature patterns, heat stress, precipitation, soil moisture, evaporation / evapotranspiration, frost risk, extreme precipitation, vegetation stress, long-term water trends.

**Local information to consider:** soil information, crop characteristics and farmer priorities — water use, forage value, nitrogen-fixation potential, erosion reduction, organic-matter improvement, market suitability.

**The tool may highlight:**
- periods when fields are typically **bare**;
- seasons when current crops look **most vulnerable**;
- rotation opportunities that could **break pest cycles, reduce water demand, improve infiltration or add supplementary income**.

### 🎯 Core deliverable behavior (our acceptance criteria)
- [ ] Compare **at least three rotation strategies, including the farmer's existing rotation**.
- [ ] For each strategy explain:
  - [ ] **why** it was suggested,
  - [ ] what **evidence** supports it (which NASA data / which local info),
  - [ ] what **benefits** it may offer,
  - [ ] where there are **information gaps**,
  - [ ] which **risks need local review** by farmers or agricultural experts.
- [ ] Clearly a **support** tool: it identifies patterns and possibilities, it does **not** replace farmers' judgment or local agricultural expertise.

## 4. Potential considerations (optional)

### Understanding conditions and data
- Relate temperature change, soil moisture, precipitation, evaporation and vegetation stress to crop vulnerability and soil health.
- Explain scientific terms: evapotranspiration, soil-moisture anomalies, vegetation indices (e.g. NDVI), frost risk, water-balance indicators.
- Clarify how satellite observations differ from ground measurements and how combining both improves accuracy.

### AI, modeling and data fusion
- Compare different AI or statistical approaches to find patterns in historical climate and soil conditions.
- Use AI to highlight seasonal transitions, bare-field periods, or moments of higher stress in current crops.
- Explain how the model handles **uncertainty** and where local expertise is needed to validate results.
- **Harmonize** datasets with different spatial/temporal resolutions (resizing, aggregating or resampling to a common analysis grid) to combine SMAP soil moisture, ECOSTRESS land-surface temperature, GPM precipitation, Landsat/MODIS vegetation indices, GEDI biomass and soil datasets into coherent features for clear, explainable rotation comparisons.

### Exploring rotation strategies
- Compare scenarios on nutrient cycling, erosion risk, organic-matter contribution, pest-cycle disruption, water use, forage potential, market considerations.
- Map rotation ideas to farmer priorities (save water, supplementary income, better soil structure).
- Briefly explain how **nitrogen-fixing crops, cover crops, deep-rooted crops and drought-tolerant crops** contribute to long-term soil health.

### Geospatial mapping and visualization
- Interactive maps to explore trends over time (long-term soil-moisture decline, heat waves, water storage).
- Visualize field-level vulnerabilities (erosion-risk zones, water-stress hotspots, frost-prone areas).
- Optional add-ons: timelines, dataset-comparison overlays, scenario sliders that adjust rainfall or temperature patterns.

### Farmer-centered design
- Easy to interpret for farmers with limited technical or geospatial experience.
- Let farmers enter their own **priorities and constraints** (water availability, equipment limits, market preferences).
- Remind users that the tool **supports, not replaces**, local expertise, and highlight where human judgment is especially important.

## 5. Our interpretation

### Focus: Málaga province
Málaga has a lot of agriculture spread across many small villages where farmers are **poorly connected to technology**. FarmLens targets them: a simple, mobile-first tool that turns NASA data into rotation options they can understand on a low/mid-range phone.

| Question (participant guide) | Our answer |
|---|---|
| What concrete problem do we tackle? | Farmers in Málaga's villages must decide which crops to rotate while rainfall drops, summers get hotter and irrigation water is restricted — without tools that translate climate data into decisions |
| Who is affected? (farmer type, region, crops) | Small and medium farmers in Málaga province — rain-fed cereal/sunflower in the inland plains (Antequera, Campillos) and small irrigated vegetable farms in the Guadalhorce valley — with **at most a low/mid-range phone, poor connectivity and few tech resources** |
| What exactly does the challenge ask? | Decision support comparing ≥3 rotations (incl. current) with why / evidence / benefits / gaps / risks |
| Which NASA resource adds real value? | NASA POWER (field climate profile and 2005–2025 trends) and MODIS MOD13Q1 NDVI (bare-soil months) — see [nasa-data.md](nasa-data.md) |
| What can we demonstrate in two days? | Pick one of the demo fields on a phone → climate calendar and trends from NASA data → current rotation + 3 alternatives with the five explanations, working offline from pre-loaded data |
| What evidence would make us change approach? | If the two demo fields produce the same suggestions (data not driving the result), or if the app is not usable on a real low-end phone by Sat 17:30 (fallback in decision 0002) |

### Demo personas (fictional)
| Persona | Field | Situation |
|---|---|---|
| **Antonio, 58** | 40 ha of rain-fed durum wheat and sunflower, Vega de Antequera | Cheap Android phone, poor coverage in the field. Springs are drier and summers hotter; unsure whether to add chickpea or stop sowing sunflower |
| **Carmen, 45** | 5 ha family vegetable farm, Guadalhorce valley (Cártama) | Irrigation restrictions due to drought; uses WhatsApp but no farming apps. Wants a rotation that uses less water and avoids bare soil |

Personas, farm sizes and crops are illustrative; climate data for each field is real (NASA POWER / MODIS).

### Demo fields (pre-loaded, offline — issue #8)
Each field falls in a **different NASA POWER grid cell** (checked 2026-11-14 with the POWER climatology API):

| ID | Field | Lat, Lon | POWER cell elevation | Mean rain | Mean July max | Type |
|---|---|---|---|---|---|---|
| F1 | Vega de Antequera | 37.05, −4.60 | 520 m | 1.28 mm/day (~470 mm/yr) | 40.6 °C | Inland rain-fed (Antonio) |
| F2 | Guadalhorce valley, Cártama | 36.72, −4.65 | 145 m | 1.38 mm/day (~500 mm/yr) | 33.9 °C | Near-coast irrigated, water-limited (Carmen) |
| F3 *(optional)* | Campillos | 37.05, −4.86 | 444 m | 1.40 mm/day (~510 mm/yr) | 41.9 °C | Hottest rain-fed plain |

**Grid-cell caveat (use it in the pitch, Validity criterion):** Antequera and the Axarquía fall in the same ~55 km POWER cell, and so do Campillos and Ronda — POWER describes the area, not the plot. MODIS NDVI (250 m) is the field-level signal.

### Scope for the hackathon
- **Must have (demo):** demo-field picker (F1, F2) → current rotation + priorities → climate calendar + trends from NASA POWER → bare months from MODIS → current + 3 alternative rotations with why / evidence / benefits / gaps / risks → works on a low/mid-range phone and offline for demo fields
- **Nice to have:** F3, custom location (map or coordinates), scenario sliders, AI-written plain-language explanations (declared)
- **Out of scope / future:** plot-level data (Landsat/ECOSTRESS), real market prices, soil tests, Spanish UI for farmers, SMAP/GPM integration

## 6. Official resources (Resources tab)
Copied from the official page on 2026-11-14. Register the ones we use in [nasa-data.md](nasa-data.md). **At least one NASA resource below must have a real role** (Global Awards rule). Non-U.S. Government sites have their own data-use terms.

**NASA**
| Resource | Link | What it offers |
|---|---|---|
| SMAP | https://www.earthdata.nasa.gov/data/platforms/space-based-platforms/smap | Surface soil moisture & freeze/thaw, every 2–3 days |
| GPM & IMERG | https://gpm.nasa.gov/data | Global precipitation rate/accumulation |
| Landsat | https://earthexplorer.usgs.gov/ | 30 m reflectance / NDVI |
| MODIS | https://lpdaac.usgs.gov/products/ | 250–1000 m vegetation indices |
| VIIRS | https://search.earthdata.nasa.gov/search?q=VIIRS | Vegetation indices (MODIS successor) |
| NASA POWER | https://power.larc.nasa.gov/ | Agroclimatology: temperature, humidity, radiation, derived indicators |
| SRTM | https://www.earthdata.nasa.gov/data/instruments/srtm | Elevation → slope, runoff, erosion risk |
| ECOSTRESS | https://ecostress.jpl.nasa.gov/data | Land-surface temperature & evapotranspiration (~70 m) |
| NLDAS / GLDAS | https://www.earthdata.nasa.gov/ (search "GLDAS") | Gridded soil moisture, ET, temperature, precipitation |
| GEDI | https://gedi.umd.edu/data | Vegetation structure / biomass |

**Partners & others** (many are USA-only; for Málaga prefer the global ones marked 🌍)
USDA Ag Data Commons · Web Soil Survey · CropScape (CDL) · PRISM · SSURGO/STATSGO2 · NAIP · NLCD · CoCoRaHS · USGS NWIS · USDA AMS Market News · USDA NASS QuickStats · OpenET · LANDFIRE · 🌍 FAO GAEZ (https://gaez.fao.org/) · 🌍 Copernicus Sentinel-2 (https://dataspace.copernicus.eu/) · 🌍 ERA5 (https://cds.climate.copernicus.eu/).

## 7. Double-diamond notes (from the brainstorming poster)
| Box | Notes |
|---|---|
| People — who do we need to involve? | |
| Challenges — what must we address? | |
| Opportunity (potential) | |
| Problem (verified) | |
| Solution (validated) | |
| Storytelling — how do we communicate it? | |
| Management — how do we deliver & track? | |
| Vision | |
| Impact — what difference will we make? | |
