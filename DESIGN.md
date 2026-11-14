# FarmLens design system

The visual direction of the app and the rules that keep it consistent. Read with
[`docs/ux-guidelines.md`](docs/ux-guidelines.md) (project rules, they win) and [`docs/ui-skills.md`](docs/ui-skills.md).

- **Surface mode:** Operate (Impeccable). The farmer comes to finish one task: compare rotations for their field.
  Familiar controls, plain words, precision over decoration.
- **Use scene:** a farmer outdoors, on a low/mid-range Android phone, slow data, bright sun. Light theme is the
  reference; the dark theme follows the phone setting and passes the same contrast checks.

## 1. Where things live

| What | File |
|---|---|
| Tokens (colours for light and dark, type scale, spacing, radius) and every component style | `web/styles.css` |
| Page flow (masthead, four steps, button, feedback) and results view | `web/js/app.js` |
| What to expect (predictions and alert cards) | `web/js/expect.js`, `web/js/expect-format.js` |
| Plain-English sentences and number formatting | `web/js/format.js` |

The early Streamlit harness (`.streamlit/config.toml`, `ui_theme.py`, `ui_results.py`, `src/app.py`) was retired;
its tokens and components were ported to `web/styles.css`. Never write a colour, size or radius directly in a
component; add a token in `:root` instead. Every data string placed in HTML goes through `esc()` (`web/js/format.js`).

## 2. Palette

Derived from the Taste skill's palette deal for the closest trade it knows ("workshop" → *clay and pine*). Its cream
ground was replaced by a near-white one: more contrast in sunlight, and cream is a common generated-UI default.

| Token | Light | Dark | Use | Contrast |
|---|---|---|---|---|
| ground | `#FAFAF7` | `#121510` | page | — |
| panel | `#EFEEE7` | `#1D211B` | quiet surfaces (location, trend rows) | — |
| ink | `#1E231C` | `#ECEDE6` | text | 15.3 / 15.6 : 1 |
| muted | `#545B50` | `#B1B7AA` | captions, labels | 6.7 / 9.0 : 1 |
| line | `#CFCDC2` | `#3C4238` | hairlines | decorative |
| accent (pine) | `#2E5B44` | `#3F8160` | primary button, selection, focus ring, score bars | white text 7.8 / 4.65 : 1 |
| accent-ink | `#2E5B44` | `#8FCDA8` | accent used as text | 7.5 / 10 : 1 |

Crop families (rotation strip fills, same in both themes, dark ink text ≥ 7.5 : 1, name always printed):
cereal `#E3C26A` · legume `#9CC27A` · oilseed `#EFA445` · cover crop `#7FBFA6` · fallow `#C8B597` · other `#C9CCC2`.
Chart: rain `#1F6FB2` (bars), water need `#B3541E` (dashed line with ◆), so the chart also reads in grayscale.

## 3. Type

System fonts only (`system-ui`, Roboto on Android): no web-font download on slow data, and the farmer's own phone
font. One family; fixed rem scale, ratio ≈ 1.2: h1 28 px, step h2 22 px, section h3 18 px, card titles 20 px, body
16 px, secondary 14 px (13 px only for the month-table headers on screens ≤ 360 px). Sentence case; no all-caps labels.

## 4. Spacing, radius, targets, motion

- Spacing scale 4 · 8 · 12 · 16 · 24 · 32 · 48 px (`--fl-s1` … `--fl-s7`). Page gutter 16 px (12 px ≤ 340 px).
- Radius 6 / 8 / 12 px; buttons and inputs 8 px; tags fully round.
- Touch targets ≥ 48 px (primary button 56 px); focus ring = 3 px accent + 5 px halo, visible on both themes.
- Motion only as feedback: 140 ms press on buttons. `prefers-reduced-motion` removes the movement, keeps the states.

## 5. Components

| Component | Rule |
|---|---|
| Step heading | Number disc + title + visible "Step N of 4" (UX launch route 02). The number is a real sequence. |
| Rotation strip (signature) | Years side by side as field plots, filled by crop family, each with "Year N" and the crop name. Used in step 2 (live preview of the answer), in every option card, with a colour key listing only the families shown. |
| Comparison list | Rotation options in the same order as the cards (current first, then by overall fit), score + bar. The answer before the evidence. |
| Score bars | One bar style (6 px) for overall and the four dimensions, filled by level: good = pine `--good`, fair = ochre `--fair`, poor = clay `--poor`. The number and level word are always printed (colour is never the only cue); the bar is hidden from screen readers. |
| Tags | Only "Best fit for your priorities" (filled accent). The current rotation needs no tag: its title says it. |
| Alerts | Banners (below); feedback appears right under the button that caused it. |
| Banners | 1 px border in the state colour + tinted background (no thick coloured side stripe). |
| Disclosures | `<details>` with a drawn chevron on the right, accent-ink label, 48 px row; the chevron turns when open. |
| Icons | Interface chrome uses plain text and a few inline SVG shapes (no icon font). Data pictograms (💧 🌱 💶 🛡️, 🔻, 🟫) stay in content because they link the priorities to the scores and are covered by tests; they always sit next to a word. |
| Cards | Only for the rotation options (comparable items with expanders). No card inside a card. |

## 6. Rejected on purpose

Gradients, glass, decorative shadows, hero images, entrance animations, custom web fonts, eyebrow labels above
headings, a modal for anything. Taste's marketing-site rules (photographs, one section per screen, dealt moments)
do not apply to the app (`docs/ui-skills.md` §4).
