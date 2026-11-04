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
        "muted": "#B5ABA2", "slice": "#A9786A", "rest": "#DDD7CE",
    },
    {  # graphite
        "bg": "#17171A", "brand": "#F2EFEA", "hook": "#EFE4E0", "accent": "#E2B8A4",
        "sub": "#AC8C8A", "num": "#AC8C8A",
        "lead": "#E2B8A4", "lead_t": "#17171A", "bar": "#2A2527", "bar_t": "#EFE4E0",
        "out_t": "#EFE4E0", "value": "#D3B9B6", "lead_v": "#E2B8A4",
        "foot": "#AC8C8A", "line": "#3A3436", "cta": "#E2B8A4",
        "muted": "#6B5A5C", "slice": "#7E3A44", "rest": "#3A3436",
    },
    {  # oxblood
        "bg": "#5C1A23", "brand": "#F2EFEA", "hook": "#EFE4E0", "accent": "#E2B8A4",
        "sub": "#D3B9B6", "num": "#AC8C8A",
        "lead": "#E2B8A4", "lead_t": "#17171A", "bar": "#6E2731", "bar_t": "#EFE4E0",
        "out_t": "#EFE4E0", "value": "#D3B9B6", "lead_v": "#E2B8A4",
        "foot": "#AC8C8A", "line": "#7E3A44", "cta": "#E2B8A4",
        "muted": "#9A5A63", "slice": "#8E4550", "rest": "#6E2731",
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


def header(d, r, t):
    ring(d, M + 16, 96, 16, t["brand"], t["bg"])
    spaced(d, M + 46, 85, "OSNOVA FINANCE", font(20, 500), t["brand"], 3)
    y = draw_hook(d, 170, r["hook"], t)
    period = f"{r['start']}-{r['year']}" if r.get("type") == "line" else str(r["year"])
    sub = f"{r['title']} · {period}"
    sf = font(28)
    while tw(d, sub, sf) > W - 2 * M and sf.size > 20:
        sf = font(sf.size - 1)
    d.text((M, y + 12), sub, font=sf, fill=t["sub"])
    return y + 100


def footer(d, r, t):
    foot = H - 150
    d.rectangle([M, foot, W - M, foot], fill=t["line"])
    d.text((M, foot + 30), f"Источник: {r['source_full']}", font=font(22), fill=t["foot"])
    cf = font(30, 600)
    cy = foot + 92
    d.text((M, cy), "Рынки и данные 24/7 в Telegram @osnovafin", font=cf, fill=t["cta"], anchor="lm")
    plane(d, W - M - 52, cy, 52, t["cta"], t["bg"])


def body_bars(d, r, t, y):
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


def body_line(d, r, t, y):
    from fmt import fmt_value
    series = r["series"]
    lab_w = 250
    x0, x1 = M + 4, W - M - lab_w
    y0, y1 = y + 30, H - 150 - 80
    xs0 = min(s["points"][0][0] for s in series)
    xs1 = max(s["points"][-1][0] for s in series)
    vmax = max(v for s in series for _, v in s["points"]) * 1.06

    def px(yr):
        return x0 + (x1 - x0) * (yr - xs0) / max(xs1 - xs0, 1)

    def py(v):
        return y1 - (y1 - y0) * v / vmax

    # сетка: 3 горизонтальные линии с подписями
    gf = font(22)
    grid = []
    import math
    raw = vmax / 1.06 / 3
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    for k in (1, 2, 3):
        v = step * k
        if v > vmax:
            break
        yy = py(v)
        d.line([x0, yy, x1, yy], fill=t["line"], width=1)
        grid.append((yy, fmt_value(v, r["unit"])))
    d.line([x0, y1, x1, y1], fill=t["line"], width=2)
    d.text((x0, y1 + 14), str(xs0), font=font(24, 500), fill=t["num"], anchor="lt")
    d.text((x1, y1 + 14), str(xs1), font=font(24, 500), fill=t["num"], anchor="rt")

    order = sorted(series, key=lambda s: s.get("hl", False))  # выделенная поверх
    for s in order:
        pts = [(px(a), py(b)) for a, b in s["points"]]
        hl = s.get("hl", False)
        d.line(pts, fill=t["lead"] if hl else t["muted"], width=8 if hl else 4, joint="curve")
        if hl:
            ex, ey = pts[-1]
            d.ellipse([ex - 9, ey - 9, ex + 9, ey + 9], fill=t["lead"])

    for yy, txt in grid:  # подписи сетки поверх линий, на подложке цвета фона
        bb = d.textbbox((x0, yy - 8), txt, font=gf, anchor="lb")
        d.rectangle([bb[0] - 4, bb[1] - 3, bb[2] + 6, bb[3] + 3], fill=t["bg"])
        d.text((x0, yy - 8), txt, font=gf, fill=t["foot"], anchor="lb")

    # подписи на концах линий без наложения
    labs = sorted(((py(s["points"][-1][1]), s) for s in series), key=lambda a: a[0])
    placed, min_gap = [], 58
    for yy, s in labs:
        if placed and yy - placed[-1][0] < min_gap:
            yy = placed[-1][0] + min_gap
        placed.append((yy, s))
    shift = max(0, placed[-1][0] - y1) if placed else 0
    for yy, s in placed:
        yy -= shift
        hl = s.get("hl", False)
        nf = font(26, 600 if hl else 500)
        d.text((x1 + 22, yy - 14), s["name"], font=nf,
               fill=t["lead_v"] if hl else t["out_t"], anchor="lm")
        d.text((x1 + 22, yy + 16), s["text"], font=font(22), fill=t["sub"], anchor="lm")


def body_donut(d, r, t, y):
    top = r["top"]
    cx, cy, R, Ri = W / 2, y + 230, 210, 132
    slices = [(x["share"], t["lead"] if i == 0 else t["slice"]) for i, x in enumerate(top)]
    slices.append((r["rest"], t["rest"]))
    a = -90.0
    for sh, col in slices:
        span = 360 * sh / 100
        d.pieslice([cx - R, cy - R, cx + R, cy + R], a, a + span, fill=col)
        a += span
    # разделители между долями цветом фона
    import math
    a = -90.0
    for sh, _ in slices:
        rad = math.radians(a)
        d.line([cx, cy, cx + R * math.cos(rad), cy + R * math.sin(rad)], fill=t["bg"], width=6)
        a += 360 * sh / 100
    d.ellipse([cx - Ri, cy - Ri, cx + Ri, cy + Ri], fill=t["bg"])
    from fmt import fmt_value
    d.text((cx, cy - 10), fmt_value(r["top_sum"], "pct0"), font=font(64, 600), fill=t["lead_v"], anchor="mm")
    d.text((cx, cy + 44), "пять стран", font=font(24, 500), fill=t["sub"], anchor="mm")

    ly = cy + R + 44
    rows = [(x["rank"], x["name"], x["text"], i == 0) for i, x in enumerate(top)]
    rows.append(("", "Остальные страны", fmt_value(r["rest"], "pct"), False))
    lh = min(46, (H - 150 - 20 - ly) / len(rows))
    for i, (rk, name, val, lead) in enumerate(rows):
        yy = ly + i * lh
        sw = t["lead"] if lead else (t["rest"] if rk == "" else t["slice"])
        d.rectangle([M, yy + 6, M + 22, yy + 28], fill=sw)
        d.text((M + 40, yy + 17), f"{rk}  {name}" if rk else name, font=font(28, 600 if lead else 500),
               fill=t["lead_v"] if lead else t["out_t"], anchor="lm")
        d.text((W - M, yy + 17), val, font=font(28, 600), fill=t["lead_v"] if lead else t["value"], anchor="rm")


def render_card(r, path, theme=0):
    t = THEMES[theme % len(THEMES)]
    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)
    y = header(d, r, t)
    kind = r.get("type", "bars")
    if kind == "line":
        body_line(d, r, t, y)
    elif kind == "donut":
        body_donut(d, r, t, y)
    else:
        body_bars(d, r, t, y)
    footer(d, r, t)
    img.save(path, optimize=True)
    # Instagram API принимает только JPEG
    img.save(os.path.splitext(path)[0] + ".jpg", quality=92, optimize=True)


def render_cover(r, photo_path, out_path):
    """Обложка карусели: стоковое фото, затемнение graphite, вывод крупно."""
    from PIL import ImageOps
    t = THEMES[1]
    ph = Image.open(photo_path).convert("RGB")
    ph = ImageOps.fit(ph, (W, H), method=Image.LANCZOS, centering=(0.5, 0.45))
    # затемнение: ровный слой + усиление к низу (разрешено правилами для фото)
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for yy in range(H):
        k = yy / H
        a = 0.42 + 0.50 * max(0.0, (k - 0.30) / 0.70) ** 1.3
        sd.line([(0, yy), (W, yy)], fill=int(255 * min(a, 0.93)))
    dark = Image.new("RGB", (W, H), t["bg"])
    img = Image.composite(dark, ph, shade)
    d = ImageDraw.Draw(img)

    d.ellipse([M, 80, M + 32, 112], outline="#F2EFEA", width=6)  # знак-кольцо поверх фото
    spaced(d, M + 46, 85, "OSNOVA FINANCE", font(20, 500), "#F2EFEA", 3)

    # вывод: снизу вверх, крупно
    segs = r["hook"]
    for size in (80, 72, 64, 58):
        f = font(size, 600)
        lines, space = layout(d, segs, f, W - 2 * M)
        if len(lines) <= 4:
            break
    lh = int(size * 1.14)
    cta_y = H - 120
    sub_y = cta_y - 90
    y = sub_y - 24 - lh * len(lines)
    for line in lines:
        x = M
        for i, (tok, hl, w) in enumerate(line):
            if i:
                x += space
            d.text((x, y), tok, font=f, fill="#E2B8A4" if hl else "#F2EFEA")
            x += w
        y += lh
    period = f"{r['start']}-{r['year']}" if r.get("type") == "line" else str(r["year"])
    sub = f"{r['title']} · {period}"
    sf = font(28)
    while tw(d, sub, sf) > W - 2 * M and sf.size > 20:
        sf = font(sf.size - 1)
    d.text((M, sub_y), sub, font=sf, fill="#D3B9B6")
    d.rectangle([M, cta_y - 24, W - M, cta_y - 23], fill="#7E3A44")
    d.text((M, cta_y + 30), "Рынки и данные 24/7 в Telegram @osnovafin", font=font(30, 600),
           fill="#E2B8A4", anchor="lm")
    plane(d, W - M - 52, cta_y + 30, 52, "#E2B8A4", "#17171A")
    img.save(out_path, quality=88, optimize=True)
