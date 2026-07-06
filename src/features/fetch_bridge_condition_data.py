"""
fetch_bridge_condition_data.py
InfraPulse — Condition Rating Feature Builder

WHY THIS SCRIPT EXISTS / WHAT CHANGED
--------------------------------------
The originally-planned source (VicRoads legacy "Bridge Structures" dataset,
BRIDGE_RATING field, discover.data.vic.gov.au/dataset/bridge-structures2)
is dead -- its CSV/GeoJSON/Esri resources all return "not available" as of
July 2026. Confirmed independently (both a direct fetch and a search of the
resource page show the download endpoint is down).

Replacement source: **Vicmap Transport**, the Victorian government's live,
authoritative statewide transport GIS layer, updated weekly (last edit
observed: 2026-07-01 -- i.e. current, not a 2020 snapshot like the dead
dataset was). It's served as a public ArcGIS FeatureServer:

  https://services-ap1.arcgis.com/P744lA0wf4LlBZ84/ArcGIS/rest/services/Vicmap_Transport/FeatureServer/0

Layer 0 ("Road Infrastructure") is a single point layer covering bridges,
tunnels, barriers, gates, fords, level crossings, roundabouts, and more, all
distinguished by a `feature_type_code` field. Filtering to
`feature_type_code = 'bridge'` gets you just the bridges, with a
`physical_condition` field -- your condition-rating target variable -- plus
`construction_type`, `structure_type`, `load_limit`, `load_limit_assess_date`,
`construction_material`, `length_m`, `width_m`, `deck_area`.

DATASET PAGE (metadata, not the API itself):
  discover.data.vic.gov.au/dataset/vicmap-transport-rest-api

JOIN STRATEGY -- SPATIAL, NOT KEY-BASED
------------------------------------------
This layer identifies bridges by `ufi`/`pfi` (Vicmap's own feature IDs), not
by the `SN####` structure number your registry uses. Both datasets are
independently-maintained authoritative government sources describing the
same physical bridges, so a nearest-point spatial join should line up very
closely -- use a **tight** tolerance (default 50m) since these aren't two
different sensor networks, they're two descriptions of the same object.
Anything not matched within that tolerance is left null, same pattern as
the traffic/weather scripts.

PAGINATION
----------
The server caps each request at 2000 records (`maxRecordCount`). This script
pages through with `resultOffset` until a page comes back with fewer
records than requested.

CONDITION CODE DECODING
------------------------
`physical_condition` is a coded single-character field. This script prints
the field's `domain.codedValues` (fetched from the layer's own metadata) on
first run so you can see the actual code -> meaning mapping live, rather
than trusting a guessed table -- Esri layers usually embed this domain
directly in the layer JSON.

OUTPUT
------
bridge_condition_features.csv, one row per bridge Name (SN####):
  Name, dist_to_vicmap_bridge_m, physical_condition, construction_type,
  structure_type, load_limit, load_limit_assess_date,
  construction_material, length_m, width_m, deck_area

USAGE
-----
    pip install requests pandas numpy
    python fetch_bridge_condition_data.py \
        --bridges bridges_master.csv \
        --output bridge_condition_features.csv \
        --threshold-m 50
"""

import argparse
import sys
import numpy as np
import pandas as pd
import requests

LAYER_URL = "https://services-ap1.arcgis.com/P744lA0wf4LlBZ84/ArcGIS/rest/services/Vicmap_Transport/FeatureServer/0"
PAGE_SIZE = 2000
EARTH_RADIUS_M = 6371000

OUT_FIELDS = [
    "ufi", "pfi", "name", "physical_condition", "construction_type",
    "structure_type", "load_limit", "load_limit_assess_date",
    "construction_material", "length_m", "width_m", "deck_area",
]


def haversine_m(lat1, lon1, lat2, lon2):
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(a))


def print_condition_code_meanings():
    """Fetch the layer's field metadata and print the physical_condition
    domain (code -> human-readable meaning), so codes aren't guessed."""
    try:
        resp = requests.get(f"{LAYER_URL}", params={"f": "json"}, timeout=30)
        resp.raise_for_status()
        fields = resp.json().get("fields", [])
        for f in fields:
            if f.get("name") == "physical_condition" and f.get("domain"):
                print("physical_condition code meanings:")
                for cv in f["domain"].get("codedValues", []):
                    print(f"  {cv['code']} -> {cv['name']}")
                return
        print("Could not find a domain for physical_condition -- check codes manually.")
    except Exception as e:
        print(f"Warning: couldn't fetch field metadata ({e}). Proceeding anyway.", file=sys.stderr)


def fetch_all_bridges():
    """Paginate through the FeatureServer, filtered to bridges only,
    reprojected to WGS84 (lat/long) directly by the server."""
    all_rows = []
    offset = 0
    while True:
        params = {
            "where": "feature_type_code='bridge'",
            "outFields": ",".join(OUT_FIELDS),
            "outSR": 4326,
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
            "returnGeometry": "true",
        }
        resp = requests.get(f"{LAYER_URL}/query", params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            sys.exit(f"API error: {data['error']}")

        features = data.get("features", [])
        print(f"  fetched {len(features)} records at offset {offset}")
        for feat in features:
            attrs = feat.get("attributes", {})
            geom = feat.get("geometry", {})
            row = dict(attrs)
            row["vicmap_lon"] = geom.get("x")
            row["vicmap_lat"] = geom.get("y")
            all_rows.append(row)

        if len(features) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return pd.DataFrame(all_rows)


def spatial_join(bridges, vicmap_bridges, threshold_m):
    vicmap_bridges = vicmap_bridges.dropna(subset=["vicmap_lat", "vicmap_lon"]).reset_index(drop=True)

    blat = bridges["LAT"].values
    blon = bridges["LONGIT"].values
    vlat = vicmap_bridges["vicmap_lat"].values
    vlon = vicmap_bridges["vicmap_lon"].values

    best_dist = np.full(len(bridges), np.inf)
    best_idx = np.full(len(bridges), -1)

    for j in range(len(vicmap_bridges)):
        d = haversine_m(blat, blon, vlat[j], vlon[j])
        closer = d < best_dist
        best_dist[closer] = d[closer]
        best_idx[closer] = j

    bridges = bridges.copy()
    bridges["dist_to_vicmap_bridge_m"] = np.round(best_dist, 1)
    matched = best_dist <= threshold_m

    out_fields_no_geom = [f for f in OUT_FIELDS if f not in ("name",)]
    matched_rows = vicmap_bridges.iloc[np.where(best_idx >= 0, best_idx, 0)].reset_index(drop=True)
    for col in out_fields_no_geom:
        bridges[col] = pd.Series([None] * len(bridges), dtype=object)
        bridges.loc[matched, col] = matched_rows.loc[matched, col].values

    return bridges


def main():
    ap = argparse.ArgumentParser(description="Fetch bridge condition ratings from Vicmap Transport and join onto bridges.")
    ap.add_argument("--bridges", required=True, help="CSV with at least Name, LAT, LONGIT")
    ap.add_argument("--output", default="bridge_condition_features.csv")
    ap.add_argument("--threshold-m", type=float, default=50.0, help="Max distance (m) to accept a match")
    args = ap.parse_args()

    print_condition_code_meanings()

    bridges = pd.read_csv(args.bridges).dropna(subset=["LAT", "LONGIT"]).copy()

    print("\nFetching bridge condition records from Vicmap Transport (paginated)...")
    vicmap_bridges = fetch_all_bridges()
    print(f"\nTotal Vicmap bridge records: {len(vicmap_bridges)}")

    result = spatial_join(bridges, vicmap_bridges, args.threshold_m)

    matched_n = result["physical_condition"].notna().sum()
    print(f"\n{matched_n}/{len(result)} bridges matched within {args.threshold_m:.0f}m "
          f"({100*matched_n/len(result):.1f}%)")

    out_cols = ["Name", "dist_to_vicmap_bridge_m"] + [f for f in OUT_FIELDS if f != "name"]
    result[out_cols].to_csv(args.output, index=False)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()