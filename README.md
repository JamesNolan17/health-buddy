<div align="center">

# 🩺 health-buddy

**跑在你自己 NAS 上的 AI 健康管家 + 自动记账本。**

刷卡 10 秒后它来问“喝了啥、几分糖”，到点催你吃饭睡觉，看得懂饭照和体检报告。<br>
数据只留在你的硬盘里，它只听你一个人的话。

[中文](README.md) · [English](README.en.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Docker amd64 / arm64](https://img.shields.io/badge/docker-amd64%20%7C%20arm64-2496ED?logo=docker&logoColor=white)
![Python 3.9+ stdlib only](https://img.shields.io/badge/python-3.9%2B%20stdlib%20only-3776AB?logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/chat-Telegram-26A5E4?logo=telegram&logoColor=white)
![Agent](https://img.shields.io/badge/agent-Claude%20Code%20%7C%20Anthropic--compatible%20models-111)

<img src="docs/demo.gif" width="440" alt="示意动画：刷卡 8 秒后机器人来问喝了啥，发小票照片后自动记下热量和这笔账">

<sub>示意动画，不是真实截图；金额和热量都是虚构的。</sub>

</div>

## 30 秒看懂

- 🍱 **吃**：拍张饭照 → 识别食物、估算热量和三大营养素、按顿归档，顺便记住这家店
- 💳 **花**：银行扣款短信 → iPhone 快捷指令自动转发 → 10 秒内它来问“吃了啥” → 自动分类入账，饭钱自动对上那顿饭
- 😴 **睡**：到点催你上床，不说“晚安”就一直催；第二天用手表的入睡时间对账
- ⌚ **身体**：Apple Health 每小时同步，建立你自己的基线；静息心率、手腕温度、HRV 一起异常 → 提前 1-2 天说“你可能要感冒了”
- 🏠 **家**：Home Assistant 的卧室温湿度、CO2 和你的睡眠、嗓子痒放在一起看
- 🔒 **全在本地**：一个容器、一个 `data/` 文件夹、一个 SQLite；除了你选的模型 API，不往任何地方发数据

本质上它是 **Claude Code（或任意命令行 agent）+ 一个 200 多行、零依赖的 Python 桥接程序**：桥接程序管 Telegram、HTTP 收件口和定时器；agent 读 `CLAUDE.md` 知道自己是谁，用 `bin/` 里的小工具读写数据库。没有框架，没有第三方库。

## 一天里的它

| 时间 | 发生了什么 |
|---|---|
| ☀️ 09:00 | 早报：昨晚 00:58 入睡 ✅，HRV 比平时高，昨天走了 1 万步 |
| 🍱 12:15 | “该出发吃午饭了。” 你拍了张照 → 自动算热量、存进“日期_午饭”文件夹、记下这家店 |
| 💳 13:40 | 刷卡 S$18.50 → 自动对上刚才那顿饭，饭钱记好了，**你什么都不用做** |
| 🧋 15:06 | 刷卡 S$4.20 → 10 秒内：“在奶茶店花了 4.2，喝了啥？几分糖？” |
| 🤒 某天 | “静息心率连续两天高了 9 下，手腕温度也高，可能要感冒了，今晚早点睡” |
| 🌙 23:00 | “离睡觉目标还有 1 小时。” 你不理它？23:30、00:00……直到你说“晚安” |
| 📅 每月 1 号 | “上个月吃饭 S$5██，奶茶 █ 杯 S$3█，外卖比上月少 3 次 👍” |

> 以上时间是默认时间表（`schedules.json`），在聊天里一句话就能让它改。

## 你需要什么

**必须**
- 一台能跑 Docker 的机器：NAS、树莓派、VPS、旧电脑都行（amd64 / arm64）
- 一个 Telegram 账号（建机器人免费）
- 一个模型，二选一：**Claude 订阅**（Pro / Max，用 `claude setup-token` 拿长期令牌）或 **Anthropic API key**。也能换成 DeepSeek / Kimi / GLM 等兼容 Anthropic 接口的模型（[见下文](#换模型--换-agent)）。模型要**能看图**，饭照识别才有用
- 手机能访问到服务器：推荐 [Tailscale](https://tailscale.com/)（免费），或者在同一个内网

**可选**（每一项都是独立插件，不装也能用）
- iPhone + Apple Watch：健康数据靠 [Health Auto Export](https://www.healthyapps.dev/) 推送（App Store，**自动同步需要 Premium 付费**）；生病预警需要手表的睡眠手腕温度
- iPhone 快捷指令：转发银行扣款短信（你的银行得发短信通知）。Android 可以用 Tasker / MacroDroid 替代
- Home Assistant：卧室传感器，以及你愿意授权的空调、灯

**不需要**：公网 IP、域名、HTTPS 证书、数据库服务、任何 Python 第三方库。

> 坦白说：没有 iPhone 的话，“健康同步”和“刷卡记账”这两块要自己找 Android 替代方案（项目只带了 iOS 的路径）。模型是唯一的持续成本，见[常见问题](#常见问题)。

## 快速开始（10 分钟）

```bash
git clone https://github.com/JamesNolan17/health-buddy && cd health-buddy
cp .env.example .env && nano .env       # 填 3 个必填项，再选一个模型
```

1. **建机器人**：Telegram 找 [@BotFather](https://t.me/BotFather) → `/newbot` → token 填进 `TELEGRAM_BOT_TOKEN`
2. **拿到你的 ID**：找 [@userinfobot](https://t.me/userinfobot)，数字填进 `OWNER_CHAT_ID`（只有这个 ID 能指挥它）
3. **收件口密钥**：`openssl rand -hex 24` 填进 `INBOX_TOKEN`
4. **模型**：A / B / C 三选一，把选中那组前面的 `#` 去掉。Claude 订阅：在任意装了 Claude Code 的电脑上运行 `claude setup-token`，把输出贴进 `CLAUDE_CODE_OAUTH_TOKEN`
5. **启动**：

```bash
docker compose up -d --build
docker compose logs -f        # 看到 "health-buddy up" 就好了
```

6. 去 Telegram 给机器人发一句“你好”，然后直接告诉它你的目标（“我想 1 点前睡”“帮我减脂”）。它的长期说明书在 `data/work/CLAUDE.md`，最后有「主人档案」可以手填
7. 时区默认 `Asia/Shanghai`，在 `.env` 里改 `TZ`；默认时间表（9:00 早报 / 12:15 午饭 / 18:30 晚饭 / 21:00 运动 / 23:00、23:30 催睡）在 `data/work/schedules.json`，改完即生效

> 不想用 Docker？装好 Python 3.9+ 和 Claude Code（`npm i -g @anthropic-ai/claude-code`），把 `workspace/` 拷到 `/data/work`，再运行 `HB_DATA=/data python3 bridge/app.py`。注意 `bin/` 里的工具写死了 `/data` 路径，所以目录必须是 `/data`。

## 接数据源（都可选）

先让手机能访问到收件口：`.env` 里把 `INBOX_BIND` 改成服务器的 Tailscale IP（`100.x.x.x`）或内网 IP，`docker compose up -d` 重启。默认 `127.0.0.1` 只有本机能访问。

**⌚ Apple Health → Health Auto Export**
1. App Store 装 [Health Auto Export](https://www.healthyapps.dev/)（自动同步要 Premium）
2. Automations → 新建 → 类型选 **REST API**
3. URL：`http://<服务器>:8790/health`；Header：`Authorization` = `Bearer <INBOX_TOKEN>`
4. Data Type：Health Metrics；Format：JSON；Version：v2；Date Range：Default；Summarize：开；Time Grouping：Hours；Sync：每 1 小时；Batch Requests：开
5. 想要历史数据：Manual Upload 先传最近 6-12 个月（从最老的开始传很慢）
6. 再建一个 Data Type = Workouts 的自动化，健身记录也能传过来
7. 不会设置？把每一步的截图发给机器人，它会带着你点（作者就是这么装的）

**💳 扣款短信 → iOS 快捷指令**（秒级唤醒：“你刚花了钱，吃了啥？”）
1. 快捷指令 → 自动化 → + → **信息** → “信息包含”填你银行扣款短信的固定开头（例如 `A transaction of`）→ **运行前确认：关**
2. 动作「获取 URL 内容」→ URL `http://<服务器>:8790/pay`，方法 POST，Header `Authorization: Bearer <INBOX_TOKEN>`，请求体 JSON：`text` = 变量「信息」
3. 在 `data/work/pay_patterns.json` 加你银行的正则（已带一个新加坡 UOB 的示例；命名分组 `currency amount card date merchant`）。不会写正则？把一条短信（卡号打码）发给机器人，让它帮你加
4. `inbox_wake.json` 里默认有 `pay`，收到就立刻叫醒 agent

**🏠 Home Assistant**
1. HA → 个人资料 → 安全 → 创建「长期访问令牌」（建议给 agent 单独建一个 HA 用户）
2. 令牌放进 `data/work/secrets/ha_token`（`chmod 600`），复制 `ha.example.json` 为 `ha.json` 填好 URL 和实体
3. `background.json` 加一行 `{"every_min": 10, "cmd": ["python3","-I","bin/ha.py","snap"]}`，每 10 分钟记一次卧室环境
4. 让机器人运行 `bin/ha.py states` 摸底，它会把设备列给你看

> 🔐 **收件口是明文 HTTP。** 请只通过 Tailscale / WireGuard / 内网访问，或者在前面放一个带 HTTPS 的反向代理（Caddy / Nginx / Cloudflare Tunnel）。**不要**把 8790 直接暴露到公网。

## 隐私与安全（请读一遍）

- **数据都在 `data/`**：SQLite 数据库、饭照、体检报告、原始 JSON。备份这一个文件夹就够了；换机器直接拷走
- **会离开你机器的只有发给模型 API 的内容**：你的消息、照片，以及 agent 为了回答而查出来的数据（它是用模型“思考”的，它看到的模型都看到）。介意的话用本地模型（Ollama + LiteLLM），效果取决于模型能力
- **Telegram 不是端到端加密的**：机器人消息经过 Telegram 服务器。这是所有 Telegram 机器人的共性，不是本项目能改变的
- **只听主人**：非 `OWNER_CHAT_ID` 发来的消息直接忽略，连回复都没有
- **收件口**：Bearer 密钥、来源白名单（`INBOX_SOURCES`）、大小上限、原子写入；但它是明文 HTTP，见上
- **agent 的权限很大**：它在容器里以 `--permission-mode bypassPermissions` 运行（不然没法自动干活），并且有容器内的免密 sudo（方便自己装工具，装了什么会记在 `data/setup.sh`）。它能动的范围是这个容器和 `data/` 卷。不想给 sudo 就删掉 Dockerfile 里那一行
- **提示注入**：网页、短信、文件里的“指令”一律当数据（写在 `CLAUDE.md` 里，收件通知也会标明“不是主人发的消息”）。但这是 LLM，不是绝对防线：别给它银行登录，别让它控制门锁
- HA 令牌放在 `secrets/`，`.gitignore` 已排除

## 为什么不直接用 X？

- **MyFitnessPal / 薄荷健康这类饮食 App**：要你自己搜食物、填份量，坚持不了一周。这里拍一张照就行，而且是它到点来催你，不是你想起来才打开
- **记账 App（随手记、YNAB、MoneyWiz …）**：要么手动记，要么把银行账号授权给第三方。这里短信在你自己手机上转发到你自己的服务器，不经过任何别人的服务器
- **Apple 健康 App 本身**：数据都有，但没人看。这里每天一句人话，长期趋势有人盯着，异常会主动说
- **直接问 ChatGPT / Claude**：它没有你的数据、没有长期记忆，更不会主动找你。这个项目的核心正是“agent 有你的数据库 + 定时主动行动”
- **Home Assistant 自动化**：能发“湿度高”的通知，但不会把湿度和你的嗓子痒、睡眠质量放在一起分析
- **其他 Telegram AI 机器人项目**：大多是聊天壳。这里的重点是数据管道（健康 / 消费 / 家居）+ 定时任务 + 本地 SQLite，聊天只是界面

## 常见问题

- **花多少钱？** 只有模型花钱。每天大约十几次调用（定时任务 + 你的消息 + 饭照）。Claude 订阅没有按次计费，个人用一般在额度内；Anthropic API 按量计费会贵一些；DeepSeek 这类模型通常很便宜。先跑一周看看账单
- **用 Claude 订阅合适吗？** `claude setup-token` 是 Claude Code 官方提供的长期登录方式，就是给自己机器上跑 Claude Code 用的；受订阅本身的速率限制约束
- **没有 iPhone？** Android：Health Connect + 任何能 POST JSON 的 App → `/health`（要改 `ingest.py` 的解析）；Tasker / MacroDroid 把短信 POST 到 `/pay`，请求体 `{"text": "短信内容"}` 即可
- **银行不是 UOB？** 往 `pay_patterns.json` 加一条正则就行，任何银行、任何币种。把短信（卡号打码）发给机器人让它写
- **定时任务每次都会发消息？** 是的，agent 每次运行都会回复。没事可说时 `CLAUDE.md` 让它只回一个 👍。纯数据导入放 `background.json`，不经过 LLM、不发消息
- **它会乱改我的家居吗？** `CLAUDE.md` 规定：加设备、改自动化、动别人房间的设备之前必须先问你；所有调用都记在 `logs/ha_actions.log`
- **想用英文？** 把 `data/work/CLAUDE.en.md` 复制成 `CLAUDE.md`，再把 `schedules.json` 里的 prompt 翻一下
- **换机器 / 备份？** 停容器，把 `data/` 整个拷过去，`docker compose up -d`
- **热量准吗？** 看图估算，误差 20-30% 很正常。它的价值在于趋势和坚持记录，不在精确到个位
- **能多人用吗？** 不能，设计上一个机器人只服务一个主人。多人就各跑一个容器

## 它是怎么工作的

```
 iPhone ──Health Auto Export──┐
 iPhone ──快捷指令(扣款短信)──┼──► POST /health /pay /ha ──► /data/inbox/<source>/*.json
 Home Assistant ──────────────┘        (bridge 收件口，Bearer 鉴权)        │
                                                                            │ 后台导入 / 收件即唤醒
 你 ◄──► Telegram ◄──► bridge/app.py ◄──► agent CLI（Claude Code 等） ◄──► /data/work
                         ▲   定时器 schedules.json                         ├ CLAUDE.md  长期说明书
                         └── 后台任务 background.json                      ├ NOTES.md   agent 自己的笔记
                                                                            ├ bin/*.py   工具
                                                                            └ db/health.db  SQLite
```

- **bridge/app.py**：一个文件、只用 Python 标准库。Telegram 收发、收件口、cron 定时器、收件即唤醒、后台任务都在这里
- **agent**：默认 Claude Code（`claude -p --resume`，自动续上会话）。它读 `CLAUDE.md` 知道自己是谁、该怎么做，自己用 `bin/` 里的工具读写 SQLite；心得写在 `NOTES.md`
- **一切都在 `/data`**：备份这一个文件夹就够了；x86 NAS ↔ ARM VPS 直接拷过去

<details>
<summary><b>📸 作者和自己 health-buddy 的 7 个真实故事（关键数字已打码，点开看）</b></summary>

**① 从零到通：看截图，手把手带着设置**

```mermaid
sequenceDiagram
    actor U as 我
    participant H as 🤖 health-buddy
    U->>H: 你得手把手教我，我啥都不会
    H-->>U: 第 1 步：打开 App，点底部 Automations，截图给我
    U->>H: [截图]
    H-->>U: 找对了！一直点 Next……
    U->>H: [截图：URL 填好了]
    H-->>U: ✅ 网址对了。下一步填密钥，截图前先把键盘收起来 😉
    U->>H: 我把从出生到现在的数据都传了，2%
    H-->>U: 📬 收到 ██ 万条，从 20██ 年开始。先帮你建个人基线
```

**② 一顿午饭：催 → 拍 → 算 → 自动记账**

```mermaid
sequenceDiagram
    actor U as 我
    participant H as 🤖 health-buddy
    participant B as 🏦 银行短信
    H-->>U: 12:15 该出发吃午饭了，吃上了拍第一份主菜 📸
    U->>H: 这些不够好吃呀，我好伤心 🥺
    H-->>U: 那就沙爹、越南粉、Tandoori 烤鸡……每周再发你一张随便吃福利卡 🎉
    U->>H: [照片：烤鸡]
    H-->>U: 🍗 约 600 kcal，蛋白 58g，焦皮撕掉能少 100
    U->>H: 饭吃了 2/3，薄脆剩 1 片
    H-->>U: 📊 这顿约 1300 kcal，晚饭还剩 600
    B->>H: A transaction of SGD ██.██ … at ████
    H-->>U: 💰 对上午饭了，饭钱记好了，不用你报
```

**③ 抓到一杯奶茶（10 秒内）**

```mermaid
sequenceDiagram
    actor U as 我
    participant S as 📱 快捷指令
    participant H as 🤖 health-buddy
    U->>S: 刷卡 S$4.20
    S->>H: POST /pay（扣款短信）
    Note over H: 收件即唤醒，不到 10 秒
    H-->>U: 🧋 抓到了！在奶茶店刷了 4.20，几分糖？
    U->>H: [小票照片]
    H-->>U: 10% 糖 + 栀子冻，约 110 kcal，选得聪明 👍
```

**④ 从手表数据里认出你哪几次生病**

```mermaid
flowchart LR
    A[静息心率比 30 天中位数高 ≥6<br/>连续 2 天以上] --> B{手腕温度也高？}
    B -- 是 --> C[🤒 疑似生病<br/>20██-09、20██-02、20██-07]
    B -- 否 --> D[问一句：出远门了？]
    C --> E[我：对！三次都发烧了]
    D --> F[我：那次是去高原玩<br/>→ 记成例外]
    E & F --> G[✅ 校准完成<br/>以后提前 1-2 天预警]
```

**⑤ 大学四年 vs 毕业后**

```mermaid
flowchart TB
    subgraph Uni["🎓 大学 4 年（越来越差）"]
      a1[入睡 0:5█ → 2:█9]
      a2[静息心率 6█ → 7█]
      a3[HRV 3█ → 2█]
      a4[站立小时 1█ → █]
    end
    subgraph After["💼 毕业后"]
      b1[步数、运动分钟 ✅ 全面翻盘]
      b2[心率 / HRV / 睡眠 ❌ 没恢复]
    end
    Uni --> After --> c[🎯 结论：只差早睡这一件事]
```

**⑥ 1:30 铁律（主人自己要求的“强制”）**

```mermaid
flowchart LR
    A[00:30 预告] --> B[01:00 上床]
    B --> C{说了“晚安”吗？}
    C -- 说了 --> D[🤫 后面的提醒全部闭嘴]
    C -- 没说 --> E[01:15 / 01:30 / 01:45 …<br/>一次比一次凶]
    E --> C
    D --> F[☀️ 早报：用手表入睡时间对账<br/>说了晚安还刷手机？照样点名 😏]
```

**⑦ 嗓子痒了 10 年 → 家里的传感器给了线索**

```mermaid
flowchart LR
    A[我：嗓子痒好多年了<br/>鼻涕倒流，空调冷了就咳] --> B[体检：炎症指标正常]
    A --> C[Home Assistant：卧室湿度 7█%]
    C --> D[湿度 > 60% 尘螨最爱]
    B & D --> E[建议：去 ENT 查过敏原、洗鼻、防螨<br/>先观察几晚再决定买不买除湿机]
```

</details>

## 换模型 / 换 agent

bridge 只是调用一个命令行 agent，所以模型和 agent 都能换。

**方式 1：Anthropic 兼容接口（改 3 个环境变量，什么代码都不用动）**

Claude Code 可以接任何兼容 Anthropic Messages API 的服务。在 `.env` 里：

| 模型 | `ANTHROPIC_BASE_URL` | `ANTHROPIC_MODEL` 示例 | 备注 |
|---|---|---|---|
| DeepSeek | `https://api.deepseek.com/anthropic` | `deepseek-chat` / `deepseek-reasoner` | 便宜；**看图能力以官方文档为准**，不能看图时饭照识别会失效，可以改成文字描述 |
| Kimi（Moonshot） | `https://api.moonshot.cn/anthropic` | `kimi-k2-…` | 国内直连 |
| 智谱 GLM | `https://open.bigmodel.cn/api/anthropic` | `glm-4.x` | 有视觉版本 |
| OpenRouter / 自建 LiteLLM | 你的网关地址 | 任意 | 可以接 GPT、Gemini、Qwen、本地 Ollama |

```env
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=sk-你的key
ANTHROPIC_MODEL=deepseek-chat
ANTHROPIC_SMALL_FAST_MODEL=deepseek-chat
# 别同时设置 ANTHROPIC_API_KEY
```

> 各家接口地址和模型名会变，以官方文档为准。工具调用、长上下文、看图这三样都要支持，体验才完整。

**方式 2：只有 OpenAI 格式接口？** 在前面放一个转换网关，比如 [LiteLLM](https://github.com/BerriAI/litellm) 或 [claude-code-router](https://github.com/musistudio/claude-code-router)，把 `ANTHROPIC_BASE_URL` 指向它。

**方式 3：换掉整个 agent**（Codex CLI、Gemini CLI、aider，或者你自己写的脚本）
```env
AGENT=cmd
AGENT_CMD=gemini -p "$(cat)"     # prompt 从 stdin 进，回复从 stdout 出
```
- 在 Dockerfile 里把 `npm install -g @anthropic-ai/claude-code` 换成对应 CLI 的安装命令
- 把 `CLAUDE.md` 复制成那个 CLI 读的文件名（Codex：`AGENTS.md`；Gemini CLI：`GEMINI.md`）
- 要求：能在 `/data/work` 里执行 shell 命令（不然用不了 `bin/` 工具），最好能自己记住会话
- 想要多轮记忆：在 `bridge/app.py` 里仿照 `run_claude()` 写一个带会话 ID 的函数

## 可替换的部分

| 组件 | 默认 | 可以换成 |
|---|---|---|
| 聊天 | Telegram | 改 `bridge/app.py` 的 `send_text` / `telegram_loop`：飞书、Discord、Slack、企业微信机器人，或者 Matrix |
| 手机健康数据 | Health Auto Export | Android：Health Connect + Tasker / HC Webhook 类 App，POST 到 `/health`（需要改 `ingest.py` 的解析） |
| 扣款通知 | iOS 快捷指令转短信 | Android：Tasker / MacroDroid 转发短信或通知；银行邮件提醒 → 邮件规则转发 |
| 家居 | Home Assistant | 任何有 HTTP API 的平台，照着 `bin/ha.py` 写一个小工具 |
| 内网穿透 | Tailscale | WireGuard、ZeroTier、Cloudflare Tunnel（记得加 HTTPS） |
| 数据库 | SQLite | 够用了。真要换，改 `bin/` 里的几个脚本 |

## ⚠️ 免责声明

health-buddy **不是医疗器械，也不提供医疗建议**。它给出的热量是估算，健康提醒只是参考。身体不舒服请去看医生。

## License

MIT
