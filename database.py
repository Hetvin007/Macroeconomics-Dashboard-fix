import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from event_db import init_events, record_revision
DB=Path(__file__).resolve().parent/'data'/'macro.sqlite'

def connect():
 DB.parent.mkdir(exist_ok=True); c=sqlite3.connect(DB); init_events(c)
 c.execute("""CREATE TABLE IF NOT EXISTS observations(indicator_id TEXT,country TEXT,date TEXT,value REAL,source TEXT,source_url TEXT,retrieved_at TEXT,PRIMARY KEY(indicator_id,country,date))"""); return c

def upsert(c,indicator_id,df):
 if df is None or df.empty:return 0
 now=datetime.now(timezone.utc).isoformat()
 for r in df.to_dict('records'):
  old=c.execute("SELECT value FROM observations WHERE indicator_id=? AND country=? AND date=?",(indicator_id,r['country'],r['date'])).fetchone()
  if old is not None and old[0] != r['value']:
   record_revision(c,indicator_id,r['country'],r['date'],old[0],r['value'],r.get('source',''))
  c.execute("""INSERT INTO observations VALUES(?,?,?,?,?,?,?) ON CONFLICT(indicator_id,country,date) DO UPDATE SET value=excluded.value,source=excluded.source,source_url=excluded.source_url,retrieved_at=excluded.retrieved_at""",(indicator_id,r['country'],r['date'],r['value'],r['source'],r['source_url'],now))
 c.commit(); return len(df)
