---
name: nasa-power-fetch
description: Fetch daily NASA POWER climate data (Tmax, Tmin, precipitation, root-zone soil wetness, and more if needed) for a field location using the existing client src/fieldshift/power.py, pre-cache it in data/samples/ so the demo works offline, and register the source in docs/nasa-data.md. Use whenever the project needs climate history for a location or a new demo location.
---

# NASA POWER fetch

Arguments: `lat lon` (e.g. `/nasa-power-fetch 36.72 -4.42`). Optional: extra parameters to add.

## 1. Use the existing client — do not create another one
The team already has `src/fieldshift/power.py`:
- `async fetch_daily(lat, lon) -> {"meta": {...}, "days": {"YYYYMMDD": {param: value}}}`
- Endpoint `https://power.larc.nasa.gov/api/temporal/daily/point`, `community=AG`, no key needed.
- Period fixed by `START_YEAR`/`END_YEAR` (2005–2025); parameters in `PARAMETERS` (`T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `GWETROOT`).
- Fill value `-999` → `None`. Coordinates rounded to 2 decimals.
- Cache via `src/fieldshift/cache.py`: reads `data/processed/cache/` (git-ignored, runtime) then `data/samples/` (committed, demo); writes to `data/processed/cache/power_<lat>_<lon>.json`.

Run it, e.g. from the repo root:
```bash
python -c "import asyncio; from src.fieldshift import power; d = asyncio.run(power.fetch_daily(36.72, -4.42)); print(len(d['days']))"
```
(adjust the import to how the package is installed/run; check `README.md`.)

## 2. Pre-cache for the demo (offline-safe)
Copy `data/processed/cache/power_<lat>_<lon>.json` to `data/samples/` for every demo location so the app works without internet. Check the file size (keep samples small; if > 5 MB, tell the team).

## 3. Adding parameters
If an indicator needs more variables (e.g. `T2M`, `ALLSKY_SFC_SW_DWN` / `TOA_SW_DWN` for evapotranspiration, `RH2M`, `WS2M`):
- Verify names and units against the official POWER parameter list first.
- Changing `PARAMETERS` invalidates existing caches (same file name, different content): delete the old cache files and re-fetch, and tell the team (track A owns `power.py`).
- The daily point endpoint limits the number of parameters per request — split calls if needed.

## 4. Traceability (mandatory)
Run or update the `nasa-dataset-check` entry for NASA POWER in `docs/nasa-data.md`:
- Meteorology is **MERRA-2 reanalysis** (~0.5° × 0.625°), solar from satellite-derived products, `GWETROOT` is **model output** — estimates for a grid cell of roughly a comarca, **not measurements at the farm**.
- Record the API version from `meta.api_version`, period, access date and the citation/acknowledgement required by the POWER project (copy it from the official site).
- `httpx` is already registered in `docs/third-party.md`; register any new dependency with `add-dependency`.

## 5. Report (in Spanish)
Location, days returned, % missing per parameter, cache/sample path, and the limitation sentence.
