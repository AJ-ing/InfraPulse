# InfraPulse — Tier 1 Extension: Week Plan & Antigravity Build Prompts

**Scope:** Post-capstone extensions that stay inside the current architecture (batch pipeline → flat CSV → read-only Streamlit dashboard). No ML, no API, no auth, no cloud added in this tier.

**Ground rule for every step below:** the risk score stays a transparent rule-based formula. Nothing in Tier 1 changes that framing, and no prompt should ever ask Antigravity to describe any part of this as "AI," "prediction," or "model output."

**Working pattern:** one slice validated before starting the next — same as the rest of the build. Each day ends in a state you could stop at and still have something working.

---

## Week-at-a-glance

| Day | Feature | Touches scoring formula? | Needs new data? |
|---|---|---|---|
| 1 | Regression test suite + CI | No | No |
| 2 | Inspection-priority output | No (pure derived label) | No |
| 3 | Adjustable weight sandbox | Interactive only, not persisted | No |
| 4 | Timber/material flag | No (display/filter only) | Investigate first |
| 5 | Regional flood-history flag (Oct 2022) | No (display/filter only) | Yes — static reference list |
| 6 | Per-bridge / per-region PDF export | No | No |
| 7 | Integration, docs, redeploy | — | — |

Day 4 and Day 5 both start with a data-availability check. If either comes back empty, skip the implementation half and just keep the documented finding — don't force a flag onto data that doesn't support it.

---

## Day 1 — Regression Safety Net (Test Suite + CI)
## Day 2 — Inspection-Priority Output
## Day 3 — Adjustable Weight Sandbox
## Day 4 — Timber/Material Flag (Investigate → Implement if Available)
## Day 5 — Regional Flood-History Flag (Oct 2022)
## Day 6 — Per-Bridge / Per-Region PDF Export
## Day 7 — Integration, Docs, Redeploy
