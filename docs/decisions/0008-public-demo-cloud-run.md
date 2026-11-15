# 0008 · Public demo hosting: Google Cloud Run

- **Date:** 2026-11-15 11:45
- **Status:** accepted — supersedes [0006](0006-public-demo-hosting.md) (Hugging Face Spaces)
- **Deciders:** tech lead @S-Santiago, with the team (deployed by @HaoJunnnzhang, #76)

## Context
Judges must open FarmLens from a public link, with no login or install, at any time until judging ends (#75).
Decision 0006 chose Hugging Face Spaces (Docker), but the Space was created with the **static** SDK, which only
serves HTML/CSS/JS and cannot run our Python API, and the Docker option was not available on that account.
The app needs one HTTPS origin for the API and the PWA, outbound internet to NASA POWER and ORNL DAAC, a writable
path for the SQLite DB, and **CPU after the response** (the MODIS download for a new map point continues in the
background, #86). It needs no secrets at run time. The NASA Space Apps Global Offers include Google Cloud
($300 credit for 90 days) and Microsoft Azure ($200 for 30 days).

## Options considered
1. **Google Cloud Run (Space Apps Google Cloud offer)**: runs our `Dockerfile` as it is ($PORT, DB in `/tmp`),
   HTTPS on `*.run.app`, region Madrid, min instances to avoid cold starts, CPU can stay allocated after the
   response. Con: needs a card for identity verification (no charge unless upgraded); continuous deployment from
   GitHub needs the Cloud Build GitHub app approved by the repo admin.
2. **Microsoft Azure (Space Apps offer)**: Container Apps / App Service would work. Con: shorter credit (30 days),
   phone + card verification, more setup steps.
3. **Render free web service**: no card, deploys from GitHub. Con: sleeps after 15 min idle (30–60 s cold start
   for most judges).
4. **Keep Hugging Face**: blocked (static SDK only on that account).

## Decision
**Option 1 — Google Cloud Run**, project `farmlens-demo-2026`, service `farmlens`:
<https://farmlens-530581375456.europe-southwest1.run.app>

| Setting | Value | Why |
|---|---|---|
| Region | `europe-southwest1` (Madrid) | Low latency in Málaga |
| Authentication | allow unauthenticated | Judges open it with no login |
| CPU | always allocated (`--no-cpu-throttling`) | The background MODIS download must keep running after the response |
| Instances | min 1 · max 2 | No cold start for judges; caps cost and abuse; each instance keeps its own `/tmp` DB and download state |
| Resources | 512 MiB · 1 CPU · timeout 300 s · port 8080 | Image ~233 MB; a new map point can be slow |
| Budget | alert at €20 (50 / 90 / 100 %) | Safety on the trial credit |

- **Deploy:** by hand from an up-to-date `main`: `gcloud run deploy farmlens --source . --region europe-southwest1`
  (~3 min, Cloud Build builds the root `Dockerfile`). No automatic deploy on merge for now; the deployment issue
  (#76) is where the team asks for a redeploy. The last redeploy happens right after the `main` freeze (Sun 15:00).
- The Hugging Face workflow (`.github/workflows/deploy-space.yml`) and `deploy/space-README.md` are removed;
  `huggingface_hub` and the CI-only GitHub Actions leave `docs/third-party.md`.
- The Cloudflare tunnel to `localhost:8000` stays only as a documented backup (README §5).

## Consequences
- Public URL in README §5, CLAUDE.md, `docs/tools.md`, `docs/architecture.md` and the technical Q&A.
- A merge to `main` does not change the public demo until someone redeploys: the submission checklist has a
  "redeploy from the final `main`" step.
- Cost comes from the trial credit (always-on instance). **After judging**, set min instances to 0 or delete the
  service.
- Optional later: connect Cloud Build to GitHub (admin approval) for automatic deploys on merge to `main`.
