# 0003 · Project license: MIT

- **Date:** 2026-11-14
- **Status:** accepted
- **Deciders:** team

## Context
The repository is public and is the *Final Project* link of the NASA Space Apps submission. Without a license, default copyright applies and nobody may legally reuse the code.

## Options considered
MIT, Apache-2.0, GPL-3.0, AGPL-3.0 (comparison in [../licensing.md](../licensing.md)).

## Decision
**MIT** for the team's code and documentation: simplest, most common in hackathons, compatible with all our current dependencies (httpx BSD-3-Clause; Streamlit Apache-2.0; pytest MIT).

## Consequences
- `LICENSE` file at the repo root; README and `docs/licensing.md` updated.
- The MIT license does **not** cover NASA/partner data (own terms in `nasa-data.md`), third-party libraries/assets (`third-party.md`), or NASA names and insignia.
- New dependencies must stay MIT-compatible; copyleft (GPL/AGPL) packages need a team discussion first.
