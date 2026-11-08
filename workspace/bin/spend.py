#!/usr/bin/env python3
"""记账汇总 / spending summary（数据来自 payments 表，扣款短信自动进来）
  spend.py month [2026-11]     本月按分类、按商家汇总
  spend.py today               今天的每一笔
  spend.py cat <file> <分类>    给一笔消费打分类（餐饮/饮料/甜品/交通/购物/订阅/医疗/其他）"""
import sqlite3, sys, datetime
c = sqlite3.connect("/data/work/db/health.db")
try: c.execute("ALTER TABLE payments ADD COLUMN category TEXT")
except Exception: pass
cmd = sys.argv[1] if len(sys.argv) > 1 else "month"
if cmd == "cat":
    c.execute("UPDATE payments SET category=? WHERE file=?", (sys.argv[3], sys.argv[2])); c.commit(); print("ok")
elif cmd == "today":
    d = datetime.date.today().isoformat()
    for r in c.execute("SELECT received, currency, amount, merchant, coalesce(category,'未分类') FROM payments WHERE kind='spend' AND substr(received,1,10)=? ORDER BY received", (d,)):
        print(*r)
else:
    m = sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().strftime("%Y-%m")
    print(f"== {m} 按分类 / by category")
    for r in c.execute("SELECT coalesce(category,'未分类'), currency, round(sum(amount),2), count(*) FROM payments WHERE kind='spend' AND substr(received,1,7)=? GROUP BY 1,2 ORDER BY 3 DESC", (m,)):
        print(*r)
    print(f"== {m} 商家 Top 10 / top merchants")
    for r in c.execute("SELECT merchant, currency, round(sum(amount),2), count(*) FROM payments WHERE kind='spend' AND substr(received,1,7)=? GROUP BY 1,2 ORDER BY 3 DESC LIMIT 10", (m,)):
        print(*r)
