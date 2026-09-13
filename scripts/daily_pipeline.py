"""v1.2 event-driven pipeline. Requires FRED_API_KEY for the FRED calendar/market layer."""
import pathlib, subprocess, sys
BASE=pathlib.Path(__file__).resolve().parents[1]
for cmd in [[sys.executable,str(BASE/'refresh.py')],[sys.executable,str(BASE/'scripts/event_refresh.py')]]:
    p=subprocess.run(cmd,cwd=BASE); 
    if p.returncode: raise SystemExit(p.returncode)
print('Daily macro pipeline complete')
