# Data Notes & Findings

## Timber / Material Flag (Tier 1 Extension - Day 4)

An investigation was conducted into the feasibility of adding a `timber` or `material_type` flag to the dashboard to highlight timber bridges, which are historically prone to poor condition.

**Findings:**
- `construction_material`: The column exists in the raw `bridges_master.csv` but is 100% empty (NaN) across all 6,554 records.
- `structure_type`: Also 100% empty.
- `construction_type`: Missing for 75% of the records. The remaining 25% use opaque integer codes (e.g., `11.0`, `4.0`, `1.0`) with no provided data dictionary.

**Conclusion:**
There is no reliable material field currently available in the Transport Victoria registry dataset provided. We cannot safely infer or impute material type (e.g., timber vs. concrete) without an authoritative source. This feature is parked for future scope pending the availability of better structural metadata.
