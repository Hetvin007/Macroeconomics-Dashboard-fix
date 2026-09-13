import pandas as pd
from analytics.signals import risk_score, regime

MACRO_IDS = ['us_real_gdp_growth','us_cpi','us_unemployment','us_fed_funds']

def _asof_series(vintage_df, indicator_id, asof):
    x=vintage_df[(vintage_df.indicator_id==indicator_id) & (pd.to_datetime(vintage_df.vintage_date)<=pd.Timestamp(asof))].copy()
    if x.empty: return pd.Series(dtype=float)
    x['date']=pd.to_datetime(x.date); x['vintage_date']=pd.to_datetime(x.vintage_date)
    # For each observation date, keep the latest vintage known by the as-of date.
    x=x.sort_values(['date','vintage_date']).drop_duplicates(['date'],keep='last')
    x=x[x.date<=pd.Timestamp(asof)].sort_values('date')
    return x.set_index('date').value.astype(float)

def snapshot(vintage_df, asof):
    rows=[]
    for iid in MACRO_IDS:
        s=_asof_series(vintage_df,iid,asof)
        if s.empty: continue
        dt=s.index.max(); rows.append({'indicator_id':iid,'observation_date':dt,'value':float(s.iloc[-1]),'asof_date':pd.Timestamp(asof)})
    return pd.DataFrame(rows)

def _cpi_yoy(vintage_df, asof):
    s=_asof_series(vintage_df,'us_cpi',asof)
    if s.empty: return None
    # Use the latest observation and its 12-month prior observation available as of the same vintage.
    latest=s.index.max(); prior=s[s.index<=latest-pd.DateOffset(months=12)]
    if prior.empty: return None
    base=prior.iloc[-1]
    return (s.iloc[-1]/base-1)*100 if base else None

def build_pit_history(vintage_df, asof_dates=None):
    if vintage_df is None or vintage_df.empty: return pd.DataFrame()
    dates=asof_dates or sorted(pd.to_datetime(vintage_df.vintage_date).drop_duplicates())
    rows=[]
    for asof in dates:
        snap=snapshot(vintage_df,asof)
        vals={r.indicator_id:r.value for r in snap.itertuples()}
        growth=vals.get('us_real_gdp_growth'); inflation=_cpi_yoy(vintage_df,asof); unemployment=vals.get('us_unemployment'); fed=vals.get('us_fed_funds')
        real_policy=(fed-inflation) if fed is not None and inflation is not None else None
        score=risk_score(growth,inflation,unemployment,real_policy)
        rows.append({'asof_date':pd.Timestamp(asof),'growth':growth,'inflation':inflation,'unemployment':unemployment,
                     'fed_funds':fed,'real_policy':real_policy,'score':score,'regime':regime(score),
                     'known_observations':len(snap)})
    return pd.DataFrame(rows).sort_values('asof_date')

def explain_pit():
    return ('Point-in-time mode selects, for each observation, the latest vintage that was available on or before the selected as-of date. '
            'This avoids using later revisions to explain earlier decisions. Market outcomes are evaluated only after the as-of date. '
            'It is historical/descriptive research, not a forecast.')
