"""Towns pre-fetched for the live demo (data/samples/prefetch_points.csv) answer from the DB, never from NASA."""

import csv

import httpx
import pytest
from fastapi.testclient import TestClient

from fieldshift import api, db, samples

with samples.PREFETCH_CSV.open(encoding="utf-8", newline="") as f:
    POINTS = list(csv.DictReader(f))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELDSHIFT_DB", str(tmp_path / "prefetch.db"))
    monkeypatch.setattr(api, "_modis_failed", {})
    db._ready.clear()

    def no_network(*args, **kwargs):  # power.py / modis.py read the DB cache first, so this proves no NASA call
        raise AssertionError("a pre-fetched point must not call NASA")

    monkeypatch.setattr(httpx.AsyncClient, "send", no_network)
    return TestClient(api.app)


def test_prefetch_points_are_not_demo_fields(client):
    slugs = {f["slug"] for f in client.get("/api/fields").json()}
    assert slugs.isdisjoint({p["slug"] for p in POINTS})


@pytest.mark.parametrize("point", POINTS, ids=[p["slug"] for p in POINTS])
def test_prefetch_point_answers_complete_without_network(client, monkeypatch, point):
    lat, lon = float(point["lat"]), float(point["lon"])
    sources = point["sources"].split(";")
    assert "modis" in sources
    if "power" not in sources:
        async def live_power(lat, lon):  # stands in for the ~5 s live POWER download of a satellite-only town
            return db.get_raw("power", 37.03, -4.64)
        monkeypatch.setattr(api.power, "fetch_daily", live_power)

    body = client.post("/api/analyze", json={"lat": lat, "lon": lon, "rotation": ["durum_wheat", "sunflower"]}).json()
    assert body["pending"] == [] and body["failed"] == []
    bare = [m["month"] for m in body["profile"]["months"] if m["likely_bare"]]
    assert any(m in bare for m in (7, 8, 9)), "field-crop pattern: bare in summer"
    assert not all(m["likely_bare"] for m in body["profile"]["months"]), "not a built-up pixel"

    pred = client.get("/api/predictions", params={"lat": lat, "lon": lon, "rotation": ["durum_wheat", "sunflower"]})
    assert pred.status_code == 200 and pred.json()["alerts"] is not None
