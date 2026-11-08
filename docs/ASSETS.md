# docs/ 里的图片 / Visual assets

项目名 healthy-wealthy 取自 “healthy, wealthy and wise”；中文名「又健又富」= healthy and wealthy，和英文名直接对应。

所有图片都是**示意图（mock-up），不是真实截图**，里面的金额、卡号、商家、时间都是虚构的；饭照是作者自己的两张午饭照片（已去除元数据），热量/营养数字是 agent 当时的真实估算。
All images are mock-ups, not real screenshots; every number in them is fictional.

| 文件 | 用途 |
|---|---|
| `social-preview.png` | 1280×640，国际版：英文在前的中英双语大标题、英文手机对话。GitHub 仓库的 Social preview（Settings → Social preview 手动上传），也用于 X / HN |
| `social-preview.zh.png` | 1280×640，中文优先版：中文大标题 + 中文手机对话，给 V2EX / 小红书 / 即刻等中文渠道 |
| `demo-meal.*.gif` | 饭照 → 热量/营养分析（README 顶部 2×2 网格，zh / en 各一份） |
| `demo-ledger.*.gif` | 刷卡自动记账 → 晚间账单图 → 信用卡最低消费提醒 |
| `demo-sleep.*.gif` | 催睡到说“晚安” → 早报用手表对账（含 7 晚入睡时间图） |
| `demo-trend.*.gif` | 静息心率 30 天趋势 → 生病预警 |

图片用 Python Pillow 以 2 倍分辨率渲染后 LANCZOS 缩小。字体文件**不在仓库里**，只在生成时下载：

| 字体 / 素材 | 用在哪 | 许可证 | 来源 |
|---|---|---|---|
| Noto Sans SC（可变字重） | 所有中文 | SIL Open Font License 1.1 | Google Fonts |
| Plus Jakarta Sans（可变字重） | “healthy-wealthy” 字标、英文标题 | SIL Open Font License 1.1 | Google Fonts |
| Manrope（可变字重） | 英文正文、界面文字、数字 | SIL Open Font License 1.1 | Google Fonts |
| Noto Color Emoji（Google 设计的 emoji 位图） | 图里的 emoji | Apache License 2.0 | 经 npm 包 `emoji-datasource-google`（包本身 MIT） |

Telegram、Apple Health、Home Assistant 等名称仅用于说明兼容性，商标归各自所有者。
