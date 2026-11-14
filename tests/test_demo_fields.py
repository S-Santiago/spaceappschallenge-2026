import asyncio
import time

import httpx
import pytest

from fieldshift import db, modis, power


@pytest.fixture(autouse=True)
def offline_fresh_db(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELDSHIFT_DB", str(tmp_path / "demo.db"))
    db._ready.clear()

    def no_network(*args, **kwargs):
        raise AssertionError("demo fields must load without network")

    monkeypatch.setattr(httpx.AsyncClient, "send", no_network)


def test_demo_fields_load_offline_and_fast():
    start = time.perf_counter()
    fields = db.get_locations(demo_only=True)  # first call builds the DB from the committed seeds
    assert len(fields) >= 2
    for field in fields:
        daily = asyncio.run(power.fetch_daily(field["lat"], field["lon"]))
        ndvi = asyncio.run(modis.fetch_ndvi(field["lat"], field["lon"]))
        assert len(daily["days"]) > 7000
        assert len(ndvi["points"]) > 40
        assert field["elevation_m"] is not None
    assert time.perf_counter() - start < 3


def test_samples_stay_small():
    size = sum(f.stat().st_size for f in db.SAMPLES_DIR.iterdir() if f.is_file())
    assert size < 5 * 1024 * 1024
