---
name: rotation-card
description: Build the comparison of crop-rotation strategies required by Challenge 06 — at least three, including the farmer's current rotation — each as a card that states why it was suggested, the evidence behind it (NASA indicators + crop traits + local info), benefits, information gaps and risks needing local review, scored against the farmer's priorities. Use when designing, generating or reviewing rotation suggestions shown by the tool.
---

# Rotation card

Inputs: location (or its indicator results), the farmer's **current rotation**, farmer **priorities** (e.g. save water, extra income, soil structure, less erosion, less fertilizer, forage) and **constraints** (water availability, machinery, market).

## 1. Strategies
- Card **A is always the current rotation** (baseline). Then **at least two alternatives** (B, C…).
- Alternatives must be agronomically plausible for the location: check cycle, frost/heat limits and water needs against `data/crops.csv` and the indicators. Use classic levers: add a legume (nitrogen), a cover crop in bare periods, a deep-rooted crop, a drought-tolerant crop, a different botanical family (pest cycles).

## 2. Card structure (identical for every strategy)
```
### <Letter> · <Rotation, e.g. Wheat → Chickpea → Barley> (<years>-year cycle)
**Why suggested:** <1–2 sentences linked to an indicator or a farmer priority>
**Evidence:**
  - <indicator ID + value + period + dataset>  (from docs/indicators.md)
  - <crop trait + source ID>  (from data/crops.csv)
  - <local info given by the farmer>
**Possible benefits:** <soil health, water, erosion, nitrogen, pests, income, forage>
**Information gaps:** <what we do not know: prices, local diseases, soil test, plot-level data…>
**Risks needing local review:** <what a farmer or agronomist must confirm before acting>
**Fit with your priorities:** <priority → good / neutral / poor + one-line reason>
**Confidence:** high / medium / low — <why>
```

## 3. Comparison table and scores
After the cards, a table with one row per strategy and one column per farmer priority, plus water demand vs the climatic water balance and months of bare soil.
The engine (`src/fieldshift/rotations.py`, track B in `docs/work-plan.md`) returns **Shape 2** with `scores` 0–100 (`water`, `soil`, `income`, `risk`, `overall`). Scores are allowed **only if** the scoring rule is documented: add a "Scoring" section to `docs/indicators.md` explaining each sub-score (inputs, formula, weights, how farmer priorities change the weights). No hidden weights. In the UI, show scores with the words good / neutral / poor next to the number.

## 3b. Data contract
Each card maps 1:1 to a Shape 2 object: `why`, `evidence[]`, `benefits[]`, `gaps[]`, `risks_to_review[]`. Inputs: Shape 1 (climate profile) + `data/crops.csv` + farmer rotation & priorities.

## 4. Hard rules
- **No claim without evidence.** Every statement in "Why" and "Benefits" must point to an indicator, a crop trait with source, or farmer input. If it cannot, move it to "Information gaps".
- **No invented numbers** (yields, prices, savings). Use qualitative levels unless a cited source gives a number.
- Never rank a strategy as "the best": present trade-offs.
- Always end with the disclaimer: *"This tool supports, and does not replace, your judgment and local agricultural advice."*
- Use plain words for farmers; explain any technical term in one line (or link to the glossary).
- If an AI model wrote text for the cards, log it with `log-ai-usage` and show it as AI-assisted in the UI.

## 5. Review
Before showing cards in the demo, have the `agro-domain-advisor` agent review them. In the data/code, cards should be generated from structured data (JSON) so the UI and the docs show the same content.

Answer the team in Spanish; card content in English.
