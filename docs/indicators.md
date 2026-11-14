# Indicator catalog

Every number the tool shows that is derived from data must be defined here **before** it is implemented (skill `/agro-indicator`). This is our evidence for the **Validity** criterion.

## Entry template
```markdown
### I-XX · <Name>
| Field | Value |
|---|---|
| Plain meaning | What it tells a farmer, in one sentence |
| Formula | |
| Inputs | Dataset (registry ID in nasa-data.md) + variables |
| Unit | |
| Aggregation | daily → month / season / year |
| Thresholds & origin | value + where it comes from (crop table, literature, assumption) |
| Reference | FAO-56, paper, official doc… |
| Limits | resolution, model vs observation, missing data |
| Farmer sentence | "On average {n} frost days per year, mostly in {month}…" |
| Reviewed by agro-domain-advisor | yes / no |
| Implemented in | `src/...` function name |
```

## Indicators
_None implemented yet. Standard definitions to start from are listed in `.claude/skills/agro-indicator/SKILL.md` (I-01 … I-11)._
