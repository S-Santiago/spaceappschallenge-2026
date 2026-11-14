"""HTTP JSON API for the PWA (decision 0004). The same service serves the PWA static files.

Run from the repo root:  PYTHONPATH=src uvicorn fieldshift.api:app --reload
Endpoints and JSON are documented in docs/work-plan.md ("API"). No logic lives here: data comes from db.py,
the climate profile from climate.py and the strategies from rotations.py.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import unicodedata
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from . import climate, db, modis, power, rotations

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = Path(os.environ.get("FIELDSHIFT_WEB_DIR") or ROOT / "web")

# Stored profiles are reused only while climate.py is unchanged.
PROFILE_VERSION = hashlib.sha1(Path(climate.__file__).read_bytes()).hexdigest()[:12]

# MODIS (ORNL) can take minutes for a new point; POWER takes seconds. The farmer gets an answer from POWER
# after at most MODIS_WAIT_S; the NDVI download keeps going in the background and is used on the next request.
POWER_TIMEOUT_S = float(os.environ.get("FIELDSHIFT_POWER_TIMEOUT_S", 60))
MODIS_WAIT_S = float(os.environ.get("FIELDSHIFT_MODIS_WAIT_S", 3))
_inflight: dict[tuple[str, float, float], asyncio.Task] = {}  # one download per source and point

Lang = Literal["en", "es"]

app = FastAPI(title="FarmLens API", version="1")


class Priorities(BaseModel):
    water: float = Field(1, ge=0, le=3)
    soil: float = Field(1, ge=0, le=3)
    income: float = Field(1, ge=0, le=3)
    risk: float = Field(1, ge=0, le=3)


class AnalyzeRequest(BaseModel):
    field: str | None = Field(None, description="Demo field slug from GET /api/fields")
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    rotation: list[str] = Field(..., min_length=1, max_length=4, description="Crop ids, one per year")
    priorities: Priorities = Priorities()
    irrigation: Literal["none", "supplementary", "full"] = "none"
    slope: Literal["flat", "moderate", "steep"] = "flat"
    lang: Lang = "en"

    @model_validator(mode="after")
    def _location(self) -> AnalyzeRequest:
        if self.field is None and (self.lat is None or self.lon is None):
            raise ValueError("give a demo `field` or both `lat` and `lon`")
        return self


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/fields")
def fields() -> list[dict]:
    """Demo fields (pre-loaded NASA data, work offline)."""
    return [{k: f[k] for k in ("slug", "name", "lat", "lon", "elevation_m", "description")}
            for f in db.get_locations(demo_only=True)]


@app.get("/api/crops")
def crops(lang: Lang = "en") -> list[dict]:
    """Crops the farmer can pick for the current rotation, sorted by name in `lang` (accents ignored)."""
    return [{"id": c["crop_id"], "name": rotations.crop_name(c, lang), "type": c["type"], "family": c["family"],
             "n_fixing": c["n_fixing"] == "yes", "sow_month": c["sow_month"], "harvest_month": c["harvest_month"],
             "confidence": c["confidence"]}
            for c in sorted(db.get_engine_crops().values(),
                            key=lambda c: unicodedata.normalize("NFKD", rotations.crop_name(c, lang)).casefold())]


def _fetch(source: str, lat: float, lon: float) -> asyncio.Task:
    """Start (or join) the download of one NASA source for a point; it survives the request that started it."""
    key = (source, round(lat, 2), round(lon, 2))
    task = _inflight.get(key)
    if task is None:
        fetch = power.fetch_daily if source == "power" else modis.fetch_ndvi
        task = _inflight[key] = asyncio.create_task(fetch(lat, lon))
        task.add_done_callback(lambda t: (_inflight.pop(key, None), t.cancelled() or t.exception()))
    return task


async def _profile(lat: float, lon: float) -> tuple[dict, list[str]]:
    """Shape 1 profile and the sources still downloading (["ndvi"] while MODIS is slow)."""
    profile = db.get_profile(lat, lon, version=PROFILE_VERSION)
    if profile is not None:
        return profile, []

    power_task, modis_task = _fetch("power", lat, lon), _fetch("modis", lat, lon)
    try:
        power_data = await asyncio.wait_for(asyncio.shield(power_task), POWER_TIMEOUT_S)
    except Exception as exc:  # NASA POWER down, unreachable or too slow
        raise HTTPException(503, "NASA climate data is not available for this point right now. "
                                 "Try again in a few minutes or use a demo field.") from exc
    try:
        modis_data = await asyncio.wait_for(asyncio.shield(modis_task), MODIS_WAIT_S)
    except asyncio.TimeoutError:
        modis_data = None  # still downloading: answer without satellite greenness, do not store
    except Exception:
        modis_data = None  # MODIS failed: NDVI is optional

    profile = climate.build_profile(lat, lon, power_data, modis_data)
    if modis_data is not None or modis_task.done():
        db.save_profile(lat, lon, profile, version=PROFILE_VERSION)
        return profile, []
    return profile, ["ndvi"]


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> dict:
    """Shape 1 climate profile + Shape 2 strategies (current rotation + up to 3 alternatives)."""
    if req.field is not None:
        location = db.get_location(req.field)
        if location is None:
            raise HTTPException(404, f"unknown field: {req.field}")
        lat, lon = location["lat"], location["lon"]
    else:
        lat, lon = req.lat, req.lon

    profile, pending = await _profile(lat, lon)
    try:
        strategies = rotations.compare(profile, req.rotation, db.get_engine_crops(), req.priorities.model_dump(),
                                       irrigated=req.irrigation != "none", slope=req.slope, lang=req.lang)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    for s in strategies:
        s["labels"] = {k: rotations.label(v, req.lang) for k, v in s["scores"].items()}
    analysis_id = db.save_analysis(lat, lon, req.model_dump(), strategies)
    return {"analysis_id": analysis_id, "profile": profile, "strategies": strategies,
            "pending": pending,  # ["ndvi"]: bare-soil months unknown yet, ask again in a few minutes
            "disclaimer": rotations.DISCLAIMER[req.lang],
            "score_limits": {k: v[req.lang] for k, v in rotations.SCORE_LIMITS.items()}}


@app.get("/api/analyses/{analysis_id}")
def analysis(analysis_id: int) -> dict:
    found = db.get_analysis(analysis_id)
    if found is None:
        raise HTTPException(404, "analysis not found")
    return found


# The PWA (owner: frontend track) lives in web/; mounted last so /api/* routes win.
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="pwa")
else:
    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"app": "FarmLens API", "docs": "/docs", "pwa": f"not built yet ({WEB_DIR.name}/ missing)"}
