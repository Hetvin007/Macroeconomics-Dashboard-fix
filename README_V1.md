# Macro Intelligence Terminal v1.0

A free/open-data-first macro research terminal with official observations, transparent derived metrics, and an explicit economic-surprise layer.

## New in v1.0
- Daily analyst briefing tab.
- Consensus/surprise engine using a user-supplied validated consensus CSV.
- FRED release-date adapter for official US release calendars.
- Beat/Miss/In-line classification.
- Surprise score remains **Derived**, never presented as an official forecast.
- Release registry separated from observations.
- Existing World Bank, IMF, RBI and FRED layers retained.

## Consensus data
There is no universally free official API for market consensus estimates across all releases. Therefore `data/consensus_template.csv` is an explicit input contract. Populate it only from a licensed/validated source and keep the source column populated.

## FRED
FRED series observations and release endpoints require a registered API key. Set `FRED_API_KEY` in the environment.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data classes
- Official: directly retrieved from an official source.
- Derived: arithmetic/heuristic calculation from loaded observations.
- Model: scoring/analytical regime output.
