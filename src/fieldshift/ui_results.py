"""Results view (issue #13): climate calendar, trends, strategy cards, sources.

The pure helpers at the top turn Shape 1 / Shape 2 into plain-English text and rows and can be
unit-tested without Streamlit. The ``render_*`` functions draw one section each. ``render_results``
draws them all and shows a helpful empty state if a section's data is missing, so the farmer never
sees ``None``, ``NaN`` or a traceback.

Shapes are defined in docs/work-plan.md; every field's meaning, unit and limits in docs/indicators.md.
"""

from __future__ import annotations

import calendar
import logging
import math
from collections.abc import Callable, Sequence
from typing import Any

import altair as alt
import streamlit as st

from fieldshift import ui_theme as t

log = logging.getLogger(__name__)

MONTH_NAMES = list(calendar.month_name)[1:]  # "January" … "December"
MONTH_ABBR = list(calendar.month_abbr)[1:]  # "Jan" … "Dec"

# Score levels: Low < 40 ≤ Medium < 70 ≤ High. Single source of truth for labels.
SCORE_LEVELS: tuple[tuple[int, str], ...] = ((70, "High"), (40, "Medium"), (0, "Low"))

# Score dimensions in display order: (key in Shape 2 "scores", icon, label).
# `risk`: assumed higher = safer (same direction as the "Low risk" priority) — to confirm in
# docs/indicators.md "Scoring" (issue #10/#11).
SCORE_DIMENSIONS: tuple[tuple[str, str, str], ...] = (
    ("water", "💧", "Water"),
    ("soil", "🌱", "Soil health"),
    ("income", "💶", "Income"),
    ("risk", "🛡️", "Risk safety (higher = safer)"),
)
PRIORITY_LABELS = {"water": "💧 water", "soil": "🌱 soil", "income": "💶 income", "risk": "🛡️ low risk"}

# Crop icons by crop id (fallback 🌱). Family-level icons keep the sequence readable at a glance.
CROP_ICONS = {
    "durum_wheat": "🌾",
    "soft_wheat": "🌾",
    "barley": "🌾",
    "oats": "🌾",
    "chickpea": "🫘",
    "lentil": "🫘",
    "faba_bean": "🫘",
    "vetch": "🫘",
    "sunflower": "🌻",
    "rapeseed": "🌼",
    "fallow": "🟫",
}

# Thresholds used only to phrase the key sentences (not new indicators: they summarise Shape 1).
HEAT_MONTH_MIN_DAYS = 1.0  # a month counts as "hot" if it has ≥ 1 very hot day on average
FROST_RARE_MAX_DAYS_PER_YEAR = 2.0  # "frost is rare" if < 2 frost days a year on average

# Limits from docs/indicators.md → "Limits to show in the UI".
DATA_LIMITS = (
    "Climate values describe the **area around your field (~50 km)**, not the plot itself. "
    "Valleys and slopes can be different.",
    "Soil wetness is a **model estimate**, not a measurement.",
    "Greenness (NDVI) covers **only 2024–2025**, and one 250 m satellite pixel can mix several plots.",
    "A 10-year vs 10-year comparison shows a change, not a proven long-term climate trend.",
)
SUPPORT_NOTE = "FarmLens supports, and does not replace, the judgment of farmers and local advisers."


# ---------------------------------------------------------------- pure helpers


def _num(value: Any) -> float | None:
    """A finite float, or None for missing / NaN / non-numeric values."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def months_by_number(profile: dict[str, Any] | None) -> dict[int, dict[str, Any]]:
    """Shape 1 months keyed by month number 1–12 (bad entries skipped)."""
    months = (profile or {}).get("months") or []
    out = {}
    for m in months:
        if isinstance(m, dict) and isinstance(m.get("month"), int) and 1 <= m["month"] <= 12:
            out[m["month"]] = m
    return out


def month_runs(flags: Sequence[bool]) -> list[tuple[int, int]]:
    """Consecutive True months as (start, end) month numbers 1–12, wrapping Dec → Jan.

    >>> month_runs([True, True, False, False, False, False, False, False, False, True, True, True])
    [(10, 2)]
    """
    flags = list(flags)
    if len(flags) != 12 or not any(flags):
        return []
    if all(flags):
        return [(1, 12)]
    # Start scanning just after a False month so a run never gets split at the year boundary.
    start = next(i for i in range(12) if not flags[i]) + 1
    runs: list[tuple[int, int]] = []
    run_start = None
    for k in range(12):
        i = (start + k) % 12
        if flags[i] and run_start is None:
            run_start = i
        if not flags[i] and run_start is not None:
            runs.append((run_start + 1, (i - 1) % 12 + 1))
            run_start = None
    if run_start is not None:
        runs.append((run_start + 1, (start - 1) % 12 + 1))
    return runs


def format_runs(runs: Sequence[tuple[int, int]]) -> str:
    """[(10, 3), (6, 6)] → "October–March and June"."""
    parts = [MONTH_NAMES[a - 1] if a == b else f"{MONTH_NAMES[a - 1]}–{MONTH_NAMES[b - 1]}" for a, b in runs]
    return " and ".join(parts)


def _series(months: dict[int, dict[str, Any]], key: str) -> list[float] | None:
    """12 values for one field, or None if any month is missing it."""
    values = [_num(months.get(m, {}).get(key)) for m in range(1, 13)]
    return None if any(v is None for v in values) else values  # type: ignore[return-value]


def key_facts(profile: dict[str, Any] | None) -> list[tuple[str, str]]:
    """Plain-English key sentences (icon, text) derived from Shape 1. Skips any it cannot compute."""
    months = months_by_number(profile)
    facts: list[tuple[str, str]] = []

    rain = _series(months, "rain_mm")
    if rain and sum(rain) > 0:
        avg = sum(rain) / 12
        wet = [r >= avg for r in rain]
        share = sum(r for r, w in zip(rain, wet) if w) / sum(rain)
        facts.append(("🌧️", f"Most rain falls {format_runs(month_runs(wet))} ({share:.0%} of the year's rain)."))

    balance = _series(months, "water_balance_mm")
    if balance:
        runs = month_runs([b < 0 for b in balance])
        if runs:
            worst = min(range(12), key=lambda i: balance[i])
            facts.append(
                (
                    "☀️",
                    f"Water deficit {format_runs(runs)}: rain is less than the crop's water need. "
                    f"Worst in {MONTH_NAMES[worst]} ({balance[worst]:.0f} mm).".replace("-", "−"),
                )
            )
        else:
            facts.append(("💧", "Rain covers the crop's water need in every month."))

    bare = [months.get(m, {}).get("likely_bare") for m in range(1, 13)]
    if all(isinstance(b, bool) for b in bare):
        runs = month_runs(bare)  # type: ignore[arg-type]
        if runs:
            facts.append(("🟫", f"Field likely bare {format_runs(runs)} (satellite greenness, 2024–2025)."))
        else:
            facts.append(("🌿", "The field looks covered by plants all year (satellite greenness, 2024–2025)."))

    heat = _series(months, "heat_days")
    if heat and sum(heat) >= HEAT_MONTH_MIN_DAYS:
        runs = month_runs([h >= HEAT_MONTH_MIN_DAYS for h in heat])
        when = f", mainly {format_runs(runs)}" if runs else ""
        facts.append(("🔥", f"About {sum(heat):.0f} very hot days (over 35 °C) a year{when}."))

    frost = _series(months, "frost_days")
    if frost is not None:
        total = sum(frost)
        if total < FROST_RARE_MAX_DAYS_PER_YEAR:
            facts.append(("❄️", f"Frost is rare (about {total:.0f} day{'s' if round(total) != 1 else ''} a year)."))
        else:
            runs = month_runs([f >= 1 for f in frost])
            when = f", mainly {format_runs(runs)}" if runs else ""
            facts.append(("❄️", f"About {total:.0f} frost days a year{when}."))
    return facts


def calendar_rows(profile: dict[str, Any] | None) -> list[dict[str, str]]:
    """One row per month with display strings (units in the headers). Missing values → "—"."""
    months = months_by_number(profile)

    def fmt(value: Any, spec: str) -> str:
        v = _num(value)
        return "—" if v is None else format(v, spec)

    rows = []
    for m in range(1, 13):
        d = months.get(m, {})
        bal = _num(d.get("water_balance_mm"))
        if bal is None:
            balance = "—"
        elif bal < 0:
            balance = f"🔻 {bal:.0f}".replace("-", "−")
        else:
            balance = f"💧 +{bal:.0f}"
        bare = d.get("likely_bare")
        field = "🟫 Bare" if bare is True else "🌱 Crop" if bare is False else "—"
        rows.append(
            {
                "month": MONTH_ABBR[m - 1],
                "rain": fmt(d.get("rain_mm"), ".0f"),
                "et0": fmt(d.get("et0_mm"), ".0f"),
                "balance": balance,
                "frost": fmt(d.get("frost_days"), ".1f"),
                "heat": fmt(d.get("heat_days"), ".1f"),
                "field": field,
            }
        )
    return rows


def score_level(score: float) -> str:
    """0–100 score → "Low" / "Medium" / "High" (thresholds in SCORE_LEVELS)."""
    return next(label for limit, label in SCORE_LEVELS if score >= limit)


def order_strategies(strategies: Sequence[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Current rotation first, then alternatives by overall score (highest first)."""
    items = [s for s in (strategies or []) if isinstance(s, dict)]
    current = [s for s in items if s.get("id") == "current"]
    others = [s for s in items if s.get("id") != "current"]
    others.sort(key=lambda s: _num((s.get("scores") or {}).get("overall")) or 0, reverse=True)
    return current + others


def priority_line(weights: dict[str, float] | None) -> str:
    """How the farmer's priorities weight the overall score, e.g. "💧 water 40% · 🌱 soil 20% · …"."""
    weights = weights or {}
    parts = [
        f"{PRIORITY_LABELS[k]} {weights[k]:.0%}"
        for k in sorted(PRIORITY_LABELS, key=lambda k: -(weights.get(k) or 0))
        if _num(weights.get(k)) is not None
    ]
    return " · ".join(parts)


def crop_sequence(years: Sequence[str] | None, crop_names: dict[str, str]) -> str:
    """["durum_wheat", "chickpea"] → "**Year 1** 🌾 Durum wheat → **Year 2** 🫘 Chickpea"."""
    return " → ".join(
        f"**Year {i}** {CROP_ICONS.get(c, '🌱')} {crop_names.get(c, str(c).replace('_', ' ').capitalize())}"
        for i, c in enumerate(years or [], start=1)
    )


def overall_phrase(score: float) -> str:
    """66 → "out of 100 · medium fit for your priorities"."""
    return f"out of 100 · {score_level(score).lower()} fit for your priorities"


# ---------------------------------------------------------------- HTML builders (pure)


def score_list_html(scores: dict[str, Any] | None) -> str:
    """The four dimension scores as a definition list with one bar each. Missing → "not available yet"."""
    scores = scores or {}
    rows = []
    for key, icon, label in SCORE_DIMENSIONS:
        v = t._clamp_score(scores.get(key))
        if v is None:
            rows.append(f"<div class='fl-score'><dt>{icon} {label}</dt><dd>not available yet</dd></div>")
            continue
        rows.append(
            f"<div class='fl-score'><dt>{icon} {label}</dt>"
            f"<dd>{v:.0f}/100 · {score_level(v)}</dd>{t.bar(v, 'dd')}</div>"
        )
    return f"<dl class='fl-scores'>{''.join(rows)}</dl>"


def overall_html(scores: dict[str, Any] | None) -> str:
    v = t._clamp_score((scores or {}).get("overall"))
    if v is None:
        return "<p class='fl-card-sub'>Overall fit not available yet.</p>"
    return f"<p class='fl-overall'><b>{v:.0f}</b><span>{overall_phrase(v)}</span></p>"


def compare_html(ordered: Sequence[dict[str, Any]], crop_names: dict[str, str], best_id: Any) -> str:
    """One row per option: name, crops, overall score and bar. Same order as the cards below."""
    rows = []
    for s in ordered:
        is_current = s.get("id") == "current"
        name = "Your current rotation" if is_current else (s.get("name") or "Rotation option")
        crops = " → ".join(t.crop_label(c, crop_names) for c in s.get("years") or [])
        note = "<strong> · best fit</strong>" if s.get("id") == best_id else ""
        v = t._clamp_score((s.get("scores") or {}).get("overall"))
        score = f"{v:.0f}<small> /100</small>" if v is not None else "<small>not available</small>"
        rows.append(
            f"<li><span class='n'>{t.e(name)}<small>{t.e(crops)}{note}</small></span>"
            f"<span class='s'>{score}</span>{t.bar(v) if v is not None else ''}</li>"
        )
    return f"<ol class='fl-compare' aria-label='Rotation options by overall fit'>{''.join(rows)}</ol>"


_BARE_ROW = " class='is-bare'"  # shaded row: bare-field months (text says "Bare" too)


def calendar_table_html(profile: dict[str, Any] | None) -> str:
    head = (
        "<tr><th scope='col'>Month</th><th scope='col'>Rain<br>mm</th><th scope='col'>Water need<br>mm</th>"
        "<th scope='col'>Balance<br>mm</th><th scope='col'>Frost<br>days</th><th scope='col'>Heat<br>days</th>"
        "<th scope='col'>Field</th></tr>"
    )
    body = "".join(
        f"<tr{_BARE_ROW if 'Bare' in r['field'] else ''}><th scope='row'>{r['month']}</th>"
        f"<td>{r['rain']}</td><td>{r['et0']}</td><td>{r['balance']}</td>"
        f"<td>{r['frost']}</td><td>{r['heat']}</td><td>{r['field']}</td></tr>"
        for r in calendar_rows(profile)
    )
    # The table scrolls inside its own region (never the page) if it ever gets wider than the phone;
    # tabindex lets keyboard users scroll it; the caption names the table for screen readers.
    return (
        "<div class='fl-scroll' role='region' aria-label='Month-by-month climate table' tabindex='0'>"
        "<table class='fl-cal'><caption class='fl-sr'>Average month, 2005–2025, for the area around your field"
        f"</caption><thead>{head}</thead><tbody>{body}</tbody></table></div>"
    )


def trend_items(trends: dict[str, Any] | None) -> list[tuple[str, str, str]]:
    """(figure, label, sentence) for each trend that has a value. Minus signs are typographic (−)."""
    trends = trends or {}
    out = []
    rain = _num(trends.get("rain_change_pct"))
    if rain is not None:
        if rain < 0:
            text = f"It rains about {abs(rain):.0f}% less than in 2005–2014."
        elif rain > 0:
            text = f"It rains about {rain:.0f}% more than in 2005–2014."
        else:
            text = "It rains about the same as in 2005–2014."
        out.append((f"{rain:+.0f}%".replace("-", "−"), "🌧️ Rain per year", text))
    heat = _num(trends.get("heat_days_change"))
    if heat is not None:
        if heat > 0:
            text = f"About {heat:.0f} more very hot days a year than in 2005–2014."
        elif heat < 0:
            text = f"About {abs(heat):.0f} fewer very hot days a year than in 2005–2014."
        else:
            text = "About the same number of very hot days as in 2005–2014."
        out.append((f"{heat:+.1f}".replace("-", "−"), "🔥 Very hot days a year (over 35 °C)", text))
    return out


# ---------------------------------------------------------------- sections


def _empty(message: str) -> None:
    st.info(message, icon=":material/info:")


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def render_key_facts(profile: dict[str, Any]) -> None:
    facts = key_facts(profile)
    if not facts:
        _empty("The climate summary for this field is not available yet. Try **Analyze my field** again later.")
        return
    st.markdown("\n".join(f"- {icon} {text}" for icon, text in facts))


def render_calendar_table(profile: dict[str, Any]) -> None:
    if not months_by_number(profile):
        _empty("The month-by-month table is not available for this field yet.")
        return
    _html(calendar_table_html(profile))
    st.caption(
        "Average month, 2005–2025. **Water need** = water the air takes from a crop (ET0). "
        "**Balance** = rain − water need: 🔻 deficit (too little rain), 💧 spare water. "
        "**Heat** = days over 35 °C. **Field** = 🟫 bare (shaded row) or 🌱 crop, from satellite greenness 2024–2025."
    )


def render_rain_chart(profile: dict[str, Any]) -> None:
    months = months_by_number(profile)
    rain, et0 = _series(months, "rain_mm"), _series(months, "et0_mm")
    if not rain or not et0:
        _empty("The rain chart is not available for this field yet.")
        return
    rows = [{"Month": MONTH_ABBR[i], "order": i, "Rain": rain[i], "Water need (ET0)": et0[i]} for i in range(12)]
    x = alt.X("Month:N", sort=MONTH_ABBR, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=14))
    color = alt.Color(
        "series:N",
        scale=alt.Scale(domain=["Rain", "Water need (ET0)"], range=["#1f6fb2", "#b3541e"]),
        legend=alt.Legend(title=None, orient="top", labelFontSize=15, symbolSize=150),
    )
    base = alt.Chart(alt.Data(values=rows))
    bars = base.transform_fold(["Rain"], as_=["series", "mm"]).mark_bar(opacity=0.85, cornerRadiusEnd=2).encode(
        x=x,
        y=alt.Y("mm:Q", title="mm per month"),
        color=color,
        tooltip=["Month:N", alt.Tooltip("mm:Q", title="Rain (mm)")],
    )
    line = base.transform_fold(["Water need (ET0)"], as_=["series", "mm"]).mark_line(
        point=alt.OverlayMarkDef(shape="diamond", size=60), strokeWidth=3, strokeDash=[6, 3]
    ).encode(x=x, y="mm:Q", color=color, tooltip=["Month:N", alt.Tooltip("mm:Q", title="Water need (mm)")])
    chart = (
        (bars + line)
        .properties(height=240)
        .configure(font="system-ui, -apple-system, Segoe UI, Roboto, sans-serif")
        .configure_axis(titleFontSize=14, labelFontSize=14, grid=True, gridOpacity=0.25, domain=False)
        .configure_view(stroke=None)
    )
    st.altair_chart(chart, width="stretch")
    st.caption(
        "Blue bars = rain. Dashed brown line with ◆ = water need. "
        "Where the line is above the bars, the field is short of water."
    )


def render_trends(profile: dict[str, Any]) -> None:
    items = trend_items((profile or {}).get("trends"))
    if not items:
        _empty("The comparison with earlier years is not available for this field yet.")
        return
    _html(section_heading_small("Then and now: 2016–2025 compared with 2005–2014"))
    _html(
        "<ul class='fl-trend'>"
        + "".join(
            f"<li><b>{t.e(f)}</b><span class='l'>{t.e(lbl)}</span><span class='d'>{t.e(d)}</span></li>"
            for f, lbl, d in items
        )
        + "</ul>"
    )
    st.caption(DATA_LIMITS[3])


def section_heading_small(title: str) -> str:
    return f"<h4 class='fl-sub'>{t.e(title)}</h4>"


def _render_list(items: Any, empty: str) -> None:
    items = [str(i) for i in (items or []) if i]
    st.markdown("\n".join(f"- {i}" for i in items) if items else f"_{empty}_")


def render_strategy_card(
    s: dict[str, Any], crop_names: dict[str, str], *, is_baseline: bool, is_best: bool
) -> None:
    scores = s.get("scores") or {}
    with st.container(border=True):
        title = "Your current rotation" if is_baseline else (s.get("name") or "Rotation option")
        sub = (
            "What you grow today. The other options are compared with it."
            if is_baseline
            else ("A suggestion to discuss with your adviser, not an order." if is_best else "")
        )
        _html(
            t.tags(best=is_best)
            + f"<h4 class='fl-card-title'>{t.e(title)}</h4>"
            + (f"<p class='fl-card-sub'>{t.e(sub)}</p>" if sub else "")
        )
        strip = t.rotation_strip(s.get("years"), crop_names, label=f"Crop sequence: {title}")
        if strip:
            _html(strip)
        else:
            st.markdown("_Crop sequence not available yet._")
        _html(overall_html(scores) + score_list_html(scores))

        if s.get("why"):
            st.markdown(f"**Why:** {s['why']}")
        st.markdown(":material/warning: **Risks to review locally**")
        _render_list(s.get("risks_to_review"), "No risks listed yet — ask a local adviser.")

        with st.expander("Evidence", icon=":material/search:"):
            _render_list(s.get("evidence"), "No evidence listed yet.")
        with st.expander("Benefits", icon=":material/check_circle:"):
            _render_list(s.get("benefits"), "No benefits listed yet.")
        with st.expander("What we don't know yet", icon=":material/help:"):
            _render_list(s.get("gaps"), "No information gaps listed.")


def render_strategies(strategies: list[dict[str, Any]], crop_names: dict[str, str], weights: dict[str, float]) -> None:
    ordered = order_strategies(strategies)
    if not ordered:
        _empty("No rotation options could be built for this field yet. Check your answers and try again.")
        return
    best_id = next((s.get("id") for s in ordered if s.get("id") != "current"), None)
    line = priority_line(weights)
    if line:
        st.caption(f"**Overall fit** mixes four scores with your priorities: {line}.")
    _html(compare_html(ordered, crop_names, best_id))
    all_crops = [c for s in ordered for c in (s.get("years") or [])]
    _html(t.family_key(all_crops))
    st.caption("Scores out of 100: Low under 40, Medium 40–69, High 70 or more. Open each option for the details.")
    for s in ordered:
        render_strategy_card(s, crop_names, is_baseline=s.get("id") == "current", is_best=s.get("id") == best_id)


def render_sources(profile: dict[str, Any], is_mock: bool) -> None:
    sources = [str(x) for x in (profile or {}).get("sources") or [] if x]
    _html("<div class='fl-foot'></div>")
    st.markdown("**Sources and limits**")
    if sources:
        prefix = "Planned data sources (the mock values above do not come from them yet)" if is_mock else "Data sources"
        st.markdown(f"{prefix}: " + ", ".join(sources) + ".")
    else:
        st.markdown("_Data sources not available._")
    st.markdown("\n".join(f"- {limit}" for limit in DATA_LIMITS[:3]))
    st.markdown(f":material/handshake: **{SUPPORT_NOTE}**")


# ---------------------------------------------------------------- page


def _section(title: str, draw: Callable[[], None], fallback: str) -> None:
    """Draw one section; on any error show a friendly message instead of a traceback."""
    if title:
        _html(t.section_heading(title))
    try:
        draw()
    except Exception:  # noqa: BLE001 — never show a traceback to a farmer
        log.exception("Results section failed: %s", title)
        _empty(fallback)


def render_results(results: dict[str, Any], crop_names: dict[str, str], *, is_mock: bool) -> None:
    """Draw the full results view from ``{"inputs", "profile", "strategies"}``."""
    profile = results.get("profile") or {}
    strategies = results.get("strategies") or []
    weights = (results.get("inputs") or {}).get("weights") or {}

    if is_mock:
        st.warning(
            "**Mock data** — example values for testing the app, not real results for your field.",
            icon=":material/science:",
        )

    oops = "This part could not be shown. The rest of the results are still valid."
    _section("Rotation options", lambda: render_strategies(strategies, crop_names, weights), oops)
    _section("Your field through the year", lambda: render_key_facts(profile), oops)
    _section("", lambda: render_rain_chart(profile), oops)
    _section("", lambda: render_calendar_table(profile), oops)
    _section("", lambda: render_trends(profile), oops)
    _section("", lambda: render_sources(profile, is_mock), oops)
