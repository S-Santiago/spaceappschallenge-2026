# 0002 · Tech stack: Python + Streamlit + SQLite

- **Date:** 2026-11-14
- **Status:** accepted
- **Deciders:** team (issue #1, epic #16)

## Context
~36 h to build a crop-rotation decision-support tool that judges can open from a public link without installing anything. The NASA data clients (`src/fieldshift/power.py`, `modis.py`) were already written in Python. The team needs to store crops, cached climate profiles and analyses, and to work in four parallel tracks.

## Options considered
1. **Python + Streamlit + SQLite** — one language end to end; UI with maps/charts in a few lines; free hosting on Streamlit Community Cloud; SQLite needs no server. Less control over UX and mobile layout.
2. **FastAPI + React/Vite (+ Leaflet/MapLibre)** — polished UX, but two codebases and more integration risk in two days.
3. **Static web + pre-computed JSON** — trivial hosting, but no live analysis for new locations.

## Decision
Option 1:
- **Python 3.11+**.
- **Streamlit** app in `src/app.py` (run: `streamlit run src/app.py`).
- **SQLite** via `src/fieldshift/db.py`; schema + seed committed, `.db` file git-ignored and built at startup.
- **httpx** for NASA APIs (already in use), **pytest** for tests.
- Public demo on **Streamlit Community Cloud** from `main` (repo is public).

## Consequences
- Streamlit Community Cloud resets the disk on restart: the DB must be rebuilt from the seed at startup and pre-loaded demo fields must live in the committed seed (#8). Saved analyses are not persistent in the hosted demo — acceptable for a hackathon, state it in the README.
- The NASA clients are `async`; Streamlit scripts are synchronous → call them through a small sync wrapper (`asyncio.run(...)`) and cache results (`st.cache_data` / DB).
- Every new package goes to `requirements.txt` (pinned) and `docs/third-party.md` (`/add-dependency`). Streamlit (Apache-2.0) and pytest (MIT) are permissive.
- Streamlit UI must still pass `/ux-review` (font size, contrast, loading feedback).
- **Target users use low/mid-range phones with poor connectivity.** Streamlit works on mobile but is not mobile-first and needs a live connection, so the app must be built mobile-first on purpose: `layout="centered"`, single column, no essential inputs in the sidebar, light components (no heavy maps/3D on the main path), pre-loaded demo fields, aggressive caching. Streamlit Community Cloud apps **sleep when idle** and take time to wake up → open the demo link a few minutes before judging/pitch. If Streamlit proves unusable on a real low-end phone by Sat 17:30, revisit this decision (fallback: static mobile page generated from pre-computed results).
- Update `docs/architecture.md`, README "How to run" and `docs/tools.md` (hosting) — done in the same change for architecture; README "How to run" when `src/app.py` exists (#12).
