import os, requests, pandas as pd
BASE='https://api.stlouisfed.org/fred'

def fetch_vintage(series_id, indicator_id, vintage_date, api_key=None, start=None, end=None, timeout=45):
    key=api_key or os.getenv('FRED_API_KEY')
    if not key: raise ValueError('FRED_API_KEY is not configured.')
    params={'series_id':series_id,'api_key':key,'file_type':'json','sort_order':'asc',
            'realtime_start':vintage_date,'realtime_end':vintage_date}
    if start: params['observation_start']=start
    if end: params['observation_end']=end
    r=requests.get(f'{BASE}/series/observations',params=params,timeout=timeout)
    r.raise_for_status()
    rows=[]
    for x in r.json().get('observations',[]):
        if x.get('value') in (None,'.'): continue
        rows.append({'indicator_id':indicator_id,'country':'United States','date':x['date'],
                     'value':float(x['value']),'vintage_date':vintage_date,'source':'FRED/ALFRED',
                     'source_url':f'https://fred.stlouisfed.org/series/{series_id}'})
    return pd.DataFrame(rows)

def build_vintage_dates(start='2015-01-01', end=None, freq='QE'):
    end=end or pd.Timestamp.utcnow().strftime('%Y-%m-%d')
    return [d.strftime('%Y-%m-%d') for d in pd.date_range(start=start,end=end,freq=freq)]
