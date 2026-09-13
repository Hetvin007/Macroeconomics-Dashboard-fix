"""Headless refresh for configured open-data sources."""
import yaml
from database import connect, upsert
from collectors.world_bank import fetch as wb_fetch
from collectors.imf import fetch as imf_fetch
from collectors.rbi import fetch as rbi_fetch
cfg=yaml.safe_load(open('config/indicators.yaml')); rcfg=yaml.safe_load(open('config/rbi_sources.yaml')); con=connect()
for it in cfg.get('world_bank',[]):
    for c in ['IND','USA','CHN','EMU','GBR','JPN','DEU','FRA','BRA','CAN','AUS','KOR']:
        try: upsert(con,it['id'],wb_fetch(c,it['code']))
        except Exception as e: print('WB',it['id'],c,e)
for it in cfg.get('imf',[]):
    try: upsert(con,it['id'],imf_fetch(it['code']))
    except Exception as e: print('IMF',it['id'],e)
for it in rcfg.get('india_rbi',{}).get('indicators',[]):
    if not it.get('url'): continue
    try: upsert(con,it['id'],rbi_fetch(it['url'],it['id'],fmt=it.get('format','csv')))
    except Exception as e: print('RBI',it['id'],e)
print('Refresh complete')
