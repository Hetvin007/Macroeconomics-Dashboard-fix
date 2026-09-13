import pandas as pd

def detect_revisions(previous, current):
    if previous is None or current is None or previous.empty or current.empty: return pd.DataFrame()
    keys=['indicator_id','country','date']
    a=previous[keys+['value']].rename(columns={'value':'old_value'})
    b=current[keys+['value']].rename(columns={'value':'new_value'})
    x=a.merge(b,on=keys,how='inner'); x=x[x.old_value.ne(x.new_value)]
    if x.empty: return x
    x['delta']=x.new_value-x.old_value
    x['abs_delta']=x.delta.abs()
    return x.sort_values('abs_delta',ascending=False)
