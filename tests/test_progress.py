"""Live progress of the NASA downloads (src/fieldshift/progress.py, GET /api/progress)."""

import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from fieldshift import api, db, modis, progress


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(progress, "_points", {})
    monkeypatch.setattr(api, "_modis_failed", {})


def test_modis_reports_batches_and_retries_without_changing_the_data(monkeypatch):
    monkeypatch.setattr(modis.cache, "load", lambda *a: None)
    monkeypatch.setattr(modis.cache, "save", lambda *a: None)
    real_sleep = asyncio.sleep
    monkeypatch.setattr(modis.asyncio, "sleep", lambda s: real_sleep(0))
    seen = []
    busy = {"left": 2}

    async def fake_get(self, url, params=None, headers=None):
        entry = progress.current.get()
        seen.append(dict(entry["tries"]))
        request = httpx.Request("GET", url)
        if params["startDate"] == "A2024001" and busy["left"]:  # first batch: server busy twice, then fine
            busy["left"] -= 1
            return httpx.Response(503, request=request)
        return httpx.Response(200, request=request, json={"subset": [
            {"calendar_date": f"{params['startDate'][1:5]}-01-{len(seen):02d}", "data": [5000]}]})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    entry = progress.start("modis", 36.9, -4.6)
    token = progress.current.set(entry)
    try:
        result = asyncio.run(modis.fetch_ndvi(36.9, -4.6))
    finally:
        progress.current.reset(token)

    assert entry["batches_total"] == len(modis._chunks()) == 5
    assert entry["batches_done"] == 5
    assert entry["tries"] == {}  # every batch finished
    assert max(t.get(0, 1) for t in seen) == 3  # batch 0 was on its 3rd try at some point
    assert len(result["points"]) == 5  # same data as without tracking


def test_modis_without_tracking_still_works(monkeypatch):
    assert progress.current.get() is None
    progress.batches(5)
    progress.batch_try(0, 2)
    progress.batch_done(0)  # no-ops outside a tracked download


def test_snapshot_shows_the_slowest_batch_try_and_elapsed(monkeypatch):
    clock = {"t": 100.0}
    monkeypatch.setattr(progress.time, "monotonic", lambda: clock["t"])
    power = progress.start("power", 36.9, -4.6)
    modis_entry = progress.start("modis", 36.9, -4.6)
    token = progress.current.set(modis_entry)
    progress.batches(5)
    progress.batch_done(1)
    progress.batch_try(0, 2)
    progress.batch_try(3, 3)
    progress.current.reset(token)
    clock["t"] = 112.0
    progress.finish(power, ok=True)
    clock["t"] = 130.0
    snap = progress.snapshot(36.9, -4.6, stored={}, tries_max=4)
    assert snap["power"] == {"state": "done", "elapsed_s": 12}
    assert snap["modis"] == {"state": "running", "elapsed_s": 30, "batches_done": 1, "batches_total": 5,
                             "attempt": 3, "attempts_max": 4}


def test_old_entries_are_dropped(monkeypatch):
    clock = {"t": 0.0}
    monkeypatch.setattr(progress.time, "monotonic", lambda: clock["t"])
    progress.start("power", 1.0, 1.0)
    clock["t"] = progress.KEEP_S + 1
    progress.start("power", 2.0, 2.0)
    assert (1.0, 1.0) not in progress._points


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELDSHIFT_DB", str(tmp_path / "progress.db"))
    db._ready.clear()
    return TestClient(api.app)


@pytest.mark.parametrize("params", [{"lat": 91, "lon": 0}, {"lat": 0, "lon": -181}, {"lat": 36.9},
                                    {"lat": "x", "lon": 0}, {}])
def test_progress_validates_lat_lon(client, params):
    assert client.get("/api/progress", params=params).status_code == 422


def test_progress_unknown_point_is_idle_and_never_cached(client):
    resp = client.get("/api/progress", params={"lat": 10.0, "lon": 10.0})
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"
    body = resp.json()
    assert body["power"]["state"] == "idle" and body["modis"]["state"] == "idle"
    assert set(body) == {"power", "modis"}  # counters only


def test_progress_of_a_demo_field_is_done(client):
    loc = db.get_location("antequera")
    body = client.get("/api/progress", params={"lat": loc["lat"], "lon": loc["lon"]}).json()
    assert body["power"]["state"] == body["modis"]["state"] == "done"


def _sample(kind):
    import json
    return json.loads((db.SAMPLES_DIR / f"{kind}_37.07_-4.87.json").read_text(encoding="utf-8"))


def test_progress_follows_a_slow_then_failed_modis_download(client, monkeypatch):
    monkeypatch.setattr(api, "MODIS_WAIT_S", 0.05)
    state = {"fail": False}

    async def fast_power(lat, lon):
        return _sample("power")

    async def slow_modis(lat, lon):
        progress.batches(5)
        progress.batch_done(0)
        progress.batch_try(1, 2)
        while not state["fail"]:
            await asyncio.sleep(0.01)
        raise RuntimeError("ORNL down")

    monkeypatch.setattr(api.power, "fetch_daily", fast_power)
    monkeypatch.setattr(api.modis, "fetch_ndvi", slow_modis)
    body = {"lat": 40.3, "lon": -3.3, "rotation": ["durum_wheat", "sunflower"]}
    where = {"lat": 40.3, "lon": -3.3}

    with TestClient(api.app) as c:
        assert c.post("/api/analyze", json=body).json()["pending"] == ["ndvi"]
        snap = c.get("/api/progress", params=where).json()
        assert snap["power"]["state"] == "done"
        assert snap["modis"] | {"elapsed_s": 0} == {"state": "running", "elapsed_s": 0, "batches_done": 1,
                                                    "batches_total": 5, "attempt": 2, "attempts_max": 4}
        state["fail"] = True
        c.portal.call(asyncio.sleep, 0.1)
        assert c.get("/api/progress", params=where).json()["modis"]["state"] == "failed"
        assert c.post("/api/analyze", json=body).json()["failed"] == ["ndvi"]  # still failed, not restarted
        assert c.get("/api/progress", params=where).json()["modis"]["state"] == "failed"
