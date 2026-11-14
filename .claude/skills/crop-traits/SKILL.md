---
name: crop-traits
description: Add or update a crop in the crop catalogue data/crops.csv (seed of the SQLite crops table) — family, growing months, water need, drought/heat/frost tolerance, nitrogen fixation, root depth, organic matter, ground cover, forage and illustrative market value — with a cited source for every value. Use when a crop is added to any rotation, or when a crop parameter is needed by the rotation engine.
---

# Crop traits

Argument: crop name(s), and optionally the region (default: Andalusia / Mediterranean, rain-fed).

## Rules
1. **Every value needs a source** or `confidence=indicative`. Use authoritative references: FAO Irrigation & Drainage Paper 56 (crop water needs, stage lengths, root depth), FAO EcoCrop, Spanish/Andalusian agronomic services (MAPA, Junta de Andalucía / IFAPA), extension material. Open the source; never fill values from memory. If a value cannot be verified, leave it empty or mark it `indicative` with a note — an honest gap beats an invented number.
2. Prefer **Mediterranean, rain-fed** values; if the source is generic or irrigated, say so in `notes`.
3. Columns and allowed values are defined in `docs/crop-traits.md` — follow them exactly. Do not add/rename columns: the schema belongs to the DB owner (@HectorLopGar-Dev, issue #7); propose changes to him.
4. `crop_id` must match the identifiers used by the rotation engine (Shape 2 in `docs/work-plan.md`): lowercase snake_case.
5. `family` matters: rotating between botanical families is what breaks pest and disease cycles — always fill it.
6. `market_value_illustrative` is never presented as a real price; the UI must label it "illustrative".
7. Add each new reference to the list in `docs/crop-traits.md` (ID `R-XX`) and to `docs/third-party.md` section 3 if it is a dataset/database.

## How the code uses it
`src/fieldshift/db.py` loads the CSV into the `crops` table; `src/fieldshift/rotations.py` reads crops through the `db` module, never hard-coded.

## After editing
- Validate the CSV: same number of columns per row, numeric columns numeric, enums within allowed values, unique `crop_id`.
- Ask the `agro-domain-advisor` agent to sanity-check new rows.
- Report in Spanish: crops added, values left empty or indicative and why, sources used.
