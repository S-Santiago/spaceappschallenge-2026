import csv

import pytest

from fieldshift import cache, db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELDSHIFT_DB", str(tmp_path / "test.db"))
    db._ready.clear()


def test_init_is_idempotent():
    db.init_db()
    db.init_db()
    with db.connect() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)


def test_crops_match_csv():
    with db.CROPS_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    crops = db.get_crops()
    assert [c["crop"] for c in crops] == sorted(r["crop"] for r in rows)
    for crop in crops:
        assert db.get_crop(crop["crop"]) == crop


def test_demo_locations_are_loaded():
    with db.LOCATIONS_CSV.open(encoding="utf-8") as f:
        slugs = {r["slug"] for r in csv.DictReader(f)}
    assert {loc["slug"] for loc in db.get_locations(demo_only=True)} == slugs


def test_raw_cache_roundtrip_uses_rounded_key():
    assert cache.load("power", 10.0, 20.0) is None
    cache.save("power", 10.004, 19.996, {"days": {"20250101": {"T2M_MAX": 12.5}}})
    assert cache.load("power", 10.0, 20.0) == {"days": {"20250101": {"T2M_MAX": 12.5}}}
    assert cache.load("modis", 10.0, 20.0) is None


def test_profile_versioning():
    profile = {"location": {"lat": 1.0, "lon": 2.0}, "months": [], "trends": {}, "sources": []}
    db.save_profile(1.0, 2.0, profile, version="1")
    assert db.get_profile(1.0, 2.0) == profile
    assert db.get_profile(1.0, 2.0, version="1") == profile
    assert db.get_profile(1.0, 2.0, version="2") is None


def test_analyses():
    inputs = {"rotation": ["durum_wheat", "sunflower"], "priorities": ["water"]}
    strategies = [{"id": "current", "scores": {"overall": 57}}]
    first = db.save_analysis(1.0, 2.0, inputs, strategies)
    second = db.save_analysis(1.0, 2.0, inputs, [])
    assert db.get_analysis(first)["strategies"] == strategies
    assert [a["id"] for a in db.list_analyses(1.0, 2.0)] == [second, first]


def test_samples_are_loaded_offline():
    files = [*db.SAMPLES_DIR.glob("power_*.json"), *db.SAMPLES_DIR.glob("modis_*.json")]
    assert files
    for file in files:
        source, lat, lon = file.stem.split("_")
        assert db.get_raw(source, float(lat), float(lon)) is not None
