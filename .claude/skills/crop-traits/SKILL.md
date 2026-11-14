---
name: crop-traits
description: Add or update a crop in data/crops.csv (water needs, cycle length, temperature limits, frost and heat tolerance, root depth, nitrogen fixation, botanical family, forage value, ground cover) with a cited source for every value. Use when a crop is added to any rotation, or when a crop parameter is needed by an indicator or rotation card.
---

# Crop traits

Argument: crop name(s), and optionally the region (default: Andalusia / Mediterranean, rain-fed).

## Rules
1. **Every value needs a source.** Use authoritative references: FAO Irrigation & Drainage Paper 56 (crop coefficients, stage lengths, root depth), FAO EcoCrop, national/regional agronomic services (e.g. Spanish MAPA, Junta de Andalucía / IFAPA), peer-reviewed extension material. Open the source; never fill values from memory. If a value cannot be verified, leave it empty and set `confidence=low` with a note — an honest gap beats an invented number.
2. Prefer values for **Mediterranean conditions**; if the source is generic, say so in `notes`.
3. Ranges are fine (`min`/`max` columns). Units are fixed by the column name.
4. Add each new reference to the reference list in `docs/crop-traits.md` (ID like `R-03`) and to section 3/5 of `docs/third-party.md` if it is a dataset or database.
5. `family` matters: rotating between different botanical families is what breaks pest and disease cycles — always fill it.

## Columns of `data/crops.csv`
See `docs/crop-traits.md` for the meaning of each column. Do not add or rename columns without updating that document.

## How the code uses it
`data/crops.csv` is the single source of crop parameters. `src/fieldshift/crops.py` (track B in `docs/work-plan.md`) must load it rather than hard-coding values. Crop identifiers used in rotations (e.g. `durum_wheat`, `sunflower` in Shape 2) must match a `crop` row — use lowercase snake_case in the `crop` column.

## After editing
- Validate the CSV (same number of columns per row, numeric columns numeric, `n_fixing` in yes/no, levels in low/medium/high).
- Report in Spanish: crops added, values left empty and why, sources used.
