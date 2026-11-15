# CLAUDE.md — instructions for AI agents in this repository

## Context
- Team project **FarmLens** for **NASA Space Apps Challenge 2026 · Málaga**, **Challenge 06: Adapting farms with NASA data** — a decision-support tool combining NASA Earth observations with local soil info, crop traits and farmer priorities to compare **crop-rotation strategies** (≥3, including the current one; each with why / evidence / benefits / information gaps / risks needing local review). Full statement: `docs/challenge.md`. The tool supports, never replaces, farmers' judgment.
- Development window: Sat 14 Nov 2026 09:00 → **Sun 15 Nov 2026 23:59 (Europe/Madrid)**, the official NASA deadline. Local pitches Sun 17:30–19:00. Time is the scarcest resource: prefer the simplest thing that can be demoed.
- Tech stack: **mobile app as a PWA + Python API + SQLite** (`docs/decisions/0004-mobile-pwa.md`, which supersedes the Streamlit UI of `0002`). Backend: FastAPI in `src/fieldshift/api.py` over the Python engine (`src/fieldshift/`). Frontend: plain HTML/CSS/JS ES modules in `web/` with a hand-written service worker, no build step, served by the API on the same origin (`docs/decisions/0005-pwa-vanilla-js.md`). The early Streamlit test harness was retired once the PWA reached parity. Do not introduce another framework without a new decision record.
- **Predictions are statistics over NASA historical data, not AI/ML** (frequencies, percentiles, return periods, trends with confidence intervals). Define each one in `docs/indicators.md` before coding and label it "based on the last 20 years", never as a forecast.
- Work is organised in sprints: `docs/sprint-plan.md` (Scrum Master: @sebasbarrabaja-cmyk). Check the current milestone before picking a task.
- **Target users: farmers with at most a low/mid-range phone, slow or unstable mobile data and little tech experience.** Everything user-facing must be **mobile-first and lightweight** (see `docs/ux-guidelines.md` → "Mobile-first, low-end phones"). Desktop is secondary.
- **Local servers.** API + PWA: `PYTHONPATH=src uvicorn fieldshift.api:app --reload` from the repo root, always on `localhost:8000` (API docs at `/docs`). **8000 is the only allowed port** because the backup Cloudflare tunnel points at it: never start the API on another port (8001, 8002…); if 8000 is busy, stop the process holding it and restart the API on 8000.
- **Public demo:** https://farmlens-530581375456.europe-southwest1.run.app — Google Cloud Run (`europe-southwest1`, Space Apps Google Cloud offer, decision `0008`), built from the root `Dockerfile`. **Not redeployed automatically**: after a merge to `main`, ask a teammate with Cloud access to run `gcloud run deploy farmlens --source . --region europe-southwest1`. The container uses Cloud Run's `$PORT` (8080); locally the API stays on 8000.
- Project license: **MIT** (`LICENSE`, `docs/decisions/0003-project-license.md`). Every dependency and asset must stay compatible with it.

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

## Git workflow — `main` is protected
- **Never commit or push to `main`** (direct pushes, force pushes and deletion are rejected by GitHub).
- Always: `git switch main && git pull` → `git switch -c <type>/<topic>` (`feat/`, `fix/`, `data/`, `docs/`, `chore/`) → commit → `git push -u origin <branch>` → `gh pr create --fill`.
- **No approval is required**: the author may merge their own PR (`gh pr merge --squash`) once all review conversations are resolved. Only merge when the user asks you to.
- **Squash only** → the PR title becomes the commit on `main`: write it as Conventional Commits in English (`feat: add climate indicators`).
- Fill the PR template checklist. No AI attribution lines in the PR body or commits.
- For risky changes (shared code, data pipeline, demo path) suggest asking the reviewer in `.github/CODEOWNERS` first.
- If a push to `main` is rejected, do not work around it: move the commits to a new branch, push it and open a PR.
- If GitHub says the branch is out of date, update it (`gh pr update-branch` or rebase on `origin/main`).

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
- UI/UX (vendored third-party, do not edit their files): `design-taste-frontend` (art direction) → `frontend-design` (implementation) → `impeccable` (audit & refinement). Follow the hierarchy and conflict rules in `docs/ui-skills.md`; project rules (`docs/ux-guidelines.md`, decisions 0004/0005: mobile-first, < 200 KB of JS, no build step) override all three.
- Security: run the built-in `/security-review` before merging a branch into `main` and before the demo goes public.
