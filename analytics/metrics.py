import pandas as pd

def prepare(df):
    x=df.copy()
    if x.empty: return x
    x['date']=pd.to_datetime(x['date'],errors='coerce')
    x['value']=pd.to_numeric(x['value'],errors='coerce')
    return x.dropna(subset=['date','value']).sort_values(['indicator_id','country','date'])

def latest_by_indicator(df):
    x=prepare(df)
    if x.empty:return x
    return x.groupby(['indicator_id','country'],as_index=False).tail(1)

def previous_by_indicator(df):
    x=prepare(df)
    if x.empty:return x
    return x.groupby(['indicator_id','country'],as_index=False).nth(-2).reset_index()

def change_table(df):
    x=prepare(df)
    if x.empty:return x
    g=x.groupby(['indicator_id','country'])['value']
    x['change']=g.diff()
    x['pct_change']=g.pct_change()*100
    return x

def yoy(df):
    x=prepare(df)
    if x.empty:return x
    # For annual World Bank/IMF data this naturally becomes NaN; for monthly data it is 12 periods.
    x['yoy_pct']=x.groupby(['indicator_id','country'])['value'].pct_change(12)*100
    return x

def spread(a,b):
    return None if a is None or b is None else a-b

def latest_pair(df, indicator_a, indicator_b, country):
    x=latest_by_indicator(df)
    aa=x[(x.indicator_id==indicator_a)&(x.country==country)]
    bb=x[(x.indicator_id==indicator_b)&(x.country==country)]
    if aa.empty or bb.empty:return None
    return float(aa.iloc[0].value)-float(bb.iloc[0].value)
