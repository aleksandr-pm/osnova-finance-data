"""Карточка разбора компании 1080x1350 · палитра R, светлая (инверсия OSNOVA Finance) · Rubik · v1.

Знак и подпись → вывод одной фразой → подзаголовок (что и в чём) →
сгруппированные столбцы по годам (выручка oxblood, прибыль или долг приглушённым) →
легенда → источник → строка Telegram.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import font, tw, spaced, ring, plane, draw_hook, M, W, H  # noqa: E402

T = {
    "bg": "#F2EFEA", "brand": "#5C1A23", "hook": "#17171A", "accent": "#5C1A23",
    "sub": "#6B6462", "a": "#5C1A23", "b": "#B5ABA2", "neg": "#8A8380",
    "val_a": "#5C1A23", "val_b": "#6B6462", "axis": "#DDD7CE", "year": "#1E1B1C",
    "foot": "#6B6462", "line": "#DDD7CE", "cta": "#5C1A23",
}


def fmt(v):
    """Число в выбранных единицах: 3,42 · 993 · 12,4"""
    a = abs(v)
    s = f"{v:.2f}" if a < 10 else f"{v:.1f}" if a < 100 else f"{v:.0f}"
    s = s.rstrip("0").rstrip(".") if "." in s else s
    return s.replace(".", ",").replace("-", "−")


def scale(vals, cur):
    m = max(abs(v) for v in vals) or 1
    if m >= 1e9:
        return 1e9, f"млрд {cur}"
    if m >= 1e6:
        return 1e6, f"млн {cur}"
    return 1e3, f"тыс. {cur}"


def render(card, path):
    """card: brand_line, hook (список сегментов [(текст, выделить)]), sub, years, a, b, a_name, b_name, cur, source, note"""
    im = Image.new("RGB", (W, H), T["bg"])
    d = ImageDraw.Draw(im)
    ring(d, M + 16, 96, 16, T["brand"], T["bg"])
    spaced(d, M + 46, 85, "OSNOVA · РАЗБОР КОМПАНИЙ", font(20, 500), T["brand"], 3)
    y = draw_hook(d, 170, card["hook"], T)

    years = card["years"]
    a = card["a"]
    b = card["b"]
    div, unit = scale(a + b, card["cur"])
    sub = f"{card['sub']}, {unit} · {years[0]}-{years[-1]}"
    sf = font(28)
    while tw(d, sub, sf) > W - 2 * M and sf.size > 20:
        sf = font(sf.size - 1)
    d.text((M, y + 12), sub, font=sf, fill=T["sub"])

    # легенда
    ly = y + 70
    lf = font(26, 500)
    x = M
    for name, col in ((card["a_name"], T["a"]), (card["b_name"], T["b"])):
        d.rectangle([x, ly + 6, x + 26, ly + 32], fill=col)
        d.text((x + 38, ly + 2), name, font=lf, fill=T["year"])
        x += 38 + tw(d, name, lf) + 48

    # область графика
    top = ly + 110
    foot = H - 150
    bottom = foot - 90
    vals = [v / div for v in a + b]
    vmax = max(max(vals), 0)
    vmin = min(min(vals), 0)
    span = (vmax - vmin) or 1
    ph = bottom - top
    zero = top + ph * vmax / span

    n = len(years)
    gw = (W - 2 * M) / n
    bw = min(92, gw * 0.34)
    gap = 10
    vf = font(26, 600)
    yf = font(28, 500)
    for i, yr in enumerate(years):
        cx = M + gw * i + gw / 2
        for j, (v, col, vc) in enumerate(((a[i] / div, T["a"], T["val_a"]), (b[i] / div, T["b"] if b[i] >= 0 else T["neg"], T["val_b"]))):
            x0 = cx - bw - gap / 2 if j == 0 else cx + gap / 2
            h = ph * abs(v) / span
            if v >= 0:
                d.rectangle([x0, zero - h, x0 + bw, zero], fill=col)
                ty = zero - h - 36
            else:
                d.rectangle([x0, zero, x0 + bw, zero + h], fill=col)
                ty = zero + h + 6
            s = fmt(v)
            f = vf
            while tw(d, s, f) > bw + 22 and f.size > 18:
                f = font(f.size - 1, 600)
            d.text((x0 + bw / 2, ty + 15), s, font=f, fill=vc, anchor="mm")
        d.text((cx, bottom + 50), str(yr), font=yf, fill=T["year"], anchor="mm")
    d.rectangle([M, zero, W - M, zero + 1], fill=T["axis"])

    d.rectangle([M, foot, W - M, foot], fill=T["line"])
    src = f"Источник: {card['source']}"
    if card.get("note"):
        src += f" · {card['note']}"
    sf = font(22)
    while tw(d, src, sf) > W - 2 * M and sf.size > 16:
        sf = font(sf.size - 1)
    d.text((M, foot + 30), src, font=sf, fill=T["foot"])
    cf = font(30, 600)
    cy = foot + 92
    d.text((M, cy), "Рынки и данные 24/7 в Telegram @osnovafin", font=cf, fill=T["cta"], anchor="lm")
    plane(d, W - M - 52, cy, 52, T["cta"], T["bg"])
    im.save(path, quality=95)
    return path
