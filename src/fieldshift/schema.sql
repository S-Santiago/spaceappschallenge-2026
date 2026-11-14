-- Field Shift SQLite schema (migration 1). Applied by src/fieldshift/db.py.
-- Coordinates are rounded to 2 decimals (~1 km), the same key the NASA clients use.
-- JSON columns hold the payload shapes documented in docs/work-plan.md.

-- Crop characteristics, loaded from data/crops.csv (columns documented in docs/crop-traits.md).
CREATE TABLE crops (
    crop                   TEXT PRIMARY KEY,           -- snake_case id used in rotations
    scientific_name        TEXT,
    family                 TEXT NOT NULL,
    type                   TEXT NOT NULL CHECK (type IN ('cereal', 'legume', 'oilseed', 'forage', 'cover', 'other')),
    season                 TEXT CHECK (season IN ('autumn', 'spring', 'summer')),
    sow_month              INTEGER CHECK (sow_month BETWEEN 1 AND 12),
    harvest_month          INTEGER CHECK (harvest_month BETWEEN 1 AND 12),
    cycle_days_min         INTEGER,
    cycle_days_max         INTEGER,
    water_need_mm_min      REAL,
    water_need_mm_max      REAL,
    drought_tolerance      TEXT CHECK (drought_tolerance IN ('low', 'medium', 'high')),
    t_base_c               REAL,
    frost_damage_c         REAL,
    heat_stress_c          REAL,
    root_depth_m_max       REAL,
    n_fixing               TEXT NOT NULL CHECK (n_fixing IN ('yes', 'no')),
    ground_cover           TEXT CHECK (ground_cover IN ('low', 'medium', 'high')),
    forage_value           TEXT CHECK (forage_value IN ('low', 'medium', 'high')),
    residue_organic_matter TEXT CHECK (residue_organic_matter IN ('low', 'medium', 'high')),
    market_value           TEXT CHECK (market_value IN ('low', 'medium', 'high')),
    sources                TEXT,
    confidence             TEXT CHECK (confidence IN ('low', 'medium', 'high')),
    notes                  TEXT
);

-- Named fields (demo fields come from data/samples/locations.csv).
CREATE TABLE locations (
    slug        TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    lat         REAL NOT NULL,
    lon         REAL NOT NULL,
    elevation_m REAL,
    description TEXT,
    is_demo     INTEGER NOT NULL DEFAULT 0,
    UNIQUE (lat, lon)
);

-- Raw NASA API payloads (replaces the old JSON file cache).
CREATE TABLE nasa_raw (
    source     TEXT NOT NULL CHECK (source IN ('power', 'modis')),
    lat        REAL NOT NULL,
    lon        REAL NOT NULL,
    payload    TEXT NOT NULL,                          -- JSON returned by power.fetch_daily / modis.fetch_ndvi
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (source, lat, lon)
);

-- Monthly climate profile per point (shape 1), computed by climate.py.
CREATE TABLE climate_profiles (
    lat        REAL NOT NULL,
    lon        REAL NOT NULL,
    version    TEXT NOT NULL,                          -- climate.py version, so stale profiles are recomputed
    profile    TEXT NOT NULL,                          -- JSON, shape 1
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (lat, lon)
);

-- One row per rotation comparison the app runs. No personal data.
CREATE TABLE analyses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    lat        REAL NOT NULL,
    lon        REAL NOT NULL,
    inputs     TEXT NOT NULL,                          -- JSON: current rotation, priorities, irrigation, slope
    strategies TEXT NOT NULL,                          -- JSON, shape 2
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX analyses_point ON analyses (lat, lon, created_at);
