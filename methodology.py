"""
InfraPulse — Methodology page.
Documents the real data sources, the risk-scoring formula, and why the project
pivoted away from condition-based modelling. Content sourced from the project's
research briefing (VAGO 2011 and related citations) — see Sources section.
"""

import streamlit as st

st.title("Methodology")

st.write(
    "This page documents the real engineering decisions behind InfraPulse's "
    "risk score — including the parts that didn't go as planned."
)

st.header("Data sources")
st.markdown(
    """
- **Bridge registry** — Transport Victoria open data portal, 6,554 bridges after
  cleaning, including a parsing fix for 61 ISO-timestamp construction years
  (1856–1898) that had been misclassified as unknown.
- **Weather** — Open-Meteo Historical Weather API, grid-deduplicated at 0.25°
  resolution to avoid redundant calls for nearby bridges.
- **Traffic** — TIRTL 15-minute sensor data from 406 Melbourne freeway sites, with
  Austroads vehicle classes 3–12 treated as heavy vehicles, spatially joined to the
  nearest bridge within a configurable distance threshold.
- **Condition data** — attempted via three separate sources, all of which failed to
  produce usable data (see *Known limitations* below).
"""
)

st.header("Risk scoring approach")
st.markdown(
    """
The final risk score (0–100, min-max rescaled) is a **rule-based, transparent
multi-criteria formula** — not a trained predictive model:

**Likelihood** = age (45%) + traffic (30%) + climate (25%), reweighted
proportionally when a component is missing for a given bridge.

**Consequence multiplier**, applied to likelihood, based on `CD_STATE_CLASS`:
HF = 1.5, MR = 1.2, TR = 1.1, RA/FR/unknown = 1.0.

This weighting isn't arbitrary. Victoria's 2011 Auditor-General's review found that
52% of VicRoads' bridges and culverts were already in the 30–60-year window where
major repairs are typically needed to reach a 100-year design life — the same audit
found maintenance funding running at roughly half of annual depreciation over the
prior six years. Age is the same forward-looking signal the sector's own auditor
uses, not a convenience variable chosen because better data wasn't available.

The climate feature specifically targets **extreme short-duration rainfall days**
rather than total rainfall, because Victoria's average rainfall has been declining
over the past 50 years even as extreme rainfall intensity has been rising — the two
trends point in opposite directions, so a simple total-rainfall metric would have
missed the actual flood/scour risk signal.

The road-class consequence multiplier mirrors a real distinction VicRoads draws
between arterial/freight-carrying structures and local ones, reflecting roughly a
41% increase in the weight of goods carried by road over the decade to 2011.
"""
)

st.header("Known limitations")
st.markdown(
    """
The original design used physical condition ratings as a model input. That plan
was abandoned after three separate attempts to source usable condition data:

1. The legacy VicRoads "Bridge Structures" dataset was confirmed dead.
2. The Vicmap Transport ArcGIS FeatureServer's `physical_condition` field returned
   near-zero variance — almost every bridge rated identically.
3. An AURIN portal download intended for Victoria's condition data returned Western
   Australia's dataset instead.

This isn't a one-off data-sourcing failure specific to this project. The 2011
Victorian Auditor-General's audit of VicRoads and five councils found condition
data was inconsistent, stale, and incompatible even within Victoria alone — one
council's rating scale used four points, others used ten; one council's detailed
condition assessments were six years overdue; and in one documented case (Kirwans
Bridge, Strathbogie Shire), a 2009 condition rating was directly contradicted by a
2010 detailed investigation on the very same structure. Condition ratings, as
published across the sector, are demonstrably unreliable — not just in the specific
datasets this project tried.

**`physical_condition` is retained in the dataset as a reference column only and
does not feed the risk formula.**

Given that, the pivot to a rule-based score built on age, traffic, and climate —
all objective, consistently available, and independently identified by the
sector's own auditor as leading risk indicators — is a defensible methodological
choice, not a fallback forced by missing data.
"""
)

st.header("Sources")
st.caption(
    "Victorian Auditor-General's Office (2011), *Management of Road Bridges*, and "
    "related sources. Full citation list available in the project's research "
    "briefing document."
)
