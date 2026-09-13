import pandas as pd


def detect_alerts(obs: pd.DataFrame, threshold_days: int = 7) -> pd.DataFrame:
    if obs is None or obs.empty:
        return pd.DataFrame(columns=['severity','country','indicator_id','date','value','message'])
    x = obs.copy()
    x['date'] = pd.to_datetime(x['date'], errors='coerce')
    x['value'] = pd.to_numeric(x['value'], errors='coerce')
    rows = []
    for (country, indicator), g in x.dropna(subset=['date','value']).groupby(['country','indicator_id']):
        g = g.sort_values('date')
        if len(g) < 2:
            continue
        a, b = g.iloc[-2], g.iloc[-1]
        if a.value == 0:
            continue
        pct = (b.value-a.value)/abs(a.value)*100
        if abs(pct) >= 10:
            severity = 'High' if abs(pct) >= 20 else 'Watch'
            rows.append({'severity':severity,'country':country,'indicator_id':indicator,'date':b.date.date(),'value':b.value,
                         'message':f"{indicator} moved {pct:+.1f}% versus its previous observation."})
    return pd.DataFrame(rows).sort_values(['severity','date'], ascending=[True,False]) if rows else pd.DataFrame(columns=['severity','country','indicator_id','date','value','message'])


def freshness_alerts(obs: pd.DataFrame, max_age_days: int = 45) -> pd.DataFrame:
    if obs is None or obs.empty:
        return pd.DataFrame(columns=['severity','country','indicator_id','date','value','message'])
    x=obs.copy(); x['date']=pd.to_datetime(x['date'],errors='coerce'); today=pd.Timestamp.utcnow().tz_localize(None)
    latest=x.sort_values('date').groupby(['country','indicator_id'],as_index=False).tail(1)
    latest['age_days']=(today-latest['date'].dt.tz_localize(None)).dt.days
    z=latest[latest.age_days>max_age_days]
    return pd.DataFrame([{'severity':'Stale','country':r.country,'indicator_id':r.indicator_id,'date':r.date.date(),'value':r.value,
                          'message':f"Latest observation is {int(r.age_days)} days old."} for _,r in z.iterrows()])
