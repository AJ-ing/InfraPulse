

"""
fetch_bridge_weather_data.py
InfraPulse — Weather / Climate Exposure Feature Builder
 
PURPOSE
-------
Attaches a long-term climate exposure feature set to each bridge, using
lat/long from the bridge registry. This is used as one input into the
multi-criteria risk formula (alongside condition and traffic exposure) —
NOT matched to any specific date, since this is a static "how exposed is
this location, over time" feature, not a real-time weather feed.
 
DATA SOURCE
-----------
Open-Meteo Historical Weather API (ERA5-Land reanalysis, ~9km grid,
gap-free back to 1950). Free, no API key required for non-commercial use.
Docs: https://open-meteo.com/en/docs/historical-weather-api
 
WHY GRID-DEDUPLICATED, NOT ONE CALL PER BRIDGE
------------------------------------------------
ERA5-Land's native resolution is ~0.1 degrees (~9-11km). Calling the API
once per bridge (6,554 calls) would just re-fetch identical data for
bridges that are a few hundred metres apart. Instead we round each
bridge's coordinates to a 0.1-degree grid cell, fetch weather once per
UNIQUE cell, then map every bridge back to its cell. Over Victoria this
typically collapses ~6,500 bridges down to a few hundred unique cells.
 
OUTPUT
------
bridge_weather_features.csv with one row per bridge Name (SN####),
ready to left-join onto bridges_master.csv on `Name`.
 
USAGE
-----
    pip install requests pandas
    python fetch_bridge_weather_data.py \
        --input bridges_master.csv \
        --output bridge_weather_features.csv \
        --start 2015-01-01 --end 2024-12-31
 
Run this on your own machine (not in a sandboxed environment) since it
needs live internet access to archive-api.open-meteo.com.
"""
 
import argparse
import time
import sys
import requests
import pandas as pd
 
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
GRID_SIZE = 0.25         # degrees (~25km). Coarser than ERA5-Land's native
                          # ~0.1deg cell, but you're aggregating to annual
                          # stats anyway, and it cuts ~6,500 bridges down to
                          # ~320 unique API calls (~5-6 min at 1 req/sec)
                          # instead of ~1,100 (~18 min). Use 0.1 if you want
                          # finer spatial precision and don't mind the wait.
HEAVY_RAIN_MM = 40        # daily rainfall threshold counted as "extreme"
HOT_DAY_C = 35            # daily max temp threshold counted as "hot day"
REQUEST_SLEEP_SEC = 1.5    # be polite to the free API
MAX_RETRIES = 5
 
 
def round_to_grid(lat, lon, grid=GRID_SIZE):
    return round(lat / grid) * grid, round(lon / grid) * grid
 
 
def fetch_weather_for_cell(lat, lon, start_date, end_date):
    """Fetch daily precipitation + temperature for one grid cell.
    Returns a dict of derived features, or None on failure."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
        "timezone": "Australia/Sydney",
    }
 
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            if attempt == MAX_RETRIES:
                print(f"  FAILED for ({lat}, {lon}): {e}", file=sys.stderr)
                return None
            time.sleep(5 * attempt)
    else:
        return None
 
    daily = data.get("daily", {})
    precip = pd.Series(daily.get("precipitation_sum", []), dtype="float64")
    tmax = pd.Series(daily.get("temperature_2m_max", []), dtype="float64")
    tmin = pd.Series(daily.get("temperature_2m_min", []), dtype="float64")
 
    if precip.empty:
        return None
 
    n_years = len(precip) / 365.25
 
    return {
        "grid_lat": lat,
        "grid_lon": lon,
        "avg_annual_rainfall_mm": round(precip.sum() / n_years, 1),
        "extreme_rainfall_days_per_year": round((precip > HEAVY_RAIN_MM).sum() / n_years, 2),
        "mean_max_temp_c": round(tmax.mean(), 1),
        "mean_min_temp_c": round(tmin.mean(), 1),
        "hot_days_per_year": round((tmax > HOT_DAY_C).sum() / n_years, 2),
    }
 
 
def main():
    ap = argparse.ArgumentParser(description="Fetch climate exposure features for bridge locations.")
    ap.add_argument("--input", required=True, help="CSV with at least Name, LAT, LONGIT columns")
    ap.add_argument("--output", default="bridge_weather_features.csv")
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default="2024-12-31")
    args = ap.parse_args()
 
    df = pd.read_csv(args.input)
    for col in ("Name", "LAT", "LONGIT"):
        if col not in df.columns:
            sys.exit(f"Input file is missing required column: {col}")
 
    df = df.dropna(subset=["LAT", "LONGIT"]).copy()
    # Keep only necessary columns to avoid merge suffixing if running on an already-merged file
    df = df[["Name", "LAT", "LONGIT"]]
    df["grid_lat"], df["grid_lon"] = zip(*df.apply(
        lambda r: round_to_grid(r["LAT"], r["LONGIT"]), axis=1
    ))
 
    unique_cells = df[["grid_lat", "grid_lon"]].drop_duplicates().reset_index(drop=True)
    print(f"{len(df)} bridges -> {len(unique_cells)} unique grid cells to fetch.")
 
    cell_features = []
    for i, row in unique_cells.iterrows():
        print(f"[{i+1}/{len(unique_cells)}] fetching ({row.grid_lat}, {row.grid_lon})...")
        feat = fetch_weather_for_cell(row.grid_lat, row.grid_lon, args.start, args.end)
        if feat is not None:
            cell_features.append(feat)
        time.sleep(REQUEST_SLEEP_SEC)
 
    cell_df = pd.DataFrame(cell_features)
    if cell_df.empty:
        sys.exit("No weather data was successfully fetched. Check your internet connection.")
 
    merged = df.merge(cell_df, on=["grid_lat", "grid_lon"], how="left")
    out_cols = [
        "Name", "grid_lat", "grid_lon", "avg_annual_rainfall_mm",
        "extreme_rainfall_days_per_year", "mean_max_temp_c",
        "mean_min_temp_c", "hot_days_per_year",
    ]
    merged[out_cols].to_csv(args.output, index=False)
 
    missing = merged["avg_annual_rainfall_mm"].isna().sum()
    print(f"\nDone. Wrote {args.output} ({len(merged)} bridges, {missing} unmatched).")
 
 
if __name__ == "__main__":
    main()
 
