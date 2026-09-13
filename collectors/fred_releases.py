import os, requests, pandas as pd
BASE='https://api.stlouisfed.org/fred'

def release_dates(release_id, api_key=None, start=None, end=None, timeout=45):
    key=api_key or os.getenv('FRED_API_KEY')
    if not key: raise ValueError('FRED_API_KEY is not configured.')
    params={'release_id':int(release_id),'api_key':key,'file_type':'json','sort_order':'asc','include_release_dates_with_no_data':'true'}
    if start: params['realtime_start']=start
    if end: params['realtime_end']=end
    r=requests.get(f'{BASE}/release/dates',params=params,timeout=timeout); r.raise_for_status()
    return pd.DataFrame([{'release_id':int(release_id),'date':x['date'],'source':'FRED','source_url':f'https://fred.stlouisfed.org/release?rid={release_id}'} for x in r.json().get('release_dates',[])])
