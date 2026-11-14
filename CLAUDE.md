# CLAUDE.md — instructions for AI agents in this repository

## Context
- Team project for **NASA Space Apps Challenge 2026 · Málaga**, **Challenge 06: Adapting farms with NASA data** — a decision-support tool combining NASA Earth observations with local soil info, crop traits and farmer priorities to compare **crop-rotation strategies** (≥3, including the current one; each with why / evidence / benefits / information gaps / risks needing local review). Full statement: `docs/challenge.md`. The tool supports, never replaces, farmers' judgment.
- Development window: Sat 14 Nov 2026 09:00 → **Sun 15 Nov 2026 23:59 (Europe/Madrid)**, the official NASA deadline. Local pitches Sun 17:30–19:00. Time is the scarcest resource: prefer the simplest thing that can be demoed.
- Tech stack: **not decided yet**. Read `docs/architecture.md` before assuming one. Do not introduce a framework without recording it in `docs/decisions/`.
- Project license: **pending** (`docs/licensing.md`). Do not add a LICENSE file unless the team asks.

## Language
- **Everything committed to the repo is in English** (NASA rule: page, slides and written materials in English).
- Talk to the team in **Spanish** in chat.

## Non-negotiable rules (from the official participant guide)
1. **AI declaration**: whenever an AI tool produces code, text, data or media that ends up in the repo, add an entry to `docs/ai-usage.md` (skill `log-ai-usage`). Generated images/videos must carry a visible "AI-generated" mark.
2. **NASA data traceability**: every dataset used must be registered in `docs/nasa-data.md` with source, version/access date, license, variables & units, coverage, limits and role (skill `nasa-dataset-check`). At least one NASA resource from the challenge must have a real role in the solution.
3. **Third-party licenses**: every dependency, asset, font, image, snippet or dataset not created by the team goes in `docs/third-party.md` (skill `add-dependency`). Being accessible online does not make something reusable.
4. **No NASA branding** in generated content (logos, insignia, flags, mission patches or identifiers).
5. **Privacy**: no credentials, API keys or personal data in the repo. Secrets go in `.env` (git-ignored); document variables in `.env.example`. No names, voices or recognizable images of minors.
6. **Honesty**: clearly separate *built*, *simulated* and *future* in docs and demo. Never present unverified AI output as verified.
7. **Never commit organizer event material** (PDFs, posters, judge photos). It lives outside the repo.

## Working conventions
- Small commits, Conventional Commits style (`feat:`, `fix:`, `docs:`, `data:`, `chore:`).
- **No AI authorship in git**: never add `Co-Authored-By` or "Generated with" lines to commits or PRs. AI usage is declared only in `docs/ai-usage.md`.
- Large data never goes into git: use `data/raw/` and `data/processed/` (ignored); keep download scripts and a small sample in `data/samples/`.
- Record significant decisions as `docs/decisions/NNNN-title.md` (skill `record-decision`).
- Keep `README.md` sections 1–5 up to date: judges read the README first.

## Agents (`.claude/agents/`)
| Agent | Use it for |
|---|---|
| `nasa-data-scout` | Find & evaluate NASA datasets/APIs for agriculture & climate |
| `agro-domain-advisor` | Validate the agronomic logic (crops, drought indices, adaptation measures) |
| `compliance-auditor` | Check licenses, AI declaration, privacy, NASA branding |
| `ux-reviewer` | Review the UI against `docs/ux-guidelines.md` |
| `submission-auditor` | Verify the full submission against the official checklist |
| `pitch-coach` | Build the ≤7-slide / ≤30 s demo and rehearse the Q&A |

## Skills (`.claude/skills/`)
`nasa-dataset-check`, `log-ai-usage`, `add-dependency`, `record-decision`, `ux-review`, `submission-check`, `demo-builder`.
