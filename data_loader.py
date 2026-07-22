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

PRIORITY_CUTOFF_1 = 70
PRIORITY_CUTOFF_2 = 40

PRIORITY_1_LABEL = "Priority 1 – Annual/biannual"
PRIORITY_2_LABEL = "Priority 2 – 3–5 year cycle"
PRIORITY_3_LABEL = "Priority 3 – As-needed"

def assign_inspection_priority(risk_score: float) -> str:
    if pd.isna(risk_score):
        return "Unknown"
    if risk_score >= PRIORITY_CUTOFF_1:
        return PRIORITY_1_LABEL
    elif risk_score >= PRIORITY_CUTOFF_2:
        return PRIORITY_2_LABEL
    else:
        return PRIORITY_3_LABEL

@st.cache_data
def load_data(path: str = CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    if RISK_COL in df.columns:
        df['risk_tier'] = pd.cut(
            df[RISK_COL],
            bins=TIER_BINS,
            labels=TIER_LABELS,
            include_lowest=True
        )
        df['inspection_priority'] = df[RISK_COL].apply(assign_inspection_priority)
        
    # Join flood history
    flood_csv_path = ROOT_DIR / "data" / "reference" / "flood_affected_2022_municipalities.csv"
    if flood_csv_path.exists():
        flood_df = pd.read_csv(str(flood_csv_path))
        df = df.merge(flood_df[['REGION_PHYS', 'flood_affected_2022']], on='REGION_PHYS', how='left')
        df['flood_affected_2022'] = df['flood_affected_2022'].fillna(False)
    else:
        df['flood_affected_2022'] = False
        
    return df
