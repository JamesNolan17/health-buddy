#!/usr/bin/env python3
"""记账小工具 / expense ledger（数据来自 payments 表，扣款短信自动进来；只用标准库）
  spend.py month [2026-11]            本月按分类、按商家汇总
  spend.py today                      今天的每一笔
  spend.py day [2026-11-08]           今天 餐饮 vs 其他 的合计、饮料杯数，和近 30 天日均对比（晚间小结用）
  spend.py cat <file> <分类>           给一笔消费打分类（餐饮/饮料/甜品/交通/购物/订阅/医疗/其他），并记住这家商家的分类
  spend.py known <商家>                商家记忆：分类、常点的东西、来过几次（看到熟店就不用再问）
  spend.py learn <商家> <分类> [常点]   手动教它一家商家
  spend.py cards [2026-11]            每张卡本月刷了多少；配置了 cards.json 的卡会算离最低消费还差多少
  spend.py chart [2026-11] [out.png]  月度图：装了 matplotlib 就出 PNG（每日 餐饮 vs 其他 + 分类饼图），否则打印字符条形图
"""
import calendar, datetime, json, os, sqlite3, sys

DB = "/data/work/db/health.db"; WORK = "/data/work"
FOOD = ("餐饮", "饮料", "甜品")                       # 算作“吃饭花的钱” / counts as food spend
DRINK = ("饮料", "甜品")
c = sqlite3.connect(DB)
c.executescript("""
CREATE TABLE IF NOT EXISTS payments(file TEXT PRIMARY KEY, received TEXT, sender TEXT, text TEXT,
  kind TEXT, bank TEXT, currency TEXT, amount REAL, card TEXT, tdate TEXT, merchant TEXT, meal_id INTEGER, handled INTEGER DEFAULT 0, category TEXT);
CREATE TABLE IF NOT EXISTS merchants(merchant TEXT PRIMARY KEY, category TEXT, usual TEXT, note TEXT,
  times INTEGER DEFAULT 0, last_seen TEXT);
""")
try: c.execute("ALTER TABLE payments ADD COLUMN category TEXT")
except Exception: pass

def arg(i, default=None): return sys.argv[i] if len(sys.argv) > i else default
def month_of(s): return s[:7]
def fmt(v): return f"{v:,.2f}"

def remember(merchant, category=None, usual=None, when=None):
    """upsert merchant memory; bump visit counter"""
    if not merchant: return
    row = c.execute("SELECT category, usual, times FROM merchants WHERE merchant=?", (merchant,)).fetchone()
    cat = category or (row[0] if row else None); us = usual or (row[1] if row else None)
    times = (row[2] if row else 0) + (1 if when else 0)
    c.execute("INSERT OR REPLACE INTO merchants(merchant,category,usual,note,times,last_seen) VALUES(?,?,?,(SELECT note FROM merchants WHERE merchant=?),?,?)",
              (merchant, cat, us, merchant, times, when or (row and c.execute("SELECT last_seen FROM merchants WHERE merchant=?", (merchant,)).fetchone()[0])))

cmd = arg(1, "month")

if cmd == "cat":
    f, cat = arg(2), arg(3)
    c.execute("UPDATE payments SET category=? WHERE file=?", (cat, f))
    m = c.execute("SELECT merchant, received FROM payments WHERE file=?", (f,)).fetchone()
    if m and m[0]: remember(m[0], cat, when=m[1][:10])
    c.commit(); print("ok", cat, "·", (m[0] if m else ""))

elif cmd == "learn":
    remember(arg(2), arg(3), arg(4)); c.commit(); print("ok")

elif cmd == "known":
    m = arg(2, "")
    r = c.execute("SELECT merchant, category, usual, note, times, last_seen FROM merchants WHERE merchant LIKE ?", (f"%{m}%",)).fetchone()
    if not r: print("UNKNOWN"); sys.exit()
    print(f"KNOWN merchant={r[0]} category={r[1] or '?'} usual={r[2] or '-'} times={r[4]} last_seen={r[5] or '-'} note={r[3] or ''}")
    for row in c.execute("SELECT received, currency, amount FROM payments WHERE merchant=? AND kind='spend' ORDER BY received DESC LIMIT 5", (r[0],)):
        print("  ", *row)

elif cmd == "today" or cmd == "day":
    d = arg(2, datetime.date.today().isoformat()) if cmd == "day" else datetime.date.today().isoformat()
    rows = c.execute("SELECT received, currency, amount, merchant, coalesce(category,'未分类'), card FROM payments WHERE kind='spend' AND substr(received,1,10)=? ORDER BY received", (d,)).fetchall()
    if cmd == "today":
        for r in rows: print(*r)
        sys.exit()
    food = sum(r[2] or 0 for r in rows if r[4] in FOOD); other = sum(r[2] or 0 for r in rows if r[4] not in FOOD)
    drinks = sum(1 for r in rows if r[4] in DRINK)
    since = (datetime.date.fromisoformat(d) - datetime.timedelta(days=30)).isoformat()
    avg = c.execute("""SELECT coalesce(sum(CASE WHEN category IN (?,?,?) THEN amount END),0)/30.0,
                              coalesce(sum(CASE WHEN category NOT IN (?,?,?) OR category IS NULL THEN amount END),0)/30.0
                       FROM payments WHERE kind='spend' AND substr(received,1,10)>=? AND substr(received,1,10)<?""", (*FOOD, *FOOD, since, d)).fetchone()
    print(f"== {d}  餐饮 {fmt(food)}  其他 {fmt(other)}  饮料/甜品 {drinks} 杯/份  笔数 {len(rows)}")
    print(f"== 近 30 天日均  餐饮 {fmt(avg[0])}  其他 {fmt(avg[1])}")
    if avg[0] > 0: print(f"== 餐饮是日均的 {food / avg[0]:.1f} 倍")
    for r in rows: print("  ", *r)

elif cmd == "cards":
    m = arg(2, datetime.date.today().strftime("%Y-%m"))
    y, mo = map(int, m.split("-")); last = calendar.monthrange(y, mo)[1]
    today = datetime.date.today(); days_left = (last - today.day) if today.strftime("%Y-%m") == m else 0
    cfg = {}
    try: cfg = {str(x["card"]): x for x in json.load(open(f"{WORK}/cards.json"))}
    except Exception: pass
    print(f"== {m} 每张卡 / per card")
    seen = set()
    for card, cur, total, n in c.execute("SELECT coalesce(card,'?'), currency, round(sum(amount),2), count(*) FROM payments WHERE kind='spend' AND substr(received,1,7)=? GROUP BY 1,2 ORDER BY 3 DESC", (m,)):
        seen.add(card); k = cfg.get(card, {}); name = k.get("name", "")
        line = f"尾号 {card} {name}  {cur} {fmt(total)}  {n} 笔"
        if k.get("min_spend"):
            gap = k["min_spend"] - total
            line += f"  | 最低消费 {fmt(k['min_spend'])} → " + (f"还差 {fmt(gap)}，剩 {days_left} 天" if gap > 0 else "✅ 已达标")
        print(line)
    for card, k in cfg.items():
        if card not in seen and k.get("min_spend"):
            print(f"尾号 {card} {k.get('name','')}  本月 0.00  | 最低消费 {fmt(k['min_spend'])} → 还差 {fmt(k['min_spend'])}，剩 {days_left} 天")

elif cmd == "chart":
    m = arg(2, datetime.date.today().strftime("%Y-%m"))
    y, mo = map(int, m.split("-")); last = calendar.monthrange(y, mo)[1]
    days = [f"{m}-{d:02d}" for d in range(1, last + 1)]
    food = {d: 0.0 for d in days}; other = {d: 0.0 for d in days}
    for d, cat, amt in c.execute("SELECT substr(received,1,10), category, amount FROM payments WHERE kind='spend' AND substr(received,1,7)=?", (m,)):
        if d in food: (food if cat in FOOD else other)[d] += amt or 0
    cats = c.execute("SELECT coalesce(category,'未分类'), round(sum(amount),2) FROM payments WHERE kind='spend' AND substr(received,1,7)=? GROUP BY 1 ORDER BY 2 DESC", (m,)).fetchall()
    out = arg(3, f"{WORK}/files/charts/spend-{m}.png")
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for fp in ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
            if os.path.exists(fp): font_manager.fontManager.addfont(fp); plt.rcParams["font.family"] = font_manager.FontProperties(fname=fp).get_name(); break
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6), gridspec_kw={"width_ratios": [3, 1.3]})
        x = list(range(1, last + 1)); fv = [food[d] for d in days]; ov = [other[d] for d in days]
        a1.bar(x, fv, color="#f59e0b", label="餐饮 food"); a1.bar(x, ov, bottom=fv, color="#60a5fa", label="其他 other")
        a1.set_title(f"{m} 每日消费 / daily spend"); a1.legend(frameon=False); a1.spines[["top", "right"]].set_visible(False)
        if cats: a2.pie([v for _, v in cats], labels=[k for k, _ in cats], startangle=90, wedgeprops={"width": 0.45})
        a2.set_title("分类 / by category")
        os.makedirs(os.path.dirname(out), exist_ok=True); fig.tight_layout(); fig.savefig(out, dpi=160); print("PNG", out)
    except ImportError:
        print("（没装 matplotlib，用字符图。想要 PNG：sudo apt-get install -y python3-matplotlib fonts-noto-cjk，并写进 /data/setup.sh）")
        mx = max([food[d] + other[d] for d in days] + [1])
        for d in days:
            t = food[d] + other[d]
            if t: print(f"{d[-2:]}  {'█' * int(food[d] / mx * 30)}{'░' * int(other[d] / mx * 30)} {fmt(t)}")
        print("█ 餐饮  ░ 其他")
    print(f"== {m} 合计 餐饮 {fmt(sum(food.values()))}  其他 {fmt(sum(other.values()))}")
    for k, v in cats: print(f"   {k}: {fmt(v)}")

else:  # month
    m = arg(2, datetime.date.today().strftime("%Y-%m"))
    print(f"== {m} 按分类 / by category")
    for r in c.execute("SELECT coalesce(category,'未分类'), currency, round(sum(amount),2), count(*) FROM payments WHERE kind='spend' AND substr(received,1,7)=? GROUP BY 1,2 ORDER BY 3 DESC", (m,)):
        print(*r)
    print(f"== {m} 商家 Top 10 / top merchants")
    for r in c.execute("SELECT merchant, currency, round(sum(amount),2), count(*) FROM payments WHERE kind='spend' AND substr(received,1,7)=? GROUP BY 1,2 ORDER BY 3 DESC LIMIT 10", (m,)):
        print(*r)
    print(f"== {m} 每张卡 / per card")
    for r in c.execute("SELECT coalesce(card,'?'), currency, round(sum(amount),2), count(*) FROM payments WHERE kind='spend' AND substr(received,1,7)=? GROUP BY 1,2 ORDER BY 3 DESC", (m,)):
        print("尾号", *r)
c.commit()
