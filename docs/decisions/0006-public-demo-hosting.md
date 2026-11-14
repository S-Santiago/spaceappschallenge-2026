# 0006 · Public demo hosting: Hugging Face Spaces (Docker)

- **Date:** 2026-11-14 17:58
- **Status:** accepted
- **Deciders:** app owner @S-Santiago, with the team (API owner @HectorLopGar-Dev)

## Context
Judges must open FarmLens from a public link, with no login or install, at any time until judging ends (#75).
Until now the app was reached through a Cloudflare tunnel to `localhost:8000` on a team laptop, so the link died
whenever that laptop slept or went offline. Decision [0004](0004-mobile-pwa.md) left the host open ("a free host
that runs Python"). The app needs: one origin over HTTPS for the API and the PWA (service worker, installable),
outbound internet to NASA POWER and ORNL DAAC for new map points, and a writable path for the SQLite DB.
It needs no secrets at run time.

## Options considered
1. **Hugging Face Spaces, Docker SDK (free CPU)** — free, no card; sleeps only after ~48 h without visits;
   HTTPS on `*.hf.space`; outbound internet; ephemeral disk (fine: the DB is rebuilt from committed seeds).
   Con: deploys from its own git repo, not from GitHub, and rejects binary files pushed with plain git →
   solved with a GitHub Action that uploads with the `hf` CLI.
2. **Render free web service** — free, no card, auto-deploys from GitHub on every push.
   Con: sleeps after **15 min** idle, so almost every judge would wait ~30–60 s for a cold start.
3. **Fly.io** — fast restarts. Con: no free plan for new accounts (card and pay-as-you-go).

## Decision
**Option 1 — Hugging Face Spaces (Docker SDK).** The 48 h sleep window makes a cold start during judging unlikely,
and the cost is zero with no card.

- `Dockerfile` (python:3.12-slim) runs `uvicorn fieldshift.api:app --app-dir src --host 0.0.0.0 --port $PORT`
  (`PORT=7860`, the Spaces default) as user 1000. Only `src/`, `web/`, `data/crops.csv` and `data/samples/` go in.
- `FIELDSHIFT_DB=/tmp/fieldshift.db`: the SQLite DB (crops, demo fields, pre-loaded NASA data) is rebuilt from the
  committed seeds at every start. Live NASA downloads for new map points are cached in that same DB until the
  next restart. Analyses are not persistent on the hosted demo.
- The API builds the DB once at startup (FastAPI lifespan), before serving, which also removes the first-request
  race in `db.init_db` found in PR #54.
- **Deploy:** `.github/workflows/deploy-space.yml` runs on every push to `main` (and by hand from the Actions tab).
  It assembles the Space folder (code + `deploy/space-README.md`, which carries the Spaces YAML header) and uploads
  it with `hf upload --delete "*"`; the Space then rebuilds (~2–4 min). Settings: Actions secret `HF_TOKEN`
  (fine-grained token, write access to the Space only) and Actions variable `HF_SPACE` (`<user>/<space>`).
- Locally nothing changes: the API still runs on port 8000.
- The Cloudflare tunnel stays only as a documented **backup** (README §5).

## Consequences
- Public URL in README §5; "open the link 5 minutes before judging and the pitch" in the submission checklist,
  since a Space that slept needs a cold start (time measured after the first deploy, see README §5).
- `main` freezes Sun 15 Nov 15:00: every merge after that would redeploy the demo.
- New third-party items: base image `python:3.12-slim`, `huggingface_hub` (CI only), GitHub Actions
  `actions/checkout` and `actions/setup-python` → [third-party.md](../third-party.md). Hosting → [tools.md](../tools.md).
- The Space repo is a deployment copy; edits there are overwritten on the next deploy.
