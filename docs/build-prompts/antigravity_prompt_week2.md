# Antigravity Task: InfraPulse — Week 2 (Home, Methodology, Theming, README)

## Context
InfraPulse scores and ranks 6,554 Victorian bridges by risk. The multi-page
restructure (`streamlit_app.py`, `data_loader.py`, `pages/dashboard.py`,
`pages/home.py`, `pages/methodology.py`) already exists with working filters, KPIs,
map, and table. This task fills in the two placeholder pages with real content,
applies a native theme, and produces project documentation.

## Objective
1. Replace the `pages/methodology.py` TODO stubs with real, sourced content.
2. Polish `pages/home.py` with a real problem statement, not placeholder copy.
3. Apply a consistent visual theme via `.streamlit/config.toml` — not custom CSS.
4. Produce a `README.md` documenting the project with real screenshots.

## Task

### 1. Methodology content
Write three sections — **Data sources**, **Risk scoring approach**, **Known
limitations** — using only facts already established in the project's research
briefing document. Do not invent statistics, dates, or figures not present in that
briefing. Specifically include:
- The three failed condition-data attempts (legacy VicRoads dataset dead, Vicmap
  ArcGIS near-zero-variance field, AURIN returning Western Australia's data instead
  of Victoria's) and the Victorian Auditor-General's 2011 finding that condition
  data is inconsistent sector-wide (differing rating scales between councils,
  overdue assessments, the Kirwans Bridge rating contradiction) as the justification
  for why the pivot to rule-based scoring is methodologically defensible, not a
  fallback.
- The 52%-of-bridges-in-the-30–60-year-window statistic and the
  funding-below-depreciation finding as justification for the 45% age weighting.
- The declining-average-rainfall-vs-rising-extreme-rainfall-intensity finding as
  justification for using extreme rainfall days rather than total rainfall.
- The ~41% freight weight growth as justification for the road-class consequence
  multiplier.
- State explicitly that the final score is a transparent rule-based multi-criteria
  formula, not a trained predictive model — do not use the words "AI" or
  "prediction" to describe it.

### 2. Home page
Rewrite the problem statement to state the real scale (6,554 bridges) and ground it
in one concrete finding from the briefing (e.g., the funding-vs-depreciation gap),
rather than generic "infrastructure matters" framing. Add a page link to the
methodology page alongside the existing dashboard link.

### 3. Theming
Add `.streamlit/config.toml` with a `[theme]` block (primary color, background,
secondary background, text color, font). Do not add custom CSS injection anywhere
in the app — the native theme config is sufficient and lower-risk.

### 4. README
Create a root `README.md` with: a one-paragraph project description, three
embedded screenshots (KPI/table, risk map, filters in action) referencing an
`assets/screenshots/` folder, a project architecture tree, a brief risk-scoring
summary linking to the in-app methodology page for full detail, and local run
instructions.

## Constraints
- No fabricated methodology content — every claim must trace back to the research
  briefing document.
- No custom CSS for theming — config.toml only.
- Do not change any dashboard.py filter/KPI/map logic in this task.

## Acceptance Criteria
- Methodology page renders with no TODO placeholders remaining, and every factual
  claim on it is traceable to the briefing document.
- Home page shows a specific, sourced problem statement, not generic copy, and
  links to both the dashboard and methodology pages.
- App visually reflects the configured theme with no CSS injection present.
- README renders correctly on GitHub with all three screenshots visible.

## Status
Completed in this session — see `pages/methodology.py`, `pages/home.py`,
`.streamlit/config.toml`, and `README.md`.
