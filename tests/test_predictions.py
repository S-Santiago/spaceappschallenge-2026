"""Hand-checkable tests for src/fieldshift/predictions.py (P-01 weekly rain, P-03 frost dates)."""

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from fieldshift import predictions as p

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def _year(year: int, rain: float = 0.0, tmin: float = 5.0) -> dict:
    """Every day of a year with the same rain and Tmin."""
    d, out = date(year, 1, 1), {}
    while d.year == year:
        out[d.strftime("%Y%m%d")] = {"PRECTOTCORR": rain, "T2M_MIN": tmin, "T2M_MAX": 20.0}
        d += timedelta(days=1)
    return out


def _set(days: dict, day: str, **values) -> None:
    days[day].update(values)


# ------------------------------------------------------------------ helpers

def test_week_of_year_and_start():
    assert p.week_of_year(date(2005, 1, 1)) == 1
    assert p.week_of_year(date(2005, 1, 8)) == 2
    assert p.week_of_year(date(2005, 12, 31)) == 52  # day 365 folds into week 52
    assert p.week_of_year(date(2008, 12, 31)) == 52  # day 366 too
    assert p.week_start(1) == "01-01"
    assert p.week_start(2) == "01-08"


def test_leap_years_use_non_leap_day_of_year():
    assert p._doy(date(2008, 3, 1)) == p._doy(date(2005, 3, 1)) == 60


def test_rank_value_returns_observed_values_on_the_safe_side():
    assert p.rank_value([0, 32, 64], 50, upper=True) == 32
    assert p.rank_value([0, 32, 64], 90, upper=True) == 64  # rank 1.8 -> 2, never a blended 57.6
    assert p.rank_value([324, 335, 366], 10, upper=False) == 324  # rank 0.2 -> 0
    assert p.rank_value([], 50, upper=True) is None


def test_no_invented_date_next_to_frost_free_years():
    # 9 frost-free springs + 1 with last frost on day 100: linear interpolation would invent day ~90
    assert p.rank_value([0] * 9 + [100], 90, upper=True) == 100


# ------------------------------------------------------------------ P-01

def test_rain_weeks_probabilities():
    days = {**_year(2005), **_year(2006), **_year(2007)}
    _set(days, "20050103", PRECTOTCORR=2.0)  # week 1 rainy, total 2 mm
    _set(days, "20060105", PRECTOTCORR=12.0)  # week 1 rainy, total 12 mm (useful)
    weeks = p.rain_weeks(days)
    assert len(weeks) == 52
    w1 = weeks[0]
    assert w1["years"] == 3
    assert w1["prob_rain"] == 0.67  # 2 of 3 years
    assert w1["prob_useful_rain"] == 0.33  # 1 of 3 years with >= 10 mm
    assert w1["mean_rain_mm"] == pytest.approx((2 + 12 + 0) / 3, abs=0.05)
    assert weeks[10]["prob_rain"] == 0.0


def test_rain_weeks_skips_incomplete_week_and_ignores_drizzle():
    days = {**_year(2005, rain=0.5), **_year(2006, rain=0.5)}  # 0.5 mm/day: not a wet day
    _set(days, "20050110", PRECTOTCORR=None)  # 1 of 7 days missing in week 2 -> skipped
    weeks = p.rain_weeks(days)
    assert weeks[1]["years"] == 1
    assert weeks[0]["prob_rain"] == 0.0
    assert weeks[0]["mean_rain_mm"] == 3.5  # 7 x 0.5 mm


# ------------------------------------------------------------------ P-03

def test_frost_dates_percentiles():
    days = {**_year(2005), **_year(2006), **_year(2007)}
    _set(days, "20050210", T2M_MIN=-1.0)
    _set(days, "20050305", T2M_MIN=-0.5)  # last spring frost 2005: day 64
    _set(days, "20051120", T2M_MIN=-2.0)  # first autumn frost 2005: day 324
    _set(days, "20060201", T2M_MIN=-3.0)  # last spring frost 2006: day 32
    _set(days, "20061201", T2M_MIN=-1.0)  # first autumn frost 2006: day 335
    # 2007: no frost -> counts as day 0 in spring and day 366 in autumn
    f = p.frost_dates(days)
    assert f["spring"]["years"] == 3
    assert f["spring"]["years_with_frost"] == 2
    assert f["spring"]["probability"] == 0.67
    assert f["spring"]["last_frost_median"] == "02-01"  # day 32
    assert f["spring"]["last_frost_p90"] == "03-05"  # rank 1.8 -> 2 -> day 64 (observed, safe side)
    assert f["spring"]["years_by_p90"] == 3
    assert f["autumn"]["first_frost_median"] == "12-01"  # day 335
    assert f["autumn"]["first_frost_p10"] == "11-20"  # rank 0.2 -> 0 -> day 324
    assert f["autumn"]["years_from_p10"] == 3
    assert f["safe_days"] == 260  # 324 - 64


def test_frost_dates_without_any_frost():
    f = p.frost_dates({**_year(2005), **_year(2006)})
    assert f["spring"]["probability"] == 0.0
    assert f["spring"]["last_frost_p90"] is None
    assert f["autumn"]["first_frost_p10"] is None
    assert f["safe_days"] == 365


def test_frost_dates_skip_incomplete_half_year():
    days = _year(2005)
    for key in list(days):
        if key < "20050301":  # Jan-Feb missing: 59 of 181 days > 10 %
            days[key]["T2M_MIN"] = None
    f = p.frost_dates(days)
    assert f["spring"]["years"] == 0
    assert f["autumn"]["years"] == 1


# ------------------------------------------------------------------ real demo fields (sanity, not exact values)

@pytest.mark.parametrize("name", ["power_37.03_-4.64.json", "power_37.07_-4.87.json", "power_36.72_-4.67.json"])
def test_build_predictions_on_demo_fields(name):
    power = json.loads((SAMPLES / name).read_text(encoding="utf-8"))
    out = p.build_predictions(power)
    assert out["period"] == "2005-2025"
    weeks = out["rain_weeks"]
    assert len(weeks) == 52
    assert all(0 <= w["prob_rain"] <= 1 and 0 <= w["prob_useful_rain"] <= 1 for w in weeks)
    assert all(w["years"] >= 19 for w in weeks)
    summer = [w["mean_rain_mm"] for w in weeks if w["start"][:2] in ("07", "08")]
    winter = [w["mean_rain_mm"] for w in weeks if w["start"][:2] in ("11", "12")]
    assert max(summer) < sum(winter) / len(winter)  # Mediterranean: dry summer, wet late autumn
    assert 0 <= out["frost"]["spring"]["probability"] <= 1


def test_coastal_field_has_no_frost_and_inland_field_does():
    coast = json.loads((SAMPLES / "power_36.72_-4.67.json").read_text(encoding="utf-8"))
    inland = json.loads((SAMPLES / "power_37.07_-4.87.json").read_text(encoding="utf-8"))
    assert p.frost_dates(coast["days"])["spring"]["probability"] == 0.0
    assert p.frost_dates(inland["days"])["spring"]["probability"] > 0.5
