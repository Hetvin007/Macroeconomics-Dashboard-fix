from datetime import datetime, timezone

def init_events(con):
    con.executescript('''
    CREATE TABLE IF NOT EXISTS release_calendar (
      release_id TEXT PRIMARY KEY, provider TEXT, name TEXT, country TEXT,
      release_date TEXT, source_url TEXT, status TEXT, retrieved_at TEXT
    );
    CREATE TABLE IF NOT EXISTS event_log (
      event_key TEXT PRIMARY KEY, provider TEXT, event_type TEXT, name TEXT,
      country TEXT, event_date TEXT, actual REAL, previous REAL, consensus REAL,
      surprise REAL, surprise_pct REAL, direction TEXT, significance REAL,
      source_url TEXT, observed_at TEXT
    );
    CREATE TABLE IF NOT EXISTS revision_log (
      revision_key TEXT PRIMARY KEY, indicator_id TEXT, country TEXT, date TEXT,
      old_value REAL, new_value REAL, delta REAL, source TEXT, detected_at TEXT
    );
    CREATE TABLE IF NOT EXISTS fred_vintages (
      indicator_id TEXT, country TEXT, date TEXT, value REAL, vintage_date TEXT,
      source TEXT, source_url TEXT, retrieved_at TEXT,
      PRIMARY KEY(indicator_id,country,date,vintage_date)
    );
    CREATE TABLE IF NOT EXISTS refresh_runs (
      run_id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT, finished_at TEXT,
      source TEXT, status TEXT, observations INTEGER, errors INTEGER, message TEXT
    );
    '''); con.commit()

def log_run(con, source, status, observations=0, errors=0, message=''):
    now=datetime.now(timezone.utc).isoformat()
    cur=con.execute('INSERT INTO refresh_runs(started_at,finished_at,source,status,observations,errors,message) VALUES(?,?,?,?,?,?,?)',
                    (now,now,source,status,observations,errors,message))
    con.commit(); return cur.lastrowid

def upsert_release_dates(con, df):
    if df is None or df.empty: return 0
    now=datetime.now(timezone.utc).isoformat()
    n=0
    for r in df.to_dict('records'):
        key=f"{r.get('provider','FRED')}:{r['release_id']}:{r['date']}"
        con.execute('''INSERT INTO release_calendar(release_id,provider,name,country,release_date,source_url,status,retrieved_at)
                       VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(release_id) DO UPDATE SET
                       provider=excluded.provider,name=excluded.name,country=excluded.country,
                       release_date=excluded.release_date,source_url=excluded.source_url,status=excluded.status,retrieved_at=excluded.retrieved_at''',
                    (key,r.get('provider','FRED'),r.get('name',''),r.get('country',''),r['date'],r.get('source_url',''),r.get('status','scheduled'),now)); n+=1
    con.commit(); return n

def record_revision(con, indicator_id, country, date, old_value, new_value, source):
    if old_value == new_value: return False
    key=f'{indicator_id}:{country}:{date}:{old_value}:{new_value}'
    con.execute('INSERT OR IGNORE INTO revision_log VALUES(?,?,?,?,?,?,?,?,?)',
                (key,indicator_id,country,date,old_value,new_value,new_value-old_value,source,datetime.now(timezone.utc).isoformat()))
    con.commit(); return True


def upsert_fred_vintages(con, df):
    if df is None or df.empty: return 0
    now=datetime.now(timezone.utc).isoformat(); n=0
    for r in df.to_dict('records'):
        con.execute('''INSERT INTO fred_vintages(indicator_id,country,date,value,vintage_date,source,source_url,retrieved_at)
                       VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(indicator_id,country,date,vintage_date) DO UPDATE SET
                       value=excluded.value,source=excluded.source,source_url=excluded.source_url,retrieved_at=excluded.retrieved_at''',
                    (r['indicator_id'],r['country'],r['date'],r['value'],r['vintage_date'],r.get('source','FRED/ALFRED'),r.get('source_url',''),now)); n+=1
    con.commit(); return n
