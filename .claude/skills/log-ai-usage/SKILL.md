---
name: log-ai-usage
description: Append an entry to the AI usage declaration (docs/ai-usage.md) describing which AI tool generated what, where it lives and how the team verified it. Use after any AI-generated code, text, data, image or video is added to the repo or the demo.
---

# Log AI usage

1. Gather: date/time (Europe/Madrid), tool + model/version, what was generated, files/paths affected, how a human verified it (ran tests, checked numbers against source data, opened references, reviewed visually).
   - If unknown, inspect `git log` and `git diff`, then ask the team what was AI-assisted and how it was verified — do not invent it. (Commits carry no AI trailers by team policy.)
2. If the tool is new, add it to the **Tools** table in `docs/ai-usage.md` and to `docs/tools.md`.
3. Append a row to the **Log** table with the next number.
4. If the content is an **image or video**, confirm it carries a visible "AI-generated" label and contains no NASA logos/insignia/mission identifiers. If not, warn the team.
5. If the entry changes the overall picture, update the **Summary** paragraph (it is copied to the Project page).

Keep entries factual and in English.
