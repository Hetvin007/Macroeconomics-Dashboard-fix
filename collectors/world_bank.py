import requests,pandas as pd

def fetch(country,indicator):
    url=f'https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&per_page=20000'
    data=requests.get(url,timeout=30).json()[1]
    return pd.DataFrame([{'country':country,'date':x['date'],'value':x['value'],'source':'World Bank','source_url':url} for x in data if x['value'] is not None])
