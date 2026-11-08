#!/usr/bin/env python3
"""Home Assistant 小工具。配置：/data/work/ha.json，令牌：/data/work/secrets/ha_token（chmod 600）
  ha.py get <entity_id>                     看一个实体
  ha.py states                              列出所有实体（摸底用）
  ha.py snap                                把卧室环境存一条到 health.db 的 ha_env（后台任务）
  ha.py call <domain> <service> '<json>'    调服务（自动记到 logs/ha_actions.log）
HA 在局域网里时，记得把它加进 NO_PROXY，或者在 ha.json 里写 "direct": true。"""
import datetime, json, sqlite3, sys, urllib.request
CFG = json.load(open("/data/work/ha.json"))
BASE = CFG["url"].rstrip("/") + "/api"; TOK = open("/data/work/secrets/ha_token").read().strip()
op = urllib.request.build_opener(urllib.request.ProxyHandler({})) if CFG.get("direct") else urllib.request.build_opener()
def req(path, data=None):
    r = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": "Bearer " + TOK, "Content-Type": "application/json"}, method="POST" if data is not None else "GET")
    return json.load(op.open(r, timeout=20))
cmd = sys.argv[1]
if cmd == "get": print(json.dumps(req("/states/" + sys.argv[2]), ensure_ascii=False, indent=1))
elif cmd == "states":
    for e in req("/states"): print(e["entity_id"], "|", e["attributes"].get("friendly_name"), "|", e["state"], e["attributes"].get("unit_of_measurement", ""))
elif cmd == "snap":
    st = {e["entity_id"]: e for e in req("/states")}
    def num(eid):
        try: return float(st[eid]["state"])
        except Exception: return None
    row = {"at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    row.update({k: num(v) for k, v in CFG.get("snap_numbers", {}).items()})
    row.update({k: st.get(v, {}).get("state") for k, v in CFG.get("snap_states", {}).items()})
    c = sqlite3.connect("/data/work/db/health.db")
    c.execute("CREATE TABLE IF NOT EXISTS ha_env(at TEXT PRIMARY KEY, data TEXT)")
    c.execute("INSERT OR REPLACE INTO ha_env VALUES(?,?)", (row["at"], json.dumps(row, ensure_ascii=False))); c.commit()
    print(row)
elif cmd == "call":
    dom, svc = sys.argv[2], sys.argv[3]; data = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
    with open("/data/work/logs/ha_actions.log", "a") as f: f.write(f"{datetime.datetime.now():%F %T} {dom}.{svc} {json.dumps(data, ensure_ascii=False)}\n")
    print(json.dumps(req(f"/services/{dom}/{svc}", data), ensure_ascii=False)[:500])
