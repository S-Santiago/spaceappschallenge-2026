# Submission checklist

Run `/submission-check` or ask the `submission-auditor` agent. Official NASA deadline: **Sun 15 Nov 2026, before 23:59 local time**.

## Last 30 minutes (official guide)
- [ ] Correct team: everyone registered, accepted in Málaga and added to the team.
- [ ] All required fields and checkboxes completed.
- [ ] Summary 50–200 words, clear and consistent with the project.
- [ ] NASA Data explained: resource, link and real role.
- [ ] Other references, rights and licenses reviewed.
- [ ] AI declared; generated material marked where required.
- [ ] Project Demo within limits: ≤7 slides OR ≤30 s.
- [ ] Page, slides and materials in English; English subtitles if the video is in another language.
- [ ] Demo and Final Project public; tested in a private/incognito window without login.
- [ ] Privacy: no names, voices or recognizable images of minors.
- [ ] **Submit for Judging pressed and confirmation visible.**
- [ ] If anything changed afterwards: Save Progress + Submit for Judging again + confirm again.

## Repository-specific
- [ ] README sections 1–5 complete (summary, problem, solution, NASA data, how to run).
- [ ] `docs/nasa-data.md` — every dataset in use has a full entry.
- [ ] `docs/ai-usage.md` — summary written, log up to date.
- [ ] `docs/third-party.md` — every dependency and asset listed with license.
- [ ] License decided and `LICENSE` file present.
- [ ] No secrets: `.env` not committed; search history for keys.
- [ ] `/security-review` run on the last changes; findings fixed or justified.
- [ ] Every number shown in the tool is defined in `docs/indicators.md`; every crop value in `data/crops.csv` has a source.
- [ ] At least 3 rotation strategies (incl. current) with why / evidence / benefits / gaps / risks.
- [ ] Demo tested on a real low/mid-range phone over mobile data (360 px, no horizontal scroll, demo field < 3 s).
- [ ] UX launch route: all 7 stages **GO** (`/ux-review`).
- [ ] Red alert clear: no placeholder text/data, no dead buttons, no technical errors on screen (`Error`, `undefined`, `NaN`, `None`, tracebacks), no color-only states.
- [ ] Public demo link opened **5 minutes before judging and before the pitch** (Cloud Run keeps one instance warm, but check it answers).
- [ ] Public demo redeployed from the final `main` after the 15:00 freeze (Cloud Run does not redeploy on merge).
- [ ] `main` frozen from Sun 15 Nov 15:00 (the public demo is redeployed once from it).
- [ ] No organizer event material or NASA logos committed.
- [ ] Built / simulated / future clearly separated in README and demo.
- [ ] Repo is public.

## Local pitch (Málaga)
- [ ] Final duration/format/Q&A rules confirmed with the organization at the 12:30 on-stage briefing, before the local submission check (16:45–17:15).
- [ ] Tested on the real projector/laptop.
- [ ] Q&A rehearsed (see `docs/pitch/README.md`).
