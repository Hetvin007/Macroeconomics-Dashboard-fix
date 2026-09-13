import pandas as pd
import numpy as np
from analytics.regime import build_regime_history

ASSET_MAP = {
    'S&P 500': ('us_sp500', 'return'),
    'US Dollar Index': ('us_dollar_index', 'return'),
    'US 10Y Treasury Yield': ('us_10y', 'change'),
    'US 2Y Treasury Yield': ('us_2y', 'change'),
}


def _series(obs, indicator_id, country='United States'):
    x = obs[(obs.indicator_id == indicator_id) & (obs.country == country)].copy()
    if x.empty:
        return pd.Series(dtype=float)
    x['date'] = pd.to_datetime(x['date'], errors='coerce')
    x['value'] = pd.to_numeric(x['value'], errors='coerce')
    return x.dropna(subset=['date','value']).sort_values('date').drop_duplicates('date').set_index('date')['value']


def _month_end(s):
    if s.empty:
        return s
    return s.resample('ME').last().dropna()


def _forward_return(s, months):
    m = _month_end(s)
    if m.empty:
        return pd.Series(dtype=float)
    future = m.shift(-months)
    return (future / m - 1.0) * 100.0


def _forward_change(s, months):
    m = _month_end(s)
    if m.empty:
        return pd.Series(dtype=float)
    return m.shift(-months) - m


def build_macro_backtest(obs, country='IND', target=4.0, horizon_months=3):
    """Historical regime-to-market study using only observations stored in the database.

    Macro regime is sampled at month-end. Asset outcomes are subsequent market moves.
    Results are descriptive historical relationships, not forecasts or causal estimates.
    """
    hist = build_regime_history(obs, target=target, country=country)
    if hist.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    hist = hist.copy()
    hist['date'] = pd.to_datetime(hist['date'], errors='coerce')
    hist = hist.dropna(subset=['date','score'])
    macro = hist.set_index('date').resample('ME').last().dropna(subset=['score'])
    if macro.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    rows = []
    for asset, (iid, kind) in ASSET_MAP.items():
        s = _series(obs, iid)
        if s.empty:
            continue
        outcome = _forward_return(s, horizon_months) if kind == 'return' else _forward_change(s, horizon_months)
        outcome.name = 'forward_outcome'
        joined = macro[['score','regime']].join(outcome, how='inner').dropna(subset=['forward_outcome'])
        if joined.empty:
            continue
        joined = joined.reset_index().rename(columns={'index':'date'})
        joined['asset'] = asset
        joined['horizon_months'] = horizon_months
        joined['macro_change'] = joined['score'].diff()
        rows.extend(joined.to_dict('records'))
    panel = pd.DataFrame(rows)
    if panel.empty:
        return panel, pd.DataFrame(), pd.DataFrame()

    summary_rows = []
    for (asset, reg), g in panel.groupby(['asset','regime']):
        vals = pd.to_numeric(g['forward_outcome'], errors='coerce').dropna()
        if vals.empty:
            continue
        summary_rows.append({
            'asset': asset,
            'regime': reg,
            'observations': len(vals),
            'avg_forward_move': vals.mean(),
            'median_forward_move': vals.median(),
            'positive_rate_pct': (vals.gt(0).mean()*100),
            'worst': vals.min(),
            'best': vals.max(),
        })
    summary = pd.DataFrame(summary_rows)

    beta_rows = []
    for asset, g in panel.groupby('asset'):
        z = g[['macro_change','forward_outcome']].dropna()
        if len(z) >= 4 and z['macro_change'].std() > 0:
            beta = z['macro_change'].cov(z['forward_outcome']) / z['macro_change'].var()
            corr = z['macro_change'].corr(z['forward_outcome'])
        else:
            beta, corr = np.nan, np.nan
        beta_rows.append({'asset':asset,'observations':len(z),'macro_score_change_beta':beta,'correlation':corr})
    betas = pd.DataFrame(beta_rows)
    return panel.sort_values(['date','asset']), summary.sort_values(['asset','regime']), betas


def rolling_relationship(panel, asset, window=12):
    if panel.empty:
        return pd.DataFrame()
    g=panel[panel.asset.eq(asset)].copy().sort_values('date')
    if g.empty:
        return pd.DataFrame()
    g['rolling_corr']=g['macro_change'].rolling(window).corr(g['forward_outcome'])
    return g[['date','rolling_corr']].dropna()
