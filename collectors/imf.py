import requests,pandas as pd

def fetch(indicator):
    url=f'https://www.imf.org/external/datamapper/api/v1/{indicator}'
    data=requests.get(url,timeout=30).json(); vals=data.get('values',{}).get(indicator,{})
    rows=[]
    for country,series in vals.items():
        for date,value in series.items():
            if value is not None: rows.append({'country':country,'date':date,'value':value,'source':'IMF DataMapper','source_url':url})
    return pd.DataFrame(rows)
