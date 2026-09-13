import pandas as pd
import numpy as np


def _series(obs, indicator_id, country='United States'):
    x = obs[(obs.indicator_id == indicator_id) & (obs.country == country)].copy()
    if x.empty:
        return pd.DataFrame(columns=['date','value'])
    x['date'] = pd.to_datetime(x['date'], errors='coerce')
    x['value'] = pd.to_numeric(x['value'], errors='coerce')
    return x.dropna(subset=['date','value']).sort_values('date')[['date','value']]


def _nearest(s, target, direction=None):
    if s.empty:
        return None
    t = pd.Timestamp(target)
    x = s.copy()
    if direction == 'before':
        x = x[x.date <= t]
        if x.empty: return None
        return x.iloc[-1]
    if direction == 'after':
        x = x[x.date >= t]
        if x.empty: return None
        return x.iloc[0]
    i = (x.date - t).abs().idxmin()
    return x.loc[i]


def reaction_table(obs, events, market_map=None, before_days=1, after_days=1):
    """Estimate simple event-window market reactions using nearest observations.
    This is descriptive, not causal: it does not control for other news or intraday timing.
    """
    if events is None or len(events) == 0:
        return pd.DataFrame()
    if market_map is None:
        market_map = {
            'us_2y': 'US 2Y', 'us_10y': 'US 10Y',
            'us_dollar_index': 'Broad USD index', 'us_sp500': 'S&P 500'
        }
    rows=[]
    ev=pd.DataFrame(events).copy()
    date_col = 'event_date' if 'event_date' in ev.columns else ('date' if 'date' in ev.columns else None)
    if date_col is None: return pd.DataFrame()
    ev[date_col]=pd.to_datetime(ev[date_col],errors='coerce')
    ev=ev.dropna(subset=[date_col])
    for _,e in ev.iterrows():
        event_date=e[date_col]
        base={'event_date':event_date.date().isoformat(),'event':e.get('name',e.get('event','')),
              'country':e.get('country',''),'surprise':e.get('surprise',np.nan),
              'direction':e.get('direction','')}
        for ind,label in market_map.items():
            s=_series(obs,ind)
            if s.empty: continue
            pre=_nearest(s,event_date - pd.Timedelta(days=before_days),'before')
            post=_nearest(s,event_date + pd.Timedelta(days=after_days),'after')
            if pre is None or post is None or pre.value == 0: continue
            change=post.value-pre.value
            pct=change/pre.value*100
            rows.append({**base,'market':label,'indicator_id':ind,
                         'pre_date':pre.date.date().isoformat(),'pre_value':pre.value,
                         'post_date':post.date.date().isoformat(),'post_value':post.value,
                         'change':change,'pct_change':pct})
    return pd.DataFrame(rows)
