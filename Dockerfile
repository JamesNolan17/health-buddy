# healthy-wealthy —— 支持 amd64 / arm64（NAS、树莓派、VPS 都行）
FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 sqlite3 curl ca-certificates tzdata sudo procps \
    && rm -rf /var/lib/apt/lists/*

# Agent CLI（默认 Claude Code）。换别的 CLI 就在这里装，见 README「换模型 / 换 agent」
RUN npm install -g @anthropic-ai/claude-code

# Claude Code 不允许以 root 跑 bypassPermissions，所以用普通用户（可免密 sudo，方便 agent 自己装东西）
# node 镜像自带的 node 用户也占着 UID 1000，先删掉，否则 useradd 会失败 / the base image's "node" user already owns UID 1000
RUN userdel -r node 2>/dev/null; useradd -m -u 1000 -s /bin/bash agent \
    && echo "agent ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/agent

COPY bridge /app/bridge
COPY workspace /app/workspace-template
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV HB_DATA=/data HOME=/data/home TZ=Asia/Shanghai PYTHONUNBUFFERED=1 DISABLE_AUTOUPDATER=1
VOLUME /data
EXPOSE 8790
ENTRYPOINT ["/app/entrypoint.sh"]
