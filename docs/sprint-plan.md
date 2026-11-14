# Sprint plan — Scrum adapted to the hackathon

Product: **FarmLens** mobile app (PWA + Python API, [decision 0004](decisions/0004-mobile-pwa.md)).
Backlog = GitHub issues · one **milestone per sprint** · epic #16.

## Roles
| Role | Who |
|---|---|
| Scrum Master + backlog priority (Product Owner) | @sebasbarrabaja-cmyk — runs the ceremonies, removes blockers, decides scope with the supervisor/organizers |
| Tech lead | @S-Santiago |
| Developers | @S-Santiago (PWA frontend) · @HectorLopGar-Dev (API + data) · @HaoJunnnzhang (data analysis: indicators & predictions) |

## Ceremonies (time-boxed)
| Ceremony | When | Length | Output |
|---|---|---|---|
| Sprint planning | Start of each sprint | 10 min | Sprint goal + each person's current task and **next ready task** |
| Check-in ("daily") | Every ~90 min, standing | 5 min | Done · doing now · blocked? |
| Sprint review | End of each sprint | 10 min | Demo **on a real phone**; keep or cut each item (no half-merged features) |
| Retro | Right after the review | 5 min | One thing to keep, one to change |

## Working rules (everyone always busy)
- **WIP:** one main task in progress + one small one ready. If blocked > 15 min: tell the Scrum Master and pull the next ready task.
- **Definition of Ready:** clear goal, owner, "done when" checklist, data/API shape known.
- **Definition of Done:** merged to `main` via PR · works on a 360 px phone · tests pass · registries updated (`nasa-data`, `third-party`, `ai-usage`, `indicators`) · no red-alert items.
- Integrate small and often: no branch lives more than ~2 h.
- Everyone uses Claude Code with the project skills/agents; estimates assume AI-assisted work.

## Sprints and checkpoints (Europe/Madrid)
| Sprint | When | Goal | Checkpoint |
|---|---|---|---|
| **S1 · App + real data** | Sat 15:00–18:30 | API serving the real engine; installable PWA showing real results for the demo fields; prediction functions specified | **17:30** official mentoring review (show progress) · **18:30** sprint review: real results in the PWA on a phone |
| **S2 · Predictions & alerts** | Sat 18:30–22:30 | Prediction functions implemented and tested; "What to expect" screen with alert cards; offline for demo fields; public URL | **22:30** review: keep or cut each feature |
| *Rest* | Night | — | — |
| **S3 · Polish & harden** | Sun 09:00–13:00 | UX launch route GO, no red alert, performance < 3 s, security review, README; Android notification (stretch) | **13:00** content freeze |
| **S4 · Demo & submission** | Sun 13:00–16:00 | ≤ 7 slides or ≤ 30 s video, Project page, rehearsal | **15:00** `main` frozen · **16:00 Submit for Judging** · 16:30 tech test · 17:30 pitch |

Submitting at 16:00 (not 23:59) removes last-minute risk; after any later change: Save Progress + Submit again.

## Prediction functions (data analysis, no AI)
Statistics over NASA POWER 2005–2025 and MODIS NDVI, defined in `docs/indicators.md` before coding:

| ID | Function | Method |
|---|---|---|
| P-01 | Weekly rain probability | Share of years with rain ≥ 1 mm in that calendar week |
| P-02 | Heavy-rain risk & return period | Monthly frequency of days ≥ 30 mm; annual maxima fitted to a Gumbel distribution |
| P-03 | Last spring / first autumn frost dates | Percentiles (50 %, 90 %) of yearly dates with Tmin < 0 °C |
| P-04 | Heat and rain trends | Linear / Sen's slope per decade with confidence interval |
| P-05 | Season dryness | Accumulated rain vs historical distribution (SPI-style percentile) |
| P-06 | Sowing window per crop | Combine P-01…P-03 with crop limits from `data/crops.csv` |
| P-07 | Bare-soil + heavy-rain alert | Months likely bare (MODIS) × heavy-rain probability (P-02) |

Always labelled "based on the last 20 years of NASA data" — **not** a weather forecast.

**Stretch (S3, only if everything else is green):** future climate projections from NASA NEX-GDDP-CMIP6 for the demo fields (verify the dataset first with `/nasa-dataset-check`).

## Work split
| | @S-Santiago — PWA | @HectorLopGar-Dev — API & data | @HaoJunnnzhang — Data analysis | @sebasbarrabaja-cmyk — SM, UX, docs |
|---|---|---|---|---|
| **S1** | PWA shell: manifest, service worker, 4-step form wired to the API | FastAPI exposing fields, crops, analysis; close #6–#8 | Specify P-01…P-07 in `indicators.md`; implement P-01, P-03 | Ceremonies; decision records; UX criteria for the PWA; demo-field coordinates in docs |
| **S2** | Results + "What to expect" screens, offline cache | Predictions/alerts endpoints, precomputed demo payloads, deploy public URL | Implement P-02, P-04…P-07 + tests | Register methods, `/ux-review`, pitch storyline, slide draft |
| **S3** | Performance, error/empty states; Android notification (stretch) | Offline & API tests, hosting warm-up | Limits & uncertainty texts; CMIP6 (stretch) | `/security-review`, `/submission-check`, README final |
| **S4** | Screenshots, tech test | Check public link on several phones | Technical Q&A answers | Slides/video, Project page, Submit for Judging, rehearsal |
