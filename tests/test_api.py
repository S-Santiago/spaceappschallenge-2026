import httpx
import pytest
from fastapi.testclient import TestClient

from fieldshift import api, db

ROTATION = ["durum_wheat", "durum_wheat", "sunflower"]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELDSHIFT_DB", str(tmp_path / "api.db"))
    db._ready.clear()

    def no_network(*args, **kwargs):
        raise AssertionError("demo fields must not call NASA")

    monkeypatch.setattr(httpx.AsyncClient, "send", no_network)
    return TestClient(api.app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_fields(client):
    fields = client.get("/api/fields").json()
    assert {f["slug"] for f in fields} == {"antequera", "campillos", "guadalhorce"}
    assert all(f["elevation_m"] is not None for f in fields)


def test_crops_in_both_languages(client):
    en = {c["id"]: c for c in client.get("/api/crops").json()}
    es = {c["id"]: c for c in client.get("/api/crops", params={"lang": "es"}).json()}
    assert en.keys() == es.keys() == {c["crop"] for c in db.get_crops()}
    assert en["chickpea"]["name"] == "Chickpea" and es["chickpea"]["name"] == "Garbanzo"
    assert en["chickpea"]["n_fixing"] is True
    assert en["sunflower"]["scientific_name"] == "Helianthus annuus"  # searchable Latin name in the PWA
    assert en["sunflower"]["name_es"] == "Girasol"
    assert client.get("/api/crops", params={"lang": "fr"}).status_code == 422


def test_crops_sorted_by_name_for_the_dropdown(client):
    import unicodedata
    for lang in ("en", "es"):
        names = [c["name"] for c in client.get("/api/crops", params={"lang": lang}).json()]
        key = [unicodedata.normalize("NFKD", n).casefold() for n in names]
        assert key == sorted(key)


def test_engine_crops_cover_perennials():
    alfalfa = db.get_engine_crops()["alfalfa"]
    assert alfalfa["crop_id"] == "alfalfa"
    assert alfalfa["harvest_month"] == (alfalfa["sow_month"] - 2) % 12 + 1


@pytest.mark.parametrize("field", ["antequera", "campillos", "guadalhorce"])
def test_analyze_demo_field(client, field):
    resp = client.post("/api/analyze", json={"field": field, "rotation": ROTATION, "lang": "es",
                                             "priorities": {"water": 3, "soil": 1, "income": 1, "risk": 0}})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["profile"]["months"]) == 12
    strategies = body["strategies"]
    assert strategies[0]["id"] == "current" and strategies[0]["years"] == ROTATION
    assert 2 <= len(strategies) <= 4
    for s in strategies:
        assert set(s["scores"]) == {"water", "soil", "income", "risk", "overall"}
        assert s["labels"]["overall"] in ("bueno", "regular", "malo")
        for key in ("why", "evidence", "gaps", "risks_to_review"):
            assert s[key]
        assert s["benefits"] or s["id"] == "current"  # the baseline has nothing to gain over itself
    assert body["disclaimer"]
    assert set(body["score_limits"]) == {"water", "soil", "income", "risk", "overall"}
    assert "orientativo" in body["score_limits"]["income"]  # Spanish, income is illustrative
    stored = client.get(f"/api/analyses/{body['analysis_id']}").json()
    assert stored["strategies"] == strategies


def test_profile_is_stored_and_reused(client):
    client.post("/api/analyze", json={"field": "antequera", "rotation": ["barley"]})
    loc = db.get_location("antequera")
    assert db.get_profile(loc["lat"], loc["lon"], version=api.PROFILE_VERSION) is not None


@pytest.mark.parametrize("payload, status", [
    ({"field": "antequera", "rotation": ["banana"]}, 422),            # unknown crop
    ({"field": "antequera", "rotation": []}, 422),                    # empty rotation
    ({"field": "antequera", "rotation": ["barley"] * 5}, 422),        # more than 4 years
    ({"rotation": ["barley"]}, 422),                                  # no location
    ({"field": "nowhere", "rotation": ["barley"]}, 404),              # unknown demo field
    ({"field": "antequera", "rotation": ["barley"], "slope": "cliff"}, 422),
])
def test_analyze_rejects_bad_input(client, payload, status):
    assert client.post("/api/analyze", json=payload).status_code == status


def test_unknown_location_without_network_is_503(client):
    resp = client.post("/api/analyze", json={"lat": 40.0, "lon": -3.0, "rotation": ["barley"]})
    assert resp.status_code == 503


def test_missing_analysis_is_404(client):
    assert client.get("/api/analyses/999").status_code == 404


def test_root_without_pwa(client, monkeypatch):
    if api.WEB_DIR.is_dir():
        pytest.skip("PWA present: / serves it")
    assert client.get("/").json()["docs"] == "/docs"


def _sample(kind):
    import json
    return json.loads((db.SAMPLES_DIR / f"{kind}_37.07_-4.87.json").read_text(encoding="utf-8"))


def test_slow_modis_answers_with_power_and_finishes_in_background(client, monkeypatch):
    import asyncio
    monkeypatch.setattr(api, "MODIS_WAIT_S", 0.05)
    calls = {"modis": 0}
    state = {"ready": False}

    async def fast_power(lat, lon):
        return _sample("power")

    async def slow_modis(lat, lon):
        calls["modis"] += 1
        while not state["ready"]:
            await asyncio.sleep(0.01)
        return _sample("modis")

    monkeypatch.setattr(api.power, "fetch_daily", fast_power)
    monkeypatch.setattr(api.modis, "fetch_ndvi", slow_modis)
    body = {"lat": 40.0, "lon": -3.0, "rotation": ["durum_wheat", "sunflower"]}

    with TestClient(api.app) as c:  # one event loop for all requests, like the real server
        first = c.post("/api/analyze", json=body).json()
        assert first["pending"] == ["ndvi"]
        assert all(m["likely_bare"] is None for m in first["profile"]["months"])
        assert first["strategies"][0]["id"] == "current"
        assert db.get_profile(40.0, -3.0) is None  # incomplete profile is not stored

        second = c.post("/api/analyze", json=body).json()
        assert second["pending"] == ["ndvi"]
        assert calls["modis"] == 1  # the retry joins the running download instead of starting another

        state["ready"] = True
        c.portal.call(asyncio.sleep, 0.1)  # let the background download finish
        third = c.post("/api/analyze", json=body).json()
        assert third["pending"] == []
        assert db.get_profile(40.0, -3.0) is not None


def test_complete_profile_has_nothing_pending(client):
    body = client.post("/api/analyze", json={"field": "campillos", "rotation": ["barley"]}).json()
    assert body["pending"] == []


def test_power_down_is_a_friendly_503(client, monkeypatch):
    async def down(lat, lon):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(api.power, "fetch_daily", down)
    resp = client.post("/api/analyze", json={"lat": 41.0, "lon": -2.0, "rotation": ["barley"]})
    assert resp.status_code == 503
    assert "connection refused" not in resp.json()["detail"]


@pytest.mark.parametrize("field", ["antequera", "campillos", "guadalhorce"])
def test_predictions_demo_field(client, field):
    body = client.get("/api/predictions", params={"field": field}).json()
    assert body["period"] == "2005-2025" and "Not a weather forecast" in body["basis"]
    assert len(body["rain_weeks"]) == 52 and body["rain_weeks"][0]["start"] == "01-01"
    assert body["frost"]["spring"]["years"] == 21
    assert {m["month"] for m in body["heavy_rain"]["months"]} == set(range(1, 13))
    assert isinstance(body["alerts"], list)  # demo fields have pre-loaded MODIS, so bare months are known


def test_predictions_alerts_follow_rotation_and_slope(client):
    params = {"field": "antequera", "rotation": ROTATION}
    flat = {a["month"]: a for a in client.get("/api/predictions", params=params).json()["alerts"]}
    assert flat[11]["level"] == "high" and "crop_calendar" in flat[11]["sources"]  # docs/indicators.md, P-07
    assert flat[10]["level"] == "medium"
    steep = {a["month"]: a for a in client.get("/api/predictions", params={**params, "slope": "steep"}).json()["alerts"]}
    assert steep[10]["level"] == "high"  # raise_for_slope


def test_predictions_free_point_uses_the_power_cache(client, monkeypatch):
    calls = []

    async def fake_power(lat, lon):
        calls.append((lat, lon))
        return _sample("power")

    monkeypatch.setattr(api.power, "fetch_daily", fake_power)
    body = client.get("/api/predictions", params={"lat": 40.0, "lon": -3.0}).json()
    assert calls == [(40.0, -3.0)]
    assert len(body["rain_weeks"]) == 52
    assert body["alerts"] is None  # no MODIS downloaded and no rotation: bare months unknown, not "no alerts"


@pytest.mark.parametrize("params, status", [
    ({"field": "nowhere"}, 404),
    ({}, 422),
    ({"lat": 37.0}, 422),
    ({"lat": 91, "lon": -4.6}, 422),
    ({"lat": 37.0, "lon": "east"}, 422),
    ({"field": "antequera", "rotation": ["banana"]}, 422),
    ({"field": "antequera", "slope": "cliff"}, 422),
])
def test_predictions_rejects_bad_input(client, params, status):
    assert client.get("/api/predictions", params=params).status_code == status


def test_predictions_power_down_is_a_friendly_503(client, monkeypatch):
    async def down(lat, lon):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(api.power, "fetch_daily", down)
    resp = client.get("/api/predictions", params={"lat": 41.0, "lon": -2.0})
    assert resp.status_code == 503
    assert "connection refused" not in resp.json()["detail"]
