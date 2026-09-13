"""Validated RBI DBIE feed adapter.

The adapter accepts explicit CSV/JSON URLs configured by the user/project. It never
constructs undocumented RBI dataflow or series IDs. This is intentional because the
current RBI portal exposes an SDMX Data Query UI and mappings should be validated
against the live portal before automation.
"""
import io, json, requests, pandas as pd

def _normalize_records(obj):
    if isinstance(obj, dict):
        for key in ('data','observations','results','rows'):
            if key in obj: return _normalize_records(obj[key])
        # common SDMX-ish shape: data list under a nested key
        return []
    return obj

def _normalize(df, indicator_id, url, country='India'):
    if df.empty: raise ValueError('Empty response')
    cols={str(c).lower().strip():c for c in df.columns}
    date_col=next((cols[k] for k in ('date','time','period','observation_date','obs_time') if k in cols),None)
    value_col=next((cols[k] for k in ('value','obs_value','observation_value','obsvalue') if k in cols),None)
    country_col=next((cols[k] for k in ('country','ref_area','area') if k in cols),None)
    if not date_col or not value_col:
        raise ValueError(f'Response must contain date/period and value columns; got {list(df.columns)}')
    out=pd.DataFrame({
        'country': df[country_col].astype(str) if country_col else country,
        'date': pd.to_datetime(df[date_col],errors='coerce').dt.strftime('%Y-%m-%d'),
        'value': pd.to_numeric(df[value_col],errors='coerce'),
        'source':'RBI DBIE','source_url':url})
    return out.dropna(subset=['date','value'])

def fetch(url, indicator_id, country='India', timeout=45, fmt='csv'):
    r=requests.get(url,timeout=timeout,headers={'User-Agent':'MacroIntelligenceTerminal/0.7'})
    r.raise_for_status()
    if fmt.lower()=='json':
        obj=_normalize_records(r.json())
        return _normalize(pd.DataFrame(obj),indicator_id,url,country)
    if fmt.lower() in ('xlsx','xls'):
        return _normalize(pd.read_excel(io.BytesIO(r.content)),indicator_id,url,country)
    return _normalize(pd.read_csv(io.BytesIO(r.content)),indicator_id,url,country)
