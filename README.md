# InfraPulse

**Infrastructure Asset Risk and Investment Decision Support System**

A solo capstone project that scores and ranks 6,554 Victorian road bridges by
risk, to support maintenance and investment prioritisation decisions — the kind
of analysis a road authority or infrastructure consultancy would use to decide
where limited maintenance budget goes first.

**Live demo:** https://infrapulse.streamlit.app/
📖 **[Read the full INFRAPULSE Report](https://drive.google.com/file/d/1jgb1I8K_HdRcNJMNlTotnOt3tq9yNgjM/view?usp=sharing)**


---

## Screenshots

**KPI summary and top-20 ranked table**
![KPI and table](assets/screenshots/01_kpi_and_table.png)

**Risk map, colored by tier**
![Risk map](assets/screenshots/02_risk_map.png)



---

## The problem

Victoria's own 2011 Auditor-General review found that maintenance funding for
road bridges was running at roughly half of annual depreciation, even as over
half the state-managed bridge network was already inside the 30–60-year window
where major repairs are typically needed. Prioritisation decisions have to be
made with imperfect information, on a network of thousands of structures, by a
small number of engineers. InfraPulse is a working model of the kind of tool
that supports that decision — score every bridge consistently, surface the
highest-risk ones, and let filtering narrow the view by region or road class.

## Key features

- **Risk scoring for 6,554 bridges** — a transparent, rule-based multi-criteria
  formula (not a black-box model), so every score can be explained.
- **Interactive risk map** — colored by risk tier, colorblind-safe palette with
  text labels, not color alone.
- **Ranked table** — top-risk bridges surfaced first, filterable.
- **Live filters** — region, road/state class, risk tier, inspection priority, and flood history.
- **Inspection Priority** — maps risk score to standard 3-tier inspection cadences.
- **Interactive Sandbox** — dynamically adjust likelihood weights (Age, Traffic, Climate) to see real-time what-if impacts on the risk scores.
- **PDF Export** — generate and download static reports for the current filtered region view or individual bridge profiles.
- **In-app methodology page** — documents data sources, the scoring formula,
  and — deliberately — the data-quality failures that shaped the design.

## Architecture

```
infrapulse/
├── data/
│   └── processed/
│       └── bridges_risk_scored.csv     # pipeline output; the app's only data source
├── pipeline/                            # batch scoring pipeline, run independently of the app
│   ├── run_pipeline.py
│   ├── features_weather.py             # Open-Meteo historical weather, grid-deduplicated
│   ├── features_traffic.py             # TIRTL sensor data, spatial-joined to nearest bridge
│   ├── features_condition.py           # condition-data sourcing attempts (see Limitations)
│   └── risk_scoring.py                 # the likelihood/consequence formula
├── assets/screenshots/                  # README images
├── pages/
│   ├── home.py                          # overview + headline stats
│   ├── dashboard.py                     # filters, KPIs, map, ranked table
│   └── methodology.py                   # full data-source and scoring writeup
├── docs/
│   ├── infrapulse_vic_briefing.md      # research briefing backing the methodology
│   └── build-prompts/                   # Antigravity build-context prompts, archived
├── streamlit_app.py                     # entrypoint, defines navigation
├── data_loader.py                       # single source of truth for loading + risk tiers
├── .streamlit/config.toml               # theme
└── requirements.txt
```

The architecture is deliberately minimal: a batch pipeline writes a flat CSV,
and a read-only Streamlit dashboard consumes it. No cloud dependency, no
authentication, and no live API calls from the app itself — every number on
screen traces back to a pre-computed file, not a runtime request.

## Data sources

- **Bridge registry** — Transport Victoria open data portal, 6,554 bridges after
  cleaning, including a fix for 61 construction-year values that had been
  misclassified as unknown due to inconsistent date formats.
- **Weather** — Open-Meteo Historical Weather API, grid-deduplicated at 0.25°
  resolution.
- **Traffic** — TIRTL 15-minute sensor data from 406 Melbourne freeway sites,
  Austroads vehicle classes 3–12 treated as heavy vehicles, spatially joined to
  the nearest bridge.
- **Condition data** — attempted via three independent sources; all three
  proved unusable (see *Known limitations*).

## Risk scoring methodology

A transparent, rule-based multi-criteria score (0–100, min-max rescaled) —
explicitly **not** a trained predictive model:

```
Likelihood      = age (45%) + traffic (30%) + climate (25%)
                  reweighted proportionally when a component is missing

The architecture is deliberately minimal: a batch pipeline writes a flat CSV,
and a read-only Streamlit dashboard consumes it. No cloud dependency, no
authentication, and no live API calls from the app itself — every number on
screen traces back to a pre-computed file, not a runtime request.

## Data sources

- **Bridge registry** — Transport Victoria open data portal, 6,554 bridges after
  cleaning, including a fix for 61 construction-year values that had been
  misclassified as unknown due to inconsistent date formats.
- **Weather** — Open-Meteo Historical Weather API, grid-deduplicated at 0.25°
  resolution.
- **Traffic** — TIRTL 15-minute sensor data from 406 Melbourne freeway sites,
  Austroads vehicle classes 3–12 treated as heavy vehicles, spatially joined to
  the nearest bridge.
- **Condition data** — attempted via three independent sources; all three
  proved unusable (see *Known limitations*).

## Risk scoring methodology

A transparent, rule-based multi-criteria score (0–100, min-max rescaled) —
explicitly **not** a trained predictive model:

```
Likelihood      = age (45%) + traffic (30%) + climate (25%)
                  reweighted proportionally when a component is missing

Consequence     = multiplier from road/state class (CD_STATE_CLASS)
                  HF = 1.5   MR = 1.2   TR = 1.1   RA / FR / unknown = 1.0

Risk score      = Likelihood × Consequence, rescaled to 0–100
```

The weighting is grounded in the sector's own findings, not chosen arbitrarily
— the 45% age weight mirrors the same 30–60-year repair-window statistic
Victoria's Auditor-General uses as a headline risk indicator, and the climate
feature specifically targets extreme-rainfall days rather than total rainfall,
because average rainfall has been *declining* in Victoria even as extreme
rainfall intensity rises. Full reasoning, with citations, is on the in-app
**Methodology** page and in `docs/infrapulse_vic_briefing.md`.

## Known limitations

The original design planned to use physical condition ratings as a model
input. That plan was abandoned after three separate sourcing attempts failed:
the legacy VicRoads "Bridge Structures" dataset was confirmed dead, the Vicmap
Transport ArcGIS FeatureServer's condition field returned near-zero variance,
and an AURIN portal download intended for Victoria returned Western
Australia's data instead. Victoria's own 2011 Auditor-General audit found
condition-rating data inconsistent and unreliable sector-wide, independent of
this project — which is the basis for treating the pivot to rule-based scoring
as a methodologically sound choice, not a fallback. The `physical_condition`
field is retained in the dataset for reference only and does not feed the
score.

## Future Expansion: AI-Driven Data Centre Intelligence

Expand InfraPulse beyond public infrastructure to support data centre asset management and strategic planning. The platform would monitor key operational metrics such as Power Usage Effectiveness (PUE), energy consumption, cooling efficiency, carbon emissions, and equipment health through real-time analytics and predictive AI.

By integrating electricity pricing, renewable energy availability, climate conditions, fibre connectivity, land availability, and demand forecasts, InfraPulse could also recommend optimal locations for future data centre developments, enabling organisations to improve operational efficiency while supporting sustainable digital infrastructure.

Consequence     = multiplier from road/state class (CD_STATE_CLASS)
                  HF = 1.5   MR = 1.2   TR = 1.1   RA / FR / unknown = 1.0

Risk score      = Likelihood × Consequence, rescaled to 0–100
```

The weighting is grounded in the sector's own findings, not chosen arbitrarily
— the 45% age weight mirrors the same 30–60-year repair-window statistic
Victoria's Auditor-General uses as a headline risk indicator, and the climate
feature specifically targets extreme-rainfall days rather than total rainfall,
because average rainfall has been *declining* in Victoria even as extreme
rainfall intensity rises. Full reasoning, with citations, is on the in-app
**Methodology** page and in `docs/infrapulse_vic_briefing.md`.

## Known limitations

The original design planned to use physical condition ratings as a model
input. That plan was abandoned after three separate sourcing attempts failed:
the legacy VicRoads "Bridge Structures" dataset was confirmed dead, the Vicmap
Transport ArcGIS FeatureServer's condition field returned near-zero variance,
and an AURIN portal download intended for Victoria returned Western
Australia's data instead. Victoria's own 2011 Auditor-General audit found
condition-rating data inconsistent and unreliable sector-wide, independent of
this project — which is the basis for treating the pivot to rule-based scoring
as a methodologically sound choice, not a fallback. The `physical_condition`
field is retained in the dataset for reference only and does not feed the
score.

## Tech stack

Python, Pandas, Streamlit, Folium, Scikit-learn (pipeline utilities). Built
with assistance from Claude and Antigravity; all data-quality findings and
scoring decisions verified against primary/secondary sources listed in
`docs/infrapulse_vic_briefing.md`.

## Running locally

```bash
git clone https://github.com/AJ-ing/InfraPulse
cd infrapulse
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deployment

Deployed on [Streamlit Community Cloud](https://share.streamlit.io), connected
directly to this GitHub repository. Any push to `main` redeploys automatically.
Note: `data/processed/bridges_risk_scored.csv` must be committed to the repo —
the app has no live database, so this file is its only data source.

## Data licensing note

This project publishes coordinates and risk rankings for real public
infrastructure. Before treating any deployed instance as a public-facing
production tool, confirm Transport Victoria's open data licence terms permit
this kind of republication.

## Sources

Victorian Auditor-General's Office (2011), *Management of Road Bridges*, and
related sources cited in full in `docs/infrapulse_vic_briefing.md`.

## Author

Aayush Jain
