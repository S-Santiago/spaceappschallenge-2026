# 0005 · PWA frontend: vanilla JS, hand-written service worker, no build step

- **Date:** 2026-11-14 15:30
- **Status:** accepted
- **Deciders:** PWA frontend owner (@S-Santiago), per [0004](0004-mobile-pwa.md) ("framework chosen by the frontend owner in Sprint 1")

## Context
Decision [0004](0004-mobile-pwa.md) replaced the Streamlit UI with a PWA served by the Python API, and left the frontend framework open: "prefer none or a tiny one". Constraints:
- Users have low/mid-range phones and slow, unstable mobile data → target **< 200 KB of JS** on first load, fast on Slow 4G.
- Only one person builds the frontend, in ~3.5 h for Sprint 1 (#35) and ~4 h for Sprint 2 (#40).
- The FastAPI service (#36, PR #47) serves the static files from `web/` on the same origin → no CORS, no separate frontend host.
- The app is small: a 4-step form, a results screen, a "What to expect" screen with alert cards, offline cache for the demo fields.

## Options considered
1. **Vanilla JS (ES modules) + hand-written service worker, no build step** — 0 KB of framework, no `node_modules`, no build to break the deploy; files are served as they are from `web/`; every teammate can read it. Cons: manual DOM updates and routing; no component model.
2. **Preact + HTM (from a vendored file, no build)** — components in ~4 KB; still no build. Cons: one more dependency to register and learn; little gain for 3 screens.
3. **Alpine.js** — declarative markup, ~15 KB, no build. Cons: logic in HTML attributes is hard to test; less control over render cost on slow phones.
4. **Svelte (Vite build)** — very small output and good DX. Cons: Node toolchain and a build step in the deploy; more integration risk with the time left.
5. **Workbox for the service worker** — robust caching recipes. Cons: build tooling or a CDN load; our caching needs (app shell + a few JSON payloads) are simple.

## Decision
**Option 1.** Plain HTML + CSS + JavaScript ES modules in `web/`, served by FastAPI at `/`; a hand-written `web/sw.js`:
- **App shell** (HTML, CSS, JS, icons, manifest): cache-first, versioned cache name, old caches deleted on `activate`.
- **API data** (`/api/fields`, `/api/crops`, demo-field analyses and predictions): network-first with cache fallback, so the demo fields work offline after the first visit.
- Screens switched with a tiny hash router (`#/step/1`, `#/results`, `#/expect`); state kept in one module-level object and in `localStorage` for the last analysis.
- System fonts, no icon fonts or web fonts on the main path; charts as inline SVG drawn by our own code.
- No `package.json`, no bundler. If a library becomes necessary it is vendored as a single file in `web/vendor/`, registered in `docs/third-party.md`, and the 200 KB budget is re-checked.

## Consequences
- Easier: zero build in the deploy (same container as the API), tiny first load, nothing to install for teammates.
- Harder: we write the DOM updates and the router ourselves → keep screens simple and the code in small modules (`api.js`, `state.js`, `views/*.js`).
- No new dependency to register now. The design tokens of `DESIGN.md` / `ui_theme.py` are ported to CSS custom properties in `web/`.
- Testing: the API stays covered by pytest; the PWA is checked by hand in the browser at 360 px, with Slow 4G throttling and offline mode, and with `/ux-review`.
- `docs/architecture.md` and `docs/tools.md` updated in the same change. README "How to run" is updated when `web/` lands (#35).
