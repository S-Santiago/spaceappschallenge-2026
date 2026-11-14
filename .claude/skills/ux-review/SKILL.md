---
name: ux-review
description: Review a screen, component or the demo flow with the Málaga UX "launch route" (7 stages, GO / NOT YET per stage, optional extras), the red-alert list (placeholders, dead buttons, technical errors, color-only states) and the mobile-first low-end-phone rules. Use after UI changes and before recording or presenting the demo.
---

# UX review (launch route)

Target: the file(s), route or screenshot given as argument (default: the main flow of the PWA in `web/js/app.js`, served at `http://localhost:8000`).
Reference: `docs/ux-guidelines.md` (launch route table, red alert, mobile-first section).

## 1. Launch route — 7 stages
For each stage check the **required** items and the ☆ extras, with evidence (file:line, screen or measured value). A stage is **GO** only if all required items pass; otherwise **NOT YET**.

1. **Purpose at first glance** — first screen says what it is and for whom; main action stands out. ☆ understandable in 5 s by an outsider.
2. **Main flow** — key task completes end to end; forward/back possible everywhere. ☆ user knows which step they are on.
3. **Hierarchy & patterns** — one primary action per screen; repeated elements consistent. ☆ familiar patterns.
4. **Legibility** — body ≥ 16 px (team rule; sheet minimum 14), secondary ≥ 12; user's words; units shown. ☆ ≤ 3 typefaces.
5. **Contrast & color** — text ≥ 4.5:1, large text/icons/borders ≥ 3:1 (compute from colors), readable with low brightness; never color alone. ☆ works in grayscale.
6. **Touch targets** — ≥ 48 dp Android / 44 px web, ≥ 8 px spacing; nothing depends on hover. ☆ readable from 2 m on a laptop (pitch).
7. **System feedback** — visible response to every action (spinner/"Fetching NASA data…"/success); errors say what happened and how to continue. ☆ empty states say what to do.

## 2. Mobile-first, low-end phone (blocking)
Works at 360 px with no horizontal scroll; single column (`layout="centered"`, no key content in `st.columns`, no essential inputs in the sidebar); few inputs with defaults; no heavy maps/3D on the main path; demo-field results < 3 s; progress shown for live calls. If possible test with DevTools device mode (360 px, Slow 4G, CPU 4× slowdown). Any failure → overall NOT YET.

## 3. ⚠️ Red alert (blocking)
Search the code and the screens for anything that would appear in the demo:
- placeholder text/data: `lorem`, `ipsum`, `asdf`, `Title here`, `TODO`, `test`, `xxx`;
- buttons/links with no effect in the demo flow;
- technical errors visible to users: `Error 500`, `undefined`, `NaN`, `None`, tracebacks, raw API error messages (catch them and show a friendly message);
- states distinguished only by color.
Any hit → overall NOT YET.

## 4. Output (in Spanish)
| # | Etapa | Resultado (GO / AÚN NO) | Evidencia | Arreglo |
Then the red-alert hits, the mobile result, an overall verdict (**GO** only if all 7 stages GO + no red alert + mobile OK), and the top 3 fixes ordered by impact on the demo given the time left.
