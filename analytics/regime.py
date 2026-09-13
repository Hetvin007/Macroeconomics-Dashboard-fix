import pandas as pd
from analytics.signals import risk_score, regime


def _series(obs, indicator_keys, country):
    x=obs[obs.country.eq(country)].copy()
    if x.empty: return pd.Series(dtype=float)
    ids=x.indicator_id.astype(str)
    mask=False
    for key in indicator_keys:
        mask = mask | ids.str.contains(key, case=False, na=False)
    x=x[mask]
    if x.empty: return pd.Series(dtype=float)
    x['date']=pd.to_datetime(x['date'], errors='coerce')
    return x.sort_values('date').drop_duplicates('date').set_index('date')['value']


def build_regime_history(obs, target=4.0, country='IND'):
    """Build a transparent monthly-ish regime history from whatever dated observations exist.
    Uses nearest/latest observation on each date after forward-filling within each series.
    Only dates with at least two usable macro inputs are retained.
    """
    if obs.empty: return pd.DataFrame()
    g=_series(obs,['gdp_growth','growth'],country)
    i=_series(obs,['inflation_cpi','inflation'],country)
    u=_series(obs,['unemployment'],country)
    repo=_series(obs,['rbi_repo','repo_rate'], 'India')
    dates=pd.Index(sorted(set().union(g.index,i.index,u.index,repo.index)))
    if len(dates)==0: return pd.DataFrame()
    frame=pd.DataFrame(index=dates)
    frame['growth']=g.reindex(dates).ffill()
    frame['inflation']=i.reindex(dates).ffill()
    frame['unemployment']=u.reindex(dates).ffill()
    frame['repo']=repo.reindex(dates).ffill()
    frame['real_policy']=frame['repo']-frame['inflation']
    rows=[]
    for dt,r in frame.iterrows():
        vals=[r.growth,r.inflation,r.unemployment,r.real_policy]
        if sum(pd.notna(v) for v in vals)<2: continue
        score=risk_score(r.growth if pd.notna(r.growth) else None,
                         r.inflation if pd.notna(r.inflation) else None,
                         r.unemployment if pd.notna(r.unemployment) else None,
                         r.real_policy if pd.notna(r.real_policy) else None)
        rows.append({'date':dt,'growth':r.growth,'inflation':r.inflation,'unemployment':r.unemployment,
                     'real_policy':r.real_policy,'score':score,'regime':regime(score)})
    return pd.DataFrame(rows)


def regime_score_explainer():
    return ("Score starts at 0. Growth below 2% adds 25 points; growth below 0% adds another 20; "
            "inflation above 6% adds 25; unemployment above 8% adds 15; negative real policy rate adds 10. "
            "The score is capped at 100. 0–19 = Stable, 20–39 = Watch, 40–69 = Caution, 70–100 = High stress. "
            "Missing inputs do not receive points. This is a transparent heuristic and should not be treated as a forecast.")
