---
name: submission-check
description: Produce a pass/fail report of the NASA Space Apps submission against docs/submission-checklist.md, with automatic checks on the repo (README TODOs, summary word count, data/AI/license registries, secrets, LICENSE) and a list of manual checks for the team owner. Use before Submit for Judging and after any late change.
---

# Submission check

1. Read `docs/submission-checklist.md`.
2. Automatic checks:
   - `README.md` sections 1–5 contain no `TODO`.
   - Summary in README section 1 has 50–200 words (count them).
   - `docs/nasa-data.md` section 1 has ≥ 1 complete entry for a NASA resource.
   - `docs/ai-usage.md` summary is not a TODO.
   - `docs/third-party.md` covers every dependency in the manifests.
   - `LICENSE` file exists.
   - No secrets: search tracked files for patterns like `api_key`, `password`, `token`, `EARTHDATA_PASSWORD=` with a value; `.env` not tracked.
   - No NASA logo files or organizer PDFs tracked.
   - Remaining `TODO` count in `docs/`.
3. Manual checks (list for the team owner): team members registered & accepted in Málaga; demo link public in a private window; demo ≤ 7 slides or ≤ 30 s; Submit for Judging pressed and confirmation visible; re-submit after late edits.
4. Output a table ✅/❌/🔍 and the blockers first. Show the time remaining until **Sun 15 Nov 2026 23:59 Europe/Madrid**.
