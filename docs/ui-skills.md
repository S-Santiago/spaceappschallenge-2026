# UI/UX skills for Claude Code — sources and coexistence rules

The repository vendors three third-party UI/UX skills in `.claude/skills/` so every teammate gets them on clone, without installing anything globally. This file records where each one comes from and how the three work together. The skill files themselves are **unmodified upstream copies**; the rules below live here so we never have to patch them.

## 1. What is vendored

| Role | Skill (`/name`) | Folder | Upstream | Version | License |
|---|---|---|---|---|---|
| Art direction | `/design-taste-frontend` | `.claude/skills/design-taste-frontend/` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) → `skills/taste-skill/` | 2.5.1 (commit `f6b7657`) | MIT (`LICENSE` copied into the folder) |
| Implementation | `/frontend-design` | `.claude/skills/frontend-design/` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) → `plugins/frontend-design/skills/frontend-design/` | plugin 1.1.1 | Apache-2.0 (`LICENSE.txt`) |
| Audit & refinement | `/impeccable` | `.claude/skills/impeccable/` | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) → `.claude/skills/impeccable/` (the project-install build, not the `plugin/` build) | 4.9.1 (commit `1995764`), engine 0.1.24 | Apache-2.0 (`LICENSE` and `NOTICE.md` copied into the folder) |

Copied on 2026-11-14. Folder names match each skill's `name:` field; Taste's own Stop hook and Impeccable's launcher look for exactly these paths.

## 2. Project rules come first

These skills are written for generic products (Taste mainly for marketing websites). **Our own constraints override all three**:

1. `CLAUDE.md` and [`ux-guidelines.md`](ux-guidelines.md) — farmers on low/mid-range phones, slow mobile data, little tech experience: mobile-first, lightweight, 48 px targets, ≥16 px text, WCAG 2.2 AA contrast, no colour-only states.
2. [Decision 0002](decisions/0002-tech-stack.md) — the app is **Streamlit**. No React/Tailwind/other framework because a skill suggests it.
3. Honesty, licensing and branding rules — no NASA branding, every external asset registered in [`third-party.md`](third-party.md), simulated data labelled as such.

If a skill instruction conflicts with any of these, the project rule wins and the skill instruction is skipped (say so in the PR).

## 3. Hierarchy of responsibilities

| Order | Skill | Owns | Must not |
|---|---|---|---|
| 1 | **Taste** (`/design-taste-frontend`) | The art direction: palette, type pairing, tone of voice, visual personality, what "good" looks like for FarmLens | Dictate implementation details, or impose its marketing-site page plan (hero, one section per screen, stock photographs, shaders/WebGL scenes) on the Streamlit app |
| 2 | **Frontend Design** (`/frontend-design`) | Turning that direction into working, coherent UI in our stack (Streamlit components + the single global CSS layer in `src/app.py`) | Pick a new palette, typeface or personality when a Taste direction already exists; its "take aesthetic risk" applies only inside that direction |
| 3 | **Impeccable** (`/impeccable audit`, `critique`, `polish`, …) | Auditing the implementation, detecting defects and fixing or proposing fixes | Replace the art direction. It may fix defects directly (contrast, spacing, touch targets, states, consistency); anything that changes the direction is a **proposal** the team approves first |

Rules of thumb:

- **No direction yet?** Run Taste first and write the result down (palette tokens, fonts, tone) in the PR or in `DESIGN.md` if Impeccable's `document` command is used. Frontend Design and Impeccable then read it instead of inventing their own.
- **Accessibility is a floor, not a taste question.** An Impeccable finding about contrast, target size, focus or legibility is fixed even if it changes a Taste choice; the colour is adjusted within the same direction.
- **Use Impeccable's Operate mode for the app.** The FarmLens app is a task tool (Impeccable: "Operate"), where scanability and familiar patterns beat expression. Persuade mode only applies to a landing/pitch page.
- **Invoke by name.** All three descriptions match "design / redesign / polish", so Claude may pick any of them automatically. Name the skill in the prompt (`/impeccable audit …`) to get the one you want.
- **One skill per step.** Do not ask two of them to restyle the same screen in the same request.

## 4. Known conflicts and how we resolve them

| Conflict | Resolution |
|---|---|
| Taste wants real photographs, a hero entrance and effects on every page | Not in the app: heavy images and animation hurt low-end phones and slow data (`ux-guidelines.md`). Allowed only on a separate landing/pitch page, with credits |
| Taste's bundled photos/icons (Unsplash, Wikimedia CC BY/CC BY-SA, brand logos) | They are reference material for the skill. Do not ship them in the app; if one is ever used, register it in `third-party.md` with its credit line. Never use brand logos |
| Frontend Design: "make opinionated, risky choices" vs Taste's chosen system | Taste's direction is the brief; Frontend Design executes it |
| Impeccable "craft floor" bans (e.g. overused fonts, gradients) vs a Taste choice | Impeccable flags it; the team decides. Taste's choice stays unless the finding is an accessibility defect |
| Skills writing their own context files (`PRODUCT.md`, `DESIGN.md`, `.impeccable/`, `.taste-skill/`) | Allowed; they must be in English and go through a PR like any other file. `.taste-skill/` holds screenshots and runtime state and is git-ignored. Inside `.impeccable/`, commit only what Impeccable marks as shared (`config.json`, `design.json`, `surfaces/`, `critique/`) |

## 5. Runtime requirements and side effects

| Skill | Needs | Side effects to know about |
|---|---|---|
| Taste | Node 22+ and Chrome/Edge/Chromium for its scripts (`scripts/*.mjs`); ffmpeg optional | Declares a **Stop hook in its frontmatter**: once the skill is invoked in a session, `scripts/gate.mjs` runs when Claude stops (it exits quietly if no Taste build is armed in `.taste-skill/`). Writes `.taste-skill/` in the project |
| Frontend Design | Nothing (instructions only) | None |
| Impeccable | `sh` (macOS/Linux) or `impeccable.cmd` (Windows) | On first run the launcher **downloads a platform engine binary** into `~/.impeccable/bin/` (verified against `scripts/engine-checksums.txt`). A new design fetches visual directions from impeccable.style and sends anonymous choice telemetry — turn it off with `DO_NOT_TRACK=1` or `"telemetry": false` in `.impeccable/config.json`. Writes `.impeccable/`, `PRODUCT.md`, `DESIGN.md` |

Impeccable's optional **design hooks** (run its detector on every Edit/Write and on Stop) are **not** installed: they run outside model approval and would fire on every edit in the repo. Adding them to `.claude/settings.json` is a team decision (record it with `/record-decision`).

## 6. Updating, adding or removing a skill

- **Update**: re-copy the whole upstream folder over ours (keep `LICENSE`/`NOTICE.md`), update the version/commit in §1 and in `third-party.md`, and open a PR. Do not edit the skill files by hand; put project-specific rules in this file.
  ```bash
  git clone --depth 1 https://github.com/pbakaus/impeccable /tmp/impeccable
  rsync -a --delete --exclude LICENSE --exclude NOTICE.md /tmp/impeccable/.claude/skills/impeccable/ .claude/skills/impeccable/
  ```
- **Add**: copy the full skill folder (SKILL.md + references, scripts, assets) to `.claude/skills/<name>/` where `<name>` equals its `name:` field; no symlinks to folders outside the repo. Add the license file, a row in §1, `third-party.md`, `docs/tools.md` and `CLAUDE.md`.
- **Remove**: delete the folder and its rows in this file, `third-party.md`, `docs/tools.md` and `CLAUDE.md`.
- Claude Code usually picks up skill changes in a running session; if a skill does not appear when you type `/`, restart Claude Code.
