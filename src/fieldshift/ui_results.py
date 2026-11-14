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


# ---------------------------------------------------------------- sections


def _empty(message: str) -> None:
    st.info(f"ℹ️ {message}")


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
    head = (
        "<tr><th>Month</th><th>Rain<br>mm</th><th>Water need<br>mm</th><th>Balance<br>mm</th>"
        "<th>Frost<br>days</th><th>Heat<br>days</th><th>Field</th></tr>"
    )
    body = "".join(
        f"<tr><th scope='row'>{r['month']}</th><td>{r['rain']}</td><td>{r['et0']}</td><td>{r['balance']}</td>"
        f"<td>{r['frost']}</td><td>{r['heat']}</td><td>{r['field']}</td></tr>"
        for r in calendar_rows(profile)
    )
    # The table scrolls inside its own region (never the page) if it ever gets wider than the phone;
    # tabindex lets keyboard users scroll it; the caption names the table for screen readers.
    st.markdown(
        "<div class='fl-scroll' role='region' aria-label='Month-by-month climate table' tabindex='0'>"
        "<table class='fl-cal'><caption class='fl-sr'>Average month, 2005–2025, for the area around your field"
        f"</caption><thead>{head}</thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Average month, 2005–2025. **Water need** = water the air takes from a crop (ET0). "
        "**Balance** = rain − water need: 🔻 deficit (too little rain) · 💧 spare water. "
        "**Heat** = days over 35 °C. **Field** = 🟫 bare or 🌱 crop, from satellite greenness 2024–2025."
    )


def render_rain_chart(profile: dict[str, Any]) -> None:
    months = months_by_number(profile)
    rain, et0 = _series(months, "rain_mm"), _series(months, "et0_mm")
    if not rain or not et0:
        _empty("The rain chart is not available for this field yet.")
        return
    rows = [{"Month": MONTH_ABBR[i], "order": i, "Rain": rain[i], "Water need (ET0)": et0[i]} for i in range(12)]
    x = alt.X("Month:N", sort=MONTH_ABBR, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=14))
    y_title = "mm per month"
    color = alt.Color(
        "series:N",
        scale=alt.Scale(domain=["Rain", "Water need (ET0)"], range=["#1f6fb2", "#b3541e"]),
        legend=alt.Legend(title=None, orient="top", labelFontSize=15, symbolSize=150),
    )
    base = alt.Chart(alt.Data(values=rows))
    bars = base.transform_fold(["Rain"], as_=["series", "mm"]).mark_bar(opacity=0.85).encode(
        x=x, y=alt.Y("mm:Q", title=y_title), color=color, tooltip=["Month:N", alt.Tooltip("mm:Q", title="Rain (mm)")]
    )
    line = base.transform_fold(["Water need (ET0)"], as_=["series", "mm"]).mark_line(
        point=alt.OverlayMarkDef(shape="diamond", size=60), strokeWidth=3, strokeDash=[6, 3]
    ).encode(x=x, y="mm:Q", color=color, tooltip=["Month:N", alt.Tooltip("mm:Q", title="Water need (mm)")])
    chart = (bars + line).properties(height=240).configure_axis(titleFontSize=14, labelFontSize=14)
    st.altair_chart(chart, width="stretch")
    st.caption(
        "Blue bars = rain. Dashed brown line with ◆ = water need. "
        "Where the line is above the bars, the field is short of water."
    )


def render_trends(profile: dict[str, Any]) -> None:
    trends = (profile or {}).get("trends") or {}
    rain = _num(trends.get("rain_change_pct"))
    heat = _num(trends.get("heat_days_change"))
    if rain is None and heat is None:
        _empty("The comparison with earlier years is not available for this field yet.")
        return
    with st.container(border=True):
        st.markdown("**📈 Then and now: 2016–2025 compared with 2005–2014**")
        if rain is not None:
            # Less rain is bad → "normal" makes a negative delta red; the ↓/↑ arrow and the text carry the meaning.
            st.metric("🌧️ Rain per year", f"{rain:+.0f} %".replace("-", "−"), delta=f"{rain:+.0f} %", delta_color="normal")
            if rain < 0:
                st.write(f"It rains about **{abs(rain):.0f}% less** than in 2005–2014.")
            elif rain > 0:
                st.write(f"It rains about **{rain:.0f}% more** than in 2005–2014.")
            else:
                st.write("It rains about the same as in 2005–2014.")
        if heat is not None:
            # More very hot days is bad → "inverse" makes a positive delta red.
            st.metric(
                "🔥 Very hot days (over 35 °C)",
                f"{heat:+.1f} days a year".replace("-", "−"),
                delta=f"{heat:+.1f} days",
                delta_color="inverse",
            )
            if heat > 0:
                st.write(f"There are about **{heat:.0f} more very hot days** a year than in 2005–2014.")
            elif heat < 0:
                st.write(f"There are about **{abs(heat):.0f} fewer very hot days** a year than in 2005–2014.")
            else:
                st.write("The number of very hot days is about the same as in 2005–2014.")
        st.caption("⚠️ " + DATA_LIMITS[3])


def _render_score_rows(scores: dict[str, Any]) -> None:
    for key, icon, label in SCORE_DIMENSIONS:
        v = _num(scores.get(key))
        if v is None:
            st.caption(f"{icon} {label}: not available yet")
            continue
        v = max(0.0, min(100.0, v))
        st.progress(v / 100, text=f"{icon} {label} · **{v:.0f}/100 · {score_level(v)}**")


def _render_list(items: Any, empty: str) -> None:
    items = [str(i) for i in (items or []) if i]
    st.markdown("\n".join(f"- {i}" for i in items) if items else f"_{empty}_")


def render_strategy_card(
    s: dict[str, Any], crop_names: dict[str, str], *, is_baseline: bool, is_best: bool
) -> None:
    scores = s.get("scores") or {}
    with st.container(border=True):
        if is_baseline:
            st.markdown("#### 📍 Your current rotation — baseline")
            st.caption("What you grow today. The other options are compared with it.")
        else:
            if is_best:
                st.markdown("**⭐ Best fit for your priorities** — a suggestion to discuss, not an order.")
            st.markdown(f"#### {s.get('name') or 'Rotation option'}")

        seq = crop_sequence(s.get("years"), crop_names)
        st.markdown(seq if seq else "_Crop sequence not available yet._")

        overall = _num(scores.get("overall"))
        if overall is not None:
            st.markdown(f"**Overall fit: {overall:.0f}/100 · {score_level(overall)}**")
        _render_score_rows(scores)

        if s.get("why"):
            st.markdown(f"**Why:** {s['why']}")
        st.markdown("**⚠️ Risks to review locally**")
        _render_list(s.get("risks_to_review"), "No risks listed yet — ask a local adviser.")

        with st.expander("🔎 Evidence"):
            _render_list(s.get("evidence"), "No evidence listed yet.")
        with st.expander("✅ Benefits"):
            _render_list(s.get("benefits"), "No benefits listed yet.")
        with st.expander("❓ What we don't know yet"):
            _render_list(s.get("gaps"), "No information gaps listed.")


def render_strategies(strategies: list[dict[str, Any]], crop_names: dict[str, str], weights: dict[str, float]) -> None:
    ordered = order_strategies(strategies)
    if not ordered:
        _empty("No rotation options could be built for this field yet. Check your answers and try again.")
        return
    line = priority_line(weights)
    if line:
        st.caption(f"**Overall fit** mixes the four scores using your priorities: {line}.")
    st.caption("Scores: Low under 40 · Medium 40–69 · High 70 or more (out of 100).")
    best_id = next((s.get("id") for s in ordered if s.get("id") != "current"), None)
    for s in ordered:
        render_strategy_card(s, crop_names, is_baseline=s.get("id") == "current", is_best=s.get("id") == best_id)


def render_sources(profile: dict[str, Any], is_mock: bool) -> None:
    sources = [str(x) for x in (profile or {}).get("sources") or [] if x]
    st.markdown("**📚 Sources and limits**")
    if sources:
        prefix = "Planned data sources (the mock values above do not come from them yet)" if is_mock else "Data sources"
        st.markdown(f"{prefix}: " + " · ".join(sources) + ".")
    else:
        st.markdown("_Data sources not available._")
    st.markdown("\n".join(f"- {limit}" for limit in DATA_LIMITS[:3]))
    st.markdown(f"🤝 **{SUPPORT_NOTE}**")


# ---------------------------------------------------------------- page


CSS = """
<style>
.fl-scroll { overflow-x: auto; max-width: 100%; }
.fl-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
table.fl-cal { width: 100%; border-collapse: collapse; font-size: 15px; line-height: 1.25; }
table.fl-cal th, table.fl-cal td { padding: 0.35rem 0.2rem; text-align: right; border-bottom: 1px solid rgba(128,128,128,0.35); }
table.fl-cal thead th { font-size: 14px; font-weight: 600; vertical-align: bottom; }
table.fl-cal th[scope=row], table.fl-cal thead th:first-child { text-align: left; }
table.fl-cal td:last-child, table.fl-cal thead th:last-child { text-align: left; white-space: nowrap; }
table.fl-cal td:nth-child(4) { white-space: nowrap; }
/* Smallest phones (320 px): tighter cells so all 7 columns fit without scrolling */
@media (max-width: 360px) {
  table.fl-cal { font-size: 14px; }
  table.fl-cal th, table.fl-cal td { padding: 0.35rem 0.12rem; }
}
</style>
"""


def _section(title: str, draw: Callable[[], None], fallback: str) -> None:
    """Draw one section; on any error show a friendly message instead of a traceback."""
    if title:
        st.subheader(title)
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

    st.markdown(CSS, unsafe_allow_html=True)
    if is_mock:
        st.warning("⚠️ **MOCK DATA** — example values for testing the app, not real results for your field.")

    oops = "This part could not be shown. The rest of the results are still valid."
    _section("🗓️ Your field through the year", lambda: render_key_facts(profile), oops)
    _section("", lambda: render_rain_chart(profile), oops)
    _section("", lambda: render_calendar_table(profile), oops)
    _section("", lambda: render_trends(profile), oops)
    _section("🔄 Rotation options", lambda: render_strategies(strategies, crop_names, weights), oops)
    _section("", lambda: render_sources(profile, is_mock), oops)
