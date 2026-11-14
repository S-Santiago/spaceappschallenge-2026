"""Static checks for the PWA in web/ (decision 0005): served by the API, installable, light, no red-alert text.

Behaviour of the JS helpers is tested with `node --test "tests/web/*.test.mjs"`.
"""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fieldshift import api, db

WEB = Path(__file__).resolve().parents[1] / "web"
JS_BUDGET = 200 * 1024  # first-load JS, decision 0004 (the map library is loaded only on demand)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELDSHIFT_DB", str(tmp_path / "pwa.db"))
    db._ready.clear()
    return TestClient(api.app)


def test_api_serves_the_pwa(client):
    page = client.get("/")
    assert page.status_code == 200
    assert "<title>FarmLens" in page.text
    for path in ("/manifest.webmanifest", "/sw.js", "/js/app.js", "/styles.css", "/icons/icon-192.png"):
        assert client.get(path).status_code == 200, path
    assert client.get("/api/health").json() == {"status": "ok"}  # API routes still win over the static mount


def test_manifest_is_installable():
    manifest = json.loads((WEB / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["display"] == "standalone" and manifest["start_url"]
    sizes = {i["sizes"] for i in manifest["icons"] if i["type"] == "image/png"}
    assert {"192x192", "512x512"} <= sizes
    for icon in manifest["icons"]:
        assert (WEB / icon["src"]).is_file(), icon["src"]


def test_service_worker_precaches_existing_files():
    sw = (WEB / "sw.js").read_text(encoding="utf-8")
    files = re.search(r"SHELL_FILES = \[(.*?)\];", sw, re.S).group(1)
    for name in re.findall(r'"([^"]+)"', files):
        if name != "./":
            assert (WEB / name).is_file(), name


def test_first_load_js_budget():
    first_load = [p for p in (WEB / "js").glob("*.js")]
    assert sum(p.stat().st_size for p in first_load) < JS_BUDGET


def test_no_placeholders_or_mock_data_in_the_pwa():
    for path in [*(WEB / "js").glob("*.js"), WEB / "index.html"]:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"lorem ipsum|TODO|asdf|mock_", text, re.I), path.name
        assert "fetch(" not in text or path.name == "api.js", f"{path.name}: API calls belong in api.js"
