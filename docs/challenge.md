# Challenge 06 — Adapting farms with NASA data (crop rotation decision support)

| | |
|---|---|
| **Official title** | _TODO: copy the exact English title from the official challenge page_ (Spanish page: "Cambio de campo: adaptación de las granjas a los datos de la NASA") |
| **Event** | NASA Space Apps Challenge 2026 |
| **Difficulty** | Intermediate · Advanced |
| **Subjects** | Arts & multimedia · Earth science · Software |
| **Official link** | _TODO: paste URL_ |
| **Resources tab** | _TODO: paste the official Resources list (section 6). More resources may be added before the hackathon._ |

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

| Question (participant guide) | Our answer |
|---|---|
| What concrete problem do we tackle? | _TODO_ — e.g. choosing a rotation for a rain-fed field under increasing drought/heat |
| Who is affected? (farmer type, region, crops) | _TODO_ — e.g. Andalusian dryland cereal farmers (wheat/barley) considering legumes |
| What exactly does the challenge ask? | Decision support comparing ≥3 rotations (incl. current) with why / evidence / benefits / gaps / risks |
| Which NASA resource adds real value? | _TODO_ — candidates in [nasa-data.md](nasa-data.md) |
| What can we demonstrate in two days? | _TODO_ |
| What evidence would make us change approach? | _TODO_ |

### Scope for the hackathon
- **Must have (demo):** _TODO_ — location input → climate/water profile from NASA data → farmer priorities → 3 rotations compared with the five explanations
- **Nice to have:** _TODO_ — interactive map, timeline, scenario sliders, AI explanation layer
- **Out of scope / future:** _TODO_

## 6. Official resources (Resources tab)
_TODO: paste here. Register the ones we use in [nasa-data.md](nasa-data.md)._

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
