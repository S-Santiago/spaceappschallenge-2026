"""Tests for the pure helpers of the results view (issue #13)."""

from __future__ import annotations

import json
from pathlib import Path

from fieldshift import ui_results as ui

PROFILE = json.loads((Path(__file__).resolve().parents[1] / "data/samples/mock_climate_profile.json").read_text())


def test_month_runs_wraps_year_boundary():
    flags = [m in (10, 11, 12, 1, 2, 3) for m in range(1, 13)]
    assert ui.month_runs(flags) == [(10, 3)]
    assert ui.format_runs(ui.month_runs(flags)) == "October–March"


def test_month_runs_edge_cases():
    assert ui.month_runs([False] * 12) == []
    assert ui.month_runs([True] * 12) == [(1, 12)]
    assert ui.month_runs([m in (2, 7, 8) for m in range(1, 13)]) == [(2, 2), (7, 8)]
    assert ui.month_runs([True] * 3) == []  # wrong length → nothing, no crash


def test_key_facts_from_mock_profile():
    text = " ".join(t for _, t in ui.key_facts(PROFILE))
    assert "Most rain falls October–March" in text
    assert "Water deficit February–October" in text
    assert "Field likely bare July–October" in text
    assert "mainly June–August" in text
    assert "Frost is rare" in text


def test_key_facts_and_rows_survive_missing_data():
    assert ui.key_facts(None) == []
    assert ui.key_facts({"months": [{"month": 1, "rain_mm": None}]}) == []
    rows = ui.calendar_rows({"months": [{"month": 1, "rain_mm": float("nan"), "likely_bare": None}]})
    assert len(rows) == 12
    assert rows[0]["rain"] == "—" and rows[0]["field"] == "—"
    assert all("None" not in v and "nan" not in v for r in rows for v in r.values())


def test_calendar_balance_has_word_or_icon_not_only_color():
    rows = ui.calendar_rows(PROFILE)
    assert rows[0]["balance"] == "💧 +20"
    assert rows[6]["balance"] == "🔻 −179"
    assert rows[6]["field"] == "🟫 Bare" and rows[0]["field"] == "🌱 Crop"


def test_score_level_thresholds():
    assert [ui.score_level(v) for v in (0, 39, 40, 69, 70, 100)] == ["Low", "Low", "Medium", "Medium", "High", "High"]


def test_order_strategies_current_first_then_by_overall():
    strategies = [
        {"id": "a", "scores": {"overall": 60}},
        {"id": "current", "scores": {"overall": 90}},
        {"id": "b", "scores": {"overall": 70}},
        {"id": "c", "scores": {}},
    ]
    assert [s["id"] for s in ui.order_strategies(strategies)] == ["current", "b", "a", "c"]
    assert ui.order_strategies(None) == []


def test_priority_line_sorted_by_weight():
    line = ui.priority_line({"water": 0.5, "soil": 0.25, "income": 0.25, "risk": 0.0})
    assert line.startswith("💧 water 50%")
    assert line.endswith("🛡️ low risk 0%")


def test_crop_sequence_unknown_crop_is_readable():
    seq = ui.crop_sequence(["durum_wheat", "mystery_crop"], {"durum_wheat": "Durum wheat"})
    assert seq == "**Year 1** 🌾 Durum wheat → **Year 2** 🌱 Mystery crop"
