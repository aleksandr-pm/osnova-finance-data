"""Карточка рейтинга 1080x1350 в палитре R (Oxblood + Bone), шрифт Rubik."""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "fonts", "Rubik.ttf")
W, H = 1080, 1350
M = 72

THEMES = [
    {  # светлая
        "bg": "#F2EFEA", "label": "#5C1A23", "mark": "#5C1A23", "rule": "#17171A",
        "title": "#1E1B1C", "sub": "#6B6462", "num": "#6B6462", "name": "#1E1B1C",
        "value": "#1E1B1C", "lead": "#5C1A23", "bar": "#DDD7CE", "cis": "#A9786A",
        "foot": "#6B6462", "cta": "#5C1A23", "line": "#DDD7CE",
    },
    {  # graphite
        "bg": "#17171A", "label": "#E2B8A4", "mark": "#F2EFEA", "rule": "#EFE4E0",
        "title": "#EFE4E0", "sub": "#D3B9B6", "num": "#AC8C8A", "name": "#EFE4E0",
        "value": "#EFE4E0", "lead": "#E2B8A4", "bar": "#7E3A44", "cis": "#D3B9B6",
        "foot": "#AC8C8A", "cta": "#E2B8A4", "line": "#3A3436",
    },
    {  # oxblood
        "bg": "#5C1A23", "label": "#E2B8A4", "mark": "#F2EFEA", "rule": "#EFE4E0",
        "title": "#EFE4E0", "sub": "#D3B9B6", "num": "#AC8C8A", "name": "#EFE4E0",
        "value": "#EFE4E0", "lead": "#E2B8A4", "bar": "#7E3A44", "cis": "#D3B9B6",
        "foot": "#AC8C8A", "cta": "#E2B8A4", "line": "#7E3A44",
    },
]

_cache = {}


def font(size, weight=400):
    key = (size, weight)
    if key not in _cache:
        f = ImageFont.truetype(FONT, size)
        try:
            f.set_variation_by_axes([weight])
        except Exception:  # noqa: BLE001
            pass
        _cache[key] = f
    return _cache[key]


def text_w(d, s, f):
    return d.textlength(s, font=f)


def spaced(d, xy, s, f, fill, spacing):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += text_w(d, ch, f) + spacing


def wrap(d, s, f, width):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(d, t, f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def ring(d, cx, cy, r_out, color, bg):
    d.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], fill=color)
    r_in = r_out * 30 / 46
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], fill=bg)


def render_card(r, path, theme=0):
    t = THEMES[theme % len(THEMES)]
    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)

    # шапка
    spaced(d, (M, 70), f"РЕЙТИНГ · {r['source'].upper()}", font(22, 500), t["label"], 3.5)
    ring(d, W - M - 22, 84, 22, t["mark"], t["bg"])
    d.rectangle([M, 128, W - M, 129], fill=t["rule"])

    # заголовок
    y = 160
    tf = font(50, 500)
    lines = wrap(d, r["title"], tf, W - 2 * M)
    if len(lines) > 3:
        tf = font(42, 500)
        lines = wrap(d, r["title"], tf, W - 2 * M)
    for ln in lines:
        d.text((M, y), ln, font=tf, fill=t["title"])
        y += int(tf.size * 1.22)
    sub = f"{r['year']}" + (f" · {r['note']}" if r.get("note") else "")
    d.text((M, y + 8), sub, font=font(26), fill=t["sub"])
    y += 70

    # строки
    rows = r["top"][:10]
    foot_top = H - 120
    cis_out = [c for c in r["cis"] if not c["in_top10"]]
    bottom = foot_top - (60 if cis_out else 20)
    rh = min(84, (bottom - y) / max(len(rows), 1))
    vmax = max(abs(x["value"]) for x in rows) or 1
    cis_set = {c["name"] for c in r["cis"]}
    nf, vf, numf = font(30, 400), font(30, 600), font(24, 500)
    bar_x0, bar_x1 = M + 52, W - M
    for i, row in enumerate(rows):
        yy = y + i * rh
        d.text((M, yy + 3), f"{row['rank']:>2}", font=numf, fill=t["num"])
        name = row["name"]
        val = row["text"]
        vw = text_w(d, val, vf)
        f_name = nf
        while text_w(d, name, f_name) > (bar_x1 - bar_x0 - vw - 24) and f_name.size > 20:
            f_name = font(f_name.size - 2, 400)
        d.text((bar_x0, yy), name, font=f_name, fill=t["name"])
        d.text((bar_x1 - vw, yy), val, font=vf, fill=t["value"])
        bw = (bar_x1 - bar_x0) * abs(row["value"]) / vmax
        color = t["lead"] if i == 0 else (t["cis"] if name in cis_set else t["bar"])
        d.rectangle([bar_x0, yy + 44, bar_x0 + max(bw, 4), yy + 56], fill=color)

    if cis_out:
        parts = [f"{c['name']} на {c['rank']}-м" for c in cis_out]
        s = parts[0] + " месте" + "".join(", " + p for p in parts[1:]) + "."
        cf = font(26)
        while text_w(d, s, cf) > W - 2 * M and cf.size > 18:
            cf = font(cf.size - 1)
        d.text((M, bottom + 10), s, font=cf, fill=t["sub"])

    # подвал
    d.rectangle([M, foot_top, W - M, foot_top], fill=t["line"])
    d.text((M, foot_top + 26), f"Источник: {r['source_full']}, данные за {r['year']}",
           font=font(22), fill=t["foot"])
    cta = "Telegram @osnovafin"
    cf = font(24, 500)
    d.text((W - M - text_w(d, cta, cf), foot_top + 60), cta, font=cf, fill=t["cta"])
    d.text((M, foot_top + 60), "OSNOVA Finance", font=font(24, 500), fill=t["foot"])
    img.save(path, optimize=True)
