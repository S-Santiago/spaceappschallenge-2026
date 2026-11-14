---
name: record-decision
description: Create a numbered decision record in docs/decisions/ (tech stack, license, dataset choice, scope cut, architecture) from the template. Use when the team makes or changes a significant decision.
---

# Record a decision

1. Find the next number: list `docs/decisions/` and take the highest `NNNN` + 1.
2. Copy `docs/decisions/0000-template.md` to `docs/decisions/NNNN-<kebab-title>.md`.
3. Fill context, options considered (with pros/cons), the decision and consequences. Ask the team for anything missing — keep it short (hackathon pace).
4. If it supersedes an earlier record, set that record's status to `superseded by NNNN`.
5. Propagate consequences:
   - Tech stack → update `docs/architecture.md`, README "How to run", `docs/tools.md`.
   - License → add `LICENSE` file, update README table and `docs/licensing.md`.
   - Dataset → run `nasa-dataset-check`.
   - Scope cut → update README "Limitations & next steps".
