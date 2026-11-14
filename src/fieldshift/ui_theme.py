"""FarmLens design system for Streamlit: tokens, the one global CSS layer and small HTML components.

Everything visual that Streamlit's own theme (``.streamlit/config.toml``) cannot express lives here,
so the app has one source of truth. The direction is written down in ``DESIGN.md``.

Rules this module enforces (docs/ux-guidelines.md, WCAG 2.2 AA):
- every touch target ≥ 48 px high, body text ≥ 16 px, secondary text ≥ 14 px;
- text contrast ≥ 4.5:1 in both themes (values checked in DESIGN.md);
- meaning never by colour alone: every coloured mark has a word next to it;
- every string that comes from data is HTML-escaped before it is placed in markup.

The HTML builders are pure functions (string in, string out) so they can be unit-tested.
"""

from __future__ import annotations

import html
import math
from collections.abc import Mapping, Sequence
from typing import Any

# ---------------------------------------------------------------- tokens

# Mirrors [theme.light] / [theme.dark] in .streamlit/config.toml. Change both together.
TOKENS: dict[str, dict[str, str]] = {
    "light": {
        "ground": "#FAFAF7",  # page
        "panel": "#EFEEE7",  # quiet surface (stone)
        "ink": "#1E231C",  # text, 15.3:1 on ground
        "muted": "#545B50",  # secondary text, 6.7:1 on ground
        "line": "#CFCDC2",  # hairlines
        "accent": "#2E5B44",  # pine: primary action, selection, focus (white text 7.8:1)
        "accent-ink": "#2E5B44",  # accent used as text (7.5:1)
        "accent-soft": "#E1EBE4",  # tint behind the best-fit tag
        "focus-halo": "#FFFFFF",
    },
    "dark": {
        "ground": "#121510",
        "panel": "#1D211B",
        "ink": "#ECEDE6",  # 15.6:1
        "muted": "#B1B7AA",  # 9.0:1
        "line": "#3C4238",
        "accent": "#3F8160",  # white text 4.65:1, 3.96:1 against the ground (focus ring ≥ 3:1)
        "accent-ink": "#8FCDA8",  # 10:1
        "accent-soft": "#20342A",
        "focus-halo": "#121510",
    },
}

# Crop families → fill colour of a year in the rotation strip. Text on every fill is the light ink
# (#1E231C, ≥ 7.5:1), so the strip reads the same in both themes; the crop name is always printed.
FAMILY_COLORS: dict[str, str] = {
    "cereal": "#E3C26A",  # straw
    "legume": "#9CC27A",  # pod green
    "oilseed": "#EFA445",  # sunflower gold
    "cover": "#7FBFA6",  # cover-crop green-blue
    "fallow": "#C8B597",  # bare soil
    "other": "#C9CCC2",
}
FAMILY_LABELS: dict[str, str] = {
    "cereal": "Cereal",
    "legume": "Legume",
    "oilseed": "Oilseed",
    "cover": "Cover crop",
    "fallow": "Fallow",
    "other": "Other",
}
# Crop id → family. Ids from data/crops.csv and the mock catalogue; unknown ids fall back to "other".
CROP_FAMILY: dict[str, str] = {
    **dict.fromkeys(
        ("durum_wheat", "soft_wheat", "bread_wheat", "barley", "oats", "maize", "sorghum", "triticale"), "cereal"
    ),
    **dict.fromkeys(("chickpea", "lentil", "faba_bean", "pea", "vetch", "vetch_cover", "alfalfa"), "legume"),
    **dict.fromkeys(("sunflower", "rapeseed", "camelina"), "oilseed"),
    **dict.fromkeys(("mustard_cover", "vetch_oat"), "cover"),
    "fallow": "fallow",
}

STRIP_INK = "#1E231C"


def crop_family(crop_id: str) -> str:
    """Family key for a crop id ("other" when unknown)."""
    return CROP_FAMILY.get(str(crop_id), "other")


def crop_label(crop_id: Any, crop_names: Mapping[str, str]) -> str:
    """Display name of a crop; unknown ids become readable ("mystery_crop" → "Mystery crop")."""
    return crop_names.get(crop_id) or str(crop_id).replace("_", " ").capitalize()


# ---------------------------------------------------------------- CSS


def _vars(kind: str) -> str:
    return "".join(f"--fl-{k}:{v};" for k, v in TOKENS[kind].items())


def theme_vars_css(kind: str | None) -> str:
    """CSS custom properties for the active Streamlit theme.

    ``kind`` is ``st.context.theme.type`` ("light" / "dark"). When Streamlit does not know it yet
    (``None``), fall back to the system preference, which is what Streamlit itself follows by default.
    """
    if kind in TOKENS:
        return f":root{{{_vars(kind)}}}"  # type: ignore[arg-type]
    return f":root{{{_vars('light')}}}@media (prefers-color-scheme: dark){{:root{{{_vars('dark')}}}}}"


BASE_CSS = """
:root {
  --fl-target: 48px;
  --fl-s1: 4px; --fl-s2: 8px; --fl-s3: 12px; --fl-s4: 16px; --fl-s5: 24px; --fl-s6: 32px; --fl-s7: 48px;
  --fl-r-sm: 6px; --fl-r-md: 8px; --fl-r-lg: 12px;
  --fl-t-small: 0.875rem; --fl-t-body: 1rem; --fl-t-lead: 1.125rem; --fl-t-title: 1.25rem;
  --fl-ease: cubic-bezier(0.2, 0.8, 0.2, 1); --fl-fast: 140ms;
}

/* ---- Page frame: one centred column, 16 px gutters on phones */
.block-container { padding-top: 2rem; padding-left: 1rem; padding-right: 1rem; padding-bottom: 4rem; }
@media (min-width: 640px) { .block-container { padding-left: 1.5rem; padding-right: 1.5rem; } }
.stApp { font-variant-numeric: tabular-nums; }
::selection { background: var(--fl-accent); color: #fff; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { font-size: var(--fl-t-small);
  color: var(--fl-muted); }
[data-testid="stMarkdownContainer"] li { margin-bottom: 0.25rem; }

/* ---- Touch targets (WCAG 2.5.8 + our 48 px low-end-phone rule) */
div.stButton > button { min-height: var(--fl-target); font-size: 1.0625rem; font-weight: 650; }
div.stButton > button[kind="primary"] { min-height: 56px; font-size: 1.125rem; }
div.stButton > button {
  transition: transform var(--fl-fast) var(--fl-ease), background-color var(--fl-fast) var(--fl-ease);
}
div.stButton > button:active { transform: translateY(1px); }
[data-testid="stRadioOption"] { display: flex; min-height: var(--fl-target); align-items: center; }
[data-testid="stButtonGroup"] button { min-height: var(--fl-target); min-width: 44px; font-size: 1rem; }
[data-testid="stSelectbox"] [role="group"] { min-height: var(--fl-target); align-items: stretch; }
[data-testid="stExpander"] summary { min-height: var(--fl-target); }
[data-testid="stElementToolbar"] button { min-width: 44px; min-height: 44px; }

/* Selected segment: bold + theme ink (accent-on-tint text was below 4.5:1); the border still marks it */
div[data-testid="stButtonGroup"] button[role="radio"][aria-checked="true"],
div[data-testid="stButtonGroup"] button[role="radio"][aria-checked="true"] p { color: inherit; font-weight: 750; }

/* Heading permalink icons: 16 px targets and tab stops with no use for farmers */
[data-testid="stHeaderActionElements"] { display: none; }

/* ---- Focus: a two-tone ring (accent + halo) that stays ≥ 3:1 on any ground (WCAG 2.4.7 / 2.4.11) */
a:focus-visible, button:focus-visible, summary:focus-visible, [tabindex="0"]:focus-visible,
[data-testid="stSelectbox"] [role="group"]:has(input:focus-visible),
[data-testid="stRadioOption"]:has(input:focus-visible),
[data-testid="stCheckbox"] label:has(input:focus-visible) {
  outline: 3px solid var(--fl-accent); outline-offset: 2px; box-shadow: 0 0 0 5px var(--fl-focus-halo);
}

/* ---- Masthead */
.fl-head { margin: 0 0 var(--fl-s6); }
.fl-head h1 { margin: 0 0 var(--fl-s2) !important; padding: 0 !important; letter-spacing: -0.01em; }
.fl-head .fl-lead { font-size: var(--fl-t-lead); line-height: 1.5; margin: 0; max-width: 34em; }

/* ---- Step headings: the number is a real sequence (Step N of 4, UX launch route 02).
   Streamlit wraps heading text in span[data-heading-text] and resets heading margins, hence !important. */
h2.fl-step { margin: var(--fl-s6) 0 var(--fl-s2) !important; padding: var(--fl-s5) 0 0 !important;
  border-top: 1px solid var(--fl-line); scroll-margin-top: 4rem; }
h2.fl-step > [data-heading-text] { display: flex; flex-wrap: wrap; align-items: center;
  gap: var(--fl-s2) var(--fl-s3); }
.fl-step__n { flex: none; display: inline-grid; place-items: center; width: 2rem; height: 2rem; border-radius: 50%;
  background: var(--fl-accent); color: #fff; font-size: 1rem; font-weight: 750; line-height: 1; }
.fl-step__t { flex: 1 1 auto; min-width: 0; }
.fl-step__of { flex: none; font-size: var(--fl-t-small); font-weight: 500; color: var(--fl-muted); }

/* ---- Section headings inside the results */
.fl-sec { margin: var(--fl-s7) 0 var(--fl-s2) !important; padding: 0 !important; }
h4.fl-card-title { padding: 0 !important; }

/* ---- Location line */
.fl-loc { display: flex; gap: var(--fl-s2); align-items: baseline; flex-wrap: wrap; margin: var(--fl-s2) 0 0;
  padding: var(--fl-s3) var(--fl-s4); background: var(--fl-panel); border-radius: var(--fl-r-md); }
.fl-loc strong { font-size: var(--fl-t-body); }
.fl-loc span { color: var(--fl-muted); font-size: var(--fl-t-small); }

/* ---- Rotation strip: the signature element. Years as plots side by side, filled by crop family */
.fl-strip { list-style: none; margin: var(--fl-s2) 0 var(--fl-s3); padding: 0; display: grid;
  grid-template-columns: repeat(var(--n, 3), minmax(0, 1fr)); gap: 3px; }
.fl-strip li { margin: 0; padding: var(--fl-s2) var(--fl-s2) var(--fl-s3); min-height: 64px; background: var(--c);
  color: #1E231C; border: 1px solid rgba(30, 35, 28, 0.18); display: flex; flex-direction: column; gap: 2px; }
.fl-strip li:first-child { border-radius: var(--fl-r-md) 0 0 var(--fl-r-md); }
.fl-strip li:last-child { border-radius: 0 var(--fl-r-md) var(--fl-r-md) 0; }
.fl-strip li:only-child { border-radius: var(--fl-r-md); }
.fl-strip .y { font-size: var(--fl-t-small); font-weight: 600; opacity: 0.85; }
.fl-strip .c { font-size: var(--fl-t-body); font-weight: 700; line-height: 1.2; overflow-wrap: anywhere;
  hyphens: auto; }
.fl-key { display: flex; flex-wrap: wrap; gap: var(--fl-s1) var(--fl-s3); margin: 0; padding: 0; list-style: none;
  font-size: var(--fl-t-small); color: var(--fl-muted); }
.fl-key li { margin: 0; display: inline-flex; align-items: center; gap: 6px; }
.fl-key i { width: 0.875rem; height: 0.875rem; border-radius: 3px; background: var(--c);
  border: 1px solid rgba(30, 35, 28, 0.25); }

/* ---- Tags (current rotation / best fit) */
.fl-tags { display: flex; flex-wrap: wrap; gap: var(--fl-s2); margin: 0 0 var(--fl-s2); }
.fl-tag { display: inline-flex; align-items: center; min-height: 28px; padding: 2px 10px; border-radius: 999px;
  font-size: var(--fl-t-small); font-weight: 650; border: 1px solid var(--fl-line); color: var(--fl-ink); }
.fl-tag--best { background: var(--fl-accent); border-color: var(--fl-accent); color: #fff; }

/* ---- Strategy card head */
[data-testid="stMarkdownContainer"] .fl-card-title { font-size: var(--fl-t-title); font-weight: 750;
  line-height: 1.25; margin: 0 0 var(--fl-s1); padding: 0; }
.fl-card-sub { color: var(--fl-muted); font-size: var(--fl-t-small); margin: 0 0 var(--fl-s2); }

/* ---- Scores: one bar style everywhere (overall, four dimensions, comparison) */
.fl-overall { display: flex; align-items: baseline; gap: var(--fl-s2); flex-wrap: wrap;
  margin: var(--fl-s3) 0 var(--fl-s2); }
.fl-overall b { font-size: 2rem; line-height: 1; font-weight: 750; }
.fl-overall span { color: var(--fl-muted); }
.fl-scores { margin: 0 0 var(--fl-s4); padding: 0; display: grid; gap: var(--fl-s2); }
.fl-score { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px var(--fl-s3); align-items: baseline; }
.fl-score dt { margin: 0; font-weight: 500; }
.fl-score dd { margin: 0; font-weight: 650; white-space: nowrap; }
.fl-bar { grid-column: 1 / -1; height: 8px; border-radius: 4px;
  background: color-mix(in srgb, currentColor 14%, transparent); overflow: hidden; }
.fl-bar > i { display: block; height: 100%; width: var(--v); border-radius: 4px; background: var(--fl-accent); }

/* ---- Comparison at a glance */
.fl-compare { list-style: none; margin: var(--fl-s3) 0 var(--fl-s5); padding: 0; display: grid; gap: 0; }
.fl-compare li { margin: 0; padding: var(--fl-s3) 0; border-bottom: 1px solid var(--fl-line);
  display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: var(--fl-s1) var(--fl-s3); align-items: baseline; }
.fl-compare li:first-child { border-top: 1px solid var(--fl-line); }
.fl-compare .n { font-weight: 650; }
.fl-compare .n small { display: block; font-weight: 500; font-size: var(--fl-t-small); color: var(--fl-muted); }
.fl-compare .s { font-weight: 750; font-size: var(--fl-t-lead); white-space: nowrap; }
.fl-compare .s small { font-weight: 500; font-size: var(--fl-t-small); color: var(--fl-muted); }

/* ---- Sub-heading inside a results section (one step below .fl-sec) */
[data-testid="stMarkdownContainer"] .fl-sub { font-size: var(--fl-t-body); font-weight: 700;
  margin: var(--fl-s5) 0 var(--fl-s1); padding: 0; }

/* ---- Then and now */
.fl-trend { list-style: none; margin: var(--fl-s2) 0 var(--fl-s2); padding: 0; display: grid; gap: var(--fl-s3); }
.fl-trend li { margin: 0; padding: var(--fl-s3) var(--fl-s4); background: var(--fl-panel);
  border-radius: var(--fl-r-md);
  display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 2px var(--fl-s4); align-items: center; }
.fl-trend b { grid-row: span 2; font-size: 1.75rem; font-weight: 750; line-height: 1; white-space: nowrap; }
.fl-trend .l { font-weight: 650; }
.fl-trend .d { color: var(--fl-muted); font-size: var(--fl-t-small); }

/* ---- Month table: horizontal rules only, numbers right-aligned, scrolls inside its own region */
.fl-scroll { overflow-x: auto; max-width: 100%; margin: var(--fl-s2) 0 var(--fl-s2); }
.fl-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
table.fl-cal { width: 100%; border-collapse: collapse; font-size: 0.9375rem; line-height: 1.25; border: 0; }
table.fl-cal th, table.fl-cal td { padding: 0.45rem 0.2rem; text-align: right; border: 0;
  border-bottom: 1px solid var(--fl-line); background: none; }
table.fl-cal thead th { font-size: var(--fl-t-small); font-weight: 650; vertical-align: bottom;
  color: var(--fl-muted); border-bottom: 2px solid var(--fl-line); }
table.fl-cal th[scope=row], table.fl-cal thead th:first-child { text-align: left; font-weight: 650; }
table.fl-cal td:last-child, table.fl-cal thead th:last-child { text-align: left; white-space: nowrap;
  padding-left: 0.35rem; }
table.fl-cal td:nth-child(4) { white-space: nowrap; }
table.fl-cal tr.is-bare th, table.fl-cal tr.is-bare td { background: color-mix(in srgb, #C8B597 22%, transparent); }
@media (max-width: 360px) {
  table.fl-cal { font-size: 0.875rem; }
  table.fl-cal th, table.fl-cal td { padding: 0.4rem 0.1rem; }
  table.fl-cal td:last-child, table.fl-cal thead th:last-child { padding-left: 0.2rem; }
  table.fl-cal thead th { font-size: 0.8125rem; letter-spacing: -0.01em; }
}
/* Smallest phones: 12 px gutters so the 7-column month table fits without scrolling */
@media (max-width: 340px) { .block-container { padding-left: 0.75rem; padding-right: 0.75rem; } }

/* ---- Sources footer */
.fl-foot { margin-top: var(--fl-s7); padding-top: var(--fl-s4); border-top: 1px solid var(--fl-line); }

/* ---- Reduced motion: keep every state change, drop the movement */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important;
    scroll-behavior: auto !important; }
  div.stButton > button, div.stButton > button:active { transition: none; transform: none; }
}
"""


def page_css(theme_kind: str | None) -> str:
    """The full <style> block for the page."""
    return f"<style>{theme_vars_css(theme_kind)}{BASE_CSS}</style>"


# ---------------------------------------------------------------- HTML components (pure)

e = html.escape


def step_heading(n: int, total: int, title: str) -> str:
    """Numbered step heading; the "Step N of M" text stays visible (UX launch route 02)."""
    return (
        f"<h2 class='fl-step'><span class='fl-step__n' aria-hidden='true'>{n}</span>"
        f"<span class='fl-step__t'>{e(title)}</span>"
        f"<span class='fl-step__of'>Step {n} of {total}</span></h2>"
    )


def section_heading(title: str) -> str:
    return f"<h3 class='fl-sec'>{e(title)}</h3>"


def format_latlon(lat: float, lon: float) -> str:
    """36.72, -4.42 → "36.72° N, 4.42° W" (two decimals ≈ 1 km, enough for a field)."""
    return f"{abs(lat):.2f}° {'N' if lat >= 0 else 'S'}, {abs(lon):.2f}° {'E' if lon >= 0 else 'W'}"


def location_line(lat: float, lon: float, field_name: str) -> str:
    return (
        f"<p class='fl-loc'><strong>{e(field_name)}</strong>"
        f"<span>{e(format_latlon(lat, lon))} (latitude, longitude)</span></p>"
    )


def rotation_strip(years: Sequence[str] | None, crop_names: Mapping[str, str], *, label: str = "") -> str:
    """Ordered list of years, each a plot filled by crop family colour, with "Year N" and the crop name."""
    years = list(years or [])
    if not years:
        return ""
    items = "".join(
        f"<li style='--c:{FAMILY_COLORS[crop_family(c)]}'><span class='y'>Year {i}</span>"
        f"<span class='c'>{e(crop_label(c, crop_names))}</span></li>"
        for i, c in enumerate(years, start=1)
    )
    aria = f" aria-label='{e(label)}'" if label else ""
    return f"<ol class='fl-strip' style='--n:{len(years)}'{aria}>{items}</ol>"


def family_key(crop_ids: Sequence[str]) -> str:
    """Legend for the strip colours, limited to the families actually shown."""
    seen: list[str] = []
    for c in crop_ids:
        f = crop_family(c)
        if f not in seen:
            seen.append(f)
    if not seen:
        return ""
    items = "".join(
        f"<li><i style='--c:{FAMILY_COLORS[f]}' aria-hidden='true'></i>{FAMILY_LABELS[f]}</li>" for f in seen
    )
    return f"<ul class='fl-key' aria-label='Colour key: crop family'>{items}</ul>"


def _clamp_score(value: Any) -> float | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(100.0, v)) if math.isfinite(v) else None


def bar(value: float, tag: str = "span") -> str:
    """Decorative bar; the number is always printed next to it, so it is hidden from screen readers.

    ``tag="dd"`` keeps the markup valid inside a definition list.
    """
    return f"<{tag} class='fl-bar' aria-hidden='true'><i style='--v:{value:.0f}%'></i></{tag}>"


def tags(*, best: bool = False) -> str:
    """Status tags above a card title. The baseline card needs none: its title already says it."""
    out = []
    if best:
        out.append("<span class='fl-tag fl-tag--best'>Best fit for your priorities</span>")
    return f"<div class='fl-tags'>{''.join(out)}</div>" if out else ""
