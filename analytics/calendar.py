import pandas as pd

def merge_release_calendar(registry, fetched=None):
    base=pd.DataFrame(registry or [])
    if fetched is None or fetched.empty: return base
    return fetched.merge(base,on='release_id',how='left') if 'release_id' in base else fetched
