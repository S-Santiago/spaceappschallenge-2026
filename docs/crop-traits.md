# Crop traits table (`data/crops.csv`)

Characteristics of every crop that may appear in a rotation. Maintained with the `/crop-traits` skill. **Every value must trace to a reference in the list below.** Empty cells are allowed and honest; invented values are not.

## Columns

| Column | Meaning | Unit / allowed values |
|---|---|---|
| `crop` | Common name (English) | text |
| `scientific_name` | Latin name | text |
| `family` | Botanical family (key for breaking pest/disease cycles) | e.g. Poaceae, Fabaceae, Brassicaceae, Asteraceae |
| `type` | Role | cereal / legume / oilseed / forage / cover / other |
| `season` | Sowing season in the target region | autumn / spring / summer |
| `cycle_days_min`, `cycle_days_max` | Sowing to harvest | days |
| `water_need_mm_min`, `water_need_mm_max` | Seasonal crop water requirement | mm per cycle |
| `drought_tolerance` | | low / medium / high |
| `t_base_c` | Base temperature for growing degree days | °C |
| `frost_damage_c` | Temperature below which frost damage is likely (sensitive stage) | °C |
| `heat_stress_c` | Max temperature above which heat stress is likely (sensitive stage) | °C |
| `root_depth_m_max` | Maximum effective rooting depth | m |
| `n_fixing` | Biological nitrogen fixation | yes / no |
| `ground_cover` | Protection against erosion while growing | low / medium / high |
| `forage_value` | | low / medium / high |
| `residue_organic_matter` | Contribution of residues to soil organic matter | low / medium / high |
| `sources` | Reference IDs, separated by `;` | e.g. `R-01;R-02` |
| `confidence` | | low / medium / high |
| `notes` | Caveats (generic vs Mediterranean values, stage, etc.) | text |

## References
| ID | Reference | Link | License / terms |
|---|---|---|---|
| R-01 | _TODO — e.g. FAO Irrigation and Drainage Paper No. 56 (Allen et al., 1998)_ | | |
