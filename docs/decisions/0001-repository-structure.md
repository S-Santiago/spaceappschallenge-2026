# 0001 · Repository structure, documentation and AI tooling

- **Date:** 2026-11-14
- **Status:** accepted
- **Deciders:** team

## Context
The NASA Space Apps rules require the submission to be in English, publicly accessible, to declare AI usage, to trace NASA data and to respect third-party licenses. With ~36 h of development, the team needs these obligations built into the repo from minute one rather than written at the last moment.

## Decision
- English-only repository; team chat in Spanish.
- `docs/` holds living registries: `nasa-data.md`, `ai-usage.md`, `third-party.md`, `decisions/`.
- Claude Code project agents (`.claude/agents/`) and skills (`.claude/skills/`) automate the recurring obligations (data check, AI log, license log, UX review, submission audit, demo building).
- Large data is git-ignored; only small samples are committed.
- Organizer event material (PDFs, posters, judge photos) is **not** committed — it is not ours to redistribute.
- Project license and tech stack deferred to later decisions.

## Consequences
Every PR must update the relevant registry (enforced by the PR template). The submission page can be filled mostly by copying from `docs/`.
