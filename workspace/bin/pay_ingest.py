#!/usr/bin/env python3
"""/data/inbox/pay/*.json → health.db 的 payments 表；原件归档到 files/raw/pay/
消费短信的识别规则在 /data/work/pay_patterns.json（正则，命名分组 currency/amount/card/date/merchant）。
认不出来的短信（还款提醒、账单等）记为 kind=other，不当消费。"""
import glob, json, os, re, shutil, sqlite3
SRC = "/data/inbox/pay"; ARC = "/data/work/files/raw/pay"; os.makedirs(ARC, exist_ok=True)
PATS = [dict(p, rx=re.compile(p["regex"])) for p in json.load(open("/data/work/pay_patterns.json"))]
c = sqlite3.connect("/data/work/db/health.db")
c.execute("""CREATE TABLE IF NOT EXISTS payments(file TEXT PRIMARY KEY, received TEXT, sender TEXT, text TEXT,
  kind TEXT, bank TEXT, currency TEXT, amount REAL, card TEXT, tdate TEXT, merchant TEXT, meal_id INTEGER, handled INTEGER DEFAULT 0, category TEXT)""")
n = 0
for f in sorted(glob.glob(SRC + "/*.json")):
    b = os.path.basename(f)
    try: d = json.load(open(f))
    except Exception: continue
    if not isinstance(d, dict): d = {"text": json.dumps(d, ensure_ascii=False)}
    text = str(d.get("text") or "")
    row = dict(kind="other", bank=None, currency=None, amount=None, card=None, tdate=None, merchant=None)
    for p in PATS:
        m = p["rx"].search(text)
        if not m: continue
        g = m.groupdict()
        row.update(kind="spend", bank=p["bank"], currency=g.get("currency") or p.get("default_currency"),
                   amount=float(g["amount"].replace(",", "")), card=g.get("card"), merchant=(g.get("merchant") or "").strip())
        if g.get("date") and p.get("date_format") == "dd/mm/yy":
            dd, mm, yy = g["date"].split("/"); row["tdate"] = f"20{yy}-{mm}-{dd}"
        break
    r = b[:15]; received = f"{r[:4]}-{r[4:6]}-{r[6:8]} {r[9:11]}:{r[11:13]}:{r[13:15]}"
    c.execute("INSERT OR IGNORE INTO payments(file,received,sender,text,kind,bank,currency,amount,card,tdate,merchant) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
              (b, received, d.get("sender"), text, row["kind"], row["bank"], row["currency"], row["amount"], row["card"], row["tdate"], row["merchant"]))
    c.commit(); shutil.move(f, os.path.join(ARC, b)); n += 1
print(f"pay files={n}")
