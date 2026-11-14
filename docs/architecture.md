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

## Known limitations
_TODO_
