"""SQLite storage: crop catalogue, fields, cached NASA payloads, climate profiles and analysis runs.

The database file is generated (git-ignored) and rebuilt from committed seeds, so the app works offline:
- data/crops.csv                    -> crops
- data/samples/locations.csv        -> locations (demo fields)
- data/samples/{power,modis}_*.json -> nasa_raw (pre-fetched NASA data for the demo fields)

Path: env var FIELDSHIFT_DB, default data/processed/fieldshift.db. Run `python -m fieldshift.db reset` to rebuild.
"""

from __future__ import annotations

import csv
import json
import os
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "processed" / "fieldshift.db"
CROPS_CSV = ROOT / "data" / "crops.csv"
SAMPLES_DIR = ROOT / "data" / "samples"
LOCATIONS_CSV = SAMPLES_DIR / "locations.csv"

# Each entry is one migration; PRAGMA user_version stores how many have been applied.
MIGRATIONS = [
    (Path(__file__).with_name("schema.sql")).read_text(encoding="utf-8"),
    # 2: display names and season-specific frost/heat tolerance levels used by the rotation engine
    """
    ALTER TABLE crops ADD COLUMN name TEXT;
    ALTER TABLE crops ADD COLUMN name_es TEXT;
    ALTER TABLE crops ADD COLUMN frost_tolerance TEXT CHECK (frost_tolerance IN ('low', 'medium', 'high'));
    ALTER TABLE crops ADD COLUMN heat_tolerance TEXT CHECK (heat_tolerance IN ('low', 'medium', 'high'));
    """,
    # 3: crops that only make sense with irrigation in Andalusia (never proposed for rain-fed fields)
    "ALTER TABLE crops ADD COLUMN irrigation_required TEXT CHECK (irrigation_required IN ('yes', 'no'));",
]

_ready: set[Path] = set()


def db_path() -> Path:
    return Path(os.environ.get("FIELDSHIFT_DB") or DEFAULT_DB)


def _key(lat: float, lon: float) -> tuple[float, float]:
    return round(lat, 2), round(lon, 2)


def _open(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Connection to the configured DB (initialised on first use); commits on success."""
    path = db_path()
    if path not in _ready:
        init_db(path)
    conn = _open(path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db(path: Path | None = None, *, reset: bool = False) -> None:
    """Apply pending migrations and load the committed seeds."""
    path = Path(path or db_path())
    if reset and path.exists():
        path.unlink()
    conn = _open(path)
    try:
        with conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            for i, sql in enumerate(MIGRATIONS[version:], start=version + 1):
                conn.executescript(sql)
                conn.execute(f"PRAGMA user_version = {i}")
            _seed_crops(conn)
            _seed_locations(conn)
            _seed_samples(conn)
    finally:
        conn.close()
    _ready.add(path)


def _read_csv(path: Path) -> list[dict[str, str | None]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return [{k: (v.strip() or None) for k, v in row.items()} for row in csv.DictReader(f)]


def _seed_crops(conn: sqlite3.Connection) -> None:
    # The CSV is the single source of truth, so the table is reloaded every time.
    conn.execute("DELETE FROM crops")
    rows = _read_csv(CROPS_CSV)
    if rows:
        cols = list(rows[0])
        conn.executemany(
            f"INSERT INTO crops ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            [tuple(r[c] for c in cols) for r in rows],
        )


def _seed_locations(conn: sqlite3.Connection) -> None:
    for r in _read_csv(LOCATIONS_CSV):
        lat, lon = _key(float(r["lat"]), float(r["lon"]))
        conn.execute(
            "INSERT OR REPLACE INTO locations (slug, name, lat, lon, elevation_m, description, is_demo)"
            " VALUES (?, ?, ?, ?, ?, ?, 1)",
            (r["slug"], r["name"], lat, lon, r.get("elevation_m"), r.get("description")),
        )


def _seed_samples(conn: sqlite3.Connection) -> None:
    # Sample files are named like the old JSON cache: <source>_<lat>_<lon>.json
    have = {(s, la, lo) for s, la, lo in conn.execute("SELECT source, lat, lon FROM nasa_raw")}
    for file in sorted(SAMPLES_DIR.glob("*.json")):
        parts = file.stem.split("_")
        if len(parts) != 3:
            continue
        source, lat, lon = parts
        if source not in ("power", "modis"):
            continue
        lat, lon = _key(float(lat), float(lon))
        if (source, lat, lon) not in have:
            conn.execute(
                "INSERT INTO nasa_raw (source, lat, lon, payload) VALUES (?, ?, ?, ?)",
                (source, lat, lon, file.read_text(encoding="utf-8")),
            )


# --- crops & locations -------------------------------------------------------------------------


def get_crops() -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM crops ORDER BY crop")]


def get_crop(crop: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM crops WHERE crop = ?", (crop,)).fetchone()
    return dict(row) if row else None


def get_engine_crops() -> dict[str, dict]:
    """Crop catalogue in the format rotations.py expects: {crop_id: traits}.

    Renames `crop` -> `crop_id`, `root_depth_m_max` -> `root_depth_m`, `market_value` -> `market_value_illustrative`,
    and gives perennials without a harvest month (alfalfa) a 12-month window.
    """
    out = {}
    for c in get_crops():
        c = {**c, "crop_id": c["crop"], "root_depth_m": c["root_depth_m_max"],
             "market_value_illustrative": c["market_value"]}
        if c["sow_month"] is not None and c["harvest_month"] is None:
            c["harvest_month"] = (c["sow_month"] - 2) % 12 + 1  # occupies the field all year
        out[c["crop_id"]] = c
    return out


def get_locations(demo_only: bool = False) -> list[dict]:
    sql = "SELECT * FROM locations" + (" WHERE is_demo = 1" if demo_only else "") + " ORDER BY name"
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql)]


def get_location(slug: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM locations WHERE slug = ?", (slug,)).fetchone()
    return dict(row) if row else None


# --- raw NASA payloads (used by cache.py) -------------------------------------------------------


def get_raw(source: str, lat: float, lon: float) -> Any | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT payload FROM nasa_raw WHERE source = ? AND lat = ? AND lon = ?", (source, *_key(lat, lon))
        ).fetchone()
    return json.loads(row["payload"]) if row else None


def save_raw(source: str, lat: float, lon: float, payload: Any) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO nasa_raw (source, lat, lon, payload) VALUES (?, ?, ?, ?)",
            (source, *_key(lat, lon), json.dumps(payload)),
        )


# --- climate profiles (shape 1) ------------------------------------------------------------------


def get_profile(lat: float, lon: float, version: str | None = None) -> dict | None:
    """Stored profile for the point; if `version` is given, only a profile computed by that version."""
    with connect() as conn:
        row = conn.execute(
            "SELECT profile, version FROM climate_profiles WHERE lat = ? AND lon = ?", _key(lat, lon)
        ).fetchone()
    if row is None or (version is not None and row["version"] != version):
        return None
    return json.loads(row["profile"])


def save_profile(lat: float, lon: float, profile: dict, version: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO climate_profiles (lat, lon, version, profile) VALUES (?, ?, ?, ?)",
            (*_key(lat, lon), version, json.dumps(profile)),
        )


# --- analyses (inputs + shape 2) -----------------------------------------------------------------


def save_analysis(lat: float, lon: float, inputs: dict, strategies: list[dict]) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO analyses (lat, lon, inputs, strategies) VALUES (?, ?, ?, ?)",
            (*_key(lat, lon), json.dumps(inputs), json.dumps(strategies)),
        )
        return cur.lastrowid


def get_analysis(analysis_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    return _analysis(row) if row else None


def list_analyses(lat: float, lon: float, limit: int = 10) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM analyses WHERE lat = ? AND lon = ? ORDER BY id DESC LIMIT ?", (*_key(lat, lon), limit)
        )
        return [_analysis(r) for r in rows]


def _analysis(row: sqlite3.Row) -> dict:
    return {**dict(row), "inputs": json.loads(row["inputs"]), "strategies": json.loads(row["strategies"])}


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "init"
    if command not in ("init", "reset"):
        sys.exit("usage: python -m fieldshift.db [init|reset]")
    init_db(reset=command == "reset")
    with connect() as conn:
        for table in ("crops", "locations", "nasa_raw", "climate_profiles", "analyses"):
            print(f"{table}: {conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]} rows")
    print(f"database: {db_path()}")
