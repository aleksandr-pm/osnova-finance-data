"""Карточка рейтинга 1080x1350 · палитра R (Oxblood + Bone) · Rubik · v3.

Минимум элементов: знак → вывод с одной цифрой → подзаголовок →
7 толстых полос (цвет только у лидера) → источник → строка Telegram.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
W, H = 1080, 1350
M = 80
ROWS = 7

THEMES = [
    {  # светлая
        "bg": "#F2EFEA", "brand": "#5C1A23", "hook": "#17171A", "accent": "#5C1A23",
        "sub": "#6B6462", "num": "#6B6462",
        "lead": "#5C1A23", "lead_t": "#F2EFEA", "bar": "#E6E1D9", "bar_t": "#1E1B1C",
        "out_t": "#1E1B1C", "value": "#1E1B1C", "lead_v": "#5C1A23",
        "foot": "#6B6462", "line": "#DDD7CE", "cta": "#5C1A23",
    },
    {  # graphite
        "bg": "#17171A", "brand": "#F2EFEA", "hook": "#EFE4E0", "accent": "#E2B8A4",
        "sub": "#AC8C8A", "num": "#AC8C8A",
        "lead": "#E2B8A4", "lead_t": "#17171A", "bar": "#2A2527", "bar_t": "#EFE4E0",
        "out_t": "#EFE4E0", "value": "#D3B9B6", "lead_v": "#E2B8A4",
        "foot": "#AC8C8A", "line": "#3A3436", "cta": "#E2B8A4",
    },
    {  # oxblood
        "bg": "#5C1A23", "brand": "#F2EFEA", "hook": "#EFE4E0", "accent": "#E2B8A4",
        "sub": "#D3B9B6", "num": "#AC8C8A",
        "lead": "#E2B8A4", "lead_t": "#17171A", "bar": "#6E2731", "bar_t": "#EFE4E0",
        "out_t": "#EFE4E0", "value": "#D3B9B6", "lead_v": "#E2B8A4",
        "foot": "#AC8C8A", "line": "#7E3A44", "cta": "#E2B8A4",
    },
]

WEIGHTS = {400: "Rubik_400Regular", 500: "Rubik_500Medium",
           600: "Rubik_600SemiBold", 700: "Rubik_700Bold"}
_fc = {}


def font(size, weight=400):
    key = (size, weight)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(os.path.join(FONTS, WEIGHTS[weight] + ".ttf"), size)
    return _fc[key]


def tw(d, s, f):
    return d.textlength(s, font=f)


def spaced(d, x, y, s, f, fill, sp):
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += tw(d, ch, f) + sp


def ring(d, cx, cy, r, color, bg):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    ri = r * 30 / 46
    d.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=bg)


def plane(d, x, cy, s, color, bg):
    d.ellipse([x, cy - s / 2, x + s, cy + s / 2], fill=color)
    pts = [(0.21, 0.50), (0.76, 0.28), (0.67, 0.73), (0.51, 0.62),
           (0.43, 0.71), (0.42, 0.57), (0.66, 0.36), (0.38, 0.55)]
    y = cy - s / 2
    d.polygon([(x + s * a, y + s * b) for a, b in pts], fill=bg)


def layout(d, segs, f, width):
    tokens = []
    for text, hl in segs:
        tokens += [(text, True)] if hl else [(w, False) for w in text.split()]
    space = tw(d, " ", f)
    lines, cur, cw = [], [], 0
    for tok, hl in tokens:
        w = tw(d, tok, f)
        add = w if not cur else space + w
        if cur and cw + add > width:
            lines.append(cur)
            cur, cw = [(tok, hl, w)], w
        else:
            cur.append((tok, hl, w))
            cw += add
    if cur:
        lines.append(cur)
    return lines, space


def draw_hook(d, y, segs, t):
    for size in (66, 60, 54, 48):
        f = font(size, 600)
        lines, space = layout(d, segs, f, W - 2 * M)
        if len(lines) <= 3:
            break
    for line in lines:
        x = M
        for i, (tok, hl, w) in enumerate(line):
            if i:
                x += space
            d.text((x, y), tok, font=f, fill=t["accent"] if hl else t["hook"])
            x += w
        y += int(size * 1.16)
    return y


def render_card(r, path, theme=0):
    t = THEMES[theme % len(THEMES)]
    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)

    ring(d, M + 16, 96, 16, t["brand"], t["bg"])
    spaced(d, M + 46, 85, "OSNOVA FINANCE", font(20, 500), t["brand"], 3)

    y = draw_hook(d, 170, r["hook"], t)
    sub = f"{r['title']} · {r['year']}"
    sf = font(28)
    while tw(d, sub, sf) > W - 2 * M and sf.size > 20:
        sf = font(sf.size - 1)
    d.text((M, y + 12), sub, font=sf, fill=t["sub"])
    y += 100

    rows = r["top"][:ROWS]
    foot = H - 150
    row_h = (foot - 40 - y) / ROWS
    bh = min(64, int(row_h * 0.72))
    vf, nf, numf = font(32, 600), font(30, 500), font(24, 500)
    val_w = max(tw(d, x["text"], vf) for x in rows)
    x0 = M + 44
    x_val = W - M - val_w
    max_bw = x_val - 28 - x0
    vmax = max(abs(x["value"]) for x in rows) or 1
    for i, row in enumerate(rows):
        yy = int(y + i * row_h)
        cy = yy + bh / 2
        d.text((M, cy), str(row["rank"]), font=numf, fill=t["num"], anchor="lm")
        bw = max(max_bw * abs(row["value"]) / vmax, 8)
        lead = i == 0
        d.rectangle([x0, yy, x0 + bw, yy + bh], fill=t["lead"] if lead else t["bar"])
        name = row["name"]
        f_name = nf
        if tw(d, name, f_name) + 40 <= bw:
            d.text((x0 + 20, cy), name, font=f_name, fill=t["lead_t"] if lead else t["bar_t"], anchor="lm")
        else:
            room = x_val - 28 - (x0 + bw + 18)
            while tw(d, name, f_name) > room and f_name.size > 20:
                f_name = font(f_name.size - 2, 500)
            d.text((x0 + bw + 18, cy), name, font=f_name, fill=t["out_t"], anchor="lm")
        d.text((W - M, cy), row["text"], font=vf,
               fill=t["lead_v"] if lead else t["value"], anchor="rm")

    d.rectangle([M, foot, W - M, foot], fill=t["line"])
    d.text((M, foot + 30), f"Источник: {r['source_full']}", font=font(22), fill=t["foot"])
    cf = font(30, 600)
    cta = "Полный рейтинг в Telegram @osnovafin"
    cy = foot + 92
    d.text((M, cy), cta, font=cf, fill=t["cta"], anchor="lm")
    plane(d, W - M - 52, cy, 52, t["cta"], t["bg"])
    img.save(path, optimize=True)
