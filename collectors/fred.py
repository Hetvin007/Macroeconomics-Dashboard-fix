import os, requests, pandas as pd

BASE='https://api.stlouisfed.org/fred'

def fetch(series_id, indicator_id=None, api_key=None, start=None, end=None, realtime_start=None, realtime_end=None, timeout=45):
    key=api_key or os.getenv('FRED_API_KEY')
    if not key:
        raise ValueError('FRED_API_KEY is not configured. FRED requires a registered API key.')
    params={'series_id':series_id,'api_key':key,'file_type':'json','sort_order':'asc'}
    if start: params['observation_start']=start
    if end: params['observation_end']=end
    if realtime_start: params['realtime_start']=realtime_start
    if realtime_end: params['realtime_end']=realtime_end
    r=requests.get(f'{BASE}/series/observations',params=params,timeout=timeout)
    r.raise_for_status(); obj=r.json()
    rows=[]
    for x in obj.get('observations',[]):
        if x.get('value') in (None,'.'): continue
        rows.append({'country':'United States','date':x['date'],'value':float(x['value']),
                     'source':'FRED','source_url':f'https://fred.stlouisfed.org/series/{series_id}'})
    if not rows: raise ValueError(f'No observations returned for {series_id}')
    return pd.DataFrame(rows)
