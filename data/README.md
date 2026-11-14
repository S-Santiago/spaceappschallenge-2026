# data/

| Folder | In git? | Content |
|---|---|---|
| `raw/` | ❌ ignored | Original downloads, untouched |
| `processed/` | ❌ ignored | Cleaned / transformed outputs |
| `samples/` | ✅ yes | Small samples (< 5 MB) so judges can run the demo without downloading everything |

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
