"""FarmLens — Streamlit app (skeleton #12, results view #13 in fieldshift.ui_results).

Run: streamlit run src/app.py

One page, four numbered steps, mobile-first (no sidebar). All data comes from
fieldshift.mock_data until issue #14 wires in the real modules.
"""

from __future__ import annotations

import streamlit as st

from fieldshift import mock_data as data
from fieldshift import ui_theme as t
from fieldshift.mock_data import FarmerInputs
from fieldshift.ui_results import render_results

st.set_page_config(page_title="FarmLens", page_icon="🌱", layout="centered")

# The whole design system (tokens + one CSS layer) lives in fieldshift.ui_theme; see DESIGN.md.
# The CSS follows the active Streamlit theme (light / dark), or the system setting until it is known.
st.markdown(t.page_css(getattr(st.context.theme, "type", None)), unsafe_allow_html=True)

CROPS = data.get_crops()
CROP_NAMES = {c["id"]: c["name"] for c in CROPS}
CROP_IDS = [c["id"] for c in CROPS]
DEFAULT_ROTATION = ["durum_wheat", "durum_wheat", "sunflower", "durum_wheat"]

IRRIGATION = {
    "none": "None — rain only",
    "supplementary": "Supplementary — a few waterings in dry spells",
    "full": "Full — irrigated all season",
}
SLOPE = {
    "flat": "Flat — water does not run off",
    "gentle": "Gentle — some runoff after heavy rain",
    "steep": "Steep — soil washes away after storms",
}
PRIORITIES = {
    "water": "💧 Save water",
    "soil": "🌱 Soil health",
    "income": "💶 Income",
    "risk": "🛡️ Low risk",
}

st.markdown(
    "<header class='fl-head'><h1>FarmLens</h1><p class='fl-lead'>Compare crop rotations for "
    "<strong>your field</strong> using NASA climate data. Answer 4 short steps, then tap "
    "<strong>Analyze my field</strong>.</p></header>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- Step 1
st.markdown(t.step_heading(1, 4, "Your field"), unsafe_allow_html=True)
# Hints are visible text, not "?" tooltips: tooltips need hover and had 16 px targets on phones.
mode = st.radio(
    "How do you want to choose your field?",
    ["Demo field", "Point on a map"],
    captions=["Works without internet", "Needs a connection"],
    horizontal=True,
)

if mode == "Demo field":
    fields = data.get_demo_fields()
    chosen = st.selectbox("Demo field", fields, format_func=lambda f: f["name"])
    lat, lon, field_name = chosen["lat"], chosen["lon"], chosen["name"]
else:
    import folium
    from streamlit_folium import st_folium

    st.caption("Tap your field on the map.")
    start = st.session_state.get("map_point", (36.72, -4.42))
    fmap = folium.Map(location=start, zoom_start=9, control_scale=True)
    # Leaflet's +/− buttons are 30 px: enlarge them to 44 px touch targets inside the map iframe.
    fmap.get_root().header.add_child(
        folium.Element(
            "<style>.leaflet-touch .leaflet-bar a, .leaflet-bar a"
            "{width:44px;height:44px;line-height:44px;font-size:22px}</style>"
        )
    )
    folium.CircleMarker(start, radius=10, color="#b00020", fill=True, fill_opacity=0.9, tooltip="Your field").add_to(fmap)
    clicked = st_folium(fmap, height=300, use_container_width=True, returned_objects=["last_clicked"])
    if clicked and clicked.get("last_clicked"):
        point = (clicked["last_clicked"]["lat"], clicked["last_clicked"]["lng"])
        if point != st.session_state.get("map_point"):
            st.session_state["map_point"] = point
            st.rerun()
    lat, lon = st.session_state.get("map_point", start)
    field_name = "Point on the map"

st.markdown(t.location_line(lat, lon, field_name), unsafe_allow_html=True)

# ---------------------------------------------------------------- Step 2
st.markdown(t.step_heading(2, 4, "Current rotation"), unsafe_allow_html=True)
n_years = st.segmented_control(
    "How many years does your rotation last?",
    [2, 3, 4],
    default=3,
    required=True,
    format_func=lambda n: f"{n} years",
    width="stretch",
) or 3
rotation = []
for i in range(n_years):
    default = CROP_IDS.index(DEFAULT_ROTATION[i])
    crop = st.selectbox(f"Year {i + 1}", CROP_IDS, index=default, format_func=CROP_NAMES.get, key=f"year_{i}")
    rotation.append(crop)
# Live preview of the answer, in the same strip the results use (one visual language for rotations).
st.markdown(
    t.rotation_strip(rotation, CROP_NAMES, label="Your current rotation") + t.family_key(rotation),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- Step 3
st.markdown(t.step_heading(3, 4, "Your priorities"), unsafe_allow_html=True)
st.caption("Tap a number: 0 = not important · 5 = very important")
# Six big buttons instead of a slider: a 0–5 slider had a ~16 px thumb and needed dragging
# (WCAG 2.5.7 / 2.5.8); one tap is easier on a small phone.
priorities = {
    k: st.segmented_control(label, list(range(6)), default=3, required=True, key=f"prio_{k}", width="stretch")
    for k, label in PRIORITIES.items()
}
if sum(priorities.values()) == 0:
    st.caption("All priorities are 0, so they will count the same.")

# ---------------------------------------------------------------- Step 4
st.markdown(t.step_heading(4, 4, "Your farm"), unsafe_allow_html=True)
irrigation = st.radio(
    "Irrigation: how much water can you add besides rain?", list(IRRIGATION), format_func=IRRIGATION.get
)
slope = st.radio("Slope of the field (steeper fields lose more soil)", list(SLOPE), format_func=SLOPE.get)

inputs = FarmerInputs(
    lat=lat,
    lon=lon,
    field_name=field_name,
    rotation=rotation,
    priorities=priorities,
    irrigation=irrigation,
    slope=slope,
)

if st.button("Analyze my field", type="primary", icon=":material/search:", width="stretch"):
    with st.spinner("Analyzing your field…"):
        profile = data.get_climate_profile(inputs.lat, inputs.lon)
        st.session_state["results"] = {
            "inputs": inputs.to_dict(),
            "profile": profile,
            "strategies": data.get_strategies(profile, inputs),
        }
        st.session_state["just_analyzed"] = True

# ---------------------------------------------------------------- Results (#13)
# Feedback sits right under the button that caused it, where the farmer's eyes are.
results = st.session_state.get("results")
if not results:
    st.caption("Your results will appear below after you tap **Analyze my field**.")
    st.stop()

if results["inputs"] != inputs.to_dict():
    st.warning(
        "You changed some answers. Tap **Analyze my field** again to update the results below.",
        icon=":material/refresh:",
    )
elif st.session_state.pop("just_analyzed", False):
    st.success("Done. Your results are ready below.", icon=":material/check_circle:")

st.markdown(
    f"<h2 class='fl-step'><span class='fl-step__t'>Results for {t.e(results['inputs']['field_name'])}</span></h2>",
    unsafe_allow_html=True,
)
render_results(results, CROP_NAMES, is_mock=data.IS_MOCK)
