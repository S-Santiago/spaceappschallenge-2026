import copy
from pathlib import Path

import pytest

from fieldshift import rotations

FIXTURES = Path(__file__).parent / "fixtures"

# Mediterranean-like monthly climate (hand-made, not real data): wet winter, dry hot summer.
RAIN = [60, 55, 75, 45, 25, 5, 1, 3, 25, 55, 75, 65]
HEAVY = [0.2, 0.1, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.3, 0.3, 0.3]
HEAT = [0, 0, 0, 0, 0.5, 3, 8, 7, 1, 0, 0, 0]
FROST = [2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0.5, 1.5]


@pytest.fixture
def crops():
    return rotations.load_crops(FIXTURES / "crops.csv")


@pytest.fixture
def profile():
    months = [{"month": m + 1, "rain_mm": RAIN[m], "et0_mm": 80, "water_balance_mm": RAIN[m] - 80,
               "soil_wetness": 0.5, "frost_days": FROST[m], "heat_days": HEAT[m], "heavy_rain_days": HEAVY[m],
               "ndvi": 0.2 if m + 1 in (7, 8, 9, 10) else 0.5, "likely_bare": m + 1 in (7, 8, 9, 10)}
              for m in range(12)]
    return copy.deepcopy({"location": {"lat": 37.0, "lon": -4.5, "elevation_m": 300}, "months": months,
                          "trends": {"rain_change_pct": -10.0, "heat_days_change": 3.0}, "sources": ["test"]})
