from datetime import datetime, timezone
import pandas as pd
from analytics.surprise import calculate_surprises


def generate_daily_brief(obs: pd.DataFrame, events: pd.DataFrame, focus='India') -> list[str]:
    bullets=[]
    if obs is not None and not obs.empty:
        x=obs.copy(); x['date']=pd.to_datetime(x['date'],errors='coerce'); x=x.sort_values('date')
        recent=x[x['date']>=x['date'].max()-pd.Timedelta(days=45)]
        for key,label in [('gdp_growth','Growth'),('inflation','Inflation'),('unemployment','Unemployment')]:
            z=recent[recent.indicator_id.str.contains(key,case=False,na=False)]
            z=z[z.country.isin(['IND','India'])]
            if len(z)>=1:
                r=z.iloc[-1]
                bullets.append(f"{label}: {float(r.value):.2f} on {r.date.date()} (source: {r.source}).")
    if events is not None and not events.empty:
        s=calculate_surprises(events)
        s=s[s['date'].notna()].sort_values('date',ascending=False)
        for _,r in s.head(3).iterrows():
            if pd.notna(r.get('surprise')):
                bullets.append(f"{r.get('release','Release')}: {r['direction']} by {r['surprise']:.2f} ({r.get('country','')}).")
    if not bullets:
        bullets.append('No sufficiently recent observations or validated consensus events are loaded yet.')
    return bullets
