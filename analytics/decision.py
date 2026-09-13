import pandas as pd


def _num(x):
    try:
        return float(x)
    except Exception:
        return None


def build_decision_dashboard(fusion: pd.DataFrame, obs: pd.DataFrame, anchor='India') -> dict:
    """Build transparent macro decision-support signals; not investment advice."""
    out = {'anchor': anchor, 'signals': [], 'watchlist': [], 'score': None, 'regime': 'Insufficient data'}
    if fusion is None or fusion.empty:
        return out
    a = fusion[fusion.country.eq(anchor)]
    if a.empty:
        return out
    row = a.iloc[0]
    score = _num(row.get('score'))
    if score is not None:
        out['score'] = round(score, 1)
        out['regime'] = str(row.get('regime', 'Unknown'))
    growth, infl, unemp, real = map(_num, [row.get('growth'), row.get('inflation'), row.get('unemployment'), row.get('real_policy')])
    if growth is not None:
        out['signals'].append(('Growth', 'Supportive' if growth >= 5 else 'Soft', growth))
    if infl is not None:
        out['signals'].append(('Inflation', 'High pressure' if infl >= 6 else 'Moderate/low pressure', infl))
    if real is not None:
        out['signals'].append(('Real policy rate', 'Restrictive' if real > 1 else 'Accommodative/neutral', real))
    if unemp is not None:
        out['signals'].append(('Labor', 'Weak' if unemp >= 8 else 'Firm', unemp))
    # Relative watchlist: largest absolute divergence from anchor.
    x = fusion.copy()
    x['score'] = pd.to_numeric(x['score'], errors='coerce')
    a_score = _num(row.get('score'))
    if a_score is not None:
        x['vs_anchor'] = x['score'] - a_score
        x = x[~x.country.eq(anchor)].dropna(subset=['vs_anchor']).sort_values('vs_anchor')
        for _, r in pd.concat([x.head(3), x.tail(3)]).drop_duplicates('country').iterrows():
            out['watchlist'].append({'country': r['country'], 'vs_anchor': round(float(r['vs_anchor']),1), 'regime': r.get('regime','')})
    return out


def scenario_matrix(base_score: float | None) -> pd.DataFrame:
    """Simple transparent scenario stress overlay, not a forecast."""
    if base_score is None:
        return pd.DataFrame()
    scenarios = [
        ('Soft landing', -10, 'Growth holds; inflation eases'),
        ('Inflation shock', +15, 'Inflation pressure rises'),
        ('Growth shock', +15, 'Growth deteriorates materially'),
        ('Policy easing', -8, 'Real-rate pressure declines'),
        ('Global risk-off', +12, 'Cross-asset stress broadens'),
    ]
    rows=[]
    for name, delta, desc in scenarios:
        s=max(0,min(100,base_score+delta))
        if s < 25: r='Stable'
        elif s < 40: r='Watch'
        elif s < 60: r='Caution'
        else: r='High Stress'
        rows.append({'scenario':name,'score':round(s,1),'regime':r,'assumption':desc})
    return pd.DataFrame(rows)
