import os, requests, pandas as pd
BASE='https://api.stlouisfed.org/fred'

def fetch_release_calendar(releases, api_key=None, start=None, end=None, timeout=45):
    key=api_key or os.getenv('FRED_API_KEY')
    if not key: raise ValueError('FRED_API_KEY is not configured.')
    rows=[]
    for rel in releases:
        params={'release_id':int(rel['release_id']),'api_key':key,'file_type':'json','sort_order':'asc','include_release_dates_with_no_data':'true'}
        if start: params['realtime_start']=start
        if end: params['realtime_end']=end
        r=requests.get(f'{BASE}/release/dates',params=params,timeout=timeout); r.raise_for_status()
        for x in r.json().get('release_dates',[]):
            rows.append({'release_id':rel['release_id'],'provider':'FRED','name':rel['name'],'country':rel.get('country',''),'date':x['date'],'source_url':f"https://fred.stlouisfed.org/release?rid={rel['release_id']}",'status':'scheduled'})
    return pd.DataFrame(rows)
