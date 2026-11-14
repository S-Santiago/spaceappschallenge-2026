# Architecture

> 🔴 **Stack not decided yet.** Record the choice in `docs/decisions/0002-tech-stack.md` (skill `record-decision`) and then fill in this document.

## Selection criteria for the stack
Given a ~36 h window and a judge who must open it without friction:
1. **Demo-ability**: a public URL or a one-command run.
2. **Team familiarity** over novelty.
3. **Geospatial/time-series support** (NASA data is usually NetCDF/HDF/GeoTIFF or JSON from APIs).
4. **Free hosting** for the public demo link.

| Option | Good for | Watch out |
|---|---|---|
| Python + Streamlit / Gradio | Fast data apps, charts, maps; NASA libraries (`earthaccess`, `xarray`) | Less control over UX |
| Python API (FastAPI) + web front (React/Vite + Leaflet/MapLibre) | Polished UX, mobile-friendly | Two codebases in 2 days |
| Static web + pre-computed data (JSON) | Zero backend, trivial hosting (GitHub Pages) | No live queries |
| Jupyter notebook + slides | Analysis-type solution | Weaker as a "tool for farmers" |

## Components (to complete)
```
[NASA data source] → [ingestion script] → [processing / indicators] → [storage / cache] → [UI] → [farmer]
```

| Component | Technology | Location | Status (built / simulated / future) |
|---|---|---|---|
| Ingestion | TBD | `src/` | — |
| Processing | TBD | `src/` | — |
| UI | TBD | `src/` | — |
| Hosting | TBD | — | — |

## Data flow
_TODO: describe or add a diagram._

## Database (SQLite)
Module `src/fieldshift/db.py`, schema `src/fieldshift/schema.sql` (migrations tracked with `PRAGMA user_version`).
The DB file is **generated** and git-ignored (`FIELDSHIFT_DB`, default `data/processed/fieldshift.db`); it is rebuilt from committed seeds on start-up, so the app works offline. Rebuild by hand: `python -m fieldshift.db reset` (with `src` on `PYTHONPATH`).

| Table | Key | Content | Seeded from | Written by |
|---|---|---|---|---|
| `crops` | `crop` | Crop traits (columns in `docs/crop-traits.md`) | `data/crops.csv` (reloaded on every start) | — |
| `locations` | `slug` | Named fields; `is_demo=1` for the demo fields | `data/samples/locations.csv` | — |
| `nasa_raw` | `source, lat, lon` | Raw NASA POWER / MODIS payloads (replaces the old JSON file cache) | `data/samples/{power,modis}_<lat>_<lon>.json` | `power.py`, `modis.py` via `cache.py` |
| `climate_profiles` | `lat, lon` | Monthly profile, shape 1 in `docs/work-plan.md`, plus the `version` of the code that computed it | — | `climate.py` |
| `analyses` | `id` | Inputs (rotation, priorities, irrigation, slope) + resulting strategies (shape 2). No personal data | — | app |

Coordinates are rounded to 2 decimals (~1 km) everywhere. Main functions: `get_crops()`, `get_crop()`, `get_locations()`, `get_location()`, `get_raw()`/`save_raw()`, `get_profile(lat, lon, version=None)`/`save_profile()`, `save_analysis()`/`get_analysis()`/`list_analyses()`.

## Known limitations
_TODO_
