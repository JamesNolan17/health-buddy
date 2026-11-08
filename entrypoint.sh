#!/bin/bash
# 第一次启动：把模板拷进 /data/work（已有的文件不覆盖）；然后跑 /data/setup.sh；最后以普通用户启动桥接程序
set -e
mkdir -p /data/work /data/inbox /data/home /data/state
cp -rn /app/workspace-template/. /data/work/
mkdir -p /data/work/db /data/work/files /data/work/logs /data/work/inbox
[ -f /data/setup.sh ] || printf '#!/bin/bash\n# 开机脚本：每次启动以 root 执行，要幂等。agent 装了软件会写在这里。\n' > /data/setup.sh
chmod +x /data/setup.sh && /data/setup.sh || echo "setup.sh failed (continuing)"
chown -R agent:agent /data
chmod 700 /data/work/secrets 2>/dev/null || true
exec runuser -u agent -- python3 -u /app/bridge/app.py
