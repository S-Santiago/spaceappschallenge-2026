"""Tests for the design-system helpers (fieldshift.ui_theme) and the new HTML builders of the results view."""

from __future__ import annotations

import json
from pathlib import Path

from fieldshift import ui_results as ui
from fieldshift import ui_theme as t

PROFILE = json.loads((Path(__file__).resolve().parents[1] / "data/samples/mock_climate_profile.json").read_text())
NAMES = {"durum_wheat": "Durum wheat", "chickpea": "Chickpea", "sunflower": "Sunflower"}


def test_theme_tokens_have_the_same_keys_in_both_themes():
    assert set(t.TOKENS["light"]) == set(t.TOKENS["dark"])


def test_theme_css_follows_known_theme_or_falls_back_to_system():
    assert "#121510" in t.theme_vars_css("dark") and "prefers-color-scheme" not in t.theme_vars_css("dark")
    fallback = t.theme_vars_css(None)
    assert "#FAFAF7" in fallback and "prefers-color-scheme: dark" in fallback


def test_format_latlon_uses_hemispheres():
    assert t.format_latlon(36.72, -4.42) == "36.72° N, 4.42° W"
    assert t.format_latlon(-1.5, 3) == "1.50° S, 3.00° E"


def test_rotation_strip_lists_every_year_with_its_name():
    strip = t.rotation_strip(["durum_wheat", "chickpea", "mystery_crop"], NAMES)
    assert strip.startswith("<ol class='fl-strip' style='--n:3'")
    assert "Year 1</span><span class='c'>Durum wheat" in strip
    assert "Mystery crop" in strip  # unknown crop still readable
    assert t.FAMILY_COLORS["legume"] in strip and t.FAMILY_COLORS["other"] in strip
    assert t.rotation_strip([], NAMES) == ""


def test_html_builders_escape_data():
    strip = t.rotation_strip(["<b>x</b>"], {"<b>x</b>": "<script>alert(1)</script>"})
    assert "<script>" not in strip and "&lt;script&gt;" in strip
    html = ui.compare_html([{"id": "a", "name": "<img src=x>", "years": [], "scores": {}}], NAMES, None)
    assert "<img" not in html


def test_family_key_lists_only_families_shown():
    key = t.family_key(["durum_wheat", "barley", "chickpea"])
    assert "Cereal" in key and "Legume" in key and "Oilseed" not in key
    assert t.family_key([]) == ""


def test_score_list_shows_numbers_levels_and_missing_values():
    html = ui.score_list_html({"water": 80, "soil": float("nan"), "income": 120, "risk": None})
    assert "80/100 · High" in html
    assert "100/100 · High" in html  # clamped
    assert html.count("not available yet") == 2
    assert "nan" not in html.lower().replace("not available", "")


def test_overall_and_compare_rows():
    assert "medium fit" in ui.overall_html({"overall": 57})
    assert "not available" in ui.overall_html({})
    ordered = ui.order_strategies(
        [
            {"id": "b", "name": "Legume break", "years": ["durum_wheat", "chickpea"], "scores": {"overall": 64}},
            {"id": "current", "years": ["sunflower"], "scores": {"overall": 57}},
        ]
    )
    html = ui.compare_html(ordered, NAMES, "b")
    assert html.index("Your current rotation") < html.index("Legume break")
    assert "Durum wheat → Chickpea" in html and "best fit" in html


def test_calendar_table_marks_bare_rows_with_class_and_word():
    html = ui.calendar_table_html(PROFILE)
    assert html.count("class='is-bare'") == 4  # July–October in the mock
    assert html.count("Bare") == 4


def test_trend_items_use_plain_words_and_typographic_minus():
    items = ui.trend_items({"rain_change_pct": -8, "heat_days_change": 3.1})
    assert items[0][0] == "−8%" and "8% less" in items[0][2]
    assert items[1][0] == "+3.1" and "3 more very hot days" in items[1][2]
    assert ui.trend_items(None) == []
