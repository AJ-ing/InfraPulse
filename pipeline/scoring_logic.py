import pandas as pd
import numpy as np

def min_max_scale(series):
    # Min-max scale a pandas Series (ignores NA)
    min_val = series.min()
    max_val = series.max()
    if max_val > min_val:
        return (series - min_val) / (max_val - min_val)
    return series.fillna(0.0)

def apply_risk_scoring(df, w_age=0.45, w_traffic=0.30, w_climate=0.25):
    """
    Computes risk_score dynamically given a dataframe that already contains:
    - age_risk (or age_risk_raw)
    - traffic_risk (or traffic_risk_raw)
    - climate_risk (or climate_risk_raw)
    - CD_STATE_CLASS
    """
    # Create a copy so we don't mutate the original dataframe
    df = df.copy()
    
    # 1. Map columns if needed
    if 'age_risk_raw' in df.columns and 'age_risk' not in df.columns:
        df['age_risk'] = df['age_risk_raw']
    if 'traffic_risk_raw' in df.columns and 'traffic_risk' not in df.columns:
        df['traffic_risk'] = df['traffic_risk_raw']
    if 'climate_risk_raw' in df.columns and 'climate_risk' not in df.columns:
        df['climate_risk'] = df['climate_risk_raw']

    # 2. Dynamic Likelihood Weighting
    age_valid = df['age_risk'].notna()
    traffic_valid = df['traffic_risk'].notna()
    climate_valid = df['climate_risk'].notna()

    total_weight = (
        age_valid.astype(float) * w_age +
        traffic_valid.astype(float) * w_traffic +
        climate_valid.astype(float) * w_climate
    )

    score = (
        df['age_risk'].fillna(0) * (age_valid.astype(float) * w_age) +
        df['traffic_risk'].fillna(0) * (traffic_valid.astype(float) * w_traffic) +
        df['climate_risk'].fillna(0) * (climate_valid.astype(float) * w_climate)
    )

    valid_mask = total_weight > 0
    
    # Initialize with np.nan
    df['likelihood_score'] = np.nan
    df.loc[valid_mask, 'likelihood_score'] = score[valid_mask] / total_weight[valid_mask]
    
    # Construct likelihood_components_used strings vectorically
    # To match the original exactly
    def make_components_str(a, t, c):
        res = []
        if a: res.append("age")
        if t: res.append("traffic")
        if c: res.append("climate")
        return ",".join(res) if res else "none_imputed_median"
        
    df['likelihood_components_used'] = [
        make_components_str(a, t, c) 
        for a, t, c in zip(age_valid, traffic_valid, climate_valid)
    ]

    # 3. Consequence Multiplier
    mapping = {'HF': 1.5, 'MR': 1.2, 'TR': 1.1, 'RA': 1.0, 'FR': 1.0}
    df['consequence_multiplier'] = df['CD_STATE_CLASS'].astype(str).str.strip().map(mapping).fillna(1.0)

    # 4. Raw Risk Score
    # We must explicitly force float type to avoid type issues with pd.NA
    df['raw_risk_score'] = df['likelihood_score'].astype(float) * df['consequence_multiplier'] * 100

    # 5. Impute Medians for Missing Coordinates
    # Calculate median on the valid raw scores
    median_score = df['raw_risk_score'].median()

    # Fill NA raw scores with median
    df['raw_risk_score'] = df['raw_risk_score'].fillna(median_score).infer_objects(copy=False)

    # 6. Min-Max Rescale to 0-100
    rescaled = min_max_scale(df['raw_risk_score']) * 100
    df['risk_score'] = rescaled.round(1)
    
    return df
