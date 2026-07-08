"""
InfraPulse — Home / overview page.
Single screen: problem statement, three headline stats, link to the dashboard.
"""

import streamlit as st

from data_loader import RISK_COL, load_data

df = load_data()

st.title("InfraPulse")
st.subheader("Infrastructure Asset Risk and Investment Decision Support")

st.write(
    "Victoria's own 2011 Auditor-General review found that maintenance funding for "
    "road bridges was running at roughly half of annual depreciation, even as over "
    "half the network entered its highest-risk repair window. InfraPulse scores and "
    "ranks 6,554 Victorian bridges by risk — using age, traffic, and climate signals "
    "rather than condition ratings the sector's own auditor has repeatedly found "
    "unreliable — to support maintenance and investment prioritisation decisions."
)

col1, col2, col3 = st.columns(3)
col1.metric("Bridges scored", f"{len(df):,}")
col2.metric("Average risk score", f"{df[RISK_COL].mean():.1f}")
col3.metric("Highest risk score", f"{df[RISK_COL].max():.1f}")

st.divider()
st.page_link("pages/dashboard.py", label="Launch dashboard", icon=":material/monitoring:")
st.page_link("pages/methodology.py", label="Read the methodology", icon=":material/description:")
