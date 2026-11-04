"""Карточка рейтинга 1080x1350 · палитра R (Oxblood + Bone) · Rubik.

Структура: шапка с кольцом → заголовок-крючок с выделенной цифрой →
толстые полосы с флагом и страной внутри → строка СНГ → источник →
плашка перехода в Telegram.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
EMOJI_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
]
W, H = 1080, 1350
M = 64

THEMES = [
    {  # светлая
        "bg": "#F2EFEA", "brand": "#5C1A23", "label": "#6B6462", "rule": "#17171A",
        "hook": "#17171A", "plate": "#5C1A23", "plate_t": "#F2EFEA",
        "sub": "#6B6462", "num": "#6B6462",
        "lead": "#5C1A23", "lead_t": "#F2EFEA",
        "bar": "#DDD7CE", "bar_t": "#1E1B1C",
        "cis": "#A9786A", "cis_t": "#FFFFFF",
        "out_t": "#1E1B1C", "value": "#1E1B1C",
        "foot": "#6B6462", "cta": "#5C1A23", "cta_t": "#F2EFEA", "cta_s": "#E2B8A4",
    },
    {  # graphite
        "bg": "#17171A", "brand": "#F2EFEA", "label": "#AC8C8A", "rule": "#EFE4E0",
        "hook": "#EFE4E0", "plate": "#E2B8A4", "plate_t": "#17171A",
        "sub": "#D3B9B6", "num": "#AC8C8A",
        "lead": "#E2B8A4", "lead_t": "#17171A",
        "bar": "#7E3A44", "bar_t": "#EFE4E0",
        "cis": "#D3B9B6", "cis_t": "#17171A",
        "out_t": "#EFE4E0", "value": "#EFE4E0",
        "foot": "#AC8C8A", "cta": "#E2B8A4", "cta_t": "#17171A", "cta_s": "#5C1A23",
    },
    {  # oxblood
        "bg": "#5C1A23", "brand": "#F2EFEA", "label": "#D3B9B6", "rule": "#EFE4E0",
        "hook": "#EFE4E0", "plate": "#E2B8A4", "plate_t": "#17171A",
        "sub": "#D3B9B6", "num": "#D3B9B6",
        "lead": "#E2B8A4", "lead_t": "#17171A",
        "bar": "#7E3A44", "bar_t": "#EFE4E0",
        "cis": "#D3B9B6", "cis_t": "#17171A",
        "out_t": "#EFE4E0", "value": "#EFE4E0",
        "foot": "#D3B9B6", "cta": "#17171A", "cta_t": "#EFE4E0", "cta_s": "#E2B8A4",
    },
]

_fc = {}
WEIGHTS = {400: "Rubik_400Regular", 500: "Rubik_500Medium",
           600: "Rubik_600SemiBold", 700: "Rubik_700Bold"}


def font(size, weight=400):
    key = (size, weight)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(os.path.join(FONTS, WEIGHTS[weight] + ".ttf"), size)
    return _fc[key]


_emoji_font = None
_emoji_cache = {}


def emoji_img(ch, size):
    """Цветной флаг: Noto Color Emoji рисуется только в размере 109, затем масштаб."""
    global _emoji_font
    if not ch:
        return None
    if _emoji_font is None:
        for p in EMOJI_PATHS:
            if os.path.exists(p):
                _emoji_font = ImageFont.truetype(p, 109)
                break
        else:
            _emoji_font = False
    if not _emoji_font:
        return None
    key = (ch, size)
    if key not in _emoji_cache:
        im = Image.new("RGBA", (160, 136), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=_emoji_font, embedded_color=True)
        bb = im.getbbox()
        if not bb:
            _emoji_cache[key] = None
        else:
            im = im.crop(bb)
            h = size
            w = round(im.width * h / im.height)
            _emoji_cache[key] = im.resize((w, h), Image.LANCZOS)
    return _emoji_cache[key]


def tw(d, s, f):
    return d.textlength(s, font=f)


def spaced(d, x, y, s, f, fill, sp):
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += tw(d, ch, f) + sp
    return x


def spaced_w(d, s, f, sp):
    return sum(tw(d, ch, f) + sp for ch in s) - sp


def ring(d, cx, cy, r, color, bg):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    ri = r * 30 / 46
    d.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=bg)


def plane(d, x, y, s, color, bg):
    """Знак Telegram: круг и бумажный самолётик, s сторона квадрата."""
    d.ellipse([x, y, x + s, y + s], fill=color)
    pts = [(0.21, 0.50), (0.76, 0.28), (0.67, 0.73), (0.51, 0.62),
           (0.43, 0.71), (0.42, 0.57), (0.66, 0.36), (0.38, 0.55)]
    d.polygon([(x + s * a, y + s * b) for a, b in pts], fill=bg)


def layout_hook(d, segs, f, width):
    """segs: [(текст, выделить)] → строки из токенов, выделение не переносится."""
    tokens = []
    for text, hl in segs:
        if hl:
            tokens.append((text, True))
        else:
            tokens += [(w, False) for w in text.split()]
    pad = 12
    lines, cur, cur_w = [], [], 0
    space = tw(d, " ", f)
    for t, hl in tokens:
        w = tw(d, t, f) + (2 * pad if hl else 0)
        add = w if not cur else space + w
        if cur and cur_w + add > width:
            lines.append(cur)
            cur, cur_w = [(t, hl, w)], w
        else:
            cur.append((t, hl, w))
            cur_w += add
    if cur:
        lines.append(cur)
    return lines, pad, space


def draw_hook(d, x, y, segs, t, max_w, max_lines=4):
    for size in (68, 62, 56, 50):
        f = font(size, 600)
        lines, pad, space = layout_hook(d, segs, f, max_w)
        if len(lines) <= max_lines:
            break
    lh = int(size * 1.18)
    for line in lines:
        xx = x
        for i, (tok, hl, w) in enumerate(line):
            if i:
                xx += space
            if hl:
                top = y + int(size * 0.10)
                d.rectangle([xx, top, xx + w, top + int(size * 1.08)], fill=t["plate"])
                d.text((xx + pad, y), tok, font=f, fill=t["plate_t"])
            else:
                d.text((xx, y), tok, font=f, fill=t["hook"])
            xx += w
        y += lh
    return y


def render_card(r, path, theme=0):
    t = THEMES[theme % len(THEMES)]
    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)

    # шапка
    ring(d, M + 18, 74, 18, t["brand"], t["bg"])
    spaced(d, M + 50, 62, "OSNOVA FINANCE", font(22, 500), t["brand"], 3)
    lab = f"РЕЙТИНГ · {r['year']}"
    lf = font(22, 500)
    spaced(d, W - M - spaced_w(d, lab, lf, 3), 62, lab, lf, t["label"], 3)

    # заголовок-крючок
    y = draw_hook(d, M, 128, r["hook"], t, W - 2 * M)
    sub = r["title"] + (f" · {r['note']}" if r.get("note") else "")
    sf = font(28, 400)
    while tw(d, sub, sf) > W - 2 * M and sf.size > 20:
        sf = font(sf.size - 1, 400)
    d.text((M, y + 6), sub, font=sf, fill=t["sub"])
    y += 66

    # полосы
    rows = r["top"][:10]
    cis_out = [c for c in r["cis"] if not c["in_top10"]]
    cta_top = H - 164
    src_y = cta_top - 48
    bars_end = src_y - (58 if cis_out else 18)
    n = max(len(rows), 1)
    row_h = (bars_end - y) / n
    bh = min(66, int(row_h * 0.80))
    vf = font(34, 600)
    nf = font(32, 500)
    numf = font(26, 500)
    val_w = max(tw(d, x["text"], vf) for x in rows)
    x0 = M + 48
    x_val = W - M - val_w
    max_bw = x_val - 20 - x0
    vmax = max(abs(x["value"]) for x in rows) or 1
    cis_names = {c["name"] for c in r["cis"]}
    fl_h = int(bh * 0.52)
    for i, row in enumerate(rows):
        yy = int(y + i * row_h)
        cy = yy + bh / 2
        d.text((M, cy), f"{row['rank']}", font=numf, fill=t["num"], anchor="lm")
        bw = max(max_bw * abs(row["value"]) / vmax, 10)
        if i == 0:
            fill, txt = t["lead"], t["lead_t"]
        elif row["name"] in cis_names:
            fill, txt = t["cis"], t["cis_t"]
        else:
            fill, txt = t["bar"], t["bar_t"]
        d.rectangle([x0, yy, x0 + bw, yy + bh], fill=fill)

        fl = emoji_img(row.get("flag", ""), fl_h)
        name = row["name"]
        f_name = nf
        inner = (fl.width + 14 if fl else 0) + tw(d, name, f_name)
        inside = inner + 36 <= bw
        if not inside:
            # не влезает в полосу: пишем справа от неё, ужимаем при нехватке места
            room = x_val - 20 - (x0 + bw + 16)
            while inner > room and f_name.size > 22:
                f_name = font(f_name.size - 2, 500)
                inner = (fl.width + 14 if fl else 0) + tw(d, name, f_name)
        tx = x0 + 18 if inside else x0 + bw + 16
        color = txt if inside else t["out_t"]
        if fl:
            img.paste(fl, (int(tx), int(cy - fl.height / 2)), fl)
            tx += fl.width + 14
        d.text((tx, cy), name, font=f_name, fill=color, anchor="lm")
        d.text((W - M, cy), row["text"], font=vf, fill=t["value"], anchor="rm")

    if cis_out:
        parts = [f"{c['name']} на {c['rank']}-м" for c in cis_out]
        s = parts[0] + " месте" + "".join(", " + p for p in parts[1:]) + "."
        cf = font(28, 500)
        while tw(d, s, cf) > W - 2 * M and cf.size > 20:
            cf = font(cf.size - 1, 500)
        d.text((M, bars_end + 12), s, font=cf, fill=t["sub"])

    d.text((M, src_y + 10), f"Источник: {r['source_full']}, данные за {r['year']}",
           font=font(22), fill=t["foot"])

    # плашка Telegram
    d.rectangle([0, cta_top, W, H], fill=t["cta"])
    d.text((M, cta_top + 34), "Полный рейтинг и рынки 24/7", font=font(38, 600), fill=t["cta_t"])
    d.text((M, cta_top + 88), "в Telegram @osnovafin", font=font(38, 600), fill=t["cta_s"])
    plane(d, W - M - 96, cta_top + 34, 96, t["cta_t"], t["cta"])
    img.save(path, optimize=True)
