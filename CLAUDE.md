# CLAUDE.md — instructions for AI agents in this repository

## Context
- Team project for **NASA Space Apps Challenge 2026 · Málaga**, **Challenge 06: Adapting farms with NASA data** — a decision-support tool combining NASA Earth observations with local soil info, crop traits and farmer priorities to compare **crop-rotation strategies** (≥3, including the current one; each with why / evidence / benefits / information gaps / risks needing local review). Full statement: `docs/challenge.md`. The tool supports, never replaces, farmers' judgment.
- Development window: Sat 14 Nov 2026 09:00 → **Sun 15 Nov 2026 23:59 (Europe/Madrid)**, the official NASA deadline. Local pitches Sun 17:30–19:00. Time is the scarcest resource: prefer the simplest thing that can be demoed.
- Tech stack: **Python 3.11+ · Streamlit · SQLite** (`docs/decisions/0002-tech-stack.md`). Do not introduce another framework without a new decision record.
- **Target users: farmers with at most a low/mid-range phone, slow or unstable mobile data and little tech experience.** Everything user-facing must be **mobile-first and lightweight** (see `docs/ux-guidelines.md` → "Mobile-first, low-end phones"). Desktop is secondary.
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

## Git workflow — `main` is protected (ruleset "Protect main")
- **Never commit or push to `main`.** Direct pushes, force pushes and deletion are blocked for everyone (no bypass).
- Always: `git switch main && git pull` → `git switch -c <type>/<topic>` (`feat/`, `fix/`, `data/`, `docs/`) → commit → `git push -u origin <branch>` → `gh pr create`.
- **PR title = final commit message** (merge is squash-only) → write it in Conventional Commits form, in English (`feat: add climate indicators`).
- Fill the PR template checklist. No AI attribution lines in the PR body.
- A PR needs **1 approval from someone other than the last pusher** and **all review threads resolved**. Pushing after approval dismisses it → finish the changes before requesting review.
- Reviewers: code → @S-Santiago; visuals/docs → @sebasbarrabaja-cmyk (auto-requested via `.github/CODEOWNERS`); any teammate's approval counts.
- If a push to `main` is rejected, do not try to work around it: move the commits to a branch (`git switch -c <branch>`; then reset local `main` to `origin/main` only after the branch is pushed) and open a PR.

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
- Compliance: `nasa-dataset-check`, `log-ai-usage`, `add-dependency`, `record-decision`, `ux-review`, `submission-check`, `demo-builder`.
- Core product: `nasa-power-fetch` → `agro-indicator` → `crop-traits` → `rotation-card`. Any derived number must be defined in `docs/indicators.md`; any crop value must have a source in `data/crops.csv`.
- Security: run the built-in `/security-review` before merging a branch into `main` and before the demo goes public.
