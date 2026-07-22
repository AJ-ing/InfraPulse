import streamlit as st

st.set_page_config(page_title="InfraPulse", layout="wide")

pages = {
    "Overview": [
        st.Page("pages/home.py", title="Home", icon="🏠", default=True),
        st.Page("pages/methodology.py", title="Methodology", icon="📚"),
    ],
    "Analytics": [
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/sandbox.py", title="What-If Sandbox", icon="🧪"),
    ]
}

pg = st.navigation(pages)
pg.run()
