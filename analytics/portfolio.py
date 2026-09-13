import pandas as pd

DEFAULT_ASSETS = [
    {'asset':'Indian Equities','growth':0.85,'inflation':-0.55,'rates':-0.70,'fx':0.25,'liquidity':0.75,'risk_off':-0.80},
    {'asset':'Indian Government Bonds','growth':-0.35,'inflation':-0.80,'rates':0.90,'fx':0.10,'liquidity':0.75,'risk_off':0.35},
    {'asset':'US Equities','growth':0.75,'inflation':-0.35,'rates':-0.75,'fx':0.05,'liquidity':0.65,'risk_off':-0.65},
    {'asset':'US Treasuries','growth':-0.45,'inflation':-0.85,'rates':0.95,'fx':0.10,'liquidity':0.70,'risk_off':0.65},
    {'asset':'Gold','growth':-0.10,'inflation':0.55,'rates':-0.55,'fx':0.45,'liquidity':0.35,'risk_off':0.85},
    {'asset':'USD','growth':-0.15,'inflation':0.20,'rates':0.65,'fx':0.95,'liquidity':0.30,'risk_off':0.80},
]

FACTOR_LABELS = {
    'growth':'Growth impulse', 'inflation':'Inflation impulse', 'rates':'Rates impulse',
    'fx':'FX impulse', 'liquidity':'Liquidity impulse', 'risk_off':'Risk-off impulse'
}

def portfolio_attribution(regime_score=None, inflation=None, real_policy=None, yield_spread=None, fx_change=None):
    # Directional macro factor impulses. These are intentionally simple and auditable.
    factors = {
        'growth': 0.0 if regime_score is None else max(-1, min(1, (50-regime_score)/50)),
        'inflation': 0.0 if inflation is None else max(-1, min(1, (inflation-4.0)/3.0)),
        'rates': 0.0 if real_policy is None else max(-1, min(1, real_policy/4.0)),
        'fx': 0.0 if fx_change is None else max(-1, min(1, fx_change/3.0)),
        'liquidity': 0.0 if yield_spread is None else max(-1, min(1, yield_spread/2.0)),
        'risk_off': 0.0 if regime_score is None else max(-1, min(1, (regime_score-50)/50)),
    }
    rows=[]
    for asset in DEFAULT_ASSETS:
        contrib={k: asset[k]*factors[k] for k in factors}
        score=sum(contrib.values())
        rows.append({'asset':asset['asset'],'directional_score':score, **{f'{k}_contribution':v for k,v in contrib.items()}})
    out=pd.DataFrame(rows)
    out['interpretation']=out.directional_score.map(lambda x: 'Positive sensitivity' if x>0.25 else ('Negative sensitivity' if x<-0.25 else 'Mixed / limited'))
    return out.sort_values('directional_score',ascending=False).reset_index(drop=True), factors

def factor_matrix():
    return pd.DataFrame(DEFAULT_ASSETS).set_index('asset')[[*FACTOR_LABELS]].rename(columns=FACTOR_LABELS)
