# FarmLens design system

The visual direction of the app and the rules that keep it consistent. Read with
[`docs/ux-guidelines.md`](docs/ux-guidelines.md) (project rules, they win) and [`docs/ui-skills.md`](docs/ui-skills.md).
Why it looks this way: [decision 0006](docs/decisions/0006-low-tech-redesign.md).

- **Surface mode:** Operate (Impeccable). The farmer comes to finish one task: compare rotations for their field.
  Familiar controls, plain words, precision over decoration.
- **Use scene:** a farmer with little tech experience, outdoors, on a low/mid-range Android phone, slow data, bright
  sun. One light theme whatever the phone setting; there is no dark theme.

## 1. Where things live

| What | File |
|---|---|
| Tokens (colours, type scale, spacing, radius, sizes, motion) and every component style | `web/styles.css` |
| Page flow (masthead, stepper, four steps, results) | `web/js/app.js` |
| Icons (hand-drawn inline SVG) | `web/js/icons.js` |
| What to expect (predictions and alert cards) | `web/js/expect.js`, `web/js/expect-format.js` |
| Plain-English sentences, number, coordinate and evidence formatting | `web/js/format.js` |

Never write a colour, size or radius directly in a component; add a token in `:root` instead (the only literals in
`styles.css` are the seven base colours). Every data string placed in HTML goes through `esc()` (`web/js/format.js`).

## 2. Palette

Seven base tones chosen by the team for an earth-and-crop feel that stays readable in sunlight. **No other hue** (no
blue, no red): tints and shades are derived with `color-mix()` from these.

| Token | Colour | Use | Contrast |
|---|---|---|---|
| `--ground` | `#F5F4ED` | page | — |
| `--surface` | `#FFFFFF` | cards, controls | — |
| `--ink` | `#242A26` | all text | 13.3 : 1 on ground, 14.6 : 1 on surface |
| `--accent` | `#285943` | primary button, selection, focus, level good, rain bars | 7.3 : 1 on ground; white text on it 8.1 : 1 |
| `--sage` | `#8BAF70` | legumes, secondary fills. **Never text** | ink on it 5.9 : 1 |
| `--tan` | `#C69B62` | oilseeds, level poor, errors. **Never text** | ink on it 5.8 : 1 |
| `--ochre` | `#D9A441` | cereals, level fair, warnings. **Never text** | ink on it 6.5 : 1 |

Text is ink, accent, or white on accent; there is no grey secondary text (secondary text is ink at 16 px).
Derived tokens (all checked): `--line` (control borders, card borders, bar tracks) 3.7 : 1 on ground · `--ochre-dark`
(warning borders, fair outline, water-loss line) 4.9 : 1 · `--tan-dark` (error borders, poor outline) 5.3 : 1 ·
tints for selected options, warnings and errors keep ink text ≥ 9 : 1.

- **Crop families** (rotation strip, name always printed, ink text): cereal = ochre · legume = sage · oilseed = tan ·
  cover crop = accent tint · fallow = tan tint · forage = sage tint · other = neutral tint.
- **Chart:** rain in accent bars, water lost by a grass field in a dashed dark-ochre line: it reads in grayscale.
- **Warnings / errors:** ochre (warning) or tan (error) border in the dark shade + tint + icon + one sentence of
  what happened and what to do.
- **Check:** every rendered text/background, border, bar and chart pair is measured in the browser on every screen
  (27 unique pairs, none below WCAG AA) before merging a visual change.

## 3. Type

System fonts only (`system-ui`, Roboto on Android): no web-font download on slow data, and the farmer's own phone
font. One family, fixed rem scale: h1 30 px, step count and step title 24 px, card titles and h3 20 px, **body 18 px**,
secondary 16 px (nothing on screen below 16 px except chart axis labels). Sentence case; no all-caps, no eyebrow labels.

## 4. Spacing, targets, motion

- Spacing scale 4 · 8 · 12 · 16 · 24 · 32 · 48 px (`--s1` … `--s7`). Page gutter 16 px.
- Radius 6 / 8 / 12 px; tags fully round.
- Every target ≥ 48 px with ≥ 8 px between neighbours; primary button 56 px, full width. Focus ring 3 px accent.
- Motion only as feedback (140 ms press, spinner). `prefers-reduced-motion` removes the movement, keeps the states.

## 5. Components

| Component | Rule |
|---|---|
| Stepper | One step on screen at a time. "Step N of 4" in large type + four segments (current one taller, so the text, not colour, is the cue). Each step has its own address (`#/step/N`), so the phone's Back button works. |
| Step navigation | One primary action: **Next** (step 4: **Analyze my field**), in a bar that sticks to the bottom of the screen so it is in reach on the first view of every step. **Back** as a full-width secondary button below the step. Loading and error feedback scroll into view above the bar. Example answers are filled in, so "Analyze now with these answers" is a quiet text button on steps 1–3: tapping it without touching anything gives results. |
| Inputs | Choice cards (radio), segmented buttons with words ("A little", "Very important"), native `<select>` for crops grouped by family. No free typing on the main path. |
| Rotation strip (signature) | Years side by side as field plots filled by crop family, each with "Year N" and the crop name. Step 2 preview and every option card, with a key listing only the families shown. |
| Answer block | First thing on the results: "Best match for your priorities: …", its level meter, why, how the current rotation scores, and one primary button to its card. Never "the best": it is a match to the farmer's own priorities. |
| Level meter | Word + bar + number everywhere a score shows ("Good ▬▬▬ 76/100"). Bar fill: good = accent, fair = ochre, poor = tan, the last two with a dark outline (≥ 3 : 1). Bar hidden from screen readers. |
| Option cards | Only for rotation options. Visible: title, strip, why, overall meter, "Check on your farm before deciding". Under **More detail** (`<details>`): the four sub-scores, evidence (codes turned into "Confidence: … · Sources: …"), benefits, information gaps. |
| Banners | 1 px border in the state shade + tint + icon on the left. Feedback appears right under the button that caused it. |
| Disclosures | `<details>` with a drawn chevron, accent label, 48 px row. |
| Icons | Hand-drawn inline SVG in `web/js/icons.js`: 24 px, 2 px stroke, `currentColor`, `aria-hidden="true"`, always next to a word. **No emoji or Unicode pictograms anywhere in `web/`** (they render differently or as boxes on cheap phones and wash out in sunlight); `tests/test_pwa.py` fails if one appears. No icon font, no icon library. |

## 6. Rejected on purpose

Gradients, glass, decorative shadows, hero images, entrance animations, custom web fonts, eyebrow labels above
headings, a modal for anything, emoji as icons, grey text. Taste's marketing-site rules (photographs, one section per
screen, dealt moments) do not apply to the app (`docs/ui-skills.md` §4).
