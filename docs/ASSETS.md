# docs/ 里的图片 / Visual assets

所有图片都是**示意图（mock-up），不是真实截图**，里面的金额、热量、时间都是虚构的。
All images are mock-ups, not real screenshots; every number in them is fictional.

| 文件 | 用途 |
|---|---|
| `social-preview.png` | 1280×640，GitHub 仓库的 Social preview（Settings → Social preview 手动上传） |
| `demo.zh.gif` | README.md 顶部的中文示意动画 |
| `demo.en.gif` | README.en.md 顶部的英文示意动画 |

图片用 Python Pillow 以 2 倍分辨率渲染后 LANCZOS 缩小。字体文件**不在仓库里**，只在生成时下载：

| 字体 / 素材 | 用在哪 | 许可证 | 来源 |
|---|---|---|---|
| Noto Sans SC（可变字重） | 所有中文 | SIL Open Font License 1.1 | Google Fonts |
| Plus Jakarta Sans（可变字重） | “health-buddy” 字标、英文标题 | SIL Open Font License 1.1 | Google Fonts |
| Manrope（可变字重） | 英文正文、界面文字、数字 | SIL Open Font License 1.1 | Google Fonts |
| Noto Color Emoji（Google 设计的 emoji 位图） | 图里的 emoji | Apache License 2.0 | 经 npm 包 `emoji-datasource-google`（包本身 MIT） |

Telegram、Apple Health、Home Assistant 等名称仅用于说明兼容性，商标归各自所有者。
