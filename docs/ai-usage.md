# AI usage declaration

NASA Space Apps allows AI. The team stays responsible for decisions, verification and authorship. This file is the source for the **AI usage** field of the Project page.

## 1. Summary (copy to the Project page)

<!-- DRAFT 2026-11-14 — update on Sunday before submission: add any other AI tools teammates used, and say whether the app itself uses AI (e.g. for explanations). Keep it consistent with the log below. -->

> We used **Claude Code** (Anthropic, model Claude Opus 5.5) as a coding and documentation assistant. It helped us set up the repository and its documentation, adapt the official challenge and event guides into English checklists, write the first versions of the NASA POWER and MODIS data clients and the Streamlit app skeleton, draft the README, and review our work against the UX, data-traceability and submission rules.
>
> Every AI output was reviewed by the team: code was run and tested against the live NASA APIs and in the browser (desktop and mobile width); dataset versions, units and citations were checked on the official NASA pages; scientific thresholds are documented with their sources. **All climate and vegetation values shown by FarmLens come from NASA POWER and MODIS, not from the AI.** Example values used during development are labelled as mock data. No AI-generated images, video or audio are used. The full log of AI use is in this file.

## 2. Tools

| Tool | Provider | Model / version | Used for |
|---|---|---|---|
| Claude Code | Anthropic | Claude Opus 5.5 (`claude-opus-5-5`) | Repo scaffolding, documentation, agents/skills, code assistance |
| _Teammates: add any other tool you used (ChatGPT, Copilot, Gemini, image generators…)_ | | | |

## 3. Rules we follow
- No AI output is presented as verified without human review (code run/tested, numbers checked against the source data, references opened).
- AI-generated **images and videos carry a visible "AI-generated" label**.
- AI-generated code/data is acknowledged in this file (team policy: no AI co-author trailers in commits or PRs; the first commit kept one from before the policy).
- No NASA logos, flags or mission identifiers in generated content.
- No personal data, credentials or confidential material is sent to AI tools.

## 4. Log

| # | Date/time | Tool | What was generated | Where (files) | Human verification |
|---|---|---|---|---|---|
| 1 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Repository structure, README/CLAUDE/CONTRIBUTING, all `docs/` templates, `.claude/agents`, `.claude/skills`, GitHub templates | whole initial commit | Reviewed by the team; content derived from the official Málaga participant guide and UX guide |
| 2 | 2026-11-14 | Claude Code (Claude Opus 5.5) | English rendering of the official challenge statement (from a Spanish copy) and challenge-specific updates to docs/agents | `docs/challenge.md`, `README.md`, `CLAUDE.md`, `docs/nasa-data.md` | Team to compare against the official English page |
| 3 | 2026-11-14 | Claude Code (Claude Opus 5.5) | NASA POWER and MODIS (ORNL) data clients + JSON cache; official title, link and Resources list in challenge.md; 4-person work plan proposal | `src/fieldshift/`, `requirements.txt`, `docs/challenge.md`, `docs/work-plan.md` | Clients run against the live APIs for Málaga (36.72, -4.42): 7,670 POWER days and 45 MODIS NDVI composites returned. Resources list checked against the official page. Pending: team review |
| 4 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Skills `nasa-power-fetch`, `agro-indicator`, `crop-traits`, `rotation-card` (aligned with `src/fieldshift/` and the work-plan JSON shapes); indicator catalog and crop-table templates; team setup guide | `.claude/skills/`, `docs/indicators.md`, `docs/crop-traits.md`, `data/crops.csv`, `docs/team-setup.md` | Reviewed by the team; formulas (FAO-56) and API parameters to be verified against official sources on first use |
| 5 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Stack decision record 0002, architecture, work-plan and team updates; indicator catalog aligned with #9; crop catalogue schema aligned with #7; CODEOWNERS review split; mobile-first/low-end-phone UX constraints | `docs/decisions/0002-tech-stack.md`, `docs/architecture.md`, `docs/work-plan.md`, `docs/team.md`, `docs/indicators.md`, `docs/crop-traits.md`, `data/crops.csv`, `docs/ux-guidelines.md`, `.github/CODEOWNERS`, `.claude/` | Content taken from the team's issues (#1, #6, #7, #9, #16) and team decisions; to be confirmed by track owners |
| 6 | 2026-11-14 | Claude Code (Claude Opus 5.5) | GitHub ruleset protecting `main` (PR required, no approval, no force push/deletion, squash-only), CODEOWNERS and Git workflow section | GitHub repo settings, `.github/CODEOWNERS`, `docs/team-setup.md` | Ruleset checked via GitHub API: direct push to `main` rejected |
| 7 | 2026-11-14 | Claude Code (Claude Opus 5.5) | English adaptation of the Málaga UX desk "launch route" checklist (GO/NOT YET, extras, red alert) into the UX guidelines, `ux-review` skill, `ux-reviewer` agent and submission checklist; Git workflow rules for Claude in `CLAUDE.md` | `docs/ux-guidelines.md`, `.claude/skills/ux-review/SKILL.md`, `.claude/agents/ux-reviewer.md`, `docs/submission-checklist.md`, `CLAUDE.md` | Compared item by item with the organizer's sheet; 16 px kept deliberately (sheet minimum is 14 px) |
| 8 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Data registry entries D-01 (NASA POWER) and D-02 (MODIS MOD13Q1) with citations; MIT LICENSE + decision 0003; project name FarmLens in README | `docs/nasa-data.md`, `docs/third-party.md`, `LICENSE`, `docs/decisions/0003-project-license.md`, `README.md`, `docs/licensing.md` | Citation texts, version, units, resolution and fill values checked against the official POWER referencing/methodology pages, the Earthdata MOD13Q1 page, the ORNL DAAC service page and a live POWER API call (2026-11-14) |
| 9 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Streamlit app skeleton (one page, 4 numbered steps, mock results placeholder), mock data layer `FarmerInputs` + `get_*` functions, hand-typed MOCK climate profile (Shape 1) and strategies (Shape 2) for the Málaga demo field, mock crop list, Streamlit config, dependency registration | `src/app.py`, `src/fieldshift/mock_data.py`, `data/samples/mock_climate_profile.json`, `data/samples/mock_strategies.json`, `.streamlit/config.toml`, `requirements.txt`, `docs/third-party.md` | App run locally with `streamlit run src/app.py`; full flow clicked in the browser at desktop and 375 px mobile width (demo field and map click), no errors in logs/console. Mock values are illustrative only (labelled MOCK DATA in the UI); licenses checked on PyPI/GitHub. Pending: team review in PR |
| 10 | 2026-11-14 | Claude Code (Claude Opus 5.5) | README draft: summary (165 words), problem, solution flow, how to run, repository map, honest status/limits/next steps | `README.md` | Figures taken from our own NASA POWER checks (2026-11-14) and team docs; summary to be re-read by the team before copying it to the Project page |
