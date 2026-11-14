"""FarmLens — Streamlit app (skeleton #12, results view #13 in fieldshift.ui_results).

Run: streamlit run src/app.py

One page, four numbered steps, mobile-first (no sidebar). All data comes from
fieldshift.mock_data until issue #14 wires in the real modules.
"""

from __future__ import annotations

import streamlit as st

from fieldshift import mock_data as data
from fieldshift.mock_data import FarmerInputs
from fieldshift.ui_results import render_results

st.set_page_config(page_title="FarmLens", page_icon="🌱", layout="centered")

# Streamlit's base font is already 16 px; here: tighter side padding on phones and 48 px buttons.
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-left: 1rem; padding-right: 1rem; }
    div.stButton > button { min-height: 48px; font-size: 18px; font-weight: 600; }
    [data-testid="stRadioOption"] { min-height: 44px; align-items: center; }
    [data-testid="stButtonGroup"] button { min-height: 44px; }
    [data-testid="stTable"] td, [data-testid="stTable"] th { font-size: 16px; padding: 0.3rem 0.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

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

st.title("🌱 FarmLens")
st.write(
    "Compare crop rotations for **your field** using NASA climate data. "
    "Answer 4 short steps, then tap **Analyze my field**."
)

# ---------------------------------------------------------------- Step 1
st.subheader("Step 1 of 4 · Your field")
mode = st.radio(
    "How do you want to choose your field?",
    ["Demo field", "Point on a map"],
    horizontal=True,
    help="The demo field works without internet. The map needs a connection.",
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
    folium.CircleMarker(start, radius=10, color="#b00020", fill=True, fill_opacity=0.9, tooltip="Your field").add_to(fmap)
    clicked = st_folium(fmap, height=300, use_container_width=True, returned_objects=["last_clicked"])
    if clicked and clicked.get("last_clicked"):
        point = (clicked["last_clicked"]["lat"], clicked["last_clicked"]["lng"])
        if point != st.session_state.get("map_point"):
            st.session_state["map_point"] = point
            st.rerun()
    lat, lon = st.session_state.get("map_point", start)
    field_name = "Point on the map"

st.info(f"📍 Location: **{lat:.4f}, {lon:.4f}** (latitude, longitude)")

# ---------------------------------------------------------------- Step 2
st.subheader("Step 2 of 4 · Current rotation")
n_years = st.segmented_control(
    "How many years does your rotation last?", [2, 3, 4], default=3, format_func=lambda n: f"{n} years"
) or 3
rotation = []
for i in range(n_years):
    default = CROP_IDS.index(DEFAULT_ROTATION[i])
    crop = st.selectbox(f"Year {i + 1}", CROP_IDS, index=default, format_func=CROP_NAMES.get, key=f"year_{i}")
    rotation.append(crop)

# ---------------------------------------------------------------- Step 3
st.subheader("Step 3 of 4 · Your priorities")
st.caption("0 = not important · 5 = very important")
priorities = {k: st.slider(label, 0, 5, 3, key=f"prio_{k}") for k, label in PRIORITIES.items()}
if sum(priorities.values()) == 0:
    st.caption("All priorities are 0, so they will count the same.")

# ---------------------------------------------------------------- Step 4
st.subheader("Step 4 of 4 · Your farm")
irrigation = st.radio(
    "Irrigation", list(IRRIGATION), format_func=IRRIGATION.get, help="How much water can you add besides rain?"
)
slope = st.radio("Slope of the field", list(SLOPE), format_func=SLOPE.get, help="Steeper fields lose more soil.")

inputs = FarmerInputs(
    lat=lat,
    lon=lon,
    field_name=field_name,
    rotation=rotation,
    priorities=priorities,
    irrigation=irrigation,
    slope=slope,
)

if st.button("🔎 Analyze my field", type="primary", width="stretch"):
    with st.spinner("Analyzing your field…"):
        profile = data.get_climate_profile(inputs.lat, inputs.lon)
        st.session_state["results"] = {
            "inputs": inputs.to_dict(),
            "profile": profile,
            "strategies": data.get_strategies(profile, inputs),
        }
        st.session_state["just_analyzed"] = True

# ---------------------------------------------------------------- Results (#13)
results = st.session_state.get("results")
if not results:
    st.caption("Your results will appear here after you tap **Analyze my field**.")
    st.stop()

st.divider()
st.header("✅ Results")
if st.session_state.pop("just_analyzed", False):
    st.success("Done ✓ Your results are ready.")
if results["inputs"] != inputs.to_dict():
    st.warning("You changed some answers. Tap **Analyze my field** again to update the results.")

render_results(results, CROP_NAMES, is_mock=data.IS_MOCK)
