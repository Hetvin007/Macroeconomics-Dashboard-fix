import pandas as pd


def _zscore(s):
    s = pd.to_numeric(s, errors='coerce')
    if s.notna().sum() < 2 or s.std(ddof=0) == 0:
        return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / s.std(ddof=0)


def build_relative_macro(fusion: pd.DataFrame, anchor: str = 'India') -> pd.DataFrame:
    """Compare each economy's macro profile with an anchor economy.

    Positive relative score means the economy looks stronger on the configured
    growth/inflation/labor/rate dimensions. This is a transparent heuristic,
    not a forecast or investment recommendation.
    """
    if fusion is None or fusion.empty:
        return pd.DataFrame()
    x = fusion.copy()
    for c in ['growth','inflation','unemployment','policy_rate','real_policy','score']:
        if c not in x.columns:
            x[c] = pd.NA
        x[c] = pd.to_numeric(x[c], errors='coerce')
    # Higher growth and real policy rate are treated as supportive; lower
    # inflation and unemployment are treated as supportive.
    x['growth_component'] = _zscore(x['growth'])
    x['inflation_component'] = -_zscore(x['inflation'])
    x['labor_component'] = -_zscore(x['unemployment'])
    x['real_rate_component'] = _zscore(x['real_policy'])
    x['relative_score'] = (
        0.35*x['growth_component'] +
        0.25*x['inflation_component'] +
        0.20*x['labor_component'] +
        0.20*x['real_rate_component']
    ) * 20
    if anchor in set(x['country']):
        a = x.loc[x['country'].eq(anchor), 'relative_score'].iloc[0]
        x['vs_anchor'] = x['relative_score'] - a
    else:
        x['vs_anchor'] = pd.Series(float('nan'), index=x.index, dtype='float64')
    x['relative_regime'] = pd.cut(
        x['vs_anchor'],
        bins=[-float('inf'), -15, -5, 5, 15, float('inf')],
        labels=['Much weaker','Weaker','Similar','Stronger','Much stronger']
    ).astype('string')
    x['anchor'] = anchor
    return x.sort_values('vs_anchor', ascending=False).reset_index(drop=True)


def pairwise_matrix(relative: pd.DataFrame, countries=None) -> pd.DataFrame:
    if relative is None or relative.empty:
        return pd.DataFrame()
    x = relative[['country','relative_score']].dropna().drop_duplicates('country').set_index('country')
    if countries:
        x = x.reindex([c for c in countries if c in x.index]).dropna()
    if x.empty:
        return pd.DataFrame()
    vals = x['relative_score']
    return pd.DataFrame({c: vals - vals.loc[c] for c in vals.index}, index=vals.index)
