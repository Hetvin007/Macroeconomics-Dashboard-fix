# Macro Intelligence Terminal v1.5

v1.5 adds **Global Macro Signal Fusion** on top of the v1.4 cross-asset attribution engine.

## New
- Cross-country macro score table
- Global regime estimate from available country scores
- Stress breadth across configured economies
- Explicit derived/model labels
- Downloadable fusion dataset

## Design principle
Official observations remain separate from derived analytics. The global score is a transparent heuristic and is **not a forecast**.

## Sources
- RBI DBIE / SDMX: https://data.rbi.org.in/
- FRED API: https://fred.stlouisfed.org/docs/api/fred/
- World Bank Indicators API
- IMF DataMapper

FRED supports release calendars, series observations, updates and vintages, which remain the basis for the event/revision layers.
