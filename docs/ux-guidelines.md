# UX minimums for the demo

Adapted from the *UX support guide* provided by the Málaga UX desk (Ladies That UX Málaga). Examples are guidance; the **minimum values** are the reference to meet. Judges see many demos in a row: if they don't understand ours in seconds, they disconnect.

| # | Principle | Do | Avoid | Minimum values |
|---|---|---|---|---|
| 01 | **Purpose at first glance** | Clear title, one sentence, one prominent button (e.g. "See my field") | Only a big logo and "Start" | — |
| 02 | **Main flow** | Every step leads to the next until a clear "done" | Screens with no way forward or back | — |
| 03 | **Hierarchy & patterns** | One primary button; same elements on every screen | Buttons without hierarchy; every screen different | — |
| 04 | **Legibility** | User words and comfortable sizes ("Soil moisture: low") | Technical jargon, tiny text (`SM_anom=-0.21`) | Body 16 px web / 16 sp Android / 17 pt iOS · secondary ≥ 12 · max 3 font families |
| 05 | **Contrast & color** | Color + icon/text (works in grayscale) | Color as the only signal (red/green dots) | Text 4.5:1 · large text, icons, borders 3:1 · check with WebAIM Contrast Checker |
| 06 | **Touch targets** | Whole button is tappable, generous size | Small icons close together | iOS 44×44 pt · Android 48×48 dp · Web 44×44 px (min 24) · 8 spacing · no hover on mobile |
| 07 | **System feedback** | Each action responds: "Analyzing…" → "Done ✓"; helpful errors & empty states | Nothing happens on click; raw errors (`request failed 0x00F3`) | — |

## Launch route — self-assessment before showing the demo

Adapted from the *Launch route* sheet of the Málaga UX desk (Ladies That UX Málaga), same numbering 01–07. Walk through the demo as a team; it is a help, not an exam. Each stage gets **GO** when all its required items are met, otherwise **NOT YET**. ☆ Extras add value but are optional. **All stages GO → ready to show.** Questions: UX desk (Product Designer UX/UI) at the venue.

> Text size: the sheet asks for *at least* 14 px; we keep **16 px** for body text (guide value, better on low-end phones).

| # | Stage | Required | ☆ Extra |
|---|---|---|---|
| 01 | Purpose at first glance | First screen says what it is and who it is for · the main action stands out most | Someone from another team understands it in 5 seconds |
| 02 | Main flow | Key task completes from start to end · from every screen you can go forward or back | **The user knows which step they are on** (e.g. "Step 2 of 4") |
| 03 | Hierarchy & patterns | One primary action per screen, secondary ones more discreet · repeated elements (buttons, cards, menu) look the same everywhere | Familiar patterns (magnifier = search, X = close) |
| 04 | Legibility | Body text readable without effort (we use ≥ 16 px) · buttons and titles use the user's words | Max 3 typefaces |
| 05 | Contrast & color | Text readable on its background **even with low screen brightness** · important things never rely on color alone (add text or icon) | Everything still understandable in grayscale |
| 06 | Touch targets | Buttons and links easy to tap with a finger · enough spacing to avoid tapping the neighbor | **Readable from 2 m** with the laptop on the table (pitch) |
| 07 | System feedback | Every action shows a visible response (change, message or loading indicator) · errors say what happened and how to continue | **Empty screens say what to do** |

### ⚠️ Red alert — must NOT appear in the demo
- Placeholder text or data: "lorem ipsum", "Title here", "asdf", "TODO", "test".
- Buttons that do nothing in the flow you are going to show.
- Technical errors on screen: "Error 500", "undefined", "NaN", "None", Python tracebacks, raw API error messages.
- States distinguished only by color, without text or icon.

## Mobile-first, low-end phones (primary target)

Our users are farmers with **at most a low/mid-range Android phone**, small screen, slow or unstable mobile data (often in the field), limited data plans and little technical experience. Design for that phone first; desktop is a bonus.

| Area | Rule |
|---|---|
| Layout | Single column. Must work at **360 × 640 px** with no horizontal scroll. No side-by-side columns for key content (they stack badly), **no essential inputs hidden behind a menu** |
| Flow | One step per screen section: field → current rotation → priorities → **one big "Analyze my field" button** → results. Few inputs, sensible defaults, demo field preselected |
| Inputs | Selectboxes/radio/sliders with large targets (≥ 48 px); avoid free typing; no map required — a map is optional, demo fields and a simple list come first |
| Weight | Text, icons and simple tables first. Charts: lightweight and few; avoid heavy interactive maps/3D (pydeck) on the main path. No large images; compress any image; no custom web fonts |
| Speed | Results for demo fields in **< 3 s** from pre-loaded data; never trigger the ~25 s MODIS call in the demo path; show progress ("Fetching NASA data…") when a live call is unavoidable |
| Connectivity | Tolerate reconnections; cache everything (`st.cache_data` + DB); keep the page usable if a chart fails |
| Language | Short sentences, everyday words, units always shown; technical terms explained in one line. (Repo/UI text in English per NASA rules — keep it simple English) |
| Results | Strategy cards stacked vertically; the key message of each card visible without expanding; details in expanders |
| Test | Before each merge to `main`: Chrome DevTools device mode (360 px, "Slow 4G" + CPU 4× slowdown) **and** a real low/mid-range phone before the demo |

## Agriculture-specific notes
- Farmers often use the phone **outdoors**: high contrast, large text, works on slow connections.
- Translate indices into decisions: not "NDVI 0.42" but "Crop vigor below normal for this week — check irrigation".
- Always show **units and the date of the data**, and where it comes from (builds trust and answers the Relevance criterion).
- Show uncertainty honestly ("satellite estimate, ~9 km resolution").

Use the `/ux-review` skill or the `ux-reviewer` agent to check a screen.
