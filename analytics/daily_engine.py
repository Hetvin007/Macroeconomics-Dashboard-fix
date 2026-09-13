from datetime import datetime, timezone
import pandas as pd
from analytics.events import normalize_event_table

def build_intelligence(obs, consensus=None, release_calendar=None):
    lines=[]
    if obs is not None and not obs.empty:
        for country in ['India','United States']:
            x=obs[obs.country.eq(country)].sort_values('date')
            if x.empty: continue
            recent=x.tail(1).iloc[0]
            lines.append(f'{country}: latest loaded observation is {recent.indicator_id} = {recent.value:g} on {recent.date}.')
    events=normalize_event_table(consensus if consensus is not None else pd.DataFrame())
    if not events.empty:
        events=events.sort_values('significance',ascending=False)
        for _,r in events.head(5).iterrows():
            lines.append(f"{r.get('event_name',r.get('indicator_id','Event'))}: {r.direction} by {r.surprise:g} ({r.surprise_pct:.2f}% vs consensus).")
    upcoming=release_calendar if release_calendar is not None else pd.DataFrame()
    if not upcoming.empty:
        today=datetime.now(timezone.utc).date().isoformat()
        u=upcoming[upcoming.release_date>=today].sort_values('release_date').head(5)
        if not u.empty: lines.append('Next scheduled releases: '+', '.join(f"{r.name} ({r.release_date})" for _,r in u.iterrows()))
    return lines
