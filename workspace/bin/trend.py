#!/usr/bin/env python3
"""健康趋势 / health trend（metrics 表，Apple Health 导入；只用标准库）
  trend.py <metric> [days]            最近 N 天（默认 30）的日值 + 字符迷你折线，这周均值 vs 前 30 天均值
  trend.py <metric> [days] --png out  装了 matplotlib 就另外画一张 PNG（没装就只打印）
  trend.py list                       看有哪些指标名
常用 metric：resting_heart_rate、heart_rate_variability、step_count、apple_sleeping_wrist_temperature、active_energy
"""
import datetime, sqlite3, sys
c = sqlite3.connect("/data/work/db/health.db")
if len(sys.argv) < 2 or sys.argv[1] == "list":
    for (m,) in c.execute("SELECT DISTINCT metric FROM metrics ORDER BY 1"): print(m)
    sys.exit()
metric = sys.argv[1]; days = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 30
png = sys.argv[sys.argv.index("--png") + 1] if "--png" in sys.argv else None
since = (datetime.date.today() - datetime.timedelta(days=days + 30)).isoformat()
rows = c.execute("SELECT substr(date,1,10), avg(coalesce(qty,avg)) FROM metrics WHERE metric=? AND substr(date,1,10)>=? GROUP BY 1 ORDER BY 1", (metric, since)).fetchall()
if not rows: print("NO DATA for", metric); sys.exit()
recent = rows[-days:]; before = [v for d, v in rows[:-days]] or [v for d, v in recent]
week = [v for d, v in recent[-7:]]
avg_w, avg_b = sum(week) / len(week), sum(before) / len(before)
lo, hi = min(v for _, v in recent), max(v for _, v in recent)
bars = "▁▂▃▄▅▆▇█"
spark = "".join(bars[int((v - lo) / (hi - lo + 1e-9) * (len(bars) - 1))] for _, v in recent)
print(f"== {metric} 最近 {len(recent)} 天  {recent[0][0]} → {recent[-1][0]}")
print(spark, f" 最低 {lo:.1f} 最高 {hi:.1f}")
print(f"== 这周均值 {avg_w:.1f}  vs 之前 30 天均值 {avg_b:.1f}  差 {avg_w - avg_b:+.1f}")
for d, v in recent[-7:]: print("  ", d, f"{v:.1f}")
if png:
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 3)); ax.plot([d[5:] for d, _ in recent], [v for _, v in recent], color="#f472b6", lw=2)
        ax.axhline(avg_b, color="#94a3b8", ls="--", lw=1); ax.set_title(f"{metric} · last {len(recent)} days (dashed = 30-day baseline)")
        ax.spines[["top", "right"]].set_visible(False); ax.set_xticks(ax.get_xticks()[::max(1, len(recent) // 6)])
        fig.tight_layout(); fig.savefig(png, dpi=160); print("PNG", png)
    except ImportError: print("（没装 matplotlib，跳过 PNG）")
