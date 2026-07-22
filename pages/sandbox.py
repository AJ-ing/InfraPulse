import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from data_loader import (
    load_data, ID_COL, RISK_COL, REGION_COL, STATE_CLASS_COL, LAT_COL, LON_COL, 
    TIER_BINS, TIER_LABELS, TIER_COLORS, assign_inspection_priority
)
from pipeline.scoring_logic import apply_risk_scoring

st.set_page_config(page_title="InfraPulse Sandbox", page_icon="🧪")

st.title("🧪 What-If Sandbox")
st.markdown("""
This interactive sandbox lets you adjust the weights of the Likelihood formula (Age, Traffic, and Climate risks) to see how the risk scores and rankings change.
**Note:** This does not modify the production batch scores.
""")

df = load_data()

# --- Sliders ---
st.sidebar.header("Formula Weights")
st.sidebar.markdown("Adjust weights. They will be automatically normalized to sum to 1.0.")

w_age_raw = st.sidebar.slider("Age Weight", 0.0, 1.0, 0.45, 0.05)
w_traffic_raw = st.sidebar.slider("Traffic Weight", 0.0, 1.0, 0.30, 0.05)
w_climate_raw = st.sidebar.slider("Climate Weight", 0.0, 1.0, 0.25, 0.05)

total_raw = w_age_raw + w_traffic_raw + w_climate_raw
if total_raw == 0:
    st.sidebar.error("Weights cannot all be zero!")
    w_age, w_traffic, w_climate = 0.45, 0.30, 0.25
else:
    w_age = w_age_raw / total_raw
    w_traffic = w_traffic_raw / total_raw
    w_climate = w_climate_raw / total_raw

st.sidebar.write("### Normalized Weights")
st.sidebar.write(f"- Age: **{w_age:.2f}**")
st.sidebar.write(f"- Traffic: **{w_traffic:.2f}**")
st.sidebar.write(f"- Climate: **{w_climate:.2f}**")

if st.sidebar.button("Reset to Default"):
    w_age, w_traffic, w_climate = 0.45, 0.30, 0.25

# --- Recompute Scores ---
with st.spinner("Recomputing scores..."):
    # Apply scoring on a copy to avoid mutating the cached df
    sandbox_df = apply_risk_scoring(df, w_age=w_age, w_traffic=w_traffic, w_climate=w_climate)
    
    # Recalculate tier and priority based on new scores
    sandbox_df['risk_tier'] = pd.cut(
        sandbox_df[RISK_COL],
        bins=TIER_BINS,
        labels=TIER_LABELS,
        include_lowest=True
    )
    sandbox_df['inspection_priority'] = sandbox_df[RISK_COL].apply(assign_inspection_priority)

# --- Display Results ---
col1, col2 = st.columns(2)
col1.metric("Average Risk Score", f"{sandbox_df[RISK_COL].mean():.1f}", 
            delta=f"{sandbox_df[RISK_COL].mean() - df[RISK_COL].mean():.1f}" if w_age!=0.45 or w_traffic!=0.30 or w_climate!=0.25 else None,
            delta_color="inverse")
col2.metric("Highest Risk Score", f"{sandbox_df[RISK_COL].max():.1f}")

st.subheader("Sandbox Risk Map")
if LAT_COL in sandbox_df.columns and LON_COL in sandbox_df.columns:
    map_df = sandbox_df.dropna(subset=[LAT_COL, LON_COL]).head(1000) # limit to 1000 for map perf in sandbox
    if not map_df.empty:
        mean_lat = map_df[LAT_COL].mean()
        mean_lon = map_df[LON_COL].mean()
        m = folium.Map(location=[mean_lat, mean_lon], zoom_start=7)
        
        for idx, row in map_df.iterrows():
            tier = str(row.get('risk_tier', 'Unknown'))
            color = TIER_COLORS.get(tier, "gray")
            popup_text = f"ID: {row.get(ID_COL, 'Unknown')}<br>Tier: {tier}<br>Score: {row.get(RISK_COL, 0):.1f}"
            
            folium.CircleMarker(
                location=[row[LAT_COL], row[LON_COL]],
                radius=3,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=popup_text
            ).add_to(m)
            
        st_folium(m, width="100%", height=400, returned_objects=[])

st.subheader("Top 20 Sandbox Bridges")
top20 = sandbox_df.sort_values(RISK_COL, ascending=False).head(20)
display_cols = [c for c in [ID_COL, REGION_COL, STATE_CLASS_COL, 'risk_tier', RISK_COL, 'inspection_priority'] if c in sandbox_df.columns]
st.dataframe(top20[display_cols], width='stretch')
