# Team setup (5 minutes)

Everything the team shares — rules (`CLAUDE.md`), agents (`.claude/agents/`), skills (`.claude/skills/`) and settings (`.claude/settings.json`) — lives **inside this repository**. Nothing needs to be installed per skill: clone or pull and it is there.

## 1. First time
1. Install Git and [Claude Code](https://docs.claude.com/en/docs/claude-code) and log in with **your own** account.
2. Ask the repo owner to add you as a collaborator on GitHub (needed to push).
3. Clone and open Claude Code **from the repository root** (otherwise it will not find the project skills):
   ```bash
   git clone https://github.com/S-Santiago/spaceappschallenge-2026.git
   cd spaceappschallenge-2026
   claude
   ```
4. Accept the "trust this folder" prompt.
5. Type `/` — you should see the project skills (`/rotation-card`, `/agro-indicator`, `/crop-traits`, `/nasa-power-fetch`, …). Type `/agents` to see the project agents.
6. Copy `.env.example` to `.env` and fill in your own keys if you need them. Never commit `.env`.

## 2. Every time you start working
```bash
git pull          # gets the latest code AND the latest skills/agents/rules
claude
```
If someone changes a skill or agent while your session is open, restart Claude Code to load it.

## 3. What is shared vs personal
| Shared (in git) | Personal (not in git) |
|---|---|
| `CLAUDE.md` — project rules | Your Claude account and login |
| `.claude/agents/`, `.claude/skills/` | `.claude/settings.local.json` — your own permissions/preferences |
| `.claude/settings.json` — no AI co-author attribution in commits/PRs | `.env` — your API keys / Earthdata login |

Do not re-enable AI attribution in your local settings: the team policy is no AI co-authorship in git; AI use is declared in [`ai-usage.md`](ai-usage.md).

## 4. Quick reference
| I want to… | Use |
|---|---|
| Get climate data for a location | `/nasa-power-fetch <lat> <lon>` (uses `src/fieldshift/power.py`) |
| Turn data into a farmer-friendly number | `/agro-indicator <name>` |
| Add a crop and its characteristics | `/crop-traits <crop>` |
| Build/compare the rotation cards | `/rotation-card` |
| Check a new dataset | `/nasa-dataset-check <dataset>` |
| Declare AI use | `/log-ai-usage` |
| Add a library or image | `/add-dependency <name>` |
| Record a decision | `/record-decision` |
| Review a screen | `/ux-review` |
| Security review of my branch before merging | `/security-review` |
| Are we ready to submit? | `/submission-check` |
| Draft the demo | `/demo-builder slides` or `/demo-builder video` |

Full details: [tools.md](tools.md).
