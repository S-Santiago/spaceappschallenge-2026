# AI usage declaration

NASA Space Apps allows AI. The team stays responsible for decisions, verification and authorship. This file is the source for the **AI usage** field of the Project page.

## 1. Summary (copy to the Project page)

> _TODO before submission — e.g.:_ "We used Claude Code (Anthropic, model Claude Opus 5.5) to scaffold the repository and documentation, to draft code for <X> and to review UX and compliance. All AI-generated code was reviewed and tested by the team; all data values come from the NASA sources listed in our data registry, not from the AI. No AI-generated images/video were used." _(adapt)_

## 2. Tools

| Tool | Provider | Model / version | Used for |
|---|---|---|---|
| Claude Code | Anthropic | Claude Opus 5.5 (`claude-opus-5-5`) | Repo scaffolding, documentation, agents/skills, code assistance |
| _add others (ChatGPT, Copilot, image generators…)_ | | | |

## 3. Rules we follow
- No AI output is presented as verified without human review (code run/tested, numbers checked against the source data, references opened).
- AI-generated **images and videos carry a visible "AI-generated" label**.
- AI-generated code/data is acknowledged here and, where relevant, in file headers or commit trailers.
- No NASA logos, flags or mission identifiers in generated content.
- No personal data, credentials or confidential material is sent to AI tools.

## 4. Log

| # | Date/time | Tool | What was generated | Where (files) | Human verification |
|---|---|---|---|---|---|
| 1 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Repository structure, README/CLAUDE/CONTRIBUTING, all `docs/` templates, `.claude/agents`, `.claude/skills`, GitHub templates | whole initial commit | Reviewed by the team; content derived from the official Málaga participant guide and UX guide |
| 2 | 2026-11-14 | Claude Code (Claude Opus 5.5) | English rendering of the official challenge statement (from a Spanish copy) and challenge-specific updates to docs/agents | `docs/challenge.md`, `README.md`, `CLAUDE.md`, `docs/nasa-data.md` | Team to compare against the official English page |
| 3 | 2026-11-14 | Claude Code (Claude Opus 5.5) | NASA POWER and MODIS (ORNL) data clients + JSON cache; official title, link and Resources list in challenge.md; 4-person work plan proposal | `src/fieldshift/`, `requirements.txt`, `docs/challenge.md`, `docs/work-plan.md` | Clients run against the live APIs for Málaga (36.72, -4.42): 7,670 POWER days and 45 MODIS NDVI composites returned. Resources list checked against the official page. Pending: team review |
| 5 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Stack decision record 0002, architecture, work-plan and team updates; indicator catalog aligned with #9; crop catalogue schema aligned with #7; CODEOWNERS review split; mobile-first/low-end-phone UX constraints | `docs/decisions/0002-tech-stack.md`, `docs/architecture.md`, `docs/work-plan.md`, `docs/team.md`, `docs/indicators.md`, `docs/crop-traits.md`, `data/crops.csv`, `docs/ux-guidelines.md`, `.github/CODEOWNERS`, `.claude/` | Content taken from the team's issues (#1, #6, #7, #9, #16) and team decisions; to be confirmed by track owners |
| 4 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Skills `nasa-power-fetch`, `agro-indicator`, `crop-traits`, `rotation-card` (aligned with `src/fieldshift/` and the work-plan JSON shapes); indicator catalog and crop-table templates; team setup guide | `.claude/skills/`, `docs/indicators.md`, `docs/crop-traits.md`, `data/crops.csv`, `docs/team-setup.md` | Reviewed by the team; formulas (FAO-56) and API parameters to be verified against official sources on first use |
| 6 | 2026-11-14 | Claude Code (Claude Opus 5.5) | GitHub ruleset protecting `main` (PR required, no approval, no force push/deletion, squash-only), CODEOWNERS and Git workflow section | GitHub repo settings, `.github/CODEOWNERS`, `docs/team-setup.md` | Ruleset checked via GitHub API: direct push to `main` rejected |
| 7 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Climate indicators module (I-01..I-11 → Shape 1), unit tests, threshold justifications in the indicator catalog | `src/fieldshift/climate.py`, `tests/test_climate.py`, `pytest.ini`, `docs/indicators.md`, `docs/architecture.md` | 10 pytest tests pass (hand-checked values, FAO-56 example 8 for Ra); run on live NASA data for Málaga (36.72, -4.42). Threshold references and the NDVI threshold still to be reviewed by @HaoJunnnzhang / `agro-domain-advisor` |
| 8 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Rotation engine (candidates, scoring, card texts → Shape 2), its tests and test-only crop fixture, Scoring section of the indicator catalog | `src/fieldshift/rotations.py`, `tests/test_rotations.py`, `tests/conftest.py`, `tests/fixtures/crops.csv`, `docs/indicators.md`, `docs/work-plan.md`, `docs/architecture.md` | 26 pytest tests pass; run on the Málaga profile with several priority/irrigation/slope settings and outputs checked by hand. Crop values in the fixture are test-only, not for the demo. Scoring rules still to be reviewed by @HaoJunnnzhang / `agro-domain-advisor` |
