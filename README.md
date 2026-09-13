# Macro Intelligence Terminal v0.9

A free/open-data-first Streamlit macro research terminal for India and global economies.

## v0.9 focus
- One-click refresh for World Bank, IMF, configured RBI feeds and FRED.
- India macro analytics: inflation gap and real policy rate.
- US yield curve: 2Y/5Y/10Y/30Y and 10Y–2Y spread.
- Transparent historical Macro Regime Engine.
- Explicit separation of official observations and derived analytics.
- Source URLs and retrieval timestamps for provenance.
- FRED real-time-period parameters are supported by the collector for future vintage/revision analysis.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

For FRED market data, set `FRED_API_KEY` using `.env`/your shell environment. FRED requires a registered API key for API requests.

## Important
RBI machine-readable series identifiers are not guessed. Configure only validated official feeds in `config/rbi_sources.yaml`.

## Data classification
- **Official**: fetched observations from a named source.
- **Derived**: arithmetic/heuristic calculations from stored observations.
- **Model**: reserved for future explicit models; v0.9 does not present a forecast as an official value.

## v2.0 — Point-in-Time Macro Research

v2.0 adds a revision-aware FRED/ALFRED research layer. The dashboard can store quarterly vintage snapshots for selected US macro series and reconstruct the information set that was available as of each vintage date. This is designed to reduce look-ahead bias in historical macro research.

### Point-in-time workflow

1. Configure `FRED_API_KEY`.
2. Use **🕰 Build FRED point-in-time history** in the sidebar.
3. The app requests quarterly real-time periods for US real GDP growth, CPI, unemployment and effective fed funds.
4. Each observation is stored with both its observation date and vintage/as-of date.
5. The **🧭 Point-in-Time** tab reconstructs the latest vintage known at each as-of date.

FRED documents real-time periods and vintage dates as the mechanism for retrieving what information was known during a historical period. See https://fred.stlouisfed.org/docs/api/fred/realtime_period.html and https://fred.stlouisfed.org/docs/api/fred/series_observations.html.

**Research caution:** the point-in-time score is descriptive and should not be treated as a causal model or investment forecast. The current v2.0 implementation uses quarterly vintage sampling; higher-frequency/event-time vintages can be added later.
