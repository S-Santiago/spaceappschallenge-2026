"""Tests for src/fieldshift/rotations.py (scoring rules in docs/indicators.md -> Scoring)."""

import pytest

from fieldshift import rotations as r

SHAPE_2_KEYS = {"id", "name", "years", "scores", "why", "evidence", "benefits", "gaps", "risks_to_review"}


def test_window_wraps_new_year(crops):
    assert r.window(crops["durum_wheat"]) == [11, 12, 1, 2, 3, 4, 5, 6]
    assert r.window(crops["fallow"]) == []


def test_rain_coverage(crops, profile):
    # chickpea Feb-Jun: 55+75+45+25+5 = 205 mm vs need (250+400)/2 = 325 mm
    assert r.rain_coverage(crops["chickpea"], profile) == pytest.approx(205 / 325)
    assert r.rain_coverage(crops["fallow"], profile) == 1.0


def test_drought_penalty_only_when_rain_fed(crops, profile):
    # maize Apr-Sep: 104 mm vs 700 mm need -> 15 % coverage, low drought tolerance
    assert any("drought" in reason for reason, _ in r.climate_penalties(crops["maize"], profile, irrigated=False))
    assert sum(p for _, p in r.climate_penalties(crops["maize"], profile, irrigated=False)) >= 30
    assert not any("drought" in reason for reason, _ in r.climate_penalties(crops["maize"], profile, irrigated=True))
    assert not r.suitable(crops["maize"], profile, irrigated=False)


def test_frost_penalty(crops, profile):
    # chickpea Feb-Jun has 1 frost day -> not > 1, no penalty; sunflower Mar-Aug has none either
    assert not any("frost" in reason for reason, _ in r.climate_penalties(crops["chickpea"], profile, False))
    profile["months"][1]["frost_days"] = 4  # February
    assert any("frost" in reason for reason, _ in r.climate_penalties(crops["chickpea"], profile, False))


def test_overall_uses_priority_weights():
    s = {"water": 100, "soil": 0, "income": 0, "risk": 0}
    assert r.overall(s, {}) == 25
    assert r.overall(s, {"water": 3, "soil": 1, "income": 0, "risk": 0}) == 75
    assert r.overall(s, dict.fromkeys(r.PRIORITIES, 0)) == 25  # all zero -> equal weights


def test_labels():
    assert [r.label(v) for v in (0, 33, 34, 66, 67, 100)] == ["poor", "poor", "neutral", "neutral", "good", "good"]


def test_monoculture_has_no_pest_break(crops, profile):
    s = r.score([crops["durum_wheat"]], None, profile, False, "flat")
    assert s["_parts"]["pest_break"] == 0
    s2 = r.score([crops["durum_wheat"], crops["chickpea"]], None, profile, False, "flat")
    assert s2["_parts"]["pest_break"] == 20
    assert s2["_parts"]["nitrogen"] == 25


def test_all_fallow_edge_case(crops, profile):
    s = r.score([crops["fallow"], crops["fallow"]], None, profile, False, "flat")
    assert s["water"] == 100 and s["income"] == 0 and s["risk"] == 100
    assert s["_parts"]["bare_months_per_year"] == 12
    assert s["_parts"]["erosion"] == 15  # fully exposed, flat slope factor 0.5


def test_steep_slope_lowers_soil_score(crops, profile):
    years = [crops["durum_wheat"], crops["sunflower"]]
    flat = r.score(years, None, profile, False, "flat")
    steep = r.score(years, None, profile, False, "steep")
    assert steep["soil"] < flat["soil"]


def test_cover_crop_reduces_bare_months(crops, profile):
    years = [crops["durum_wheat"], crops["sunflower"]]
    without = r.score(years, None, profile, False, "flat")
    with_cover = r.score(years, (0, crops["vetch_cover"]), profile, False, "flat")
    assert with_cover["_parts"]["bare_months_per_year"] < without["_parts"]["bare_months_per_year"]
    assert with_cover["_parts"]["erosion"] >= without["_parts"]["erosion"]
    assert with_cover["_parts"]["nitrogen"] == 15


def test_gap_between_harvest_and_next_sowing(crops):
    years = [crops["durum_wheat"], crops["sunflower"]]
    assert r.gap(years, 0) == [7, 8, 9, 10, 11, 12, 1, 2]  # wheat harvested Jun, sunflower sown Mar
    assert r.gap(years, 1) == [9, 10]  # sunflower harvested Aug, wheat sown Nov
    assert r.cover_fits(years, 0, crops["vetch_cover"])  # Oct-Feb
    assert not r.cover_fits(years, 1, crops["vetch_cover"])


def test_bare_months_whole_cycle(crops):
    years = [crops["durum_wheat"], crops["sunflower"]]
    assert len(r._bare_months(years, None)) == len(r.gap(years, 0)) + len(r.gap(years, 1))
    assert len(r._bare_months(years, (0, crops["vetch_cover"]))) == 10 - 5


def test_compare_returns_current_plus_three(crops, profile):
    result = r.compare(profile, ["durum_wheat", "durum_wheat", "sunflower"], crops,
                       priorities={"water": 2, "soil": 1, "income": 1, "risk": 1})
    assert result[0]["id"] == "current" and result[0]["years"] == ["durum_wheat", "durum_wheat", "sunflower"]
    assert len(result) == 4
    assert len({s["id"] for s in result}) == 4
    assert len({(tuple(s["years"]), str(s["cover_crop"])) for s in result}) == 4  # no duplicate rotations
    for s in result:
        assert SHAPE_2_KEYS <= set(s)
        assert set(s["scores"]) == {"water", "soil", "income", "risk", "overall"}
        assert all(0 <= v <= 100 for v in s["scores"].values())
        assert s["why"] and s["evidence"] and s["gaps"] and s["risks_to_review"]
    overalls = [s["scores"]["overall"] for s in result[1:]]
    assert overalls == sorted(overalls, reverse=True)


def test_rain_fed_never_proposes_unsuitable_crop(crops, profile):
    result = r.compare(profile, ["barley", "barley"], crops, irrigated=False)
    assert all("maize" not in s["years"] for s in result[1:])


def test_irrigation_allows_thirsty_crops(crops, profile):
    assert r.suitable(crops["maize"], profile, irrigated=True)


def test_invalid_rotation(crops, profile):
    with pytest.raises(ValueError):
        r.compare(profile, [], crops)
    with pytest.raises(ValueError):
        r.compare(profile, ["banana"], crops)
