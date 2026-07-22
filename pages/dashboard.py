import streamlit as st
import folium
from streamlit_folium import st_folium
from data_loader import (
    load_data, ID_COL, RISK_COL, REGION_COL, STATE_CLASS_COL, LAT_COL, LON_COL, TIER_LABELS, TIER_COLORS
)
from utils.pdf_export import generate_region_pdf, generate_bridge_pdf

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filters")

unique_regions = sorted(df[REGION_COL].dropna().unique())
selected_regions = st.sidebar.multiselect("Region", options=unique_regions, default=unique_regions)

unique_classes = sorted(df[STATE_CLASS_COL].dropna().unique())
selected_classes = st.sidebar.multiselect("Road / State Class", options=unique_classes, default=unique_classes)

selected_tiers = st.sidebar.multiselect("Risk Tier", options=TIER_LABELS, default=TIER_LABELS)

unique_priorities = sorted(df['inspection_priority'].dropna().unique())
selected_priorities = st.sidebar.multiselect("Inspection Priority", options=unique_priorities, default=unique_priorities)

flood_affected_filter = st.sidebar.checkbox("Show only Oct 2022 Flood Affected Regions", value=False)

filtered = df[
    df[REGION_COL].isin(selected_regions) &
    df[STATE_CLASS_COL].isin(selected_classes) &
    df['risk_tier'].isin(selected_tiers) &
    df['inspection_priority'].isin(selected_priorities)
]

if flood_affected_filter:
    filtered = filtered[filtered['flood_affected_2022'] == True]

st.sidebar.caption(f"{len(filtered):,} of {len(df):,} bridges shown")

# --- Main App ---
st.title("Dashboard")
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
    st.subheader("Risk Map")
    
    # PDF export for filtered view
    filters_text = f"Region: {len(selected_regions)}, Class: {len(selected_classes)}, Tier: {len(selected_tiers)}"
    if flood_affected_filter:
        filters_text += ", Flood Affected Only"
    
    st.download_button(
        label="📄 Download Region Summary PDF",
        data=generate_region_pdf(filtered, filters_text=filters_text),
        file_name="region_summary.pdf",
        mime="application/pdf"
    )
    
    if LAT_COL in filtered.columns and LON_COL in filtered.columns:
        map_df = filtered.dropna(subset=[LAT_COL, LON_COL])
        if not map_df.empty:
            mean_lat = map_df[LAT_COL].mean()
            mean_lon = map_df[LON_COL].mean()
            m = folium.Map(location=[mean_lat, mean_lon], zoom_start=7)
            
            for idx, row in map_df.iterrows():
                tier = str(row.get('risk_tier', 'Unknown'))
                color = TIER_COLORS.get(tier, "gray")
                flood_flag = "⚠️ Oct 2022 Flood Affected" if row.get('flood_affected_2022') else "No"
                popup_text = f"ID: {row.get(ID_COL, 'Unknown')}<br>Tier: {tier}<br>Score: {row.get(RISK_COL, 0):.1f}<br>Priority: {row.get('inspection_priority', 'Unknown')}<br>Flood History: {flood_flag}"
                
                folium.CircleMarker(
                    location=[row[LAT_COL], row[LON_COL]],
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
        st.warning(f"Missing latitude/longitude columns (expected '{LAT_COL}' and '{LON_COL}').")

    st.divider()

    st.subheader("Top 20 highest-risk bridges")
    top20 = filtered.sort_values(RISK_COL, ascending=False).head(20)
    display_cols = [c for c in [ID_COL, REGION_COL, STATE_CLASS_COL, 'risk_tier', RISK_COL, 'inspection_priority', 'flood_affected_2022'] if c in filtered.columns]
    st.dataframe(top20[display_cols], width='stretch')

    st.divider()
    
    st.subheader("Bridge Detail Export")
    bridge_options = filtered[ID_COL].dropna().unique()
    if len(bridge_options) > 0:
        selected_bridge_id = st.selectbox("Select a bridge to generate a detailed PDF", options=bridge_options)
        bridge_row = filtered[filtered[ID_COL] == selected_bridge_id].iloc[0]
        
        st.download_button(
            label=f"📄 Download PDF for {selected_bridge_id}",
            data=generate_bridge_pdf(bridge_row),
            file_name=f"{selected_bridge_id.replace(' ', '_')}_profile.pdf",
            mime="application/pdf"
        )
