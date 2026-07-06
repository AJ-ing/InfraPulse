import pandas as pd
import argparse
import sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="data/processed/bridges_master.csv")
    ap.add_argument("--condition", default="bridge_condition_features.csv")
    ap.add_argument("--traffic", default="bridge_traffic_features.csv")
    ap.add_argument("--weather", default="bridge_weather_features.csv")
    ap.add_argument("--output", default="data/processed/bridges_master_merged.csv")
    args = ap.parse_args()

    print(f"Reading master {args.master}...")
    try:
        df = pd.read_csv(args.master, low_memory=False)
    except FileNotFoundError:
        sys.exit(f"Error: Could not find {args.master}")
    
    for feat_file in [args.condition, args.traffic, args.weather]:
        print(f"Merging {feat_file}...")
        try:
            feat_df = pd.read_csv(feat_file, low_memory=False)
        except FileNotFoundError:
            print(f"Warning: {feat_file} not found. Skipping...", file=sys.stderr)
            continue
            
        if 'Name' not in feat_df.columns:
            sys.exit(f"Error: 'Name' column missing in {feat_file}")
        
        # Drop these feature columns from master if they already exist, so we can overwrite them
        cols_to_drop = [c for c in feat_df.columns if c in df.columns and c != 'Name']
        df = df.drop(columns=cols_to_drop)
        
        df = df.merge(feat_df, on="Name", how="left")

    print(f"Writing merged data to {args.output}...")
    df.to_csv(args.output, index=False)
    print(f"Done. Final shape: {df.shape}")

if __name__ == "__main__":
    main()
