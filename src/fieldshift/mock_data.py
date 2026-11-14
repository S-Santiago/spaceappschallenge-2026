"""Mock data layer for the app skeleton (issue #12).

The UI (src/app.py) only talks to the four functions below. Issue #14 swaps them for
the real modules without touching the UI:

    get_demo_fields()                      -> db.py demo-field seed (#6/#8)
    get_crops()                            -> db.get_crops() (#7)
    get_climate_profile(lat, lon)          -> climate.py, Shape 1 (#9)
    get_strategies(profile, inputs)        -> rotations.py, Shape 2 (#10/#11)

Everything returned here is MOCK DATA, typed by hand, not computed from NASA data.
"""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"

IS_MOCK = True  # the UI shows a "mock data" warning while this is True

PRIORITY_KEYS = ("water", "soil", "income", "risk")  # same keys as Shape 2 "scores"


@dataclass
class FarmerInputs:
    """Everything the farmer enters, in the form the engine will need."""

    lat: float
    lon: float
    field_name: str
    rotation: list[str]  # crop ids, one per year, same ids as Shape 2 "years"
    priorities: dict[str, int]  # raw slider values 0-5, keys = PRIORITY_KEYS
    irrigation: str  # "none" | "supplementary" | "full"
    slope: str  # "flat" | "gentle" | "steep"
    weights: dict[str, float] = field(init=False)  # priorities normalized to sum 1

    def __post_init__(self) -> None:
        self.weights = normalize_priorities(self.priorities)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_priorities(priorities: dict[str, int]) -> dict[str, float]:
    """Turn 0-5 slider values into weights that add up to 1 (equal weights if all are 0)."""
    total = sum(priorities.get(k, 0) for k in PRIORITY_KEYS)
    if total == 0:
        return {k: 1 / len(PRIORITY_KEYS) for k in PRIORITY_KEYS}
    return {k: priorities.get(k, 0) / total for k in PRIORITY_KEYS}


def get_demo_fields() -> list[dict[str, Any]]:
    """Demo fields that work offline."""
    return [
        {"id": "malaga_dryland", "name": "Demo field — Málaga (dryland)", "lat": 36.72, "lon": -4.42},
    ]


def get_crops() -> list[dict[str, str]]:
    """Mock crop catalogue (id + English label). Real one: data/crops.csv via the DB (#7)."""
    return [
        {"id": "durum_wheat", "name": "Durum wheat"},
        {"id": "soft_wheat", "name": "Bread wheat"},
        {"id": "barley", "name": "Barley"},
        {"id": "oats", "name": "Oats"},
        {"id": "chickpea", "name": "Chickpea"},
        {"id": "lentil", "name": "Lentil"},
        {"id": "faba_bean", "name": "Faba bean"},
        {"id": "vetch", "name": "Vetch"},
        {"id": "sunflower", "name": "Sunflower"},
        {"id": "rapeseed", "name": "Rapeseed"},
        {"id": "fallow", "name": "Fallow (no crop)"},
    ]


def _load(name: str) -> Any:
    return json.loads((SAMPLES_DIR / name).read_text(encoding="utf-8"))


def get_climate_profile(lat: float, lon: float) -> dict[str, Any]:
    """Shape 1. The mock ignores the location except for echoing it back."""
    profile = _load("mock_climate_profile.json")
    profile.pop("_note", None)
    profile["location"].update({"lat": round(lat, 4), "lon": round(lon, 4)})
    return profile


def get_strategies(profile: dict[str, Any], inputs: FarmerInputs) -> list[dict[str, Any]]:
    """Shape 2: the farmer's current rotation + 3 alternatives.

    Mock behaviour: the "current" strategy takes the farmer's rotation, and "overall" is the
    priority-weighted mean of the four mock scores so the sliders visibly matter. The real
    scoring belongs to rotations.py and must be defined in docs/indicators.md.
    """
    strategies = copy.deepcopy(_load("mock_strategies.json"))
    for s in strategies:
        if s["id"] in ("current", "cover_crop"):
            s["years"] = list(inputs.rotation)
        s["scores"]["overall"] = round(sum(s["scores"][k] * inputs.weights[k] for k in PRIORITY_KEYS))
    return strategies
