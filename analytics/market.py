import pandas as pd

def latest_value(obs, indicator_id, country='United States'):
    x=obs[(obs.indicator_id==indicator_id)&(obs.country==country)].sort_values('date')
    return None if x.empty else float(x.iloc[-1].value)

def spread(obs, long_id, short_id, country='United States'):
    a=obs[(obs.indicator_id==long_id)&(obs.country==country)][['date','value']].rename(columns={'value':'long'})
    b=obs[(obs.indicator_id==short_id)&(obs.country==country)][['date','value']].rename(columns={'value':'short'})
    x=a.merge(b,on='date').sort_values('date'); x['spread']=x['long']-x['short']; return x
