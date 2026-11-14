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

<!-- Copied to the Project page on spaceappschallenge.org. Keep it between 50 and 200 words and in sync with section 9 (what is really built). -->

FarmLens is a mobile-first web tool that helps small farmers in Málaga, Spain, choose crop rotations that cope with hotter summers, drier springs and water restrictions. A farmer picks their field, enters the current rotation, irrigation, slope and priorities (save water, soil health, income, low risk). FarmLens turns 20 years of NASA POWER daily climate data (2005–2025) into a 12-month field calendar of rain, water deficit, frost, heat and heavy-rain days, and uses MODIS satellite vegetation data to find the months when the soil is left bare. It then compares the current rotation with three alternatives, such as adding a legume, sowing a cover crop in the bare window or switching to a less thirsty crop. For each option it explains why it is suggested, the evidence behind it, its benefits, what we do not know and which risks a local expert should check. It is designed for low-end phones and works offline for the demo fields. FarmLens supports, and does not replace, farmers' judgment.

## 2. The problem

Málaga province has a lot of agriculture spread across many small villages, where most farmers have **at most a low/mid-range phone, poor mobile coverage in the field and little access to digital tools**.

They face a hard, recurring decision: **which crops to rotate next season**. The climate is changing under their feet:

- **Heat:** in the inland plains, the average July maximum is already about **40 °C** (NASA POWER, Antequera area).
- **Water:** rain-fed fields get only around **470–510 mm of rain a year**, and irrigated farms in the Guadalhorce valley face **drought restrictions**.
- **Soil:** fields left bare after harvest are exposed to heavy autumn storms that wash soil away.

Choosing a new crop is risky: a crop that improves the soil may need too much water, not fit the season or not sell locally. Satellite and climate data that could help exist, but they are not available in a form a farmer can use on a cheap phone.

<!-- TODO (#9): add 1–2 trend numbers from climate.py (2005–2014 vs 2016–2025: rain change %, extra heat days) for F1 and F2. -->

**Who we design for (fictional personas):** *Antonio*, 58, 40 ha of rain-fed durum wheat and sunflower near Antequera; *Carmen*, 45, 8 ha of irrigated maize, alfalfa and faba bean in the Guadalhorce valley. Details in [`docs/challenge.md`](docs/challenge.md#demo-personas-fictional).

## 3. Our solution

**FarmLens** turns NASA data into rotation options a farmer can read on a phone, in four short steps:

1. **Your field**: pick a demo field (works offline) or a point on a map.
2. **Current rotation**: the crop of each year (2–4 years).
3. **Your priorities**: save water, soil health, income, low risk.
4. **Your farm**: irrigation and slope → **Analyze my field**.

**What the farmer gets:**

| Result | Built from |
|---|---|
| 📅 **Field calendar (12 months)**: rain, water surplus/deficit, frost days, hot days, heavy-rain days, months with bare soil | NASA POWER 2005–2025 + MODIS NDVI 2024–2025 |
| 📈 **What is changing**: last 10 years vs previous 10 (rain, hot days) | NASA POWER |
| 🔄 **Current rotation + 3 alternatives**, each with a score and an explanation | Climate profile + crop catalogue (sourced) + farmer inputs |

<!-- TODO (#13): add a phone screenshot of the results here (assets/), no personal data. -->

Required by the challenge — for **at least three rotation strategies (including the current one)** the tool explains: why it was suggested · supporting evidence · benefits · information gaps · risks needing local review. It supports, and does not replace, farmers' judgment.

## 4. NASA data used

At least one NASA resource listed by the challenge is **mandatory** for Global Awards. Full traceability (source, version, license, variables, coverage, limits, role) lives in [`docs/nasa-data.md`](docs/nasa-data.md).

| Resource | Role in the solution |
|---|---|
| [NASA POWER](https://power.larc.nasa.gov/) Daily API v2.10.3 — temperature, precipitation, root-zone soil wetness, 2005–2025 | Climate profile of the field: water balance, frost/heat/heavy-rain days, decade trends → evidence for every rotation card |
| [MODIS/Terra MOD13Q1 v061](https://doi.org/10.5067/MODIS/MOD13Q1.061) NDVI, 250 m, 16-day (via ORNL DAAC) — 2024–2025 | Detects the months the field is likely bare → cover-crop and erosion-reduction suggestions |

## 5. How to run it

**Public demo (no install, no login):** _TODO (#15): Streamlit Community Cloud link._

**Run locally** (Python 3.11+):

```bash
git clone https://github.com/S-Santiago/spaceappschallenge-2026.git
cd spaceappschallenge-2026
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501). No API keys are needed: NASA POWER and the ORNL DAAC MODIS service are open, and the demo fields work offline from `data/samples/`.

<!-- TODO (#14): confirm these steps once the DB and real modules are wired in; add `pytest` command (#11). -->

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
├── src/
│   ├── app.py          # Streamlit app (entry point)
│   └── fieldshift/     # NASA clients (power.py, modis.py), indicators, rotation engine, DB
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
| [docs/ui-skills.md](docs/ui-skills.md) | UI/UX skills for Claude Code: sources, versions and coexistence rules |

### UI/UX skills for Claude Code (developers)

The repo ships three third-party UI/UX skills so anyone who opens it with Claude Code has them, with nothing to install:

| Skill | Role | Use it for |
|---|---|---|
| `/design-taste-frontend` ([Taste](https://github.com/Leonxlnx/taste-skill), MIT) | **1 · Art direction** | Palette, type, tone and visual personality — what "good" looks like for FarmLens |
| `/frontend-design` ([Anthropic](https://github.com/anthropics/claude-plugins-official), Apache-2.0) | **2 · Implementation** | Turning that direction into coherent, working Streamlit UI |
| `/impeccable` ([Impeccable](https://github.com/pbakaus/impeccable), Apache-2.0) | **3 · Audit & refinement** | `audit`, `critique`, `polish`, `typeset`, `layout`, `harden`… on screens that already exist |

- **Where**: `.claude/skills/design-taste-frontend/`, `.claude/skills/frontend-design/`, `.claude/skills/impeccable/` — complete upstream copies (instructions, references, scripts, assets), unmodified.
- **How Claude Code finds them**: any folder `.claude/skills/<name>/SKILL.md` in the project is loaded as a project skill when Claude Code is opened from the repository root. Type `/` to see them; Claude can also pick one automatically from its description.
- **Who decides what**: Taste sets the direction, Frontend Design implements it, Impeccable audits it and only *proposes* changes to the direction. Our own rules (mobile-first for low-end phones in [`docs/ux-guidelines.md`](docs/ux-guidelines.md), Streamlit only, licensing) override all three. Full rules: [`docs/ui-skills.md`](docs/ui-skills.md).
- **Requirements**: Taste's scripts need Node 22+ and Chrome/Edge/Chromium. Impeccable downloads its engine binary to `~/.impeccable/bin/` on first use and sends anonymous telemetry unless `DO_NOT_TRACK=1` is set.

Example prompts (name the skill so Claude uses the right one):

```text
/design-taste-frontend Propose an art direction for the FarmLens Streamlit app: farmers in southern Spain on low-end phones, outdoor sunlight, slow data. Palette tokens, one font stack, tone of voice. No photos, no animation.
/frontend-design Apply the agreed art direction (DESIGN.md) to the results view in src/fieldshift/ui_results.py, using Streamlit components and the global CSS layer in src/app.py.
/impeccable audit the 4-step form in src/app.py at 360 px width (Operate mode). List defects by severity; do not change the palette.
/impeccable polish the strategy cards in src/fieldshift/ui_results.py
/impeccable critique http://localhost:8501
```

**Add / update / remove a skill**: copy the full folder into `.claude/skills/<name>/` (`<name>` = the `name:` in its `SKILL.md`, no symlinks), keep its license file, and register it in `docs/ui-skills.md`, `docs/third-party.md`, `docs/tools.md` and `CLAUDE.md`; to update, re-copy the upstream folder and bump the version; to remove, delete the folder and those rows. Step-by-step: [`docs/ui-skills.md` §6](docs/ui-skills.md#6-updating-adding-or-removing-a-skill).

## 8. Use of AI

AI tools were used during this hackathon. Tools, scope and human verification are declared in [`docs/ai-usage.md`](docs/ai-usage.md).

## 9. Limitations & next steps

Honest status — updated as the work lands (built · simulated · next).

| Part | Status |
|---|---|
| NASA POWER and MODIS data clients | ✅ Built and tested on real API calls |
| Streamlit app: 4-step form, mobile-first layout | ✅ Built |
| Results in the app | 🟡 **Simulated** — example data until the real modules are connected (#14) |
| Climate indicators (field calendar, trends) | 🔧 In progress (#9) |
| Rotation engine (current + 3 alternatives) | 🔧 In progress (#10) |
| Database, crop catalogue, offline demo fields | 🔧 In progress (#6, #7, #8) |

**Known limits:** NASA POWER describes a ~55 km area, not the plot; root-zone soil wetness is a model estimate; MODIS covers only 2024–2025 at 250 m; crop market values are illustrative. Details: [`docs/architecture.md`](docs/architecture.md#known-limitations).

**Next steps:** Spanish version of the app (UI texts kept in one place to make translation easy), plot-level satellite data (Landsat, ECOSTRESS), SMAP soil moisture and GPM rainfall, real local prices, soil tests, vegetable crops.

## 10. Acknowledgements

NASA Space Apps Challenge, the Málaga local organization, mentors and 42 Málaga Fundación Telefónica.

> This project is an independent participant submission and is not endorsed by NASA. NASA logos, insignia and mission identifiers are **not** used in this repository.
