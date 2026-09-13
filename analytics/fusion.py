import pandas as pd
from analytics.signals import risk_score, regime

def latest_country(obs, country):
    x=obs[obs["country"].astype(str).str.upper().eq(country.upper())].copy()
    if x.empty: return {}
    x["date"]=pd.to_datetime(x["date"],errors="coerce")
    out={}
    for iid,g in x.sort_values("date").groupby("indicator_id"):
        g=g.dropna(subset=["value"])
        if not g.empty: out[str(iid)]=float(g.iloc[-1]["value"])
    return out

def _pick(d, names):
    for k,v in d.items():
        if any(n.lower() in k.lower() for n in names):
            return v
    return None

def country_signal(obs, country):
    d=latest_country(obs,country)
    growth=_pick(d,["gdp_growth","growth"])
    inflation=_pick(d,["inflation_cpi","inflation"])
    unemployment=_pick(d,["unemployment"])
    repo=_pick(d,["rbi_repo","repo_rate","policy_rate"])
    real_policy=(repo-inflation) if repo is not None and inflation is not None else None
    score=risk_score(growth,inflation,unemployment,real_policy)
    return {"country":country,"growth":growth,"inflation":inflation,"unemployment":unemployment,
            "policy_rate":repo,"real_policy":real_policy,"score":score,"regime":regime(score)}

def build_global_signal_fusion(obs, countries=None):
    countries=countries or ["IND","USA","CHN","EMU","GBR","JPN","DEU","FRA","BRA","CAN","AUS","KOR"]
    rows=[country_signal(obs,c) for c in countries]
    df=pd.DataFrame(rows)
    if df.empty:return df
    valid=df["score"].dropna()
    global_score=float(valid.mean()) if len(valid) else None
    global_regime=regime(global_score) if global_score is not None else "Insufficient data"
    df["global_score"]=global_score
    df["global_regime"]=global_regime
    # Breadth: share of economies in caution/high-stress regimes.
    df["stress_flag"]=df["score"].ge(40)
    return df

def cross_asset_context(attr_df):
    if attr_df is None or attr_df.empty:return {}
    high=(attr_df["response_consistency"]=="High").sum() if "response_consistency" in attr_df else 0
    mixed=(attr_df["response_consistency"]=="Mixed").sum() if "response_consistency" in attr_df else 0
    n=len(attr_df)
    return {"events":n,"high_consistency_pct":round(100*high/n,1) if n else 0,
            "mixed_pct":round(100*mixed/n,1) if n else 0}
