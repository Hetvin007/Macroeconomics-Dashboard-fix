# Macro Intelligence Terminal v1.2

v1.2 adds an event-driven intelligence layer on top of v1.1.

## New modules
- `database/event_db.py` — release calendar, event log, revision log and refresh-run audit tables.
- `collectors/fred_calendar.py` — official FRED release-date ingestion.
- `analytics/events.py` — surprise normalization and event priority.
- `analytics/revisions.py` — compares snapshots to identify revised observations.
- `analytics/daily_engine.py` — combines observations, surprises and upcoming releases into intelligence bullets.
- `scripts/event_refresh.py` — refreshes the configured FRED release calendar.
- `scripts/daily_pipeline.py` — runs the standard refresh plus release-calendar refresh.
- `.github/workflows/daily_pipeline.yml` — weekday automation template.

## Important data rules
1. Consensus is never invented. Populate `data/consensus_template.csv` from a validated provider/source.
2. FRED API access requires a registered API key. The application should display the required FRED attribution/notice when used with FRED data.
3. RBI remains strict: do not guess DBIE/SDMX series identifiers.
4. Model/derived outputs are clearly distinct from official observations.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

For the event calendar:
```bash
export FRED_API_KEY='your_key'
python scripts/event_refresh.py
```
