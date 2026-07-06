import argparse
import pandas as pd
from datetime import datetime, timedelta
import sys

def parse_year(val):
    if pd.isna(val):
        return pd.NA, "unknown"
    
    val_str = str(val).strip()
    
    if val_str in ("0", "NULL", "nan", "", "None"):
        return pd.NA, "unknown"
        
    try:
        date = datetime.strptime(val_str, "%d/%m/%Y")
        return date.year, "date_string"
    except ValueError:
        pass
        
    try:
        date = datetime.strptime(val_str, "%Y-%m-%d")
        return date.year, "date_string"
    except ValueError:
        pass
        
    # Treat all-numeric as Excel serial (days since 1899-12-30)
    if val_str.replace('.', '', 1).isdigit():
        try:
            days = int(float(val_str))
            epoch = datetime(1899, 12, 30)
            date = epoch + timedelta(days=days)
            return date.year, "excel_serial"
        except Exception:
            pass
            
    return pd.NA, "unknown"

def main():
    parser = argparse.ArgumentParser(description="Build bridges master dataset.")
    parser.add_argument("--input", default="data/raw/bridge_dataset_raw.csv", help="Path to raw dataset")
    parser.add_argument("--output", default="bridges_master.csv", help="Path to output master dataset")
    args = parser.parse_args()

    print(f"Reading {args.input}...")
    df = pd.read_csv(args.input, low_memory=False)
    
    initial_rows = len(df)
    
    # 5. Check for duplicate Name values
    if df['Name'].duplicated().any():
        dups = df[df['Name'].duplicated()]['Name'].tolist()
        print(f"ERROR: Found {len(dups)} duplicate 'Name' values, e.g. {dups[:5]}.", file=sys.stderr)
        sys.exit(1)
        
    # 1. YEAR_CONSTRUCTED parsing
    print("Parsing YEAR_CONSTRUCTED...")
    parsed = df['YEAR_CONSTRUCTED'].apply(parse_year)
    df['year_constructed_clean'] = [x[0] for x in parsed]
    df['year_constructed_source'] = [x[1] for x in parsed]
    df['year_constructed_clean'] = df['year_constructed_clean'].astype('Int64')
    
    # Sanity-check parsed years
    valid_years = df['year_constructed_clean'].dropna()
    out_of_bounds = valid_years[(valid_years < 1850) | (valid_years > 2026)]
    if not out_of_bounds.empty:
        print("\nWARNING: Parsed years outside 1850-2026 range found for the following rows:", file=sys.stderr)
        print(df.loc[out_of_bounds.index, ['Name', 'YEAR_CONSTRUCTED', 'year_constructed_clean']], file=sys.stderr)
        print("\n", file=sys.stderr)

    # 2. Missing coordinates
    df['has_coordinates'] = df['LAT'].notna() & df['LONGIT'].notna()
    
    # 3. Correlated nulls
    df['road_classification_unknown'] = df['CD_STATE_CLASS'].isna() & df['NM_ROAD_PART'].isna() & df['NM_ROAD_TYPE'].isna()
    
    # 4. STRUCTURE_STATUS rule
    df['is_active_asset'] = df['STRUCTURE_STATUS'].isin(['Structure Open', 'Open', 'Under Construction'])
    
    # Save output
    print(f"Writing {args.output}...")
    df.to_csv(args.output, index=False)
    
    # Output Requirements Summary
    print("\n--- DATA QUALITY SUMMARY ---")
    print(f"Total rows: {len(df)} (Original: {initial_rows})")
    
    print("\nNull counts per column:")
    print(df.isna().sum())
    
    print("\n'year_constructed_source' value counts:")
    print(df['year_constructed_source'].value_counts(dropna=False))
    
    print("\n'is_active_asset' breakdowns:")
    print(df['is_active_asset'].value_counts(dropna=False))
    
    print("\n'has_coordinates' breakdowns:")
    print(df['has_coordinates'].value_counts(dropna=False))
    
    print("\n'road_classification_unknown' breakdowns:")
    print(df['road_classification_unknown'].value_counts(dropna=False))

if __name__ == "__main__":
    main()
