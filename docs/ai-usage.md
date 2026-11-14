# AI usage declaration

NASA Space Apps allows AI. The team stays responsible for decisions, verification and authorship. This file is the source for the **AI usage** field of the Project page.

## 1. Summary (copy to the Project page)

> _TODO before submission — e.g.:_ "We used Claude Code (Anthropic, model Claude Opus 5.5) to scaffold the repository and documentation, to draft code for <X> and to review UX and compliance. All AI-generated code was reviewed and tested by the team; all data values come from the NASA sources listed in our data registry, not from the AI. No AI-generated images/video were used." _(adapt)_

## 2. Tools

| Tool | Provider | Model / version | Used for |
|---|---|---|---|
| Claude Code | Anthropic | Claude Opus 5.5 (`claude-opus-5-5`) | Repo scaffolding, documentation, agents/skills, code assistance |
| _add others (ChatGPT, Copilot, image generators…)_ | | | |

## 3. Rules we follow
- No AI output is presented as verified without human review (code run/tested, numbers checked against the source data, references opened).
- AI-generated **images and videos carry a visible "AI-generated" label**.
- AI-generated code/data is acknowledged here and, where relevant, in file headers or commit trailers.
- No NASA logos, flags or mission identifiers in generated content.
- No personal data, credentials or confidential material is sent to AI tools.

## 4. Log

| # | Date/time | Tool | What was generated | Where (files) | Human verification |
|---|---|---|---|---|---|
| 1 | 2026-11-14 | Claude Code (Claude Opus 5.5) | Repository structure, README/CLAUDE/CONTRIBUTING, all `docs/` templates, `.claude/agents`, `.claude/skills`, GitHub templates | whole initial commit | Reviewed by the team; content derived from the official Málaga participant guide and UX guide |
| 2 | 2026-11-14 | Claude Code (Claude Opus 5.5) | English rendering of the official challenge statement (from a Spanish copy) and challenge-specific updates to docs/agents | `docs/challenge.md`, `README.md`, `CLAUDE.md`, `docs/nasa-data.md` | Team to compare against the official English page |
