"""
build_bridge_traffic_features.py
InfraPulse — Traffic Exposure Feature Builder

PURPOSE
-------
Turns the raw TIRTL 15-minute sensor data into a per-bridge traffic
exposure feature: average daily volume + heavy-vehicle volume/percentage,
matched to the nearest bridge within a distance threshold.

WHY A DISTANCE THRESHOLD, NOT A KEY-BASED JOIN
------------------------------------------------
TIRTL sites have no bridge ID -- they're independent sensor locations.
A nearest-neighbour spatial join is the only option. Coverage is real but
limited: TIRTL is a Melbourne-freeway-biased sensor network (M1, M80,
Tullamarine Fwy, Hume Fwy, etc), not a statewide one. At a 500m threshold,
expect only a small fraction of the ~6,554 bridges to get a direct match
(most of the rest are on local/rural roads with no nearby sensor). This
is expected, not a bug -- see the "NM_ROAD_TYPE fallback" note below.

VEHICLE CLASS CODES (Austroads Level 3, per data.vic.gov.au data
dictionary for this dataset)
------------------------------------------------------------------
  0  Motorcycles                                        }
  1  Short vehicle                                       }  LIGHT
  2  Short vehicle towing                                }
  14 Bicycles                                            }
  3  Two axle rigid truck or bus                         }
  4  Three axle rigid truck or bus                       }
  5  >3 axle rigid truck, bus or crane                   }
  6  Three axle articulated/rigid + trailer               }  HEAVY
  7  Four axle articulated/rigid + trailer                }  (this is
  8  Five axle articulated/rigid + trailer                }  the bridge-
  9  Six+ axle articulated/rigid + trailer                }  loading
  10 B-double or heavy truck trailer                      }  signal)
  11 Double road train or heavy truck + trailers          }
  12 Triple road train or heavy truck + 3 trailers        }
  13 Error -- excluded entirely (~0.005% of volume, checked on a sample day)

OUTPUT
------
bridge_traffic_features.csv, one row per bridge Name (SN####):
  Name, matched_site, dist_to_site_m,
  avg_daily_volume, avg_daily_heavy_volume, pct_heavy_vehicles

Bridges with no site within the threshold get nulls in the traffic
columns -- for those, fall back to NM_ROAD_TYPE / CD_STATE_CLASS
(highway/arterial/local) as a coarse traffic-exposure proxy in the risk
formula, since that's already in bridges_master.csv.

USAGE
-----
    python build_bridge_traffic_features.py \
        --bridges bridges_master.csv \
        --sites tirtl_sites.csv \
        --traffic-glob "TIRTLDATA_2026*.csv" \
        --output bridge_traffic_features.csv \
        --threshold-m 500
"""

import argparse
import glob
import sys
import numpy as np
import pandas as pd

HEAVY_CLASSES = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
ERROR_CLASS = 13
EARTH_RADIUS_M = 6371000


def haversine_m(lat1, lon1, lat2, lon2):
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(a))


def load_and_aggregate_traffic(traffic_glob):
    """Reads every matching daily CSV, sums volume per (date, site),
    splitting heavy vs all vehicles, then averages across days per site."""
    files = sorted(glob.glob(traffic_glob))
    if not files:
        sys.exit(f"No files matched glob: {traffic_glob}")
    print(f"Found {len(files)} traffic file(s): {files[0]} ... {files[-1]}")

    daily_rows = []
    for f in files:
        chunk = pd.read_csv(f)
        chunk = chunk[chunk["vehicle_class"] != ERROR_CLASS]
        chunk["is_heavy"] = chunk["vehicle_class"].isin(HEAVY_CLASSES)
        agg = chunk.groupby(["date", "site"]).apply(
            lambda g: pd.Series({
                "total_volume": g["volume"].sum(),
                "heavy_volume": g.loc[g["is_heavy"], "volume"].sum(),
            })
        ).reset_index()
        daily_rows.append(agg)
        print(f"  {f}: {agg['site'].nunique()} active sites")

    daily = pd.concat(daily_rows, ignore_index=True)

    # average across all days present, per site (missing days for a site
    # -- e.g. sensor outage -- just don't contribute to that site's mean)
    per_site = daily.groupby("site").agg(
        avg_daily_volume=("total_volume", "mean"),
        avg_daily_heavy_volume=("heavy_volume", "mean"),
        days_observed=("total_volume", "count"),
    ).reset_index()
    per_site["pct_heavy_vehicles"] = round(
        100 * per_site["avg_daily_heavy_volume"] / per_site["avg_daily_volume"], 2
    )
    return per_site


def spatial_join(bridges, sites_with_traffic, threshold_m):
    """For each bridge, find the nearest TIRTL site and keep the match
    only if it's within threshold_m."""
    blat = bridges["LAT"].values
    blon = bridges["LONGIT"].values
    slat = sites_with_traffic["latitude"].values
    slon = sites_with_traffic["longitude"].values

    best_dist = np.full(len(bridges), np.inf)
    best_idx = np.full(len(bridges), -1)

    for j in range(len(sites_with_traffic)):
        d = haversine_m(blat, blon, slat[j], slon[j])
        closer = d < best_dist
        best_dist[closer] = d[closer]
        best_idx[closer] = j

    bridges = bridges.copy()
    bridges["dist_to_site_m"] = np.round(best_dist, 1)
    matched = best_dist <= threshold_m

    for col in ["site", "avg_daily_volume", "avg_daily_heavy_volume", "pct_heavy_vehicles"]:
        bridges[col if col != "site" else "matched_site"] = np.nan

    site_cols = sites_with_traffic.iloc[np.where(best_idx >= 0, best_idx, 0)].reset_index(drop=True)
    for col, out_col in [
        ("site", "matched_site"),
        ("avg_daily_volume", "avg_daily_volume"),
        ("avg_daily_heavy_volume", "avg_daily_heavy_volume"),
        ("pct_heavy_vehicles", "pct_heavy_vehicles"),
    ]:
        bridges.loc[matched, out_col] = site_cols.loc[matched, col].values

    return bridges


def main():
    ap = argparse.ArgumentParser(description="Build per-bridge traffic exposure features from TIRTL data.")
    ap.add_argument("--bridges", required=True, help="CSV with at least Name, LAT, LONGIT")
    ap.add_argument("--sites", required=True, help="TIRTL sites CSV (site, site_description, latitude, longitude)")
    ap.add_argument("--traffic-glob", required=True, help="Glob pattern for daily TIRTLDATA CSVs, e.g. 'TIRTLDATA_2026*.csv'")
    ap.add_argument("--output", default="bridge_traffic_features.csv")
    ap.add_argument("--threshold-m", type=float, default=500.0, help="Max distance (m) to accept a bridge-to-site match")
    args = ap.parse_args()

    bridges = pd.read_csv(args.bridges).dropna(subset=["LAT", "LONGIT"]).copy()
    sites = pd.read_csv(args.sites)

    per_site_traffic = load_and_aggregate_traffic(args.traffic_glob)
    sites_with_traffic = sites.merge(per_site_traffic, on="site", how="inner")
    print(f"\n{len(sites)} TIRTL sites -> {len(sites_with_traffic)} with usable traffic data")

    result = spatial_join(bridges, sites_with_traffic, args.threshold_m)

    matched_n = result["matched_site"].notna().sum()
    print(f"\n{matched_n}/{len(result)} bridges matched to a site within {args.threshold_m:.0f}m "
          f"({100*matched_n/len(result):.1f}%)")

    out_cols = ["Name", "matched_site", "dist_to_site_m",
                "avg_daily_volume", "avg_daily_heavy_volume", "pct_heavy_vehicles"]
    result[out_cols].to_csv(args.output, index=False)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()