#!/usr/bin/env python3
"""健康数据库小工具。用法：
  hdb.py init
  hdb.py meal  --kind 午饭|晚饭|早饭|甜品|饮料|加餐 --desc "..." [--kcal 650] [--cost 32.5] [--photo 路径] [--at "2026-11-08 12:30"] [--note "..."]
  hdb.py report --date 2026-05-20 --org "某医院" --file 路径 [--summary "..."]
  hdb.py item  --report ID --name 空腹血糖 --value 5.4 [--unit mmol/L] [--ref "3.9-6.1"] [--flag 高|低]
  hdb.py workout --kind 走路|无氧|跑步 [--minutes 40] [--detail "卧推 60kg 5x5"] [--at ...]
  hdb.py sleep --night 2026-11-08 [--bed "01:40"] [--wake "09:10"] [--note ...]
  hdb.py sql "SELECT ..."
"""
import argparse, sqlite3, shutil, os, sys, datetime
DB = "/data/work/db/health.db"
FILES = "/data/work/files"
SCHEMA = """
CREATE TABLE IF NOT EXISTS meals(
  id INTEGER PRIMARY KEY, at TEXT NOT NULL, kind TEXT NOT NULL, descr TEXT,
  kcal REAL, cost REAL, photo TEXT, note TEXT, created TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS reports(
  id INTEGER PRIMARY KEY, date TEXT, org TEXT, file TEXT, summary TEXT,
  created TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS report_items(
  id INTEGER PRIMARY KEY, report_id INTEGER REFERENCES reports(id), name TEXT, value TEXT,
  unit TEXT, ref TEXT, flag TEXT);
CREATE INDEX IF NOT EXISTS meals_at ON meals(at);
CREATE TABLE IF NOT EXISTS workouts(
  id INTEGER PRIMARY KEY, at TEXT NOT NULL, kind TEXT, minutes REAL, detail TEXT, note TEXT,
  created TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS sleep_log(
  id INTEGER PRIMARY KEY, night TEXT NOT NULL, bed_at TEXT, wake_at TEXT, note TEXT,
  created TEXT DEFAULT (datetime('now','localtime')));
"""
MIGRATE = {"meals": ["category TEXT", "protein REAL", "carb REAL", "fat REAL", "eaten REAL", "place TEXT"]}
EXTRA = """
CREATE TABLE IF NOT EXISTS places(name TEXT PRIMARY KEY, area TEXT, address TEXT, cuisine TEXT, ordered TEXT,
  healthy_pick TEXT, avoid TEXT, price TEXT, liked TEXT, note TEXT, updated TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS symptoms(id INTEGER PRIMARY KEY, date TEXT, kind TEXT, severity INTEGER, note TEXT,
  created TEXT DEFAULT (datetime('now','localtime')));
"""
def con():
    c = sqlite3.connect(DB); c.executescript(SCHEMA + EXTRA)
    for t, cols in MIGRATE.items():
        have = {r[1] for r in c.execute(f"PRAGMA table_info({t})")}
        for col in cols:
            if col.split()[0] not in have: c.execute(f"ALTER TABLE {t} ADD COLUMN {col}")
    return c
def keep(src, sub):
    if not src: return None
    d = os.path.join(FILES, sub); os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, os.path.basename(src))
    if os.path.abspath(src) != dst: shutil.copy2(src, dst)
    return dst
def main():
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("init")
    m = s.add_parser("meal")
    for a in ("kind","desc","photo","at","note"): m.add_argument("--"+a)
    m.add_argument("--kcal", type=float); m.add_argument("--cost", type=float)
    for x in ("category","place"): m.add_argument("--"+x)
    for x in ("protein","carb","fat","eaten"): m.add_argument("--"+x, type=float)
    up = s.add_parser("mealupd"); up.add_argument("id", type=int)
    for x in ("desc","kcal","cost","category","place","protein","carb","fat","eaten","note"): up.add_argument("--"+x)
    r = s.add_parser("report")
    for a in ("date","org","file","summary"): r.add_argument("--"+a)
    i = s.add_parser("item"); i.add_argument("--report", type=int, required=True)
    for a in ("name","value","unit","ref","flag"): i.add_argument("--"+a)
    w = s.add_parser("workout")
    for x in ("kind","detail","at","note"): w.add_argument("--"+x)
    w.add_argument("--minutes", type=float)
    sl = s.add_parser("sleep")
    for x in ("night","bed","wake","note"): sl.add_argument("--"+x)
    q = s.add_parser("sql"); q.add_argument("q")
    a = p.parse_args(); c = con()
    if a.cmd == "meal":
        at = a.at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        # 每顿饭一个文件夹：正餐 = 日期_类型；甜品/饮料/加餐 = 日期_时分_类型
        sub = f"{at[:10]}_{a.kind}" if a.kind in ("早饭","午饭","晚饭") else f"{at[:10]}_{at[11:16].replace(':','')}_{a.kind}"
        cur = c.execute("INSERT INTO meals(at,kind,descr,kcal,cost,photo,note,category,place,protein,carb,fat,eaten) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (at, a.kind, a.desc, a.kcal, a.cost, keep(a.photo, "meals/"+sub), a.note, a.category, a.place, a.protein, a.carb, a.fat, a.eaten)); print("meal id", cur.lastrowid)
    elif a.cmd == "mealupd":
        for k in ("desc","kcal","cost","category","place","protein","carb","fat","eaten","note"):
            v = getattr(a, k)
            if v is not None: c.execute(f"UPDATE meals SET {'descr' if k=='desc' else k}=? WHERE id=?", (v, a.id))
        print("updated", a.id)
    elif a.cmd == "report":
        cur = c.execute("INSERT INTO reports(date,org,file,summary) VALUES(?,?,?,?)",
            (a.date, a.org, keep(a.file, "reports"), a.summary)); print("report id", cur.lastrowid)
    elif a.cmd == "item":
        cur = c.execute("INSERT INTO report_items(report_id,name,value,unit,ref,flag) VALUES(?,?,?,?,?,?)",
            (a.report, a.name, a.value, a.unit, a.ref, a.flag)); print("item id", cur.lastrowid)
    elif a.cmd == "workout":
        at = a.at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cur = c.execute("INSERT INTO workouts(at,kind,minutes,detail,note) VALUES(?,?,?,?,?)",
            (at, a.kind, a.minutes, a.detail, a.note)); print("workout id", cur.lastrowid)
    elif a.cmd == "sleep":
        cur = c.execute("INSERT INTO sleep_log(night,bed_at,wake_at,note) VALUES(?,?,?,?)",
            (a.night, a.bed, a.wake, a.note)); print("sleep id", cur.lastrowid)
    elif a.cmd == "sql":
        cur = c.execute(a.q)
        if cur.description: print("\t".join(d[0] for d in cur.description))
        for row in cur: print("\t".join("" if v is None else str(v) for v in row))
    c.commit()
    if a.cmd in ("meal","mealupd"): write_txt(c)
def write_txt(c):
    """每个饭的文件夹里写一份 记录.txt（食物、热量、三大营养素、价格）"""
    rows = c.execute("SELECT id,at,kind,descr,category,kcal,protein,carb,fat,eaten,cost,place,note,photo FROM meals WHERE photo IS NOT NULL").fetchall()
    folders = {}
    for r in rows: folders.setdefault(os.path.dirname(r[13]), []).append(r)
    for d, rs in folders.items():
        L = []; tk = tp = 0
        for (i,at,kind,descr,cat,kcal,p,cb,f,eaten,cost,place,note,photo) in rs:
            e = eaten if eaten is not None else 1
            L.append(f"#{i} {at} {kind} @ {place or ''}\n  食物：{descr}\n  类型：{cat or ''}\n  估算(整份)：{kcal or '?'} kcal ｜ 蛋白 {p or '?'}g 碳水 {cb or '?'}g 脂肪 {f or '?'}g\n  实际吃了：{'未确认' if eaten is None else f'{eaten:.0%}'}\n  价格：{cost if cost is not None else '未知'}\n  照片：{os.path.basename(photo)}\n  备注：{note or ''}\n")
            tk += (kcal or 0) * e; tp += (p or 0) * e
        L.append(f"合计（按实际吃的比例，未确认按全吃）：约 {tk:.0f} kcal，蛋白 {tp:.0f} g")
        open(os.path.join(d, "记录.txt"), "w").write("\n".join(L))
if __name__ == "__main__": main()
