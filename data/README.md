# data/

| Folder | In git? | Content |
|---|---|---|
| `raw/` | ❌ ignored | Original downloads, untouched |
| `processed/` | ❌ ignored | Cleaned / transformed outputs |
| `samples/` | ✅ yes | Small samples (< 8 MiB) so judges can run the demo without downloading everything |

Rules:
1. Every file here must come from a source registered in [`../docs/nasa-data.md`](../docs/nasa-data.md).
2. Downloads must be reproducible: put the script in `src/` (or `notebooks/`) and reference it in the registry.
3. Synthetic or simulated data must be named `*_synthetic.*` and declared as such.
4. Never store credentials (Earthdata `.netrc`, API keys) here.

## Demo fields (`samples/`)
Pre-fetched so the demo loads in under 3 s with no network (the live MODIS call takes ~25 s):

| File | Content |
|---|---|
| `samples/locations.csv` | Demo fields in Málaga province (slug, name, lat, lon, elevation from POWER, description) |
| `samples/power_<lat>_<lon>.json` | NASA POWER daily point data 2005–2025 (`src/fieldshift/power.py`) |
| `samples/modis_<lat>_<lon>.json` | MODIS MOD13Q1 NDVI 2024–2025 (`src/fieldshift/modis.py`) |

Regenerate with `PYTHONPATH=src python -m fieldshift.samples` (fields are read from `locations.csv`). The files are loaded into the SQLite database on start-up (`src/fieldshift/db.py`). Points were checked to show a field-crop NDVI pattern (green in winter–spring, bare in summer) rather than orchards or built-up land.

## Pre-fetched map points (`samples/prefetch_points.csv`)
**Why.** A new point on the map waits for NASA live: POWER takes about 5 s, the MODIS satellite photos 1–3 minutes (sometimes the ORNL service fails). For the live demo we cache **real** NASA data (not mock data) for a few towns, so searching them in "Town or area" answers at once, complete with the likely-bare months. These towns are **not** demo fields: they do not appear in the demo-field list. Any other point still downloads live, as before.

**Keys.** Each town was resolved on 2026-11-15 exactly as the PWA does it (`findPlace` in `web/js/map.js`: same Nominatim query, province ES-MA and outline filter, `roundPoint` to 2 decimals), so the file name matches the point the app sends. If OpenStreetMap moves a town's centre, the key may change and that town will download live again.

**Fetched on 2026-11-15** with the same clients as the demo fields (`power.fetch_daily`, `modis.fetch_ndvi`):

| Town | Key | Sources | NDVI check (MOD13Q1 2024–2025, monthly mean) |
|---|---|---|---|
| Fuente de Piedra | 37.14, −4.73 | POWER + MODIS | 0.48 in Mar → 0.22, bare Jun–Oct |
| Sierra de Yeguas | 37.12, −4.87 | POWER + MODIS | 0.54 in Mar → 0.20, bare Jun–Oct |
| Teba | 36.98, −4.92 | POWER + MODIS | 0.42 in Dec → 0.22, bare Jun–Oct |
| Villanueva del Rosario | 37.00, −4.37 | POWER + MODIS | 0.53 in Mar–Apr → 0.21, bare Jul–Sep, Nov |
| Almargen | 37.00, −5.02 | MODIS | 0.60 in Apr → 0.23, bare Jul–Sep |
| Mollina | 37.13, −4.66 | MODIS | 0.45 in Mar → 0.21, bare Jun–Oct |
| Archidona | 37.09, −4.39 | MODIS | 0.40 → 0.23, bare Jul–Oct (weak signal, pixel mixes town edge and fields) |

Towns checked and **dropped**: Antequera, Coín, Alhaurín el Grande, Villanueva de Algaidas (built-up pixel: flat NDVI 0.14–0.25 all year), Ronda, Álora, Humilladero, Cañete la Real (green all year: woodland, olive groves or irrigation, no bare months), Campillos town and Cártama (mixed pixel; the demo fields cover those areas). Moving a town to a nearby field was not an option: search would never send that key.

**Sizes.** MODIS ≈ 1.8 KB per town; POWER ≈ 1.0 MB per town. POWER is a ½° × ⅝° grid (≈ 55 km), so neighbouring towns share a cell: Fuente de Piedra and Sierra de Yeguas have the same POWER history as the Campillos demo field, and Villanueva del Rosario the same as Vega de Antequera (byte-identical files, stored once by git). What differs from town to town is the 250 m satellite greenness. `samples/` totals 6.72 MiB.

**Budget rule.** Raised from 5 MB to **8 MiB** on 2026-11-15 to fit four demo-script towns with POWER (team decision; enforced by `tests/test_demo_fields.py`).

Regenerate or retry failed towns with `PYTHONPATH=src python -m fieldshift.samples --points` (files already present are kept; delete one to fetch it again).
