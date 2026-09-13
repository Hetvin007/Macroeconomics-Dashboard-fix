import pandas as pd


def calculate_surprises(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=['release','country','date','actual','previous','consensus','surprise','surprise_pct','direction'])
    x=df.copy()
    for c in ['actual','previous','consensus']:
        if c in x: x[c]=pd.to_numeric(x[c],errors='coerce')
    x['surprise']=x['actual']-x['consensus']
    x['surprise_pct']=x['surprise']/x['consensus'].abs()*100
    x.loc[x['consensus'].isna(),'surprise']=pd.NA
    x.loc[x['consensus'].isna(),'surprise_pct']=pd.NA
    x['direction']=x['surprise'].apply(lambda v: 'Beat' if pd.notna(v) and v>0 else ('Miss' if pd.notna(v) and v<0 else ('In line' if pd.notna(v) else 'No consensus')))
    return x


def macro_surprise_score(df: pd.DataFrame) -> float | None:
    x=calculate_surprises(df)
    x=x[x['surprise'].notna()]
    if x.empty: return None
    vals=x['surprise_pct'].clip(-100,100)
    return float(vals.mean())
