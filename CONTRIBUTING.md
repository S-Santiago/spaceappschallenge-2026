# Contributing (team workflow)

## Branches
- `main` must always be demo-able. Freeze risky changes on `main` after **Sunday 15:00**.
- `main` is **protected** (GitHub ruleset "Protect main", no bypass for anyone): no direct pushes, no force pushes, no deletion, linear history.
- Use short-lived branches: `feat/<topic>`, `data/<dataset>`, `docs/<topic>`, `fix/<topic>`.

```bash
git switch main && git pull
git switch -c feat/my-topic
# ...work, commit...
git push -u origin feat/my-topic
gh pr create          # or open the PR on GitHub
```

## Pull Requests
- **Squash merge only** → the **PR title becomes the commit on `main`**: use Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`).
- **1 approval required**, from someone **other than the last person who pushed** to the PR.
- **Pushing after an approval dismisses it** → finish your changes, then ask for review.
- **All review conversations must be resolved** before merging.
- After merging, delete the branch and `git switch main && git pull`.
- **Sunday night:** agree who stays available to approve last-minute fixes until the 23:59 submission — nobody can merge alone.
- Open a Pull Request (template in `.github/`). Reviewers are requested automatically via `.github/CODEOWNERS`:

  | Area | Reviewer |
  |---|---|
  | Code (`src/`), data pipeline, tests, dependencies | @S-Santiago |
  | Visual/UX of the app, docs, README, pitch | @sebasbarrabaja-cmyk |

  A PR that touches both areas needs both reviews. When @S-Santiago authors code, any other teammate can review it so he is not blocked. Target: review within ~30 min.

## Commits
Conventional Commits: `feat:`, `fix:`, `docs:`, `data:`, `chore:`, `refactor:`.
Commits are authored by team members only: no AI co-author trailers (`Co-Authored-By:` from AI tools) in commits or PRs. Claude Code is configured for this in `.claude/settings.json`. AI usage is declared in `docs/ai-usage.md` instead (required by NASA).

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
