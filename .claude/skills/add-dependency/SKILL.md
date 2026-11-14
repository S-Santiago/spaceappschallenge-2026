---
name: add-dependency
description: Record a third-party library, framework, font, icon set, image, map tile provider, code snippet or model in docs/third-party.md with its exact license and attribution requirements, and flag incompatible licenses. Use whenever a package is installed or an external asset/snippet is added.
---

# Add dependency / asset

1. Identify the item and exact version (from the manifest or lock file, or the asset source page).
2. Find the license from an authoritative source: the package registry metadata (`npm view <pkg> license`, `pip show <pkg>`), the repository `LICENSE` file, or the asset's license page. Never guess.
3. Classify:
   - ✅ Permissive (MIT, BSD, Apache-2.0, ISC, CC0, CC BY, public domain) → OK, note attribution if required.
   - ⚠️ Copyleft (GPL, LGPL, AGPL, MPL, CC BY-SA) → warn the team; discuss impact on `docs/licensing.md`.
   - ❌ Non-commercial / no-derivatives / unknown / "free for personal use" → do not use; propose an alternative.
4. Add a row to the right section of `docs/third-party.md` (software, assets, data, snippets).
5. If attribution is required in the UI (e.g. map tiles "© OpenStreetMap contributors"), remind the team to add it.
6. If it is a tool rather than a library (editor, hosting, design app), add it to `docs/tools.md` instead.

Answer in Spanish with the verdict and the row you added.
