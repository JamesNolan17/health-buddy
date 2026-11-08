#!/usr/bin/env python3
"""晚安标记。凌晨 6 点前算前一晚。
  night.py gn      主人说了晚安 → 写标记
  night.py check   已说晚安输出 SLEPT，否则 AWAKE
"""
import sys, os, datetime as dt
now=dt.datetime.now(); night=(now-dt.timedelta(hours=6)).date().isoformat()
f=f"/data/work/state/goodnight-{night}"
if sys.argv[1]=="gn":
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f,"w").write(now.strftime("%H:%M")); print("ok", night, now.strftime("%H:%M"))
else:
    print("SLEPT "+open(f).read() if os.path.exists(f) else "AWAKE")
