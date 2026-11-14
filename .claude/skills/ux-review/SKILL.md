---
name: ux-review
description: Quick checklist review of a screen, component or flow against the 7 UX minimums of the Málaga UX guide (purpose, main flow, hierarchy, legibility, contrast, touch targets, system feedback). Use after UI changes or before recording the demo.
---

# UX review

Target: the file(s), route or screenshot given as argument (default: the main screen in `src/`).

Check each item against `docs/ux-guidelines.md` and give ✅/⚠️/❌ with evidence:

1. **Purpose at first glance** — title + one sentence + one prominent primary action?
2. **Main flow** — every step leads forward to a clear end; back navigation exists; no dead ends.
3. **Hierarchy & patterns** — one primary button per screen; consistent components.
4. **Legibility** — body ≥ 16 px (web) / 16 sp / 17 pt; secondary ≥ 12; ≤ 3 font families; plain words, units shown.
5. **Contrast & color** — compute contrast for text/background pairs (≥ 4.5:1; large text/icons/borders ≥ 3:1); color never the only signal.
6. **Touch targets** — ≥ 44×44 px web / pt iOS, 48 dp Android, ≥ 8 spacing; nothing depends on hover.
7. **System feedback** — loading, success, helpful error and empty states exist.

Plus farmer context: data date + source + uncertainty visible; readable outdoors.

8. **Mobile-first, low-end phone** (primary target — see `docs/ux-guidelines.md`): works at 360 px width with no horizontal scroll; single column (`layout="centered"`, no key content in `st.columns`, no essential inputs in the sidebar); one primary button; few inputs with defaults; no heavy maps/3D on the main path; demo-field results < 3 s; progress shown for live calls. If possible test with DevTools device mode (360 px, Slow 4G, CPU 4× slowdown).

Treat any failure of item 8 as ❌ blocking.

Finish with the top 3 fixes ordered by impact on the demo. Answer in Spanish.
