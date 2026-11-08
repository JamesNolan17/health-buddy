#!/usr/bin/env python3
"""把 /data/inbox/health/*.json (Health Auto Export v2) 导入 health.db，原件归档到 /data/work/files/raw/health/"""
import json, os, sqlite3, shutil, sys, glob
DB="/data/work/db/health.db"; SRC="/data/inbox/health"; ARC="/data/work/files/raw/health"
os.makedirs(ARC, exist_ok=True)
c=sqlite3.connect(DB)
c.executescript("""
CREATE TABLE IF NOT EXISTS metrics(metric TEXT, date TEXT, units TEXT, qty REAL, min REAL, avg REAL, max REAL, source TEXT,
  PRIMARY KEY(metric,date,source));
CREATE TABLE IF NOT EXISTS sleep(date TEXT, source TEXT, sleep_start TEXT, sleep_end TEXT, in_bed_start TEXT, in_bed_end TEXT,
  total REAL, deep REAL, core REAL, rem REAL, awake REAL, in_bed REAL, asleep REAL, PRIMARY KEY(date,source));
CREATE TABLE IF NOT EXISTS hae_workouts(id TEXT PRIMARY KEY, name TEXT, start TEXT, end TEXT, duration REAL, raw TEXT);
""")
files=sorted(glob.glob(SRC+"/*.json")); n=0; bad=0
for f in files:
    try: d=json.load(open(f))
    except Exception as e:
        # 可能还在写入，下次再处理
        bad+=1; continue
    data=d.get("data",d)
    for m in data.get("metrics",[]):
        name=m.get("name"); u=m.get("units")
        for r in m.get("data",[]):
            src=r.get("source") or ""
            if name=="sleep_analysis":
                c.execute("INSERT OR REPLACE INTO sleep VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(r.get("date"),src,r.get("sleepStart"),r.get("sleepEnd"),
                  r.get("inBedStart"),r.get("inBedEnd"),r.get("totalSleep"),r.get("deep"),r.get("core"),r.get("rem"),r.get("awake"),r.get("inBed"),r.get("asleep")))
            else:
                c.execute("INSERT OR REPLACE INTO metrics VALUES(?,?,?,?,?,?,?,?)",(name,r.get("date"),u,r.get("qty"),r.get("Min"),r.get("Avg"),r.get("Max"),src))
            n+=1
    for w in data.get("workouts",[]):
        c.execute("INSERT OR REPLACE INTO hae_workouts VALUES(?,?,?,?,?,?)",(w.get("id") or w.get("start"),w.get("name"),w.get("start"),w.get("end"),
          (w.get("duration")), json.dumps(w,ensure_ascii=False)))
    c.commit()
    shutil.move(f, os.path.join(ARC, os.path.basename(f)))
print(f"files={len(files)-bad} rows={n} pending_bad={bad}")
