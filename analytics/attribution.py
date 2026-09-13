import pandas as pd


def classify_surprise(event):
    """Classify macro surprise into directional macro impulse buckets.
    Uses explicit event metadata where supplied; otherwise conservative name rules.
    """
    name = str(event.get('event_name', '')).lower()
    surprise = event.get('surprise')
    if pd.isna(surprise):
        return 'No surprise'
    try:
        s = float(surprise)
    except Exception:
        return 'Unknown'
    if any(k in name for k in ['cpi', 'inflation', 'ppi', 'prices']):
        return 'Inflationary' if s > 0 else 'Disinflationary'
    if any(k in name for k in ['unemployment', 'jobless', 'claims']):
        return 'Labor-strong' if s < 0 else 'Labor-weak'
    if any(k in name for k in ['gdp', 'retail sales', 'industrial production', 'payroll', 'employment']):
        return 'Growth-positive' if s > 0 else 'Growth-negative'
    if any(k in name for k in ['fed', 'ecb', 'rbi', 'boe', 'boj', 'rate decision']):
        return 'Hawkish' if s > 0 else 'Dovish'
    return 'Positive surprise' if s > 0 else 'Negative surprise'


def reaction_label(row):
    rates = row.get('rates_direction')
    usd = row.get('usd_direction')
    eq = row.get('equity_direction')
    if pd.isna(rates) and pd.isna(usd) and pd.isna(eq):
        return 'Insufficient market data'
    # Direction is expressed as observed change, not causal sign.
    if rates > 0 and usd > 0 and eq < 0:
        return 'Tightening-style response'
    if rates < 0 and usd < 0 and eq > 0:
        return 'Easing-style response'
    if rates > 0 and eq > 0:
        return 'Growth/risk-positive despite higher yields'
    if rates < 0 and eq < 0:
        return 'Growth/risk-negative despite lower yields'
    return 'Mixed / cross-asset response'


def cross_asset_attribution(reaction_df):
    if reaction_df is None or reaction_df.empty:
        return pd.DataFrame()
    df = reaction_df.copy()
    for c in ['rates_change', 'usd_change', 'equity_change', 'surprise']:
        if c not in df:
            df[c] = pd.NA
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['rates_direction'] = df['rates_change']
    df['usd_direction'] = df['usd_change']
    df['equity_direction'] = df['equity_change']
    df['macro_impulse'] = df.apply(classify_surprise, axis=1)
    df['market_response'] = df.apply(reaction_label, axis=1)
    # Consistency is descriptive: compare observed signs with common tightening/easing patterns.
    def consistency(r):
        vals = [r['rates_change'], r['usd_change'], r['equity_change']]
        if sum(pd.notna(x) for x in vals) < 2:
            return 'Low evidence'
        if (r['rates_change'] > 0 and r['usd_change'] > 0 and r['equity_change'] < 0) or (r['rates_change'] < 0 and r['usd_change'] < 0 and r['equity_change'] > 0):
            return 'High'
        if len([x for x in vals if pd.notna(x)]) >= 2:
            return 'Mixed'
        return 'Low evidence'
    df['response_consistency'] = df.apply(consistency, axis=1)
    return df
