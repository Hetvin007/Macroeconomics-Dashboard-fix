# Macro Intelligence Terminal v1.9

## Empirical Macro Factor Backtesting

v1.9 adds a historical backtesting layer that links the stored macro regime score to subsequent market observations.

### Included assets
- S&P 500
- US Dollar Index
- US 10Y Treasury yield
- US 2Y Treasury yield

### Method
1. Build the transparent macro regime score from stored macro observations.
2. Sample the regime at month-end.
3. Measure subsequent 1M/3M/6M market outcomes.
4. Group outcomes by historical regime.
5. Estimate a simple descriptive beta between changes in the macro score and subsequent market outcomes.
6. Show rolling correlation when enough observations exist.

### Important limitation
This is **historical descriptive analysis**, not a predictive model and not causal attribution. Results depend on data availability, revisions, sample size and the current heuristic regime definition.

## Data discipline
FRED's official API supports observations, real-time periods, vintage dates and release-level bulk observations. These capabilities are useful for future point-in-time backtesting and revision-aware research. See the official documentation:
https://fred.stlouisfed.org/docs/api/fred/series_observations.html
https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
https://fred.stlouisfed.org/docs/api/fred/v2/release_observations.html
