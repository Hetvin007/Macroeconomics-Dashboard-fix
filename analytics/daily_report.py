from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from analytics.brief import generate_daily_brief
from analytics.alerts import detect_alerts, freshness_alerts


def build_report(obs, consensus=None):
    now=datetime.now(timezone.utc).isoformat()
    bullets=generate_daily_brief(obs, consensus if consensus is not None else pd.DataFrame())
    alerts=pd.concat([detect_alerts(obs), freshness_alerts(obs)], ignore_index=True)
    lines=["# Daily Macro Intelligence Brief", "", f"Generated: {now}", "", "## Executive takeaways"]
    lines += [f"- {b}" for b in bullets]
    lines += ["", "## Alerts"]
    if alerts.empty: lines.append("- No threshold alerts detected from loaded observations.")
    else:
        for _,r in alerts.head(20).iterrows(): lines.append(f"- **{r.severity}** — {r.country} / {r.indicator_id}: {r.message}")
    lines += ["", "## Methodology", "This report uses only observations loaded into the local database. Alerts are transparent rule-based diagnostics, not forecasts or investment recommendations."]
    return "\n".join(lines)


def save_report(text, root):
    out=Path(root)/'reports'; out.mkdir(exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    path=out/f'macro_brief_{stamp}.md'; path.write_text(text,encoding='utf-8'); return path
