"""Headless v1.0 refresh. Run with: python refresh_v1.py"""
import os, yaml, pathlib
from database.db import connect, upsert
from collectors.fred import fetch as fred_fetch
from collectors.fred_releases import release_dates
BASE=pathlib.Path(__file__).parent
con=connect(); cfg=yaml.safe_load(open(BASE/'config/fred.yaml')); n=0
for it in cfg.get('series',[]):
    try: n += upsert(con,it['id'],fred_fetch(it['fred_id']))
    except Exception as e: print('FRED series:',it['id'],e)
print('FRED observations processed:',n)
