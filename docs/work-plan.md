# Work plan — proposal for a team of 4

> **Proposal, not a decision.** Discuss it in the team, adjust names and scope, then record the stack choice with `/record-decision` (`docs/decisions/0002-tech-stack.md`).

## Proposed product (MVP)
A web tool where a farmer picks a field on a map, enters the current rotation and their priorities (save water, soil health, income, low risk). The tool then shows:
1. **Field climate calendar** (12 months): rain, water deficit, soil moisture, frost and heat days, and months when the field is bare, all taken from NASA data.
2. **Long-term trends**: 2005–2014 vs 2016–2025 (rainfall, heat days).
3. **Rotation comparison**: the current rotation plus **3 alternatives** (legume break, cover crop in the bare window, water-saving swap, forage/diversification). Each one shows *why · evidence · benefits · information gaps · risks to review locally*.

## Already built (branch `feat/rotation-mvp`)
| File | What it does | Status |
|---|---|---|
| `src/fieldshift/power.py` | NASA POWER daily point data 2005–2025 (Tmax, Tmin, precipitation, root-zone soil wetness) | ✅ built, tested on Málaga (7,670 days) |
| `src/fieldshift/modis.py` | MODIS MOD13Q1 NDVI 2024–2025 via ORNL DAAC (no login), parallel requests | ✅ built, tested (45 composites, ~25 s first call) |
| `src/fieldshift/cache.py` | JSON cache: `data/processed/cache` (ignored) → `data/samples` (committed demo data) | ✅ built |

## Work split (4 people, 4 independent tracks)
Each track owns its own files, so the four can work in parallel without conflicts. Interfaces between tracks are the JSON shapes below. Agree on them first (15 min).

| # | Track | Owner | Files | Done when |
|---|---|---|---|---|
| A | **Climate indicators** (data) | _TBD_ | `src/fieldshift/climate.py` | From `power.fetch_daily` + `modis.fetch_ndvi`, returns the monthly profile and trends (shape 1). Also registers POWER + MODIS with `/nasa-dataset-check` and saves demo samples in `data/samples/`. |
| B | **Crops & rotation engine** (agronomy) | _TBD_ | `src/fieldshift/crops.py`, `src/fieldshift/rotations.py` | Given shape 1 + rotation + priorities, returns current + 3 strategies (shape 2). Crop table checked with the `agro-domain-advisor` agent; values marked "indicative". |
| C | **API + frontend** (dev/UX) | _TBD_ | `src/fieldshift/api.py`, `src/web/` | Map → form → results screens; uses mock JSON until A and B land; passes `/ux-review`. Records the stack decision. |
| D | **Story, docs & submission** | _TBD_ | `README.md`, `docs/`, `docs/pitch/` | README sections 1–5, Project page texts, ≤7 slides or ≤30 s video (`/demo-builder`), `/submission-check` green, Submit for Judging before Sun 23:59. Also collects the farmer persona and the demo field. |

### Shape 1 — climate profile (A → B, C)
```json
{
  "location": {"lat": 36.72, "lon": -4.42, "elevation_m": 144},
  "months": [{"month": 1, "rain_mm": 60, "et0_mm": 45, "water_balance_mm": 15,
              "soil_wetness": 0.6, "frost_days": 0.2, "heat_days": 0, "heavy_rain_days": 0.4,
              "ndvi": 0.15, "likely_bare": true}],
  "trends": {"rain_change_pct": -8, "heat_days_change": 3.1},
  "sources": ["NASA POWER 2005-2025", "MODIS MOD13Q1 2024-2025"]
}
```

### Shape 2 — strategies (B → C)
```json
[{"id": "current", "name": "Current rotation", "years": ["durum_wheat", "durum_wheat", "sunflower"],
  "scores": {"water": 62, "soil": 40, "income": 70, "risk": 55, "overall": 57},
  "why": "...", "evidence": ["..."], "benefits": ["..."], "gaps": ["..."], "risks_to_review": ["..."]}]
```

## Suggested timeline (Europe/Madrid)
| When | Milestone |
|---|---|
| Sat by 13:30 (mentoring) | Interfaces agreed; persona + demo field chosen; stack decided |
| Sat 17:30 (review) | A and B return real JSON; C shows it end-to-end, even if ugly |
| Sun 13:00 | Feature freeze on content; polish UX and wording |
| Sun 15:00 | `main` frozen (CONTRIBUTING rule); demo recorded / slides done |
| Sun 16:30 | Technical pitch test |
| Sun before 23:59 | Submit for Judging, then re-check the confirmation |
