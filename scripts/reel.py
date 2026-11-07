"""Reels для Instagram: рейтинг из банка → ролик 1080×1920 с музыкой → публикация.

python scripts/reel.py                 собрать следующий ролик и опубликовать
python scripts/reel.py --dry-run       только собрать ролик (reel.mp4) и показать подпись
python scripts/reel.py --id <id>       взять конкретный рейтинг
python scripts/reel.py --theme dark    принудительно тёмная тема

Данные: bank/rankings.json (Всемирный банк, ФАО) и bank/rankings_markets.json
(companiesmarketcap.com, Forbes Real-Time). Музыка: assets/music.
Ключи: IG_TOKEN, IG_USER_ID (секреты GitHub). Состояние: bank/state_reels.json.
"""
import csv
import datetime as dt
import functools
import glob
import html
import io
import json
import os
import subprocess
import sys
import time

import requests
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from publish import IG, check, ig_user_id, tag  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "bank")
ASSETS = os.path.join(ROOT, "assets")
STATE = os.path.join(BANK, "state_reels.json")
REPEAT_DAYS = 90

W, H, FPS = 1080, 1920, 30
LX = 72
NB = " "
LIGHT = dict(bone="#F2EFEA", graphite="#17171A", ink="#1E1B1C", smoke="#6B6462",
             line="#DDD7CE", bar="#C9C1B6", blush="#D3B9B6")
DARK = dict(bone="#5C1A23", graphite="#E2B8A4", ink="#EFE4E0", smoke="#AC8C8A",
            line="#7E3A44", bar="#7E3A44", blush="#5C1A23")
C = dict(LIGHT)
CONTENT_BOTTOM, SRC_Y, CTA_Y = 1286, 1300, 1366


def log(*a):
    print(*a, flush=True)


# ---------- шрифты и мелочи ----------
_fc = {}


def F(size, w):
    if (size, w) not in _fc:
        f = ImageFont.truetype(os.path.join(ASSETS, "Rubik.ttf"), size)
        f.set_variation_by_axes([w])
        _fc[(size, w)] = f
    return _fc[(size, w)]


def hexa(h, a=1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (int(255 * max(0, min(1, a))),)


def ease(u):
    u = max(0, min(1, u))
    return 1 - (1 - u) ** 3


def fade(t, a):
    if a >= 1:
        return t
    t = t.copy()
    t.putalpha(t.getchannel("A").point(lambda p: int(p * max(0, a))))
    return t


def num1(v):
    t = f"{v:.1f}".replace(".", ",")
    return t[:-2] if t.endswith(",0") else t


def times(r):
    """«в 2,4 раза», «в 5 раз», «в 22 раза»."""
    if r < 10:
        s = num1(r)
        if "," in s:
            return f"в{NB}{s}{NB}раза"
        n = int(s)
    else:
        n = int(round(r))
    w = "раза" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "раз"
    return f"в{NB}{n}{NB}{w}"


def fmt(v, unit):
    """Сумма для итоговой плашки в том же формате, что и тексты банка."""
    def k(x):
        return f"{x:,.1f}".replace(",", " ").replace(".", ",").replace(",0", "").replace(" ", NB)
    if unit == "usd":
        for d, s in ((1e12, "трлн"), (1e9, "млрд"), (1e6, "млн")):
            if v >= d:
                return f"${k(v / d)}{NB}{s}"
        return f"${k(v)}"
    if unit == "t":
        if v >= 1e6:
            return f"{k(v / 1e6)}{NB}млн т"
        return f"{k(v / 1e3)}{NB}тыс. т"
    if unit == "num":
        if v >= 1e6:
            return f"{k(v / 1e6)}{NB}млн чел."
        return f"{k(v / 1e3)}{NB}тыс. чел."
    return k(v)


def wrap(d, s, f, maxw):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) > maxw and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = t
    lines.append(cur)
    return lines


def fit(d, s, size, w, maxw, minsize=18):
    while size > minsize and d.textlength(s, font=F(size, w)) > maxw:
        size -= 2
    return F(size, w)


def label(d, xy, s, size, color, track=4):
    f = F(size, 500)
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=color)
        x += d.textlength(ch, font=f) + track


# ---------- иконки ----------
def ring(px, color):
    s = px * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, ro, ri = s / 2, s * .46, s * .30
    d.ellipse([c - ro, c - ro, c + ro, c + ro], fill=color)
    d.ellipse([c - ri, c - ri, c + ri, c + ri], fill=(0, 0, 0, 0))
    return im.resize((px, px), Image.LANCZOS)


def tg(px, color, bg):
    s = px * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=color)
    u = s / 100
    d.polygon([(x * u, y * u) for x, y in [(22, 49), (74, 28), (66, 71), (49, 59), (40, 67), (41, 56), (63, 37), (36, 54)]], fill=bg)
    d.polygon([(x * u, y * u) for x, y in [(36, 54), (63, 37), (41, 56), (40, 67)]], fill=color)
    d.polygon([(x * u, y * u) for x, y in [(36, 54), (41, 56), (40, 67)]], fill=bg)
    return im.resize((px, px), Image.LANCZOS)


ICON = {}


def set_theme(name):
    C.update(DARK if name == "dark" else LIGHT)
    ICON.update(ring=ring(48, C["graphite"]), tg_m=tg(60, C["bone"], C["graphite"]),
                tg_cta=tg(72, C["bone"], C["graphite"]), tg_huge=tg(220, C["bone"], C["graphite"]))
    flag.cache_clear()
    tile.cache_clear()


# ---------- флаги, логотипы, монограммы ----------
RU_COUNTRY = {"US": "США", "KR": "Южная Корея", "HK": "Гонконг", "MO": "Макао", "AE": "ОАЭ",
              "GB": "Великобритания", "CZ": "Чехия", "CD": "ДР Конго", "TW": "Тайвань"}


def country_ru(iso2):
    if iso2 in RU_COUNTRY:
        return RU_COUNTRY[iso2]
    try:
        from babel import Locale
        return Locale("ru").territories.get(iso2, iso2)
    except Exception:  # noqa: BLE001
        return iso2


@functools.lru_cache(maxsize=None)
def flag(iso2, h):
    p = os.path.join(ASSETS, "flags", f"{iso2}.png")
    w = int(h * 4 / 3)
    out = Image.new("RGBA", (w + 4, h + 4), hexa(C["line"]))
    if os.path.exists(p):
        out.alpha_composite(Image.open(p).convert("RGBA").resize((w, h), Image.LANCZOS), (2, 2))
    return out


SYMBOLS = None


def symbol(name):
    global SYMBOLS
    if SYMBOLS is None:
        SYMBOLS = {}
        for p in sorted(glob.glob(os.path.join(BANK, "raw_markets", "cmc_*.csv"))):
            try:
                with open(p, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        SYMBOLS.setdefault(row["Name"].strip(), row["Symbol"].strip())
            except Exception:  # noqa: BLE001
                pass
    return SYMBOLS.get(name)


LOGO_LOG = []


def logo_img(name):
    """Логотип компании: кэш assets/logos, иначе companiesmarketcap.com."""
    sym = symbol(name)
    if not sym:
        return None
    key = "".join(ch for ch in sym if ch.isalnum() or ch in ".-_")
    p = os.path.join(ASSETS, "logos", f"{key}.png")
    if not os.path.exists(p):
        try:
            r = requests.get(f"https://companiesmarketcap.com/img/company-logos/256/{sym}.webp", timeout=20,
                             headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                                                    "(KHTML, like Gecko) Chrome/126 Safari/537.36"})
            if r.status_code != 200 or len(r.content) < 200:
                LOGO_LOG.append(f"{name}: HTTP {r.status_code}")
                return None
            im = Image.open(io.BytesIO(r.content)).convert("RGBA")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            im.save(p)
        except Exception as e:  # noqa: BLE001
            LOGO_LOG.append(f"{name}: {e}")
            return None
    return Image.open(p).convert("RGBA")


def on_white(im, w, h, pad):
    """Логотип на белой плашке; белые логотипы перекрашиваются в графит."""
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    px = im.load()
    tot = ws = 0
    for y in range(0, im.height, 2):
        for x in range(0, im.width, 2):
            r, g, b, a = px[x, y]
            if a > 128:
                tot += 1
                ws += min(r, g, b) > 225
    if tot and ws / tot > 0.3:
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if a and min(r, g, b) > 200:
                    px[x, y] = (23, 23, 26, a)
    t = Image.new("RGBA", (w, h), "#FFFFFF")
    im.thumbnail((w - 2 * pad, h - pad), Image.LANCZOS)
    t.alpha_composite(im, ((w - im.width) // 2, (h - im.height) // 2))
    return t


def initials(name):
    parts = [p for p in name.replace("&", " ").split() if p[:1].isalpha()]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    stop = {"с", "семьёй", "family", "and", "и"}
    parts = [p for p in parts if p.lower() not in stop] or parts
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else parts[0][:2].upper()


@functools.lru_cache(maxsize=None)
def tile(kind, name, iso2, w, h):
    """Визуальный знак строки: флаг страны, логотип компании, монограмма человека."""
    if kind == "country":
        fh = h - 4
        fl = flag(iso2, fh)
        t = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        t.alpha_composite(fl, (0, (h - fl.height) // 2))
        return t
    if kind == "company":
        im = logo_img(name)
        if im is not None:
            return on_white(im, w, h, max(4, h // 6))
        t = Image.new("RGBA", (w, h), "#FFFFFF")
        d = ImageDraw.Draw(t)
        f = fit(d, name, int(h * 0.42), 600, w - h // 3, 8)
        d.text((w / 2, h / 2), name, font=f, fill="#17171A", anchor="mm")
        return t
    s = min(w, h) * 4
    t = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    d.ellipse([0, 0, s - 1, s - 1], fill=C["graphite"])
    d.text((s / 2, s / 2), initials(name), font=F(int(s * 0.38), 600), fill=C["bone"], anchor="mm")
    t = t.resize((min(w, h), min(w, h)), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(t, (0, (h - t.height) // 2))
    return out


# ---------- данные ----------
DONE_BY_HAND = [  # уже вышли роликами вручную до запуска автоматики
    "mkt_sector_semis", "mkt_sector_pharma", "mkt_sector_airlines", "mkt_sector_banks", "mkt_sector_auto",
    "mkt_world_cap", "mkt_world_rev", "mkt_world_earn", "mkt_world_emp", "bil_world", "bil_country_ru",
    "wdi_fi_res_totl_cd_desc", "wdi_sl_uem_totl_zs_asc", "wdi_ny_gdp_mktp_cd_desc", "cis_fp_cpi_totl_zg",
]
BANNED = ("недвиж", "real estate", "realestate")
BAD_DATA = {  # ошибки или дубли в источнике
    "mkt_world_div",       # доходности 20%+ у Apple и др.: в выгрузке не дивиденды
    "mkt_sector_ai",       # совпадает с технологическими компаниями
    "mkt_sector_gaming",   # Microsoft целиком на первом месте
}


def load_rankings():
    out = []
    for fn in ("rankings_markets.json", "rankings.json"):
        p = os.path.join(BANK, fn)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for r in json.load(f):
                if r.get("type", "bars") != "bars" or len(r.get("top", [])) < 5:
                    continue
                if r["id"] in BAD_DATA or any(b in (r["id"] + r["title"]).lower() for b in BANNED):
                    continue
                for x in r["top"]:
                    x["name"] = html.unescape(x["name"])
                out.append(r)
    return out


def kind_of(r):
    return {"companies": "company", "billionaires": "person"}.get(r["block"], "country")


def is_asc(r):
    v = [x["value"] for x in r["top"]]
    return r["id"].endswith("_asc") or v[0] < v[-1]


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    t = dt.datetime.now(dt.timezone.utc).isoformat()
    return {"posted": [{"id": i, "block": "manual", "at": t, "post": "manual"} for i in DONE_BY_HAND]}


def save_state(st):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


ORDER = ["companies", "billionaires", "economy", "companies", "agro", "billionaires", "cis", "companies", "money"]


def pick(rankings, st):
    """Ротация блоков: компании и миллиардеры чаще, макро и агро между ними.
    Рейтинг не повторяется 90 дней."""
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=REPEAT_DAYS)
    recent = {p["id"] for p in st["posted"] if dt.datetime.fromisoformat(p["at"]) > cutoff}
    pool = [r for r in rankings if r["id"] not in recent]
    if not pool:
        return None
    auto = [p for p in st["posted"] if p.get("block") != "manual"]
    n = len(auto)
    for k in range(len(ORDER)):
        want = ORDER[(n + k) % len(ORDER)]
        cand = [r for r in pool if r["block"] == want]
        if cand:
            break
    else:
        cand = pool
    # внутри блока: сначала мировые рейтинги и крупные страны, порядок стабильный
    pri = {"mkt_world": 0, "mkt_sector": 1, "bil_ind": 1, "bil_country": 2, "mkt_country_cap": 2, "wdi": 0, "cis": 0}

    def score(r):
        p = next((v for k, v in pri.items() if r["id"].startswith(k)), 3)
        return (p, rankings.index(r))
    return min(cand, key=score)


# ---------- тексты ----------
def story(r):
    """Главная мысль ролика: обложка, пояснение, плашка, подпись."""
    top = r["top"]
    v = [x["value"] for x in top]
    unit = r["unit"]
    asc = is_asc(r)
    additive = unit in ("usd", "t", "num") and not asc
    n1 = top[0]["name"]
    stat = ""
    if additive and len(v) >= 4 and v[0] > v[1] + v[2] + v[3]:
        stat = "Больше, чем №2, №3 и №4 вместе"
    elif additive and len(v) >= 3 and v[0] > v[1] + v[2]:
        stat = "Больше, чем №2 и №3 вместе"
    elif not asc and v[1] > 0 and v[0] / v[1] >= 1.3:
        stat = f"{times(v[0] / v[1]).capitalize()} больше, чем у №2"
    elif not asc and v[-1] > 0 and v[0] / v[-1] >= 1.3:
        stat = f"{times(v[0] / v[-1]).capitalize()} больше, чем у №{len(v)}"
    # пояснение метрики
    i = r["id"]
    if i.startswith("bil_"):
        what = f"Состояние по оценке Forbes в реальном времени, {r.get('note', '')}."
    elif "_rev" in i:
        what = "Выручка за последние 12 месяцев."
    elif "_earn" in i:
        what = "Прибыль за последние 12 месяцев."
    elif "_emp" in i:
        what = "Число сотрудников по последней отчётности."
    elif "_div" in i:
        what = "Дивиденды за год в процентах от цены акции."
    elif i.startswith("mkt_"):
        what = "Капитализация: сколько стоят все акции компании на бирже."
    else:
        what = f"Данные: {r['source_full']}, {r['year']} год." + (f" Учтены {r['note']}." if r.get("note") else "")
    # итоговая плашка
    cis = [c for c in r.get("cis", []) if not c.get("in_top10")]
    if cis and kind_of(r) == "country":
        punch = ["Страны бывшего СССР вне топа:",
                 ", ".join(f"{c['name']} {c['rank']}-е место" for c in cis[:3])]
    elif cis:
        c = cis[0]
        punch = ["Первый в списке из России или Казахстана:", f"{c['name']}, {c['rank']}-е место"]
    elif additive:
        punch = [f"Топ-{len(v)} вместе:", fmt(sum(v), unit)]
    elif v[-1] > 0 and v[0] != v[-1]:
        a, b = (v[-1], v[0]) if asc else (v[0], v[-1])
        punch = [f"№1 и №{len(v)}:", f"разница {times(a / b)}"]
    else:
        punch = [f"№1: {n1}", top[0]["text"]]
    return dict(stat=stat, what=what, punch=punch)


def sub_line(r):
    if r["block"] in ("companies", "billionaires"):
        return f"{r['source']} · {r.get('note', '')}"
    return f"{r['source']} · {r['year']} год"


def kicker(r):
    k = {"companies": "КОМПАНИИ", "billionaires": "МИЛЛИАРДЕРЫ", "economy": "ЭКОНОМИКА",
         "cis": "СТРАНЫ БЫВШЕГО СССР", "money": "ДЕНЬГИ", "agro": "СЫРЬЁ И ЕДА"}.get(r["block"], "РЕЙТИНГ")
    return f"ТОП-{len(r['top'])} · {k}"


QUESTIONS = {
    "companies": ["Какую компанию вы ожидали увидеть выше?", "Кто будет №1 через пять лет?",
                  "Кого не хватает в этом списке?"],
    "billionaires": ["Кто из списка удивил?", "Кто поднимется выше через пять лет?",
                     "Кого вы ожидали увидеть в топе?"],
}
Q_DEFAULT = ["Какая страна удивила?", "Где ваша страна в этом рейтинге?", "Что удивило в этом списке?"]
TAGS = {
    "companies": ["акции", "компании", "капитализация", "фондовыйрынок", "бизнес"],
    "billionaires": ["миллиардеры", "forbes", "богатство", "бизнес", "успех"],
    "economy": ["экономика", "мироваяэкономика", "ввп", "макроэкономика"],
    "money": ["деньги", "капитал", "мироваяэкономика"],
    "cis": ["снг", "экономикаснг", "казахстан", "узбекистан"],
    "agro": ["сельскоехозяйство", "агро", "экспорт", "продовольствие"],
}
TAG_BASE = ["инвестиции", "финансы", "статистика", "рейтинг", "топ10", "рилс"]


def caption(r, n):
    s = story(r)
    top = r["top"]
    hook = f"{r['title']}: №1 {top[0]['name']}, {top[0]['text']}."
    if s["stat"]:
        hook += f" {s['stat']}."
    rows = "\n".join(f"{x['rank']}. {x['flag']} {x['name']}: {x['text']}" for x in top)
    q = (QUESTIONS.get(r["block"]) or Q_DEFAULT)[n % 3]
    tags, seen = [], set()
    for t in TAGS.get(r["block"], []) + [top[0]["name"]] + TAG_BASE:
        h = tag(t)
        if len(h) > 2 and h not in seen:
            seen.add(h)
            tags.append(h)
    return "\n\n".join([
        hook, rows, q,
        "Каждый день рынки, сделки инсайдеров из отчётов SEC и данные в Telegram @osnovafin, ссылка в профиле.",
        f"Источник: {r['source_full']}" + (f", {r['note']}" if r["block"] in ("companies", "billionaires") else f", {r['year']} год")
        + ". Не индивидуальная инвестиционная рекомендация.",
        " ".join(tags[:12]),
    ]).replace(NB, " ")


# ---------- кадр ----------
T_COV, T_EX = int(2.0 * FPS), int(1.6 * FPS)
T_IT, T_FIN, T_END = int(3.9 * FPS), int(7.5 * FPS), int(3.5 * FPS)


def chrome(im, d, n, total, src):
    d.rectangle([0, 0, int(W * n / (total - 1)), 7], fill=C["graphite"])
    im.alpha_composite(ICON["ring"], (LX, 256))
    f = F(38, 600)
    s_ = "@osnovafin"
    bw = 18 + 60 + 14 + int(d.textlength(s_, font=f)) + 22
    x0 = W - LX - bw
    d.rectangle([x0, 242, W - LX, 318], fill=C["graphite"])
    im.alpha_composite(ICON["tg_m"], (x0 + 18, 250))
    d.text((x0 + 92, 280), s_, font=f, fill=C["bone"], anchor="lm")
    ff = F(21, 400)
    d.text((LX, SRC_Y), src, font=ff, fill=C["smoke"])
    d.text((LX, SRC_Y + 26), "Не индивидуальная инвестиционная рекомендация.", font=ff, fill=C["smoke"])
    d.rectangle([LX, CTA_Y, W - LX, CTA_Y + 124], fill=C["graphite"])
    im.alpha_composite(ICON["tg_cta"], (LX + 24, CTA_Y + 26))
    d.text((LX + 116, CTA_Y + 36), "Больше в Telegram", font=F(30, 500), fill=C["blush"], anchor="lm")
    d.text((LX + 116, CTA_Y + 84), "@osnovafin", font=F(52, 600), fill=C["bone"], anchor="lm")


def end_card(im, d, a):
    d.rectangle([0, 340, W, CONTENT_BOTTOM], fill=hexa(C["bone"], a))
    d.rectangle([LX, 420, W - LX, 1240], fill=hexa(C["graphite"], a))
    im.alpha_composite(fade(ICON["tg_huge"], a), ((W - 220) // 2, 480))
    d.text((W / 2, 790), "@osnovafin", font=F(110, 600), fill=hexa(C["bone"], a), anchor="mm")
    d.text((W / 2, 880), "Telegram · OSNOVA Finance", font=F(36, 400), fill=hexa(C["blush"], a), anchor="mm")
    for i, l in enumerate(["Больше в Telegram", "Рейтинги, сделки инсайдеров,", "новости рынков каждый день"]):
        d.text((W / 2, 980 + i * 60), l, font=F(42, 600 if i < 2 else 400),
               fill=hexa(C["bone"] if i < 2 else C["blush"], a), anchor="mm")


def make_frames(r):
    top = r["top"]
    n = len(top)
    kind = kind_of(r)
    st = story(r)
    asc = is_asc(r)
    vals = [abs(x["value"]) for x in top]
    vmax = max(vals) or 1
    total = T_COV + T_EX + n * T_IT + T_FIN + T_END
    src = f"Источник: {r['source_full']}" + (f", {r['note']}." if r["block"] in ("companies", "billionaires")
                                             else f", {r['year']} год.")
    title = r["title"]
    ttl_f = F(50, 500)

    def header(d):
        label(d, (LX, 362), kicker(r), 24, C["smoke"])
        f = ttl_f
        lines = wrap(d, title, f, W - 2 * LX)
        if len(lines) > 1:
            f = F(42, 500)
            lines = wrap(d, title, f, W - 2 * LX)[:2]
        y = 396
        for l in lines:
            d.text((LX, y), l, font=f, fill=C["ink"])
            y += int(f.size * 1.18)
        d.text((LX, y + 6), sub_line(r), font=F(28, 400), fill=C["smoke"])
        return y + 50

    def compare(i):
        if i == 0:
            return st["stat"]
        a, b = vals[0], vals[i]
        if a <= 0 or b <= 0:
            return ""
        q = (b / a) if asc else (a / b)
        if q < 1.1:
            return "Почти вровень с №1"
        return f"{times(q).capitalize()} {'больше' if asc else 'меньше'}, чем у №1"

    def frame(f):
        im = Image.new("RGBA", (W, H), C["bone"])
        d = ImageDraw.Draw(im)
        if f < T_COV:  # обложка: цифра №1 и тема, имя №1 скрыто до конца отсчёта
            a = ease(f / 6)
            label(d, (LX, 380), kicker(r), 26, hexa(C["smoke"], a))
            big = top[0]["text"]
            fs = 240
            while d.textlength(big, font=F(fs, 600)) > W - 2 * LX:
                fs -= 6
            d.text((LX - 6, 430), big, font=F(fs, 600), fill=hexa(C["graphite"], a))
            y = 430 + int(fs * 1.2)
            for l in wrap(d, title, F(64, 600), W - 2 * LX)[:3]:
                d.text((LX, y), l, font=F(64, 600), fill=hexa(C["ink"], a))
                y += 78
            d.text((LX, y + 24), "Кто №1? Смотрите до конца", font=F(40, 400), fill=hexa(C["smoke"], a))
        elif f < T_COV + T_EX:  # короткое пояснение
            a = ease((f - T_COV) / 5)
            d.rectangle([LX, 470, LX + 10, 480], fill=hexa(C["graphite"], a))
            label(d, (LX + 26, 462), "ЧТО ЭТО ЗНАЧИТ", 26, hexa(C["smoke"], a))
            y = 530
            for l in wrap(d, st["what"], F(54, 500), W - 2 * LX)[:5]:
                d.text((LX, y), l, font=F(54, 500), fill=hexa(C["ink"], a))
                y += 70
        elif f < T_COV + T_EX + n * T_IT:  # обратный отсчёт
            k = (f - T_COV - T_EX) // T_IT
            m = (f - T_COV - T_EX) % T_IT
            idx = n - 1 - k
            x = top[idx]
            a = ease(m / 8)
            y0 = header(d) + 20
            nf = F(44, 600)
            ns = f"№{NB}{idx + 1}"
            d.text((LX, y0), ns, font=nf, fill=hexa(C["smoke"], a))
            nx = LX + d.textlength(ns, font=nf) + 24
            d.text((nx, y0), x["name"], font=fit(d, x["name"], 44, 600, W - LX - nx), fill=hexa(C["ink"], a))
            ty = y0 + 70
            if kind == "company":
                t = tile(kind, x["name"], x["iso2"], W - 2 * LX, 130)
                im.alpha_composite(fade(t, a), (LX, ty))
                vy = ty + 146
            else:
                t = tile(kind, x["name"], x["iso2"], 200, 150)
                im.alpha_composite(fade(t, a), (LX, ty))
                vy = ty + 166
            if kind == "country":
                vx, vyy = LX + 230, ty + 10
            else:
                vx, vyy = (LX + 190, ty + 10) if kind == "person" else (LX, vy)
            sl = ease((m - 3) / 14)
            vf = fit(d, x["text"], 110, 600, W - LX - vx)
            d.text((vx - int(40 * (1 - sl)), vyy), x["text"], font=vf, fill=hexa(C["graphite"], a * sl))
            dy = max(vy, vyy + 130) if kind != "company" else vy + 130
            info = []
            if kind != "country":
                info.append(country_ru(x["iso2"]))
            c = compare(idx)
            if c:
                info.append(c)
            if info:
                im.alpha_composite(fade(flag(x["iso2"], 30), a), (LX, dy + 4)) if kind != "country" else None
                ix = LX + (56 if kind != "country" else 0)
                for j, l in enumerate(wrap(d, " · ".join(info), F(32, 400), W - LX - ix)[:2]):
                    d.text((ix, dy + j * 42), l, font=F(32, 400), fill=hexa(C["ink"], a))
            # мини-таблица уже показанных мест
            ly = 1286 - n * 40 - 10
            for j in range(idx, n):
                al = 1.0 if j > idx else (ease((m - 34) / 14) if m > 34 else 0)
                if al <= 0:
                    continue
                xx = top[j]
                y = ly + j * 40
                d.text((LX + 14, y + 16), str(j + 1), font=F(24, 600), fill=hexa(C["smoke"], al), anchor="mm")
                im.alpha_composite(fade(tile(kind, xx["name"], xx["iso2"], 80 if kind == "company" else 42, 32), al), (LX + 36, y))
                nm_x = LX + (130 if kind == "company" else 92)
                d.text((nm_x, y + 16), xx["name"], font=fit(d, xx["name"], 24, 500, LX + 400 - nm_x - 10, 14),
                       fill=hexa(C["ink"], al), anchor="lm")
                bw = int(300 * vals[j] / vmax * ease(al))
                d.rectangle([LX + 400, y + 6, LX + 400 + max(bw, 3), y + 28], fill=hexa(C["bar"], al))
                d.text((LX + 400 + max(bw, 3) + 12, y + 17), xx["text"], font=F(24, 600), fill=hexa(C["ink"], al), anchor="lm")
        elif f < T_COV + T_EX + n * T_IT + T_FIN:  # итоговая таблица
            m = f - T_COV - T_EX - n * T_IT
            y0 = header(d) + 14
            step = min(62, (1150 - y0) // n)
            for i, xx in enumerate(top):
                al = ease((m - i * 2) / 10)
                y = y0 + i * step
                d.text((LX, y + 22), str(i + 1), font=F(28, 600), fill=hexa(C["smoke"], al), anchor="lm")
                tw = 110 if kind == "company" else 58
                im.alpha_composite(fade(tile(kind, xx["name"], xx["iso2"], tw, 44), al), (LX + 44, y))
                tx = LX + 44 + tw + 16
                d.text((tx, y + 2), xx["name"], font=fit(d, xx["name"], 24, 500, W - LX - tx, 14), fill=hexa(C["ink"], al), anchor="lt")
                bw = int(480 * vals[i] / vmax * ease((m - i * 2) / 18))
                d.rectangle([tx, y + 34, tx + max(bw, 3), y + 52], fill=hexa(C["graphite"] if i == 0 else C["bar"], al))
                d.text((tx + max(bw, 3) + 14, y + 43), xx["text"], font=F(24, 600), fill=hexa(C["ink"], al), anchor="lm")
            b = ease((m - 45) / 10)
            d.rectangle([LX, 1166, W - LX, 1282], fill=hexa(C["graphite"], b))
            for j, l in enumerate(st["punch"]):
                fl = F(28, 400) if j == 0 else fit(d, l, 32, 600, W - 2 * LX - 52)
                d.text((LX + 26, 1184 + j * 44), l, font=fl, fill=hexa(C["bone"], b))
        else:
            header(d)
            end_card(im, d, ease((f - (total - T_END)) / 8))
        chrome(im, d, f, total, src)
        return im.convert("RGB")
    return total, frame


# ---------- видео ----------
def tracks():
    return sorted(glob.glob(os.path.join(ASSETS, "music", "*.mp3")))


def render(r, out, n, theme=None):
    set_theme(theme or ("dark" if n % 5 in (1, 3) else "light"))  # bone и oxblood примерно 3:2
    total, frame = make_frames(r)
    dur = total / FPS
    music = tracks()[n % len(tracks())]
    log(f"Рендер {r['id']}: {dur:.1f} с, тема {'dark' if C['bone'] == DARK['bone'] else 'light'}, музыка {os.path.basename(music)}")
    p = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", music,
        "-filter_complex", f"[1:a]atrim=0:{dur:.2f},asetpts=PTS-STARTPTS,afade=t=in:d=0.4,"
                           f"afade=t=out:st={dur - 2.5:.2f}:d=2.5,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]",
        "-map", "0:v", "-map", "[a]", "-t", f"{dur:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for k in range(total):
        p.stdin.write(frame(k).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg: ошибка кодирования")
    if LOGO_LOG:
        log("Логотипы не загрузились: " + "; ".join(LOGO_LOG[:10]))
    return os.path.basename(music)


# ---------- публикация ----------
def publish_reel(token, path, cap):
    uid = ig_user_id(token)
    c = check(requests.post(f"{IG}/{uid}/media", data={
        "media_type": "REELS", "upload_type": "resumable", "caption": cap,
        "share_to_feed": "true", "thumb_offset": "1000", "access_token": token,
    }, timeout=60), "Instagram контейнер Reels")
    cid = c["id"]
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        up = requests.post(f"https://rupload.facebook.com/ig-api-upload/{IG.rsplit('/', 1)[1]}/{cid}", data=f, headers={
            "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size),
            "Content-Type": "application/octet-stream"}, timeout=600)
    check(up, "Instagram загрузка видео")
    for _ in range(60):  # до 10 минут на обработку
        time.sleep(10)
        s = check(requests.get(f"{IG}/{cid}", params={
            "fields": "status_code,status", "access_token": token}, timeout=30), "Instagram статус")
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram: обработка видео не прошла {s}")
    else:
        raise RuntimeError("Instagram: видео не обработалось за 10 минут")
    p = check(requests.post(f"{IG}/{uid}/media_publish", data={
        "creation_id": cid, "access_token": token}, timeout=60), "Instagram публикация Reels")
    return p["id"]


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    want = args[args.index("--id") + 1] if "--id" in args else ""
    theme = args[args.index("--theme") + 1] if "--theme" in args else None
    out = args[args.index("--out") + 1] if "--out" in args else os.path.join(ROOT, "reel.mp4")
    rankings = load_rankings()
    st = load_state()
    r = next((x for x in rankings if x["id"] == want), None) if want else pick(rankings, st)
    if not r:
        log("Нет рейтинга для ролика: " + (f"{want} не найден" if want else "все публиковались за 90 дней"))
        return 1
    n = len([p for p in st["posted"] if p.get("block") != "manual"])
    music = render(r, out, n, theme)
    cap = caption(r, n)
    log(f"reels: {r['id']} ({r['block']})\n---\n{cap}\n---")
    token = os.environ.get("IG_TOKEN", "")
    if dry or not token:
        log("Публикации нет: " + ("dry-run" if dry else "токен не задан"))
        save_state(st) if not os.path.exists(STATE) else None
        return 0
    pid = publish_reel(token, out, cap)
    st["posted"].append({"id": r["id"], "block": r["block"], "at": dt.datetime.now(dt.timezone.utc).isoformat(),
                         "post": pid, "music": music})
    save_state(st)
    log(f"Опубликовано: {pid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
