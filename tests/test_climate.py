"""Hand-checkable tests for src/fieldshift/climate.py (indicators I-01..I-11)."""

from datetime import date, timedelta

import pytest

from fieldshift import climate


def _days(year: int, month: int, values: dict, n: int | None = None) -> dict:
    """Every day of a month (or the first n) with the same values."""
    d, out = date(year, month, 1), {}
    while d.month == month and (n is None or len(out) < n):
        out[d.strftime("%Y%m%d")] = dict(values)
        d += timedelta(days=1)
    return out


BASE = {"T2M_MAX": 20.0, "T2M_MIN": 10.0, "PRECTOTCORR": 1.0, "GWETROOT": 0.5}


def test_ra_matches_fao56_example_8():
    # FAO-56 example 8: 20 deg S, 3 September -> Ra = 32.2 MJ m-2 day-1
    assert climate.extraterrestrial_radiation_mm(-20, 246) / climate.MJ_TO_MM == pytest.approx(32.2, abs=0.1)


def test_hargreaves_formula():
    # 0.0023 * (15 + 17.8) * sqrt(10) * 10
    assert climate.hargreaves_et0(20, 10, 10) == pytest.approx(0.0023 * 32.8 * 10**0.5 * 10)


def test_ra_polar_night_is_zero_not_error():
    assert climate.extraterrestrial_radiation_mm(80, 355) == pytest.approx(0, abs=1e-6)


def test_counts_and_sums_for_one_month():
    days = _days(2010, 1, BASE)  # 31 days
    days["20100101"].update(T2M_MIN=-2.0)
    days["20100102"].update(T2M_MIN=-0.1)
    days["20100103"].update(T2M_MIN=0.0)  # not frost: strictly below 0
    days["20100104"].update(T2M_MAX=36.0)
    days["20100105"].update(T2M_MAX=35.0)  # not heat: strictly above 35
    days["20100106"].update(PRECTOTCORR=30.0)  # heavy: >= 30
    s = climate.month_year_stats(days, 37.0)[(2010, 1)]
    assert s["frost_days"] == 2
    assert s["heat_days"] == 1
    assert s["heavy_rain_days"] == 1
    assert s["rain_mm"] == pytest.approx(30 * 1 + 30)
    assert s["soil_wetness"] == pytest.approx(0.5)


def test_month_with_too_many_missing_days_is_skipped():
    days = _days(2010, 1, BASE)
    for k in list(days)[:4]:  # 4/31 = 13 % missing > 10 %
        days[k]["PRECTOTCORR"] = None
    s = climate.month_year_stats(days, 37.0)[(2010, 1)]
    assert s["rain_mm"] is None and s["heavy_rain_days"] is None
    assert s["frost_days"] == 0  # temperature still complete


def test_few_missing_days_are_rescaled_to_full_month():
    days = _days(2010, 1, BASE)
    days["20100101"]["PRECTOTCORR"] = None  # 1/31 missing
    s = climate.month_year_stats(days, 37.0)[(2010, 1)]
    assert s["rain_mm"] == pytest.approx(31.0)


def test_monthly_mean_and_water_balance():
    days = {**_days(2010, 3, BASE), **_days(2011, 3, {**BASE, "PRECTOTCORR": 3.0})}
    months = climate.monthly_climate(climate.month_year_stats(days, 37.0))
    march = months[2]
    assert march["rain_mm"] == pytest.approx((31 + 93) / 2)
    assert march["water_balance_mm"] == pytest.approx(march["rain_mm"] - march["et0_mm"])
    assert months[0]["rain_mm"] is None  # no January data at all


def test_ndvi_and_bare_flag():
    points = [{"date": "2024-07-03", "ndvi": 0.1}, {"date": "2025-07-12", "ndvi": 0.2},
              {"date": "2024-03-21", "ndvi": 0.6}]
    ndvi = climate.monthly_ndvi(points)
    assert ndvi[7] == pytest.approx(0.15) and climate.likely_bare(ndvi[7]) is True
    assert climate.likely_bare(ndvi[3]) is False
    assert climate.likely_bare(None) is None


def _year(year: int, values: dict) -> dict:
    out = {}
    for m in range(1, 13):
        out.update(_days(year, m, values))
    return out


def test_trends_compare_decades():
    days = {}
    for y in range(2005, 2015):
        days.update(_year(y, {**BASE, "PRECTOTCORR": 2.0}))
    for y in range(2016, 2026):
        days.update(_year(y, {**BASE, "PRECTOTCORR": 1.5, "T2M_MAX": 36.0}))
    t = climate.trends(climate.month_year_stats(days, 37.0))
    assert t["rain_change_pct"] == pytest.approx(-25.0)
    assert t["heat_days_change"] == pytest.approx(365.3)  # 3 leap years (2016, 2020, 2024) in 10


def test_build_profile_shape_1_without_modis():
    days = _year(2010, BASE)
    power = {"meta": {"period": "2005-2025", "elevation_m": 144}, "days": days}
    p = climate.build_profile(36.72, -4.42, power, None)
    assert set(p) >= {"location", "months", "trends", "sources"}
    assert len(p["months"]) == 12
    assert set(p["months"][0]) == {"month", "rain_mm", "et0_mm", "water_balance_mm", "soil_wetness", "frost_days",
                                   "heat_days", "heavy_rain_days", "ndvi", "likely_bare"}
    assert p["months"][0]["ndvi"] is None and p["months"][0]["likely_bare"] is None
    assert p["trends"]["rain_change_pct"] is None  # no decades available
    assert len(p["sources"]) == 1
    assert p["limits"] == climate.LIMITS
