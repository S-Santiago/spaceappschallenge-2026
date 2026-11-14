# 0004 · Mobile app as a PWA (Progressive Web App) + Python API

- **Date:** 2026-11-14
- **Status:** accepted — **supersedes the UI part of [0002](0002-tech-stack.md)** (Streamlit). Python, SQLite and the engine modules from 0002 stay.
- **Deciders:** team (Scrum Master @sebasbarrabaja-cmyk), after the supervisor's feedback. A PWA was the team's original idea.

## Context
FarmLens targets farmers in Málaga's villages with at most a low/mid-range phone and poor connectivity. The team wants a **mobile app** that works offline and can **alert** the farmer (e.g. heavy-rain risk on bare soil). A supervisor suggested **predictions** built from NASA's historical data. Streamlit is a web page that needs a live connection and cannot send notifications. Judges must still be able to open the demo from a **public link without installing anything**.

## Options considered
1. **PWA + Python API** — installable from the browser to the home screen, works offline (service worker), notifications on Android, one public link for judges, light on cheap phones. Not in app stores; limited notifications on iPhone.
2. **Native app (Flutter / React Native)** — full app and notifications; new technology, judges must install an APK, more work in the time left.
3. **Keep Streamlit** — no extra work; not an app, no offline, no notifications.

## Decision
**Option 1 — PWA + Python API.**
- **Backend:** the existing Python modules (`power.py`, `modis.py`, `climate.py`, `rotations.py`, `db.py`, SQLite) behind a small **HTTP JSON API** (recommended: FastAPI). The same service serves the PWA static files (one URL, no CORS issues).
- **Frontend (PWA):** mobile-first and light (target < 200 KB of JS on first load): web app manifest + icons, service worker (offline app shell + cached demo-field results), the 4-step form, results and "What to expect" (predictions & alerts) screens. Framework chosen by the frontend owner in Sprint 1 — prefer none or a tiny one (vanilla JS, Preact, Alpine, Svelte).
- **Predictions:** statistical functions over NASA historical data (frequencies, percentiles, return periods, trends with confidence intervals, dryness index) — **no AI/ML models**. Each one defined in `docs/indicators.md` before it is implemented, and shown as "based on the last 20 years", never as a weather forecast.
- **Alerts:** first as **in-app alert cards**; Android notifications are a Sprint 3 stretch goal.
- **Hosting:** a free host that runs Python (e.g. Render, Hugging Face Spaces, Fly.io), chosen in Sprint 1. Free tiers may sleep → open the app a few minutes before judging and the pitch.

## Consequences
- The Streamlit UI (`src/app.py`, `ui_results.py`) was only a **technical test harness** for the engine. It is not part of the product or the demo; it can stay as an internal developer tool. The PWA has its own visual design.
- New contract: API endpoints and JSON shapes (Shape 1, Shape 2, predictions) documented in `docs/work-plan.md`.
- `docs/ux-guidelines.md` mobile rules still apply; Streamlit-specific advice no longer does. New checks: installable (manifest + icons), works offline for demo fields, fast first load on Slow 4G.
- Notifications need user permission; push from a server needs a stored subscription (personal data → explicit consent). Not needed for in-app alerts.
- README "How to run", `docs/architecture.md`, `docs/tools.md` and `docs/third-party.md` are updated when the API and PWA land.
