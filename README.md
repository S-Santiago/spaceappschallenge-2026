# 🌱 FarmLens — NASA Space Apps Challenge 2026 · Málaga

> **Challenge 06 · Adapting farms with NASA data**
> *A decision-support tool that combines NASA Earth observations with local soil information, crop characteristics and farmer priorities to help farmers explore crop-rotation strategies that strengthen soil health and resilience to changing climate and water conditions.* — full statement in [`docs/challenge.md`](docs/challenge.md)

| | |
|---|---|
| **Event** | NASA Space Apps Challenge 2026 · Local event: Málaga (42 Málaga Fundación Telefónica) |
| **Dates** | 14–15 November 2026 · Development started Sat 14, 09:00 local time |
| **Official deadline** | Sun 15 November 2026, **before 23:59** local time (Submit for Judging) |
| **Status** | 🚧 In development |
| **License** | [MIT](LICENSE) (code & docs). NASA data and third-party components keep their own terms — see [`docs/licensing.md`](docs/licensing.md) |

---

## 1. Summary (50–200 words)

> _TODO: Fill in once the solution is defined. This text is copied to the Project page on spaceappschallenge.org. It must say **what we built, how it answers the challenge and why it matters**._

## 2. The problem

_TODO: Which farmers / region / crop? Which climate impact (drought, heat stress, irregular rainfall, frost…)? What decision do they struggle to make today?_

## 3. Our solution

_TODO: What it does, main user flow, screenshot or diagram._

Required by the challenge — for **at least three rotation strategies (including the current one)** the tool explains: why it was suggested · supporting evidence · benefits · information gaps · risks needing local review. It supports, and does not replace, farmers' judgment.

## 4. NASA data used

At least one NASA resource listed by the challenge is **mandatory** for Global Awards. Full traceability (source, version, license, variables, coverage, limits, role) lives in [`docs/nasa-data.md`](docs/nasa-data.md).

| Resource | Role in the solution |
|---|---|
| [NASA POWER](https://power.larc.nasa.gov/) Daily API v2.10.3 — temperature, precipitation, root-zone soil wetness, 2005–2025 | Climate profile of the field: water balance, frost/heat/heavy-rain days, decade trends → evidence for every rotation card |
| [MODIS/Terra MOD13Q1 v061](https://doi.org/10.5067/MODIS/MOD13Q1.061) NDVI, 250 m, 16-day (via ORNL DAAC) — 2024–2025 | Detects the months the field is likely bare → cover-crop and erosion-reduction suggestions |

## 5. How to run it

> _TODO: complete once the stack is chosen. A judge must be able to run or review the project in a few minutes._

```bash
git clone https://github.com/S-Santiago/spaceappschallenge-2026.git
cd spaceappschallenge-2026
# ...install & run steps...
```

## 6. Repository map

```
.
├── .claude/            # Claude Code agents & skills used by the team (see docs/tools.md)
│   ├── agents/
│   └── skills/
├── .github/            # Issue & PR templates
├── assets/             # Images/icons we created or can legally reuse (see docs/third-party.md)
├── data/               # Data folder — raw/processed are git-ignored; see data/README.md
├── docs/               # ALL documentation (index: docs/README.md)
├── notebooks/          # Exploratory analysis
├── src/                # Source code (stack TBD)
├── CLAUDE.md           # Instructions for AI agents working in this repo
├── CONTRIBUTING.md     # Team workflow
└── README.md
```

## 7. Documentation

| Document | Content |
|---|---|
| [docs/challenge.md](docs/challenge.md) | Challenge statement & our interpretation |
| [docs/hackathon-rules.md](docs/hackathon-rules.md) | Rules, deadlines, deliverables, judging criteria |
| [docs/nasa-data.md](docs/nasa-data.md) | NASA & external data registry (traceability) |
| [docs/architecture.md](docs/architecture.md) | Technical design & stack |
| [docs/decisions/](docs/decisions/) | Decision records |
| [docs/tools.md](docs/tools.md) | Every tool used and how (incl. Claude Code agents & skills) |
| [docs/ai-usage.md](docs/ai-usage.md) | **AI usage declaration** (required by NASA) |
| [docs/third-party.md](docs/third-party.md) | Third-party dependencies, assets and their licenses |
| [docs/licensing.md](docs/licensing.md) | Project license decision |
| [docs/ux-guidelines.md](docs/ux-guidelines.md) | UX minimums for the demo |
| [docs/submission-checklist.md](docs/submission-checklist.md) | Final 30-minute checklist |
| [docs/pitch/](docs/pitch/) | Project Demo (≤7 slides or ≤30 s video) & local pitch |
| [docs/team.md](docs/team.md) | Team roles |
| [docs/team-setup.md](docs/team-setup.md) | **Teammates start here**: Claude Code setup, shared skills & agents |
| [docs/indicators.md](docs/indicators.md) | Catalog of agroclimatic indicators |
| [docs/crop-traits.md](docs/crop-traits.md) | Crop characteristics table & references |

## 8. Use of AI

AI tools were used during this hackathon. Tools, scope and human verification are declared in [`docs/ai-usage.md`](docs/ai-usage.md).

## 9. Limitations & next steps

_TODO: What works today, what is simulated, what is planned._

## 10. Acknowledgements

NASA Space Apps Challenge, the Málaga local organization, mentors and 42 Málaga Fundación Telefónica.

> This project is an independent participant submission and is not endorsed by NASA. NASA logos, insignia and mission identifiers are **not** used in this repository.
