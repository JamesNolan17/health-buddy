<div align="center">

# 🩺 health-buddy

**A private AI health butler + an expense ledger that writes itself.**

Runs on your own computer, NAS or cloud box — your data never leaves home.<br>
It nags you to eat and sleep on time, reads meal photos and lab reports, and asks "what did you get, sugar level?" ten seconds after you tap your card.

[中文](README.md) · [English](README.en.md)

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Runs on](https://img.shields.io/badge/runs%20on-your%20PC%20%7C%20NAS%20%7C%20cloud%20box-2496ED)
![Telegram](https://img.shields.io/badge/chat-Telegram-26A5E4?logo=telegram&logoColor=white)
![AI](https://img.shields.io/badge/AI-Claude%20or%20compatible%20models-111)

<img src="docs/demo.en.gif" width="440" alt="Mock-up animation: a tap at a known shop is logged after a one-word reply; the nightly ledger comes with a chart and a gentle call-out; a month-end credit-card minimum-spend reminder; a resting-heart-rate trend chart on request">

<sub>Mock-up animation, not a real screenshot. Amounts and calories are fictional.</sub>

</div>

## In 30 seconds

- 🍱 **Eat**: snap a meal photo → food identified, kcal and macros estimated, filed per meal, restaurant remembered
- 💸 **Spend (the ledger writes itself)**: your bank's spend SMS is forwarded by your phone → every charge is categorised automatically, card included; food charges are matched to the meal you photographed, taxis / groceries / subscriptions are logged along the way — you type nothing
- 🧋 **Known shops need no explanation**: it remembers the places you go and what you usually order; next time it just asks "the usual, less sugar?"
- 👀 **Someone watches your food money**: a small nightly ledger — "food today was 1.6× your usual, that's bubble tea #2" gets a gentle call-out; categories summarised on the 1st of each month
- 💳 **Credit-card minimum-spend reminders**: tell it which card needs how much per month for cashback or miles; before month-end it tells you "S$85 to go, 6 days left"
- 😴 **Sleep**: bedtime nudges that keep coming until you say "good night"; audited against your watch the next morning
- ⌚ **Body**: your Apple Watch data syncs every hour so it learns what is *normal for you*; resting heart rate + wrist temperature + heart-rate variability all off together → "you may be getting sick" 1–2 days early
- 📈 **Charts on request**: "plot this month's food vs other spending", "resting heart rate, last 30 days" → it sends you a picture
- 🏠 **Home**: bedroom temperature / humidity / CO2 (from Home Assistant) next to your sleep and symptoms
- 🔒 **Your data stays yours**: everything lives in one folder on your own machine — backing up means copying it. Nothing is sent anywhere except to the AI model service you pick

It uses an AI model (Claude by default) to understand your messages and photos, then a few small tools write the results into your own database. All you do is chat with it on Telegram. Technical details in [How it works](#how-it-works).

## A day with it

| Time | What happens |
|---|---|
| ☀️ 09:00 | Morning report: asleep at 00:58 ✅, HRV above baseline, 10k steps yesterday |
| 🍱 12:15 | "Time to go eat." You snap a photo → calories estimated, filed under "date_lunch", restaurant remembered |
| 💳 13:40 | Card charged S$18.50 → matched to that lunch automatically. **You do nothing.** |
| 🧋 15:06 | Card charged S$4.20 → within 10 s: "Lemon Tea Co. again — the usual, less sugar?" You reply "yep" and it's logged |
| 🧾 21:30 | Nightly ledger: "Food today S$46, 1.6× your usual, bubble tea #2 👀 Taxi S$32 logged" |
| 💳 24th | "Your cashback card ending 0000 is S$85 short of this month's minimum spend, 6 days left — put the next big purchase on it" |
| 🤒 one day | "Resting HR +9 for two days and wrist temp is up — you may be getting sick. Sleep early tonight." |
| 🌙 23:00 | "One hour to your bedtime goal." Ignore it? 23:30, 00:00 … until you say good night |
| 📅 1st of month | "Last month: food S$560, 9 bubble teas S$38, 3 fewer deliveries 👍" |

> These are the default schedule (`schedules.json`); one sentence in chat changes it.

## Requirements

**Required**
- A Docker host: NAS, Raspberry Pi, VPS or an old laptop (amd64 / arm64)
- A Telegram account (creating a bot is free)
- A model, one of: a **Claude subscription** (Pro / Max, long-lived token via `claude setup-token`) or an **Anthropic API key**. DeepSeek / Kimi / GLM and other Anthropic-compatible endpoints also work ([see below](#other-models--other-agents)). The model must **understand images** for meal photos to work
- Your phone must be able to reach the server: [Tailscale](https://tailscale.com/) (free) or the same LAN

**Optional** (each one is an independent plug-in)
- iPhone + Apple Watch: health data arrives via [Health Auto Export](https://www.healthyapps.dev/) (App Store; **automations require the paid Premium tier**). Illness early-warning needs the watch's sleeping wrist temperature
- iPhone Shortcuts: forwards your bank's spend SMS (your bank has to send SMS alerts). Android: Tasker / MacroDroid instead
- Home Assistant: bedroom sensors, plus any AC / lights you choose to let it touch

**Not needed**: a public IP, a domain, TLS certificates, a database server, any Python package.

> Honest caveat: without an iPhone the "health sync" and "card spend" halves need your own Android plumbing — the repo only ships the iOS path. The model is the only recurring cost, see [FAQ](#faq).

## Quick start (10 minutes)

```bash
git clone https://github.com/JamesNolan17/health-buddy && cd health-buddy
cp .env.example .env && nano .env       # 3 required values + pick one model
```

1. **Bot**: talk to [@BotFather](https://t.me/BotFather) → `/newbot` → token into `TELEGRAM_BOT_TOKEN`
2. **Your ID**: ask [@userinfobot](https://t.me/userinfobot) → `OWNER_CHAT_ID` (only this ID can command the bot)
3. **Inbox secret**: `openssl rand -hex 24` → `INBOX_TOKEN`
4. **Model**: uncomment exactly one of A / B / C. For a Claude subscription run `claude setup-token` on any machine with Claude Code installed and paste the result into `CLAUDE_CODE_OAUTH_TOKEN`
5. **Run**:

```bash
docker compose up -d --build
docker compose logs -f        # wait for "health-buddy up"
```

6. Say hi to your bot and tell it your goals ("asleep by 1 am", "lose fat"). Its long-term handbook is `data/work/CLAUDE.md`; the "Owner profile" at the end can be filled in by hand.
   **English speakers**: copy `data/work/CLAUDE.en.md` over `data/work/CLAUDE.md` and translate the prompts in `schedules.json` (the defaults are Chinese)
7. Timezone defaults to `Asia/Shanghai` — change `TZ` in `.env`. The default schedule (09:00 report / 12:15 lunch / 18:30 dinner / 21:00 workout / 23:00 + 23:30 bedtime) lives in `data/work/schedules.json` and is live-reloaded

> No Docker? Install Python 3.9+ and Claude Code (`npm i -g @anthropic-ai/claude-code`), copy `workspace/` to `/data/work`, run `HB_DATA=/data python3 bridge/app.py`. The tools in `bin/` hard-code `/data`, so the directory has to be exactly that.

## Data sources (all optional)

First make the inbox reachable from your phone: set `INBOX_BIND` in `.env` to the server's Tailscale IP (`100.x.x.x`) or LAN IP and `docker compose up -d`. The default `127.0.0.1` is reachable from the host only.

**⌚ Apple Health → Health Auto Export**
1. Install [Health Auto Export](https://www.healthyapps.dev/) (automations need Premium)
2. Automations → New → **REST API**
3. URL `http://<server>:8790/health`; header `Authorization` = `Bearer <INBOX_TOKEN>`
4. Health Metrics · JSON · v2 · Date Range Default · Summarize on · Time Grouping Hours · every 1 hour · Batch Requests on
5. History: use Manual Upload for the last 6–12 months first (uploading "since birth" starts from the oldest data and is slow)
6. Add a second automation with Data Type = Workouts
7. Stuck? Send the bot a screenshot of each step — it will walk you through (that is how the author set it up)

**💳 Card-spend SMS → iOS Shortcuts** (wake-on-inbox: "you just spent money — what was it?")
1. Shortcuts → Automation → + → **Message** → "Message contains" = the fixed prefix of your bank's spend SMS (e.g. `A transaction of`) → **Ask before running: off**
2. Action "Get Contents of URL": `http://<server>:8790/pay`, POST, header `Authorization: Bearer <INBOX_TOKEN>`, JSON body `text` = variable *Message*
3. Add a regex for your bank to `data/work/pay_patterns.json` (one Singapore UOB example included; named groups `currency amount card date merchant`). Or forward one SMS (card number masked) to the bot and ask it to add the rule
4. `pay` is in `inbox_wake.json` by default, so the agent wakes immediately

**🏠 Home Assistant**
1. HA → Profile → Security → Long-lived access token (a dedicated HA user is recommended)
2. Save it to `data/work/secrets/ha_token` (`chmod 600`); copy `ha.example.json` → `ha.json` and fill in URL & entities
3. Add `{"every_min": 10, "cmd": ["python3","-I","bin/ha.py","snap"]}` to `background.json`
4. Ask the bot to run `bin/ha.py states` and list your devices

> 🔐 **The inbox speaks plain HTTP.** Reach it only through Tailscale / WireGuard / LAN, or put an HTTPS reverse proxy in front (Caddy / Nginx / Cloudflare Tunnel). **Never** expose port 8790 to the internet directly.

## Privacy & security (please read)

- **Everything is in `data/`**: the SQLite database, meal photos, lab reports, raw JSON. Back up that one folder; move machines by copying it
- **The only thing that leaves your machine is what goes to the model API**: your messages, photos, and whatever the agent queries to answer you (it thinks with the model, so the model sees what it sees). Want zero cloud? Use a local model (Ollama + LiteLLM); quality depends on the model
- **Telegram is not end-to-end encrypted**: bot messages pass through Telegram's servers. True for every Telegram bot, not something this project can change
- **Owner only**: messages from anyone but `OWNER_CHAT_ID` are dropped without a reply
- **Inbox**: Bearer secret, allow-listed sources (`INBOX_SOURCES`), size limit, atomic writes — but plain HTTP, see above
- **The agent has a lot of power**: it runs with `--permission-mode bypassPermissions` inside the container (otherwise it cannot act on its own) and has passwordless sudo *inside the container* (to install tools; what it installs is recorded in `data/setup.sh`). Its reach is the container and the `data/` volume. Remove the sudo line in the Dockerfile if you prefer
- **Prompt injection**: "instructions" inside web pages, SMS and files are treated as data (spelled out in `CLAUDE.md`; inbox notifications are explicitly marked "not from the owner"). It is still an LLM, not a hard boundary: don't give it bank logins, don't let it control door locks
- HA token lives in `secrets/`, excluded by `.gitignore`

## Why not just use X?

- **MyFitnessPal and friends**: you search foods and type portions, and quit within a week. Here you send one photo — and the bot comes to you on schedule instead of waiting for you to open an app
- **Budgeting apps (YNAB, Mint-likes, bank aggregators)**: either manual entry or handing your bank login to a third party. Here the SMS is forwarded from your own phone to your own server; no one else's server is involved
- **Apple Health itself**: the data is there but nobody reads it. Here you get one human sentence a day and someone watching the long-term trend
- **Just asking ChatGPT / Claude**: no access to your data, no long-term memory, never reaches out first. The whole point here is "an agent that owns your database and acts on a schedule"
- **Home Assistant automations**: can notify "humidity high", but won't put humidity next to your itchy throat and sleep quality
- **Other Telegram AI bot projects**: mostly chat wrappers. This one is about the data pipeline (health / spending / home) + scheduler + local SQLite; chat is just the UI

## FAQ

- **Cost?** Only the model. Roughly a dozen calls a day (schedules + your messages + meal photos). A Claude subscription has no per-call billing and personal use generally fits in the quota; the Anthropic API bills per token and costs more; DeepSeek-class models are usually very cheap. Run it for a week and check your bill
- **Is a Claude subscription OK for this?** `claude setup-token` is Claude Code's official long-lived login for running Claude Code on your own machines; your subscription's rate limits apply
- **No iPhone?** Android: Health Connect + any app that can POST JSON → `/health` (adapt `ingest.py`); Tasker / MacroDroid POST the SMS to `/pay` with body `{"text": "<sms>"}`
- **My bank isn't UOB?** Add one regex to `pay_patterns.json` — any bank, any currency. Send the bot a masked SMS and ask it to write the rule
- **How do I set up card minimum-spend reminders?** Copy `data/work/cards.example.json` to `cards.json` with each card's last 4 digits, name and monthly minimum; on the 24th and 28th it works out what is still missing. Or just tell it in chat: "card ending 0000 needs S$500 a month"
- **How are the charts made?** The bot installs matplotlib inside its container (`sudo apt-get install python3-matplotlib`); without it you get text bar charts. Spending: `spend.py chart`; health trends: `trend.py`
- **Does every scheduled job send a message?** Yes, each agent run replies. `CLAUDE.md` tells it to answer with a single 👍 when there's nothing to say. Pure data imports belong in `background.json` (no LLM, no messages)
- **Will it mess with my home?** `CLAUDE.md` requires asking before adding devices, editing automations or touching other people's rooms; every call is logged in `logs/ha_actions.log`
- **Moving machines / backups?** Stop the container, copy `data/`, `docker compose up -d`
- **Are the calories accurate?** Photo estimates are typically off by 20–30 %. The value is in the trend and in actually keeping the log, not in the last digit
- **Multiple users?** No — one bot, one owner by design. Run one container per person

## Roadmap (not done yet)

- Android paths for health sync and SMS forwarding (only iOS ships today)
- Monthly report with the spending chart attached automatically (today you ask for it, or add a line to the monthly prompt in `schedules.json`)
- More banks' SMS formats (a one-line regex PR to `pay_patterns.json` is welcome)
- A web dashboard: everything lives in Telegram today; for long-term charts ask it to send a PNG

## How it works

```mermaid
flowchart LR
    subgraph Sources
      A1[📱 iPhone<br/>Health Auto Export]
      A2[📱 iPhone Shortcuts<br/>bank SMS]
      A3[🏠 Home Assistant]
    end
    A1 & A2 & A3 -- "POST /health /pay /ha<br/>Bearer auth" --> IN[(📥 /data/inbox/&lt;source&gt;/*.json)]
    IN -- background import / wake-on-inbox --> BR
    U[🙋 You] <--> TG[💬 Telegram] <--> BR[🔌 bridge/app.py<br/>scheduler: schedules.json<br/>background jobs: background.json]
    BR <--> AG[🤖 agent CLI<br/>Claude Code …]
    AG <--> W
    subgraph W [📁 /data/work]
      W1[CLAUDE.md long-term handbook]
      W2[NOTES.md agent's own notes]
      W3[bin/*.py tools]
      W4[(db/health.db SQLite)]
    end
```

- The whole thing = **Claude Code (or any CLI agent) + a ~200-line, zero-dependency Python bridge**. No framework, no third-party libraries
- **bridge/app.py** — a single file, Python stdlib only: Telegram I/O, inbox receiver, cron scheduler, wake-on-inbox, background jobs
- **agent** — Claude Code by default (`claude -p --resume`, the session continues automatically). It reads `CLAUDE.md` to know who it is and uses the tools in `bin/` to read and write SQLite; its own notes go to `NOTES.md`
- **Everything lives in `/data`** — back up one folder; move between an x86 NAS and an ARM VPS by copying it

<details>
<summary><b>📸 Seven real stories from the author's own health-buddy (numbers replaced with fictional values, translated — click to expand)</b></summary>

**① Zero to working, guided by screenshots**

```mermaid
sequenceDiagram
    actor U as Me
    participant H as 🤖 health-buddy
    U->>H: Walk me through it, I have no idea how
    H-->>U: Step 1: open the app, tap Automations, send a screenshot
    U->>H: [screenshot]
    H-->>U: Right place! Keep tapping Next…
    U->>H: [screenshot: URL filled in]
    H-->>U: ✅ URL is correct. Next the secret — hide the keyboard before the screenshot 😉
    U->>H: Uploading everything since I was born… 2%
    H-->>U: 📬 480k records back to 2019. Building your personal baseline
```

**② One lunch: nudge → photo → estimate → auto-bookkeeping**

```mermaid
sequenceDiagram
    actor U as Me
    participant H as 🤖 health-buddy
    participant B as 🏦 Bank SMS
    H-->>U: 12:15 Time to go eat — send me the first dish 📸
    U->>H: Your suggestions aren't tasty enough 🥺
    H-->>U: Then satay, pho, tandoori chicken… plus one free cheat-meal card a week 🎉
    U->>H: [photo: tandoori chicken]
    H-->>U: 🍗 ≈600 kcal, 58 g protein — peel the charred skin to save 100
    U->>H: Ate 2/3 of the rice, one papadum left
    H-->>U: 📊 ≈1300 kcal this meal, 600 left for dinner
    B->>H: A transaction of SGD 18.50 … at FOOD COURT
    H-->>U: 💰 Matched to lunch. Logged — no need to tell me
```

**③ Catching a bubble tea (under 10 s)**

```mermaid
sequenceDiagram
    actor U as Me
    participant S as 📱 Shortcuts
    participant H as 🤖 health-buddy
    U->>S: Tap card, S$4.20
    S->>H: POST /pay (bank SMS)
    Note over H: wake-on-inbox, < 10 s
    H-->>U: 🧋 Caught you! 4.20 at a tea shop — sugar level?
    U->>H: [receipt photo]
    H-->>U: 10 % sugar + gardenia jelly ≈110 kcal, smart pick 👍
```

**④ Finding past illnesses in watch data**

```mermaid
flowchart LR
    A[Resting HR ≥ 30-day median + 6<br/>for 2+ days] --> B{Wrist temp up too?}
    B -- yes --> C[🤒 likely sick<br/>2023-09, 2024-02, 2025-07]
    B -- no --> D[Ask: were you travelling?]
    C --> E[Me: yes! fever all three times]
    D --> F[Me: that was a high-altitude trip<br/>→ marked as exception]
    E & F --> G[✅ calibrated<br/>now warns 1–2 days early]
```

**⑤ University years vs after**

```mermaid
flowchart TB
    subgraph Uni["🎓 4 years of university (sliding)"]
      a1[asleep 0:55 → 2:19]
      a2[resting HR 62 → 71]
      a3[HRV 38 → 27]
      a4[stand hours 12 → 8]
    end
    subgraph After["💼 after graduating"]
      b1[steps, exercise ✅ fully recovered]
      b2[HR / HRV / sleep ❌ not yet]
    end
    Uni --> After --> c[🎯 conclusion: only bedtime is left to fix]
```

**⑥ The 1:30 rule (enforcement the owner asked for)**

```mermaid
flowchart LR
    A[00:30 heads-up] --> B[01:00 go to bed]
    B --> C{said good night?}
    C -- yes --> D[🤫 all later nudges go quiet]
    C -- no --> E[01:15 / 01:30 / 01:45 …<br/>sterner each time]
    E --> C
    D --> F[☀️ morning audit vs watch sleep onset<br/>said good night but kept scrolling? called out 😏]
```

**⑦ A 10-year itchy throat → the home sensors give a clue**

```mermaid
flowchart LR
    A[Me: itchy throat for years<br/>post-nasal drip, cough when AC is cold] --> B[Lab: inflammation markers normal]
    A --> C[Home Assistant: bedroom humidity 72%]
    C --> D[> 60 % is dust-mite heaven]
    B & D --> E[Suggest: see ENT for allergy tests, nasal rinse, mite control<br/>watch a few nights before buying a dehumidifier]
```

</details>

## Other models / other agents

The bridge just calls a CLI agent, so both the model and the agent are swappable.

**Option 1 — Anthropic-compatible endpoints (3 env vars, zero code)**

| Provider | `ANTHROPIC_BASE_URL` | `ANTHROPIC_MODEL` e.g. | Notes |
|---|---|---|---|
| DeepSeek | `https://api.deepseek.com/anthropic` | `deepseek-chat` / `deepseek-reasoner` | cheap; **check the docs for image support** — without vision, meal photos won't work (describe meals in text instead) |
| Kimi (Moonshot) | `https://api.moonshot.ai/anthropic` | `kimi-k2-…` | |
| Zhipu GLM | `https://open.bigmodel.cn/api/anthropic` | `glm-4.x` | vision variants available |
| OpenRouter / your LiteLLM | your gateway | anything | GPT, Gemini, Qwen, local Ollama … |

```env
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=sk-your-key
ANTHROPIC_MODEL=deepseek-chat
ANTHROPIC_SMALL_FAST_MODEL=deepseek-chat
# don't set ANTHROPIC_API_KEY at the same time
```

> Endpoints and model names change — follow each provider's docs. You want tool use, long context and vision for the full experience.

**Option 2 — OpenAI-format only?** Put [LiteLLM](https://github.com/BerriAI/litellm) or [claude-code-router](https://github.com/musistudio/claude-code-router) in front and point `ANTHROPIC_BASE_URL` at it.

**Option 3 — swap the whole agent** (Codex CLI, Gemini CLI, aider, your own script)
```env
AGENT=cmd
AGENT_CMD=gemini -p "$(cat)"     # prompt on stdin, reply on stdout
```
- Replace the Claude Code install line in the Dockerfile with your CLI
- Copy `CLAUDE.md` to the file your CLI reads (`AGENTS.md` for Codex, `GEMINI.md` for Gemini CLI)
- The agent must be able to run shell commands in `/data/work` (for the `bin/` tools) and ideally keep its own session
- Want multi-turn memory? Write a session-aware runner next to `run_claude()` in `bridge/app.py`

## Swappable parts

| Part | Default | Alternatives |
|---|---|---|
| Chat | Telegram | edit `send_text` / `telegram_loop`: Discord, Slack, Lark/Feishu, WeCom, Matrix |
| Phone health data | Health Auto Export | Android: Health Connect + Tasker / webhook apps → POST `/health` (adapt `ingest.py`) |
| Spend alerts | iOS Shortcuts SMS forward | Android Tasker / MacroDroid; bank e-mail alerts + mail rules |
| Smart home | Home Assistant | anything with an HTTP API — model a tool on `bin/ha.py` |
| Remote access | Tailscale | WireGuard, ZeroTier, Cloudflare Tunnel (add HTTPS) |
| Database | SQLite | it's enough; otherwise adapt the scripts in `bin/` |

## ⚠️ Disclaimer

health-buddy is **not a medical device and does not give medical advice**. Calorie numbers are estimates; health alerts are hints. If you feel unwell, see a doctor.

## License

MIT
