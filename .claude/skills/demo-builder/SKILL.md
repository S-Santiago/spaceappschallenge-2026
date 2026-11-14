---
name: demo-builder
description: Draft the official Project Demo — either max 7 slides (cover included) or a video script of max 30 seconds — from README and docs, following the recommended Málaga structure. Use when preparing the demo link for the Project page.
---

# Demo builder

Argument: `slides` (default) or `video`.

1. Read `README.md`, `docs/challenge.md`, `docs/nasa-data.md`, `docs/pitch/README.md`. Use only facts present in the repo; mark gaps as `[[MISSING: ...]]` instead of inventing.
2. **Slides** (≤ 7 total, cover counts):
   1. Team & project name · Challenge 06 · one-sentence solution
   2. Concrete problem & who it affects
   3. Solution & user journey (simple diagram)
   4. NASA data: origin and real role
   5. Prototype demo / result / evidence
   6. What was tested, what works, limitations (built / simulated / future)
   7. Expected impact, next step, key references
   Each slide: title ≤ 8 words, ≤ 30 words of body, one visual suggestion.
3. **Video** (≤ 30 s): four beats — problem (0–7 s), solution (7–15 s), demo (15–24 s), NASA data (24–30 s). Give on-screen text, narration and shot list; narration ≤ 75 words. English subtitles required if narration is not in English.
4. Write the draft to `docs/pitch/demo-slides.md` or `docs/pitch/demo-video-script.md`.
5. Remind: English only, public link without permissions, no NASA logos, no minors identifiable, AI-generated visuals labeled (and logged with `log-ai-usage`).
