import streamlit as st
from data_loader import load_data, RISK_COL

df = load_data()

st.title("InfraPulse — Bridge Risk Overview")
st.write("A Victorian bridge infrastructure risk assessment and investment prioritization tool.")

st.subheader("High-level Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Bridges", f"{len(df):,}")
col2.metric("Average Risk Score", f"{df[RISK_COL].mean():.1f}")
col3.metric("Highest Risk Score", f"{df[RISK_COL].max():.1f}")

st.divider()
st.page_link("pages/dashboard.py", label="Go to Dashboard to explore the map and data", icon="🗺️")
