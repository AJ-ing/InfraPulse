import pandas as pd
import argparse
import sys
import datetime

def min_max_scale(series):
    # Min-max scale a pandas Series (ignores NA)
    min_val = series.min()
    max_val = series.max()
    if max_val > min_val:
        return (series - min_val) / (max_val - min_val)
    return series.fillna(0.0)

def main():
    parser = argparse.ArgumentParser(description="Compute risk scores for bridges.")
    parser.add_argument("--input", default="data/processed/bridges_master.csv")
    parser.add_argument("--output", default="data/processed/bridges_risk_scored.csv")
    parser.add_argument("--year", type=int, default=datetime.datetime.now().year)
    args = parser.parse_args()

    print(f"Reading {args.input}...")
    df = pd.read_csv(args.input, low_memory=False)

    # 1. Component calculations
    # Age Risk
    if 'year_constructed_clean' in df.columns:
        df['age'] = args.year - df['year_constructed_clean']
        df['age_risk_raw'] = min_max_scale(df['age'])
    else:
        df['age_risk_raw'] = pd.NA

    # Traffic Risk
    if 'avg_daily_volume' in df.columns and 'pct_heavy_vehicles' in df.columns:
        v_scaled = min_max_scale(df['avg_daily_volume'])
        h_scaled = min_max_scale(df['pct_heavy_vehicles'])
        df['traffic_risk_raw'] = (v_scaled + h_scaled) / 2.0
    else:
        df['traffic_risk_raw'] = pd.NA

    # Climate Risk
    if 'extreme_rainfall_days_per_year' in df.columns and 'hot_days_per_year' in df.columns:
        r_scaled = min_max_scale(df['extreme_rainfall_days_per_year'])
        t_scaled = min_max_scale(df['hot_days_per_year'])
        df['climate_risk_raw'] = (r_scaled + t_scaled) / 2.0
    else:
        df['climate_risk_raw'] = pd.NA

    # Output components for transparency
    df['age_risk'] = df['age_risk_raw']
    df['traffic_risk'] = df['traffic_risk_raw']
    df['climate_risk'] = df['climate_risk_raw']

    # Apply shared risk scoring logic
    from scoring_logic import apply_risk_scoring
    df = apply_risk_scoring(df)

    # Cleanup temporary columns
    df.drop(columns=['age', 'age_risk_raw', 'traffic_risk_raw', 'climate_risk_raw', 'raw_risk_score'], inplace=True, errors='ignore')

    # Output specific columns first, then the rest
    out_cols_prefix = [
        'Name', 'risk_score', 'likelihood_score', 'consequence_multiplier',
        'age_risk', 'traffic_risk', 'climate_risk', 'likelihood_components_used'
    ]
    
    # Ensure physical_condition and construction_type are included if present
    # But just keeping all original columns minus what was dropped is fine
    out_cols_rest = [c for c in df.columns if c not in out_cols_prefix]
    out_cols = out_cols_prefix + out_cols_rest
    
    df = df[out_cols]
    
    print(f"Writing scored data to {args.output}...")
    df.to_csv(args.output, index=False)
    
    # Summary
    print("\n--- RISK SCORE SUMMARY ---")
    print(f"Total bridges scored: {len(df)}")
    print(df['risk_score'].describe())
    print("\nLikelihood components used:")
    print(df['likelihood_components_used'].value_counts())

if __name__ == "__main__":
    main()
