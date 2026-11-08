#!/usr/bin/env python3
"""Generate the images in docs/: two social previews + four feature animations (APNG, zh/en).

All chats are mock-ups with fictional money / card / merchant values. The meal photo is the author's own lunch.
Usage:  python3 docs/src/make_assets.py [--social-only | --anim-only] [--cache DIR]
Needs:  Pillow (pip install pillow). Fonts and emoji are downloaded into the cache dir on first run:
        Noto Sans SC, Plus Jakarta Sans, Manrope (all SIL OFL 1.1) and Google Noto emoji PNGs (Apache 2.0).
Put the real meal photo at <cache>/real/tandoori.jpg (any size); otherwise a small fallback is used.
"""
import os, re, sys, math, random, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
CACHE = sys.argv[sys.argv.index("--cache") + 1] if "--cache" in sys.argv else os.path.join(os.path.dirname(os.path.dirname(DOCS)), ".hw-cache")
FONTS = f"{CACHE}/fonts"; EMOJI_DIR = f"{CACHE}/emoji"; REAL_DIR = f"{CACHE}/real"
for d in (FONTS, EMOJI_DIR, REAL_DIR): os.makedirs(d, exist_ok=True)
S = 2  # supersampling

FONT_URLS = {
    "NotoSansSC.ttf": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf",
    "PlusJakartaSans.ttf": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/plusjakartasans/PlusJakartaSans%5Bwght%5D.ttf",
    "Manrope.ttf": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/manrope/Manrope%5Bwght%5D.ttf",
}
EMOJI = {"🧋": "1f9cb", "🍗": "1f357", "🩺": "1fa7a", "⌚": "231a", "🏠": "1f3e0", "💳": "1f4b3", "📱": "1f4f1",
         "💬": "1f4ac", "🌙": "1f319", "☀️": "2600-fe0f", "🤖": "1f916", "📸": "1f4f8", "🧾": "1f9fe", "📒": "1f4d2",
         "💸": "1f4b8", "👍": "1f44d", "📊": "1f4ca", "🍱": "1f371", "💰": "1f4b0", "🔒": "1f512", "✅": "2705",
         "⚡": "26a1", "💡": "1f4a1", "👀": "1f440", "🕤": "1f564", "📅": "1f4c5", "🍚": "1f35a", "🥦": "1f966",
         "🤒": "1f912", "🤫": "1f92b", "😏": "1f60f", "🛏️": "1f6cf-fe0f", "🕚": "1f55a", "💛": "1f49b", "🥬": "1f96c",
         "🌶️": "1f336-fe0f", "📈": "1f4c8", "🏪": "1f3ea"}

def fetch(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 1000: return
    print("downloading", os.path.basename(dst)); urllib.request.urlretrieve(url, dst)
for fn, url in FONT_URLS.items(): fetch(url, f"{FONTS}/{fn}")
for code in EMOJI.values(): fetch(f"https://cdn.jsdelivr.net/npm/emoji-datasource-google@15.1.2/img/google/64/{code}.png", f"{EMOJI_DIR}/{code}.png")

CJK_FONT, LAT_DISPLAY, LAT_TEXT = f"{FONTS}/NotoSansSC.ttf", f"{FONTS}/PlusJakartaSans.ttf", f"{FONTS}/Manrope.ttf"
EMOJI_RE = re.compile("(" + "|".join(re.escape(k) for k in sorted(EMOJI, key=len, reverse=True)) + ")")
_ec, _fc, _pc = {}, {}, {}

def emoji_img(ch, size):
    k = (ch, size)
    if k not in _ec: _ec[k] = Image.open(f"{EMOJI_DIR}/{EMOJI[ch]}.png").convert("RGBA").resize((size, size), Image.LANCZOS)
    return _ec[k]

def font(path, size, weight):
    k = (path, size, weight)
    if k not in _fc:
        f = ImageFont.truetype(path, size); f.set_variation_by_name(weight); _fc[k] = f
    return _fc[k]

def is_cjk(ch):
    o = ord(ch)
    return 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or 0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFFEF or 0x2E80 <= o <= 0x2EFF or 0x3040 <= o <= 0x30FF
CJK_PUNCT_NOSTART = set("，。、？！：；）」』》】”’…")

class Style:
    def __init__(self, size, cjk_w="Regular", lat_w="Regular", lat=LAT_TEXT, fill=(255, 255, 255), tracking=0, esize=None):
        self.size = size * S
        self.cjk = font(CJK_FONT, self.size, cjk_w); self.lat = font(lat, self.size, lat_w)
        self.fill = fill; self.tracking = tracking * S; self.esize = (esize or int(size * 1.12)) * S
        self.asc = max(self.cjk.getmetrics()[0], self.lat.getmetrics()[0]); self.desc = max(self.cjk.getmetrics()[1], self.lat.getmetrics()[1])
        self.lh = self.asc + self.desc

def tokens(text):
    out = []
    for part in EMOJI_RE.split(text):
        if not part: continue
        if part in EMOJI: out.append(("e", part)); continue
        buf = ""
        for ch in part:
            if is_cjk(ch):
                if buf: out.append(("w", buf)); buf = ""
                out.append(("c", ch))
            elif ch == " ":
                if buf: out.append(("w", buf)); buf = ""
                out.append(("s", " "))
            else: buf += ch
        if buf: out.append(("w", buf))
    return out

def tok_w(t, st):
    k, v = t
    if k == "e": return st.esize + 3 * S
    if k == "c": return st.cjk.getlength(v) + st.tracking
    f = st.lat if not any(is_cjk(c) for c in v) else st.cjk
    return f.getlength(v) + st.tracking * len(v)

def wrap(text, st, max_w):
    lines = []
    for para in text.split("\n"):
        cur, w = [], 0
        for t in tokens(para):
            tw = tok_w(t, st)
            if cur and w + tw > max_w and not (t[0] == "c" and t[1] in CJK_PUNCT_NOSTART) and t[0] != "s":
                while cur and cur[-1][0] == "s": cur.pop()
                lines.append(cur); cur, w = [], 0
            cur.append(t); w += tw
        while cur and cur[-1][0] == "s": cur.pop()
        lines.append(cur)
    return lines

def line_w(line, st): return sum(tok_w(t, st) for t in line)

def draw_line(img, x, y, line, st):
    d = ImageDraw.Draw(img); base = y + st.asc
    for k, v in line:
        if k == "e":
            im = emoji_img(v, st.esize); img.paste(im, (int(x + 1.5 * S), int(base - st.esize * 0.82)), im); x += st.esize + 3 * S
        elif k == "s": x += st.lat.getlength(" ")
        else:
            f = st.cjk if k == "c" or any(is_cjk(c) for c in v) else st.lat
            if st.tracking:
                for ch in v: d.text((x, base), ch, font=f, fill=st.fill, anchor="ls"); x += f.getlength(ch) + st.tracking
            else: d.text((x, base), v, font=f, fill=st.fill, anchor="ls"); x += f.getlength(v)

def text(img, xy, s, st, max_w=None, gap=0.3, align="left"):
    x0, y = xy[0] * S, xy[1] * S
    lines = wrap(s, st, max_w * S) if max_w else [tokens(p) for p in s.split("\n")]
    g = int(st.size * gap)
    for ln in lines:
        lw = line_w(ln, st); x = x0 if align == "left" else (x0 - lw / 2 if align == "center" else x0 - lw)
        draw_line(img, x, y, ln, st); y += st.lh + g
    return (y - g - xy[1] * S) / S

def text_w(s, st): return max(line_w(l, st) for l in [tokens(p) for p in s.split("\n")]) / S
def rr(img, box, r, fill, outline=None, width=1):
    ImageDraw.Draw(img).rounded_rectangle([int(v * S) for v in box], radius=int(r * S), fill=fill, outline=outline, width=int(width * S))
def canvas(w, h, color): return Image.new("RGB", (w * S, h * S), color)
def down(img): return img.resize((img.width // S, img.height // S), Image.LANCZOS)

BG = (11, 18, 32); CARD = (17, 26, 44); BOT = (30, 41, 61); USER = (37, 99, 235)
TXT = (240, 243, 248); SUB = (150, 163, 184); MUTED = (96, 110, 134); ACCENT = (125, 211, 252)
AMBER = (245, 158, 11); BLUE = (96, 165, 250); PINK = (244, 114, 182); GREEN = (52, 211, 153); GRID = (226, 230, 238)

# ───────────── chat primitives ─────────────
def bubble(img, x, y, s, st, max_w, side="bot", time=None, pad=13):
    lines = wrap(s, st, (max_w - 2 * pad) * S); g = int(st.size * 0.28)
    th = (len(lines) * (st.lh + g) - g) / S; tw = max(line_w(l, st) for l in lines) / S
    tst = Style(st.size / S * 0.68, "Regular", "Medium", fill=SUB if side == "bot" else (205, 222, 255))
    tw_time = text_w(time, tst) + 8 if time else 0
    one = len(lines) == 1 and tw + tw_time + 2 * pad <= max_w
    bw = min(max_w, tw + 2 * pad + (tw_time if one else 0)); bh = th + 2 * pad + (0 if one or not time else tst.lh / S * 0.9)
    bx = x if side == "bot" else x - bw; col = BOT if side == "bot" else USER
    rr(img, (bx, y, bx + bw, y + bh), 16, col); d = ImageDraw.Draw(img)
    tail = [(bx + 2, y + bh - 12), (bx - 7, y + bh), (bx + 12, y + bh)] if side == "bot" else [(bx + bw - 2, y + bh - 12), (bx + bw + 7, y + bh), (bx + bw - 12, y + bh)]
    d.polygon([(px * S, py * S) for px, py in tail], fill=col)
    yy = (y + pad) * S
    for ln in lines: draw_line(img, (bx + pad) * S, yy, ln, st); yy += st.lh + g
    if time: text(img, (bx + bw - pad + 2, y + bh - pad - tst.lh / S + 3), time, tst, align="right")
    return bh

def sys_pill(img, cx, y, s, st, max_w):
    lines = wrap(s, st, max_w * S); g = int(st.size * 0.25)
    bw = max(line_w(l, st) for l in lines) / S + 32; bh = (len(lines) * (st.lh + g) - g) / S + 16
    rr(img, (cx - bw / 2, y, cx + bw / 2, y + bh), 12, CARD); yy = (y + 8) * S
    for ln in lines: draw_line(img, (cx - bw / 2 + 16) * S, yy, ln, st); yy += st.lh + g
    return bh

def photo(name, w, h, focus=(0.42, 0.50)):
    """real meal photo cropped to w:h around a focus point (fractions), returned at 2x"""
    k = (name, w, h)
    if k not in _pc:
        cands = [f"{REAL_DIR}/{name}.jpg", f"{REAL_DIR}/{name}.jpeg", f"{REAL_DIR}/{name}.png", f"{REAL_DIR}/{name}.extracted.png"]
        path = next((p for p in cands if os.path.exists(p)), None)
        if not path: raise SystemExit(f"meal photo missing: put it at {REAL_DIR}/{name}.jpg")
        im = Image.open(path).convert("RGB"); W0, H0 = im.size
        if W0 / H0 > w / h: cw, ch = int(H0 * w / h), H0
        else: cw, ch = W0, int(W0 * h / w)
        cx, cy = int(W0 * focus[0]), int(H0 * focus[1])
        x0 = min(max(cx - cw // 2, 0), W0 - cw); y0 = min(max(cy - ch // 2, 0), H0 - ch)
        out = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((w * S, h * S), Image.LANCZOS)
        if cw < w * S: out = out.filter(ImageFilter.UnsharpMask(radius=1.5, percent=60, threshold=2))   # small source → upscaled, crisp it a little
        _pc[k] = out
    return _pc[k]

def photo_bubble(img, x_right, y, pic, time, pad=6):
    w, h = pic.width // S, pic.height // S; bw, bh = w + 2 * pad, h + 2 * pad; bx = x_right - bw
    rr(img, (bx, y, bx + bw, y + bh), 16, USER)
    mask = Image.new("L", pic.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pic.width - 1, pic.height - 1], radius=12 * S, fill=255)
    img.paste(pic, (int((bx + pad) * S), int((y + pad) * S)), mask)
    tst = Style(12.5, "Regular", "Medium", fill=(225, 235, 255))
    rr(img, (bx + bw - pad - text_w(time, tst) - 14, y + bh - pad - 20, bx + bw - pad - 4, y + bh - pad - 4), 8, (20, 40, 90))
    text(img, (bx + bw - pad - 9, y + bh - pad - 19), time, tst, align="right")
    return bh

def chart_bubble(img, x, y, chart, caption, st, bw, time, pad=10):
    ch, cw = chart.height // S, chart.width // S
    lines = wrap(caption, st, (bw - 2 * pad) * S); g = int(st.size * 0.28); th = (len(lines) * (st.lh + g) - g) / S
    tst = Style(st.size / S * 0.68, "Regular", "Medium", fill=SUB)
    bh = pad + ch + 10 + th + pad + tst.lh / S * 0.9
    rr(img, (x, y, x + bw, y + bh), 16, BOT)
    mask = Image.new("L", chart.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, chart.width - 1, chart.height - 1], radius=10 * S, fill=255)
    img.paste(chart, (int((x + pad) * S), int((y + pad) * S)), mask)
    yy = (y + pad + ch + 10) * S
    for ln in lines: draw_line(img, (x + pad + 2) * S, yy, ln, st); yy += st.lh + g
    text(img, (x + bw - pad + 2, y + bh - pad - tst.lh / S + 3), time, tst, align="right")
    return bh

# ───────────── charts (fictional data) ─────────────
def macro_card(w, h, kcal, p, c, f, lang):
    img = canvas(w, h, (250, 250, 252))
    text(img, (14, 10), f"≈ {kcal} 大卡" if lang == "zh" else f"≈ {kcal} kcal", Style(22, "Bold", "ExtraBold", lat=LAT_DISPLAY, fill=(40, 46, 60)))
    text(img, (w - 14, 17), "这顿 · 整份估算" if lang == "zh" else "this meal · whole portion", Style(11, "Regular", "Medium", fill=(150, 158, 172)), align="right")
    tot = p * 4 + c * 4 + f * 9; x0, x1, y0, y1 = 14, w - 14, 50, 66; x = x0
    cols = ((PINK, p * 4), (AMBER, c * 4), (BLUE, f * 9))
    for i, (col, v) in enumerate(cols):
        ww = (x1 - x0) * v / tot; rr(img, (x, y0, x + ww, y1), 4 if i in (0, 2) else 0, col); x += ww
    labels = ("蛋白", "碳水", "脂肪") if lang == "zh" else ("protein", "carbs", "fat"); x = 14
    for (col, _), lab, v in zip(cols, labels, (p, c, f)):
        rr(img, (x, 78, x + 10, 88), 3, col); text(img, (x + 16, 73), f"{lab} {v} g", Style(12, "Regular", "SemiBold", fill=(70, 78, 92))); x += (w - 28) / 3
    return img

def chart_bars(w, h, lang):
    img = canvas(w, h, (250, 250, 252)); d = ImageDraw.Draw(img)
    text(img, (14, 10), "今天 vs 近 30 天日均（S$）" if lang == "zh" else "Today vs 30-day daily average (S$)", Style(12.5, "Medium", "SemiBold", fill=(70, 78, 92)))
    data = [(46, 29), (55, 41)]; top, bottom, left = 40, h - 30, 36; mx = 60
    for gy in (0, 20, 40, 60):
        y = bottom - (gy / mx) * (bottom - top); d.line([(left * S, y * S), ((w - 14) * S, y * S)], fill=GRID, width=S)
        text(img, (left - 6, y - 7), str(gy), Style(10, "Regular", "Medium", fill=(150, 158, 172)), align="right")
    gw = (w - 14 - left) / 2; bw = 44; labels = ("餐饮", "其他") if lang == "zh" else ("Food", "Other")
    for i, (today, avg) in enumerate(data):
        cx = left + gw * i + gw / 2
        for j, (v, col) in enumerate(((today, AMBER if i == 0 else BLUE), (avg, (203, 210, 222)))):
            x0 = cx - bw - 4 + j * (bw + 8); y0 = bottom - (v / mx) * (bottom - top)
            rr(img, (x0, y0, x0 + bw, bottom), 4, col); text(img, (x0 + bw / 2, y0 - 16), str(v), Style(11, "Medium", "SemiBold", fill=(60, 66, 80)), align="center")
        text(img, (cx, bottom + 6), labels[i], Style(12, "Medium", "SemiBold", fill=(70, 78, 92)), align="center")
    lx = w - 14 - 150; leg = ("今天", "日均") if lang == "zh" else ("today", "average")
    rr(img, (lx, 14, lx + 12, 26), 3, AMBER); text(img, (lx + 18, 11), leg[0], Style(11, "Regular", "Medium", fill=(90, 98, 112)))
    rr(img, (lx + 78, 14, lx + 90, 26), 3, (203, 210, 222)); text(img, (lx + 96, 11), leg[1], Style(11, "Regular", "Medium", fill=(90, 98, 112)))
    return img

def chart_line(w, h, lang):
    random.seed(7)
    img = canvas(w, h, (250, 250, 252)); d = ImageDraw.Draw(img)
    text(img, (14, 10), "静息心率 · 最近 30 天（虚线 = 30 天基线）" if lang == "zh" else "Resting heart rate · last 30 days (dashed = 30-day baseline)", Style(12.5, "Medium", "SemiBold", fill=(70, 78, 92)))
    vals = [61 + random.random() * 3 for _ in range(23)] + [65 + random.random() * 3.5 for _ in range(7)]
    top, bottom, left, right = 40, h - 26, 34, w - 14; lo, hi = 58, 72
    for gy in (60, 65, 70):
        y = bottom - (gy - lo) / (hi - lo) * (bottom - top); d.line([(left * S, y * S), (right * S, y * S)], fill=GRID, width=S)
        text(img, (left - 6, y - 7), str(gy), Style(10, "Regular", "Medium", fill=(150, 158, 172)), align="right")
    yb = bottom - (62 - lo) / (hi - lo) * (bottom - top)
    for x in range(int(left), int(right), 10): d.line([(x * S, yb * S), ((x + 5) * S, yb * S)], fill=(150, 158, 172), width=S)
    pts = [((left + (right - left) * i / 29) * S, (bottom - (v - lo) / (hi - lo) * (bottom - top)) * S) for i, v in enumerate(vals)]
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).rectangle([pts[-7][0], top * S, right * S, bottom * S], fill=(244, 114, 182, 28))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"); d = ImageDraw.Draw(img)
    d.line(pts, fill=PINK, width=int(2.2 * S), joint="curve")
    for p in pts[-7:]: d.ellipse([p[0] - 3 * S, p[1] - 3 * S, p[0] + 3 * S, p[1] + 3 * S], fill=PINK)
    text(img, (left, bottom + 4), "-30d", Style(10, "Regular", "Medium", fill=(150, 158, 172)))
    text(img, (right, bottom + 4), "today", Style(10, "Regular", "Medium", fill=(150, 158, 172)), align="right")
    return img

def sleep_chart(w, h, lang):
    img = canvas(w, h, (250, 250, 252)); d = ImageDraw.Draw(img)
    text(img, (14, 10), "最近 7 晚入睡时间（目标 23:30）" if lang == "zh" else "Sleep onset, last 7 nights (goal 23:30)", Style(12.5, "Medium", "SemiBold", fill=(70, 78, 92)))
    mins = [95, 140, 70, 160, 40, 20, 42]; days = list("一二三四五六日") if lang == "zh" else list("MTWTFSS")
    top, bottom, left, right = 40, h - 28, 40, w - 14
    for lab, v in (("22:00", 0), ("23:00", 60), ("00:00", 120), ("01:00", 180)):
        y = bottom - v / 180 * (bottom - top); d.line([(left * S, y * S), (right * S, y * S)], fill=GRID, width=S)
        text(img, (left - 6, y - 7), lab, Style(9.5, "Regular", "Medium", fill=(150, 158, 172)), align="right")
    yg = bottom - 90 / 180 * (bottom - top)
    for x in range(int(left), int(right), 10): d.line([(x * S, yg * S), ((x + 5) * S, yg * S)], fill=GREEN, width=S)
    gw = (right - left) / 7
    for i, v in enumerate(mins):
        x0 = left + gw * i + gw * 0.22; x1 = left + gw * (i + 1) - gw * 0.22; y0 = bottom - v / 180 * (bottom - top)
        rr(img, (x0, y0, x1, bottom), 4, PINK if v > 90 else GREEN)
        text(img, ((x0 + x1) / 2, bottom + 6), days[i], Style(11, "Regular", "SemiBold", fill=(90, 98, 112)), align="center")
    return img

# ───────────── feature animations ─────────────
AW, AH = 520, 660; CW = 380
HDR = {"zh": ("机器人 · 只听你一个人的", "示意图，非真实截图", "消息"), "en": ("bot · only talks to you", "mock-up, not a real screenshot", "Message")}

def scripts(lang):
    zh = lang == "zh"
    pl = photo("tandoori", 260, 195, focus=(0.45, 0.52)); mc = macro_card(CW - 20, 96, 600, 58, 8, 36, lang)
    meal = [
        ("sys", "🍱 12:15 午饭提醒" if zh else "🍱 12:15 lunch nudge"),
        ("bot", ("该出发吃午饭了！目标 12:30 吃上，吃到了拍第一份主菜给我 📸" if zh else "Time to head out for lunch! Aim to eat by 12:30 — send me a photo of the first main dish 📸", "12:15")),
        ("photo", (pl, "12:24")), ("typing", None),
        ("chart", (mc, "🍗 Tandoori 烤鸡 4 块（带骨）· 薄荷酸辣酱 · 黄瓜胡萝卜\n蛋白很足；烤焦的皮撕掉能少约 100 大卡，配一拳头米饭就够" if zh else
                   "🍗 Tandoori chicken ×4 (bone-in) · mint chutney · cucumber & carrot\nHigh protein; peel the charred skin to save ~100 kcal — one fist of rice is enough", "12:24")),
        ("bot", ("📒 已记：午饭 · 今天累计 1,190 / 1,900 大卡，蛋白 82 g ✅\n晚饭还有约 700 大卡：多点蔬菜，主食别太多" if zh else
                 "📒 Logged: lunch · today 1,190 / 1,900 kcal, protein 82 g ✅\nAbout 700 kcal left for dinner — plenty of veg, go easy on the carbs", "12:24")),
        ("user", ("皮撕掉了，饭吃了一小碗" if zh else "peeled the skin, had a small bowl of rice", "12:52")),
        ("bot", ("👍 改成约 500 + 150 = 650 大卡，今天累计 1,240" if zh else "👍 Updated: ≈500 + 150 = 650 kcal, today 1,240", "12:52")),
        ("sys", "✅ 一张照片，热量、营养、花销都记好了" if zh else "✅ One photo — calories, macros and cost all logged"),
    ]
    bars = chart_bars(CW - 20, 180, lang)
    ledger = [
        ("sys", "📱 15:06 银行短信：S$4.20 · LEMON TEA CO\n→ 手机自动转发给了 healthy-wealthy" if zh else "📱 15:06 bank SMS: S$4.20 · LEMON TEA CO\n→ your phone forwarded it to healthy-wealthy"),
        ("typing", None),
        ("bot", ("🧋 又是柠檬茶铺（这个月第 9 次）。老样子，柠檬茶少糖？" if zh else "🧋 Lemon Tea Co. again (9th time this month). The usual, lemon tea less sugar?", "15:06")),
        ("user", ("嗯 少糖" if zh else "yep, less sugar", "15:07")),
        ("bot", ("✅ 已记账：饮料 · S$4.20 · 尾号 0000\n约 90 大卡。不用拍照，熟店我记得" if zh else "✅ Logged: drinks · S$4.20 · card ending 0000\n≈90 kcal. No photo needed — I know this shop", "15:07")),
        ("sys", "🕤 21:30 晚间账单" if zh else "🕤 21:30 nightly ledger"),
        ("chart", (bars, "今天吃饭 S$46，是平时的 1.6 倍 👀 第 2 杯甜饮了\n打车 S$32、超市 S$23 已自动记好，不用管" if zh else "Food today S$46 — 1.6× your usual 👀 that was sweet drink #2\nTaxi S$32 and groceries S$23 logged automatically", "21:30")),
        ("sys", "📅 24 日 10:00 信用卡检查" if zh else "📅 24th, 10:00 card check"),
        ("bot", ("💳 尾号 0000 的返现卡：本月刷了 S$415，还差 S$85 到最低消费 S$500，剩 6 天。接下来的大额消费记得刷它" if zh else
                 "💳 Cashback card ending 0000: S$415 spent this month, S$85 short of the S$500 minimum, 6 days left. Put the next big purchase on it", "10:00")),
        ("sys", "✅ 全程你只回了两个字，账已经记好" if zh else "✅ You typed one word — the ledger wrote itself"),
    ]
    sc = sleep_chart(CW - 20, 170, lang)
    sleep = [
        ("sys", "🌙 23:00"),
        ("bot", ("离 23:30 的睡觉目标还有 1 小时，开始收尾吧。上床了跟我说“晚安”" if zh else "One hour to your 23:30 bedtime goal — start winding down. Say \"good night\" when you're in bed", "23:00")),
        ("sys", "🛏️ 23:30"),
        ("bot", ("该上床了。说了晚安我就闭嘴，不说我 23:45 再来 😏" if zh else "Bed time. Say good night and I'll go quiet — otherwise I'm back at 23:45 😏", "23:30")),
        ("user", ("晚安" if zh else "good night", "23:38")),
        ("bot", ("🤫 晚安。明早我用手表数据对账" if zh else "🤫 Good night. I'll check the watch data in the morning", "23:38")),
        ("sys", "☀️ 09:00 早报" if zh else "☀️ 09:00 morning report"),
        ("chart", (sc, "手表说你 23:52 才睡着——说完晚安又刷了 14 分钟 😏 不过已经连续 3 晚达标，睡了 7.4 小时，静息心率 61 正常。今天目标不变：23:30" if zh else
                   "Watch says you fell asleep at 23:52 — 14 minutes of scrolling after \"good night\" 😏 Still, 3 nights on target in a row: 7.4 h, resting HR 61, all normal. Same goal tonight: 23:30", "09:00")),
        ("sys", "✅ 不靠意志力，靠一个不嫌烦的管家" if zh else "✅ No willpower needed — just a butler who doesn't give up"),
    ]
    line = chart_line(CW - 20, 170, lang)
    trend = [
        ("user", ("最近心率怎么样？" if zh else "How's my heart rate lately?", "10:02")), ("typing", None),
        ("chart", (line, "静息心率这周均值 67，比前 30 天高 5 👀\n这两晚都 2 点后睡，先早睡两天再看" if zh else "Resting HR averaged 67 this week, 5 above your 30-day baseline 👀\nTwo nights past 2 am — sleep early for a couple of days, then we'll look again", "10:02")),
        ("sys", "📅 两天后 09:00" if zh else "📅 two days later, 09:00"),
        ("bot", ("🤒 静息心率连续 2 天比基线高 8，睡眠手腕温度高 0.4°C，心率变异性偏低——这个组合以前三次都是感冒前兆。最近出远门、熬夜或喝酒了吗？" if zh else
                 "🤒 Resting HR 8 above baseline for 2 days, wrist temp +0.4 °C, HRV low — the last three times this combination showed up you caught a cold. Any travel, late nights or alcohol recently?", "09:00")),
        ("user", ("没有，就是有点累" if zh else "no, just a bit tired", "09:05")),
        ("bot", ("那今晚 23:00 前睡、多喝水，明早我再看一眼数据。会议能推就推 💛" if zh else "Then sleep before 23:00 tonight, drink more water, and I'll look again tomorrow morning. Postpone what you can 💛", "09:05")),
        ("sys", "✅ 手表的数据，终于有人每天看" if zh else "✅ Your watch data, finally read by someone every day"),
    ]
    return {"meal": meal, "ledger": ledger, "sleep": sleep, "trend": trend}

def render_anim(lang, steps):
    sub, tag, inp = HDR[lang]
    st = Style(17.5, "Regular", "Medium", fill=TXT); ssys = Style(13, "Regular", "Medium", fill=SUB)
    def base():
        img = canvas(AW, AH, BG); d = ImageDraw.Draw(img)
        d.rectangle((0, 0, AW * S, 66 * S), fill=CARD); d.ellipse([16 * S, 13 * S, 56 * S, 53 * S], fill=(30, 64, 175))
        em = emoji_img("🩺", 24 * S); img.paste(em, (24 * S, 21 * S), em)
        text(img, (68, 12), "healthy-wealthy", Style(17.5, "Bold", "Bold", lat=LAT_DISPLAY, fill=TXT, tracking=-0.3))
        text(img, (68, 37), sub, Style(12, "Regular", "Medium", fill=SUB))
        text(img, (AW - 14, 27), tag, Style(11, "Regular", "Medium", fill=MUTED), align="right")
        return img
    def render(upto, typing=False):
        img = base(); content = canvas(AW, 3600, BG); y = 18
        for kind, p in steps[:upto]:
            if kind == "typing": continue
            if kind == "sys": y += sys_pill(content, AW / 2, y, p, ssys, 420) + 14
            elif kind == "bot": y += bubble(content, 18, y, p[0], st, CW, "bot", p[1]) + 10
            elif kind == "user": y += bubble(content, AW - 18, y, p[0], st, 330, "user", p[1]) + 10
            elif kind == "photo": y += photo_bubble(content, AW - 18, y, p[0], p[1]) + 10
            elif kind == "chart": y += chart_bubble(content, 18, y, p[0], p[1], st, CW, p[2]) + 10
        if typing:
            rr(content, (18, y, 90, y + 36), 15, BOT); d = ImageDraw.Draw(content)
            for i in range(3): d.ellipse([(36 + i * 15) * S, (y + 14) * S, (43 + i * 15) * S, (y + 21) * S], fill=SUB)
            y += 46
        top, bottom = 66, AH - 56; avail = bottom - top; off = max(0, y - avail)
        img.paste(content.crop((0, off * S, AW * S, (off + avail) * S)), (0, top * S))
        d = ImageDraw.Draw(img); d.rectangle((0, (AH - 56) * S, AW * S, AH * S), fill=CARD)
        rr(img, (14, AH - 46, AW - 62, AH - 10), 18, BOT); text(img, (30, AH - 39), inp, Style(15.5, "Regular", "Medium", fill=MUTED))
        d.ellipse([(AW - 52) * S, (AH - 48) * S, (AW - 12) * S, (AH - 8) * S], fill=USER)
        d.polygon([((AW - 40) * S, (AH - 38) * S), ((AW - 24) * S, (AH - 28) * S), ((AW - 40) * S, (AH - 18) * S)], fill=TXT)
        return down(img)
    frames, dur = [], []
    for i, (kind, p) in enumerate(steps):
        if kind == "typing": frames.append(render(i, True)); dur.append(700)
        else: frames.append(render(i + 1)); dur.append({"sys": 1500, "user": 1400, "bot": 2400, "chart": 3400, "photo": 1600}[kind])
    dur[-1] = 4500
    return frames, dur

def save_apng(frames, dur, path):
    """full-colour animated PNG (GitHub renders it in <img>); no palette → photos stay natural"""
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=True, compress_level=9)

# ───────────── social previews ─────────────
def backdrop():
    W, H = 1280, 640
    img = canvas(W, H, BG)
    grad = Image.linear_gradient("L").rotate(-35, expand=True).resize((W * S, H * S))
    img = Image.composite(Image.new("RGB", img.size, (28, 40, 70)), img, grad.point(lambda v: int(v * 0.55)))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([760 * S, -260 * S, 1420 * S, 360 * S], fill=(37, 99, 235, 90)); gd.ellipse([-260 * S, 420 * S, 420 * S, 900 * S], fill=(16, 185, 129, 55))
    return Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(110 * S))).convert("RGB")

def wordmark(img, M, y_icon, y_text):
    em = emoji_img("🩺", 40 * S); img.paste(em, (M * S, y_icon * S), em)
    em2 = emoji_img("💰", 40 * S); img.paste(em2, ((M + 40) * S, y_icon * S), em2)
    wm = Style(40, "Bold", "ExtraBold", lat=LAT_DISPLAY, fill=TXT, tracking=-1.2)
    text(img, (M + 94, y_text), "healthy-wealthy", wm)
    text(img, (M + 94 + text_w("healthy-wealthy", wm) + 18, y_text + 12), "又健又富", Style(24, "Medium", "Medium", fill=SUB))

def phone_frame(img, px, py, pw, ph, sub):
    rr(img, (px - 4, py - 4, px + pw + 4, py + ph + 4), 42, (40, 52, 76)); rr(img, (px, py, px + pw, py + ph), 38, (13, 20, 36))
    rr(img, (px + pw / 2 - 56, py + 14, px + pw / 2 + 56, py + 30), 8, (6, 10, 20))
    text(img, (px + 24, py + 46), "healthy-wealthy", Style(18, "Bold", "Bold", lat=LAT_DISPLAY, fill=TXT, tracking=-0.3))
    text(img, (px + 24, py + 70), sub, Style(12.5, "Regular", "Medium", fill=SUB))

def social_en():
    img = backdrop(); M = 72; wordmark(img, M, 66, 56)
    y = 146
    y += text(img, (M, y), "Health + wealth, one AI butler.", Style(52, "Black", "ExtraBold", lat=LAT_DISPLAY, fill=TXT, tracking=-1.5)) + 14
    y += text(img, (M, y), "健康 + 钱包，一个 AI 管家", Style(52, "Black", "ExtraBold", lat=LAT_DISPLAY, fill=TXT, tracking=0.5)) + 26
    y += text(img, (M, y), "Runs on your own computer · 本地运行，数据不出门 · Telegram · MIT", Style(21, "Medium", "Medium", fill=(196, 206, 224))) + 34
    cst = Style(17.5, "Medium", "SemiBold", fill=TXT); x = M
    for c in ["🍱 Meal photo → kcal", "💳 Bank SMS", "⌚ Apple Health", "🏠 Home Assistant"]:
        w = text_w(c, cst) + 28; rr(img, (x, y, x + w, y + 42), 21, (24, 36, 60), outline=(60, 76, 105), width=1.5)
        text(img, (x + 14, y + 9.5), c, cst); x += w + 10
    y += 74
    text(img, (M, y), "🔒 Your data stays on your disk · github.com/JamesNolan17/healthy-wealthy", Style(18, "Regular", "Medium", fill=SUB))
    px, py, pw, ph = 892, 48, 328, 556; phone_frame(img, px, py, pw, ph, "bot · only talks to you")
    st = Style(15, "Regular", "Medium", fill=TXT); ssys = Style(11.5, "Regular", "Medium", fill=SUB); yy = py + 102; iw = pw - 40
    yy += sys_pill(img, px + pw / 2, yy, "🍱 12:15 lunch — send me your plate", ssys, pw - 36) + 12
    yy += photo_bubble(img, px + pw - 18, yy, photo("tandoori", 164, 112), "12:24") + 10
    yy += bubble(img, px + 18, yy, "🍗 Tandoori chicken ×4 ≈ 600 kcal\nP 58 g · C 8 g · F 36 g\nPeel the charred skin to save ~100 kcal 👍", st, iw - 20, "bot", "12:24", pad=11) + 10
    yy += bubble(img, px + 18, yy, "💳 Lunch S$12.80 on card ····0000 logged · S$85 to this month's minimum spend", st, iw - 20, "bot", "12:31", pad=11) + 10
    text(img, (px + pw / 2, py + ph + 13), "mock-up · fictional values · 虚构数据", Style(12.5, "Regular", "Medium", fill=SUB), align="center")
    return down(img)

def social_zh():
    img = backdrop(); M = 72; wordmark(img, M, 68, 58)
    y = 126
    y += text(img, (M, y), "健康 + 钱包，一个 AI 管家\n本地运行，数据不出门", Style(54, "Black", "ExtraBold", lat=LAT_DISPLAY, fill=TXT, tracking=0.5), gap=0.18) + 18
    y += text(img, (M, y), "拍张饭照就知道热量和营养，刷卡自动记账，到点催你睡觉。\nOne private AI butler for your health and your wallet.\nRuns on your own computer — your data never leaves home.", Style(21, "Medium", "Medium", fill=(196, 206, 224)), gap=0.26) + 24
    cst = Style(21, "Medium", "Medium", fill=TXT)
    for row in (["⌚ 健康  Apple Health", "💳 扣款短信  Bank SMS"], ["🏠 卧室传感器  Home Assistant", "💬 Telegram"]):
        x = M
        for c in row:
            w = text_w(c, cst) + 34; rr(img, (x, y, x + w, y + 44), 22, (24, 36, 60), outline=(60, 76, 105), width=1.5)
            text(img, (x + 17, y + 9), c, Style(19, "Medium", "SemiBold", fill=TXT)); x += w + 12
        y += 54
    y += 6
    text(img, (M, y), "🔒 数据只留在你自己手里 · 开源免费（MIT）· Open source, your data stays home", Style(16.5, "Regular", "Medium", fill=SUB))
    text(img, (M, y + 30), "github.com/JamesNolan17/healthy-wealthy", Style(17, "Medium", "SemiBold", fill=ACCENT))
    px, py, pw, ph = 876, 40, 344, 556; phone_frame(img, px, py, pw, ph, "机器人 · 只听你一个人的")
    st = Style(15.5, "Regular", "Medium", fill=TXT); ssys = Style(12, "Regular", "Medium", fill=SUB); yy = py + 104; iw = pw - 44
    yy += sys_pill(img, px + pw / 2, yy, "🍱 12:15 该吃午饭了，拍第一份主菜给我", ssys, pw - 40) + 12
    yy += photo_bubble(img, px + pw - 20, yy, photo("tandoori", 170, 128), "12:24") + 10
    yy += bubble(img, px + 20, yy, "🍗 Tandoori 烤鸡 4 块，约 600 大卡\n蛋白 58g · 碳水 8g · 脂肪 36g\n蛋白很足，焦皮撕掉少 100 大卡 👍", st, iw - 24, "bot", "12:24", pad=11) + 10
    yy += bubble(img, px + 20, yy, "💳 尾号 0000 的午饭 S$12.80 已自动记账，本月还差 S$85 到最低消费", st, iw - 24, "bot", "12:31", pad=11) + 10
    text(img, (px + pw / 2, py + ph + 13), "mock-up · 虚构数据 · fictional values", Style(12.5, "Regular", "Medium", fill=SUB), align="center")
    return down(img)

if __name__ == "__main__":
    out = DOCS
    if "--anim-only" not in sys.argv:
        for fn, f in (("social-preview.png", social_en), ("social-preview.zh.png", social_zh)):
            im = f(); im.save(f"{out}/{fn}", optimize=True); print(fn, im.size, os.path.getsize(f"{out}/{fn}") // 1024, "KB")
    if "--social-only" not in sys.argv:
        for lang in ("zh", "en"):
            for name, steps in scripts(lang).items():
                fr, du = render_anim(lang, steps); path = f"{out}/demo-{name}.{lang}.png"; save_apng(fr, du, path)
                print(f"demo-{name}.{lang}.png", len(fr), "frames", round(sum(du) / 1000, 1), "s", os.path.getsize(path) // 1024, "KB")
