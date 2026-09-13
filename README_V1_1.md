# Macro Intelligence Terminal v1.1

v1.1 adds the daily intelligence layer: transparent alerts, stale-data detection, downloadable daily brief, and a corrected 14-tab terminal.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Refresh

Use the sidebar buttons. FRED requires your own API key in `FRED_API_KEY`. RBI feeds are only ingested when an explicit validated URL is configured.

## Daily headless report

```bash
python refresh.py
```

The optional report helper can be used by scheduled jobs after refresh. Reports are written to `reports/` and are intentionally local artifacts.

## Data discipline

- Official observations are kept separate from derived analytics.
- Consensus is never fabricated.
- Alerts are threshold diagnostics, not forecasts.
- RBI identifiers are never guessed.
