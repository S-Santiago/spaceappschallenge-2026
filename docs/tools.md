# Tools used and how

Every tool that took part in building the project: what for, how, and under which license/terms. Keep it updated (add a row whenever a new tool is used).

## 1. Tool inventory

| Tool | Category | What we use it for | License / terms | Added |
|---|---|---|---|---|
| Git | Version control | Source history | GPL-2.0 (tool only; does not affect our code) | 2026-11-14 |
| GitHub | Hosting / collaboration | Public repo = *Final Project* link; issues, PRs | GitHub Terms of Service (proprietary service) | 2026-11-14 |
| Claude Code (Anthropic) | AI coding agent (CLI) | Repo scaffolding, documentation, agents & skills, code assistance — see [ai-usage.md](ai-usage.md) | Anthropic Commercial/Consumer Terms (proprietary). Outputs owned by the user per Anthropic terms | 2026-11-14 |
| Python 3.11+ · FastAPI · SQLite | Language / backend | NASA data clients, indicator and rotation engine, JSON API — decisions [0002](decisions/0002-tech-stack.md), [0004](decisions/0004-mobile-pwa.md) | PSF / MIT / public domain (details in [third-party.md](third-party.md)) | 2026-11-14 |
| HTML, CSS, vanilla JavaScript (no framework, no build step) | Frontend (PWA) | Mobile app, offline cache via a hand-written service worker — decision [0005](decisions/0005-pwa-vanilla-js.md) | Web standards; no third-party code | 2026-11-14 |
| _TBD_ | Hosting of demo | | | |
| _TBD_ | Slides / video editor for Project Demo | | | |

> Libraries and packages go in [third-party.md](third-party.md), not here.

## 2. Claude Code: agents and skills

The repo ships project-level configuration for [Claude Code](https://docs.claude.com/en/docs/claude-code) so every teammate gets the same assistants.

### Setup
1. Install Claude Code and log in (each teammate with their own account).
2. Open a terminal in the repo root and run `claude`.
3. Claude automatically reads [`CLAUDE.md`](../CLAUDE.md) (project rules) and discovers `.claude/agents/` and `.claude/skills/`.
4. The shared [`.claude/settings.json`](../.claude/settings.json) disables AI co-author attribution in commits and PRs for every teammate (`attribution.commit` / `attribution.pr` empty). Personal overrides go in `.claude/settings.local.json` (git-ignored) — do not re-enable attribution there.

### Agents (`.claude/agents/*.md`)
Sub-agents with a focused role. Invoke them by asking, e.g. *"use the nasa-data-scout agent to find soil moisture data for Málaga"*, or with `@agent-name`.

| Agent | Role | Typical prompt |
|---|---|---|
| `nasa-data-scout` | Finds and evaluates NASA datasets/APIs; drafts the registry entry | "Find daily precipitation and temperature for Antequera 2000–2025" |
| `agro-domain-advisor` | Sanity-checks agronomy: crop needs, drought indices, adaptation advice | "Is this irrigation recommendation rule reasonable for olive trees?" |
| `compliance-auditor` | Audits licenses, AI declaration, secrets, privacy, NASA branding | "Audit the repo before we make the demo public" |
| `ux-reviewer` | Reviews UI against the Málaga UX guide | "Review the main screen in src/..." |
| `submission-auditor` | Runs the official checklist end-to-end | "Are we ready to Submit for Judging?" |
| `pitch-coach` | Builds the ≤7-slide / ≤30 s demo and rehearses Q&A | "Draft the 7 slides from the README" |

### Skills (`.claude/skills/<name>/SKILL.md`)
Reusable procedures. Invoke them with `/<skill-name>` or let Claude trigger them from the description.

| Skill | What it does |
|---|---|
| `/nasa-dataset-check` | Runs the minimum data check (source, version, license, variables, coverage, limits, role) and writes an entry to `docs/nasa-data.md` |
| `/log-ai-usage` | Appends an entry to `docs/ai-usage.md` |
| `/add-dependency` | Records a library/asset and its license in `docs/third-party.md` |
| `/record-decision` | Creates `docs/decisions/NNNN-*.md` from the template |
| `/ux-review` | Checks a screen against the 7 UX minimums |
| `/submission-check` | Produces a pass/fail report against `docs/submission-checklist.md` |
| `/demo-builder` | Drafts the Project Demo (7 slides or 30 s script) from the docs |
| `/nasa-power-fetch` | Downloads daily NASA POWER climate data for a point/period, caches it in `data/samples/` (offline demo) and registers the source |
| `/agro-indicator` | Computes a documented agroclimatic indicator (frost days, heat stress, GDD, ET₀, water balance, anomalies, bare-field periods…) defined in `docs/indicators.md` |
| `/crop-traits` | Adds/updates crops in `data/crops.csv` with a cited source for every value (`docs/crop-traits.md`) |
| `/rotation-card` | Builds the ≥3 rotation strategies (incl. current) with why / evidence / benefits / gaps / risks and fit to farmer priorities |
| `/design-taste-frontend` | Third-party (Taste, MIT). **UI step 1 — art direction**: palette, type, tone. See [ui-skills.md](ui-skills.md) |
| `/frontend-design` | Third-party (Anthropic, Apache-2.0). **UI step 2 — implementation** of that direction in the PWA (`web/`) |
| `/impeccable` | Third-party (Impeccable, Apache-2.0). **UI step 3 — audit & refinement** (`audit`, `critique`, `polish`…); proposes, never replaces, the direction |
| `/security-review` | **Built into Claude Code** (not a project file). Security review of the pending changes on the current branch: secrets, injection, unsafe input handling. Run it before merging a branch and before making the demo public |

> Team onboarding: see [team-setup.md](team-setup.md).

### Adding a new agent or skill
- Agent: create `.claude/agents/<name>.md` with YAML frontmatter `name`, `description`, optional `tools`, then the system prompt.
- Skill: create `.claude/skills/<name>/SKILL.md` with frontmatter `name`, `description`, then the instructions.
- Add a row to the tables above and to `CLAUDE.md`, and log it in `ai-usage.md` if an AI wrote it.
