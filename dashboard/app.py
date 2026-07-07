"""
InfraPulse — Step 3 sidebar filters.
Goal: Add sidebar filters and make KPIs, Map, and Table respond to them.
Run with: streamlit run app.py
"""

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="InfraPulse", layout="wide")

# --- CONFIG ---
CSV_PATH = "data/processed/bridges_risk_scored.csv"
ID_COL = "Name"
RISK_COL = "risk_score"
REGION_COL = "REGION_PHYS"
STATE_CLASS_COL = "CD_STATE_CLASS"
# ----------------------------------------------------------------------------------

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if RISK_COL in df.columns:
        df['risk_tier'] = pd.cut(
            df[RISK_COL],
            bins=[0, 40, 60, 80, 100.01],
            labels=["Low", "Medium", "High", "Critical"],
            include_lowest=True
        )
    return df

df = load_data(CSV_PATH)

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Region filter
unique_regions = sorted(df[REGION_COL].dropna().unique())
selected_regions = st.sidebar.multiselect(
    "Region",
    options=unique_regions,
    default=unique_regions
)

# State Class filter
unique_classes = sorted(df[STATE_CLASS_COL].dropna().unique())
selected_classes = st.sidebar.multiselect(
    "Road / State Class",
    options=unique_classes,
    default=unique_classes
)

# Risk Tier filter
tier_labels = ["Low", "Medium", "High", "Critical"]
selected_tiers = st.sidebar.multiselect(
    "Risk Tier",
    options=tier_labels,
    default=tier_labels
)

# Apply filters
filtered = df[
    df[REGION_COL].isin(selected_regions) &
    df[STATE_CLASS_COL].isin(selected_classes) &
    df['risk_tier'].isin(selected_tiers)
]

st.sidebar.caption(f"{len(filtered):,} of {len(df):,} bridges shown")

# --- Main App ---
st.title("InfraPulse — Bridge Risk Overview")

# KPI row
col1, col2, col3 = st.columns(3)
col1.metric("Bridges shown", f"{len(filtered):,}")
if not filtered.empty:
    col2.metric("Average risk score", f"{filtered[RISK_COL].mean():.1f}")
    col3.metric("Highest risk score", f"{filtered[RISK_COL].max():.1f}")
else:
    col2.metric("Average risk score", "—")
    col3.metric("Highest risk score", "—")

st.divider()

if filtered.empty:
    st.info("No bridges match the current filters.")
else:
    # Map section
    st.subheader("Risk Map")
    if "LAT" in filtered.columns and "LONGIT" in filtered.columns:
        map_df = filtered.dropna(subset=["LAT", "LONGIT"])
        if not map_df.empty:
            mean_lat = map_df["LAT"].mean()
            mean_lon = map_df["LONGIT"].mean()
            m = folium.Map(location=[mean_lat, mean_lon], zoom_start=7)
            
            color_map = {
                "Low": "green",
                "Medium": "orange",
                "High": "red",
                "Critical": "darkred"
            }
            
            for idx, row in map_df.iterrows():
                tier = str(row.get('risk_tier', 'Unknown'))
                color = color_map.get(tier, "gray")
                popup_text = f"ID: {row.get(ID_COL, 'Unknown')}<br>Tier: {tier}<br>Score: {row.get(RISK_COL, 0):.1f}"
                
                folium.CircleMarker(
                    location=[row["LAT"], row["LONGIT"]],
                    radius=3,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=popup_text
                ).add_to(m)
                
            st_folium(m, width="100%", height=500, returned_objects=[])
        else:
            st.warning("No bridges with coordinate data match the current filters.")
    else:
        st.warning("Missing latitude/longitude columns (expected 'LAT' and 'LONGIT').")

    st.divider()

    # Ranked table
    st.subheader("Top 20 highest-risk bridges")
    top20 = filtered.sort_values(RISK_COL, ascending=False).head(20)
    display_cols = [c for c in [ID_COL, REGION_COL, STATE_CLASS_COL, 'risk_tier', RISK_COL] if c in filtered.columns]
    st.dataframe(top20[display_cols], width='stretch')
