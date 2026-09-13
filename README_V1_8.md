# Macro Intelligence Terminal v1.8

## Portfolio Macro Attribution
v1.8 adds a transparent directional macro-sensitivity layer for Indian equities, Indian government bonds, US equities, US Treasuries, gold and USD.

This is **not** a return forecast, valuation model, or investment recommendation. Sensitivity coefficients are illustrative and exposed in `analytics/portfolio.py` so they can later be replaced by a research-backed methodology.

### Inputs
- Macro regime score
- Inflation
- Real policy rate
- US 10Y–2Y yield spread when FRED data are available
- FX impulse slot reserved for a validated USD/INR feed

### Outputs
- Directional sensitivity score by asset
- Factor-level contributions
- Configurable sensitivity matrix

### Data architecture
FRED API v2 supports bulk observations for a release, while the series observations API supports vintage dates and initial-release/revised-observation output types. This supports the existing event/revision architecture and future point-in-time backtesting. FRED also notes that published release dates do not necessarily equal the time data becomes available on FRED/ALFRED.
