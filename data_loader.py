import pandas as pd
import streamlit as st
from pathlib import Path

# --- CONFIG ---
ROOT_DIR = Path(__file__).parent
CSV_PATH = str(ROOT_DIR / "data" / "processed" / "bridges_risk_scored.csv")
ID_COL = "Name"
RISK_COL = "risk_score"
REGION_COL = "REGION_PHYS"
STATE_CLASS_COL = "CD_STATE_CLASS"
LAT_COL = "LAT"
LON_COL = "LONGIT"

TIER_BINS = [0, 40, 60, 80, 100.01]
TIER_LABELS = ["Low", "Medium", "High", "Critical"]
TIER_COLORS = {
    "Low": "green",
    "Medium": "orange",
    "High": "red",
    "Critical": "darkred"
}

@st.cache_data
def load_data(path: str = CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    if RISK_COL in df.columns:
        df['risk_tier'] = pd.cut(
            df[RISK_COL],
            bins=TIER_BINS,
            labels=TIER_LABELS,
            include_lowest=True
        )
    return df
