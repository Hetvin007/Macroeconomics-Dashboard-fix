# Macro Intelligence Terminal v1.6

## New in v1.6 — Relative Macro Engine

The terminal now compares economies relative to a selected anchor (India by default).

### Relative score
The score is a transparent heuristic built from:
- 35% growth strength
- 25% lower inflation strength
- 20% lower unemployment strength
- 20% real policy-rate strength

The components are cross-sectional z-scores across the currently loaded economies. The result is descriptive and **not a forecast or investment recommendation**.

### New dashboard views
- **India-vs-Global Relative Macro**
- Relative strength/weakness classification
- Pairwise relative-strength matrix
- Downloadable relative-macro CSV

### v1.6 quality fix
The previous version had two dashboard sections sharing the same Streamlit tab index. v1.6 separates:
1. Global Signal Fusion
2. Relative Macro
3. Data Quality
4. Source Registry

RBI data remains strict: only explicitly configured official feeds are ingested; undocumented series IDs are not guessed. RBI's official DBIE portal is `data.rbi.org.in`. 
