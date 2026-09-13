import pandas as pd

def normalize_event_table(df):
    if df is None or df.empty: return pd.DataFrame()
    x=df.copy()
    for c in ['actual','previous','consensus']:
        if c not in x: x[c]=pd.NA
        x[c]=pd.to_numeric(x[c],errors='coerce')
    x['surprise']=x['actual']-x['consensus']
    x['surprise_pct']=x['surprise']/x['consensus'].abs().replace(0,pd.NA)*100
    x['direction']=x.apply(lambda r: 'Beat' if pd.notna(r.surprise) and r.surprise>0 else ('Miss' if pd.notna(r.surprise) and r.surprise<0 else 'In line'),axis=1)
    x['significance']=x['surprise_pct'].abs().fillna(0)
    return x

def event_priority(row):
    s=float(row.get('significance',0) or 0)
    if s>=2: return 'High'
    if s>=0.5: return 'Medium'
    return 'Low'

def detect_release_events(consensus_df):
    x=normalize_event_table(consensus_df)
    if x.empty: return x
    x['priority']=x.apply(event_priority,axis=1)
    return x.sort_values(['priority','event_date'] if 'event_date' in x else ['significance'],ascending=[True,False] if 'event_date' in x else [False])
