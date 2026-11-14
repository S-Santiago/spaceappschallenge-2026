# Contributing (team workflow)

## Branches
- `main` must always be demo-able. Freeze risky changes on `main` after **Sunday 15:00**.
- Use short-lived branches: `feat/<topic>`, `data/<dataset>`, `docs/<topic>`, `fix/<topic>`.
- Open a Pull Request (template in `.github/`) and get a quick review from a teammate.

## Commits
Conventional Commits: `feat:`, `fix:`, `docs:`, `data:`, `chore:`, `refactor:`.
If an AI tool generated a substantial part of a commit, keep its trailer (e.g. `Co-Authored-By:`) **and** log it in `docs/ai-usage.md`.

## Definition of done for any change
- [ ] Works, or is clearly marked as simulated/mock.
- [ ] New dependency or asset → `docs/third-party.md`.
- [ ] New dataset → `docs/nasa-data.md`.
- [ ] AI-generated content → `docs/ai-usage.md`.
- [ ] Relevant decision → `docs/decisions/`.
- [ ] Written in English.
- [ ] No secrets or personal data.

## Secrets
Copy `.env.example` to `.env` and fill it locally. Never commit `.env`. Earthdata Login credentials and NASA API keys are personal.

## Using Claude Code
See [`docs/tools.md`](docs/tools.md#claude-code-agents-and-skills) for how to invoke the project agents and skills.
