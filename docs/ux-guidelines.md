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

## Agriculture-specific notes
- Farmers often use the phone **outdoors**: high contrast, large text, works on slow connections.
- Translate indices into decisions: not "NDVI 0.42" but "Crop vigor below normal for this week — check irrigation".
- Always show **units and the date of the data**, and where it comes from (builds trust and answers the Relevance criterion).
- Show uncertainty honestly ("satellite estimate, ~9 km resolution").

Use the `/ux-review` skill or the `ux-reviewer` agent to check a screen.
