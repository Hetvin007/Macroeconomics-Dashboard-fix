import os, pathlib, yaml, pandas as pd
from database import connect
from event_db import init_events, upsert_release_dates, log_run
from collectors.fred_calendar import fetch_release_calendar
BASE=pathlib.Path(__file__).resolve().parents[1]
con=connect(); init_events(con)
cfg=yaml.safe_load(open(BASE/'config/releases.yaml'))
try:
    df=fetch_release_calendar(cfg.get('releases',[]), start=pd.Timestamp.utcnow().strftime('%Y-%m-%d'), end=(pd.Timestamp.utcnow()+pd.Timedelta(days=90)).strftime('%Y-%m-%d'))
    n=upsert_release_dates(con,df); log_run(con,'FRED release calendar','success',n,0,'Upcoming release calendar refreshed')
    print(f'Loaded {n} release-date rows')
except Exception as e:
    log_run(con,'FRED release calendar','error',0,1,str(e)); raise
