# Crop traits table (`data/crops.csv`)

Characteristics of every crop that may appear in a rotation. Maintained with the `/crop-traits` skill. **Every value must trace to a reference in the list below.** Empty cells are allowed and honest; invented values are not.

## Columns

Loaded into the `crops` table of the SQLite database on start-up (`src/fieldshift/db.py`); the column list must match `src/fieldshift/schema.sql`.

| Column | Meaning | Unit / allowed values |
|---|---|---|
| `crop` | Identifier used in rotations (English, lowercase snake_case) | text, e.g. `durum_wheat` |
| `name`, `name_es` | Display name in English / Spanish (shown in the app) | text |
| `scientific_name` | Latin name | text |
| `family` | Botanical family (key for breaking pest/disease cycles) | e.g. Poaceae, Fabaceae, Brassicaceae, Asteraceae |
| `type` | Role | cereal / legume / oilseed / forage / cover / other |
| `season` | Sowing season in the target region | autumn / spring / summer |
| `sow_month`, `harvest_month` | Typical sowing and harvest (or termination) month in the target region | 1–12 |
| `cycle_days_min`, `cycle_days_max` | Sowing to harvest | days |
| `water_need_mm_min`, `water_need_mm_max` | Seasonal crop water requirement **without water stress** (FAO irrigation-planning value). Not what a rain-fed crop actually uses, and not a suitability threshold | mm per cycle |
| `drought_tolerance` | | low / medium / high |
| `irrigation_required` | The crop only makes sense with irrigation in Andalusia; the engine never proposes it for a rain-fed field. Indicative (R-IND) | yes / no |
| `frost_tolerance`, `heat_tolerance` | Tolerance to frost days (Tmin < 0 °C) / heat days (Tmax > 35 °C) **during this crop's season in Andalusia**, used by the rotation engine's climate penalties. Indicative (R-IND), set with the `agro-domain-advisor` agent so no winter crop is excluded by the usual frosts of the demo fields | low / medium / high |
| `t_base_c` | Base temperature for growing degree days | °C |
| `frost_damage_c` | Temperature below which frost damage is likely (sensitive stage) | °C |
| `heat_stress_c` | Max temperature above which heat stress is likely (sensitive stage) | °C |
| `root_depth_m_max` | Maximum effective rooting depth | m |
| `n_fixing` | Biological nitrogen fixation | yes / no |
| `ground_cover` | Protection against erosion while growing | low / medium / high |
| `forage_value` | | low / medium / high |
| `residue_organic_matter` | Contribution of residues to soil organic matter | low / medium / high |
| `market_value` | Relative market value of the harvest — **illustrative only**, not a price | low / medium / high |
| `sources` | Reference IDs, separated by `;` | e.g. `R-01;R-02` |
| `confidence` | | low / medium / high |
| `notes` | Caveats (generic vs Mediterranean values, stage, etc.) | text |

## References
| ID | Reference | Link | License / terms |
|---|---|---|---|
| R-01 | Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). *Crop evapotranspiration — Guidelines for computing crop water requirements*. FAO Irrigation and Drainage Paper 56. Used: Table 11 (lengths of crop development stages), Table 22 (maximum effective rooting depth). | https://www.fao.org/4/x0490e/x0490e00.htm | © FAO. Numeric values cited with reference; no text or figures reproduced |
| R-02 | Brouwer, C., Heibloem, M. (1986). *Irrigation Water Management: Irrigation Water Needs*. FAO Training Manual No. 3. Used: Table 4 (total growing period), Table 5 (seasonal crop water need, mm). | https://www.fao.org/4/s2022e/s2022e02.htm | © FAO. Numeric values cited with reference |
| R-03 | Steduto, P., Hsiao, T.C., Fereres, E., Raes, D. (2012). *Crop yield response to water*. FAO Irrigation and Drainage Paper 66, chapter 4 (wheat, barley, maize, sorghum, sunflower). Used: base temperatures (AquaCrop calibration values, not universal field thresholds), heat effects, drought tolerance statements. | https://www.fao.org/4/i2800e/i2800e07.pdf | © FAO. Numeric values cited with reference |
| R-IND | **Indicative team classification** (sowing/harvest months for Andalusia, qualitative levels, `market_value`). Not from a published source; reviewed with the `agro-domain-advisor` agent (2026-11-14). Must be checked by a local agronomist (e.g. Junta de Andalucía / IFAPA sowing calendars). | — | — |

## Known limitations of the table
- Several FAO cycle lengths are for spring sowing; where they do not apply to autumn/winter sowing in Andalusia the cell is left empty.
- Rooting depths are maxima for non-limiting soils; shallow or calcareous Málaga soils will limit them.
- Summer crops (maize, sorghum) and alfalfa require irrigation in Andalusia.
- Rain-fed cover crops compete for stored soil water; summer soil protection relies on stubble retention rather than cover crops.
- `market_value` is illustrative and ignores prices, CAP eco-schemes and contracts.
