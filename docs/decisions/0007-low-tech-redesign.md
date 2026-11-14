# 0007 · PWA redesign for farmers with little tech experience

- **Date:** 2026-11-14 19:00
- **Status:** accepted
- **Deciders:** team (UI owner @HectorLopGar-Dev)

## Context
The PWA worked end to end, but a review against the Málaga UX launch route found 4 of 7 stages NOT YET for our
primary user (a farmer with little tech experience on a cheap phone, outdoors):
- the "Analyze my field" button sat ~2,000 px down a long form;
- control borders were 1.5 : 1 and the "fair" bar 2.2 : 1 on the soft green page (`#E8FFE8`);
- crops had to be typed (common or Latin name), priorities were the numbers 0–3;
- some jargon reached the screen (ET0, FAO-56, MODIS, evidence codes like `[R-01;R-IND, confidence medium]`);
- emoji were used as data icons; they render differently or as boxes on low-end Androids and wash out in sun.

## Options considered
1. **Polish the existing long form** — least work; keeps a 2,000 px page and many choices on screen at once.
2. **One step at a time (wizard) with defaults, answer-first results** — familiar pattern (Next / Back), one decision
   per screen, works with the phone's Back button; more JS state (kept small: hidden sections, `#/step/N`).
3. **Single "quick result" screen and an optional advanced form** — fastest to a result, but hides the current
   rotation and priorities that the challenge asks us to take into account.

## Decision
Option 2, with a quiet "Analyze now with these answers" on steps 1–3 so the demo field still gives results without
touching anything. Together with it:
- a new team palette of seven base tones (ground `#F5F4ED`, surface, ink, accent `#285943`, sage, tan, ochre) that
  replaces `#E8FFE8`; no other hue, derived shades only via `color-mix()`; all pairs measured ≥ WCAG AA;
- body text 18 px (nothing below 16 px), targets ≥ 48 px with 8 px gaps, 56 px full-width primary button;
- hand-drawn inline SVG icons (`web/js/icons.js`, no library or icon font) instead of emoji, always next to a word;
- results open with "Best match for your priorities: …" (not "the best", rotation-card rule), levels shown as
  word + bar + number, card evidence under "More detail";
- plain-English copy reviewed by the `agro-domain-advisor` (ET0 is "water lost by a short grass field", not the crop's need).

## Consequences
- `DESIGN.md` rewritten (palette, type, components, icons). `docs/ux-guidelines.md` unchanged: it is what we now meet.
- A pytest check fails if any emoji or Unicode pictogram appears in `web/`; JS tests check the SVG icon + its label.
- Crops are picked from a native list grouped by family; the Latin-name search (`format.matchCrops`) stays in the
  code and tests but is no longer on the main path.
- Service worker cache bumped (v14) and `js/icons.js` precached. No new dependency, nothing new in `third-party.md`.
- Supersedes nothing: decisions 0004/0005 (PWA, vanilla JS, no build) still hold.
