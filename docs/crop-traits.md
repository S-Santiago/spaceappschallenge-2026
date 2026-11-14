# Crop catalogue (`data/crops.csv`)

Seed data for the `crops` table of the SQLite database (issue #7, owner @HectorLopGar-Dev). The CSV is the committed source of truth; `src/fieldshift/db.py` loads it into the database at startup. Maintained with the `/crop-traits` skill.

> **Schema owner: @HectorLopGar-Dev.** If the `crops` table changes, update this file, the CSV header and the `/crop-traits` skill in the same PR.

**Every value must trace to a reference below or be marked `indicative` in `confidence`.** Empty cells are allowed and honest; invented values are not.

## Columns

| Column | Meaning | Unit / allowed values |
|---|---|---|
| `crop_id` | Identifier used in rotations (Shape 2 `years[]`) | lowercase snake_case, e.g. `durum_wheat`, `chickpea`, `fallow` |
| `name` | Common name (English) | text |
| `scientific_name` | Latin name | text (empty for `fallow`) |
| `family` | Botanical family — rotating families breaks pest/disease cycles | e.g. Poaceae, Fabaceae, Brassicaceae, Asteraceae |
| `type` | Role in the rotation | cereal / legume / oilseed / forage / cover / fallow / other |
| `season` | Sowing season in the target region | autumn / spring / summer |
| `sow_month`, `harvest_month` | Growing months in Andalusia (rain-fed unless stated) | 1–12 |
| `water_need_mm_min`, `water_need_mm_max` | Seasonal crop water need | mm per cycle |
| `drought_tolerance`, `heat_tolerance`, `frost_tolerance` | | low / medium / high |
| `n_fixing` | Biological nitrogen fixation | yes / no |
| `root_depth_m` | Maximum effective rooting depth | m |
| `residue_organic_matter` | Contribution of residues to soil organic matter | low / medium / high |
| `ground_cover` | Protection against erosion while growing | low / medium / high |
| `forage_value` | | low / medium / high |
| `market_value_illustrative` | **Illustrative only** — must be shown as such in the UI | low / medium / high |
| `sources` | Reference IDs separated by `;` | e.g. `R-01;R-02` |
| `confidence` | | high / medium / low / indicative |
| `notes` | Caveats (generic vs Mediterranean values, irrigated vs rain-fed…) | text |

Target list (issue #7): durum wheat, barley, oats, chickpea, lentil, faba bean, vetch–oat, sunflower, sorghum, maize, alfalfa, camelina, mustard/vetch cover, fallow.

## References
| ID | Reference | Link | License / terms |
|---|---|---|---|
| R-01 | _TODO — e.g. FAO Irrigation and Drainage Paper No. 56 (Allen et al., 1998)_ | | |
