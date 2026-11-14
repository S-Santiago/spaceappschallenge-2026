# data/

| Folder | In git? | Content |
|---|---|---|
| `raw/` | ❌ ignored | Original downloads, untouched |
| `processed/` | ❌ ignored | Cleaned / transformed outputs |
| `samples/` | ✅ yes | Small samples (< 5 MB) so judges can run the demo without downloading everything |

Rules:
1. Every file here must come from a source registered in [`../docs/nasa-data.md`](../docs/nasa-data.md).
2. Downloads must be reproducible: put the script in `src/` (or `notebooks/`) and reference it in the registry.
3. Synthetic or simulated data must be named `*_synthetic.*` and declared as such.
4. Never store credentials (Earthdata `.netrc`, API keys) here.
