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
    C["seg"] = (["#F2EFEA", "#E2B8A4", "#C08A80", "#A2646C", "#D3B9B6"] if name == "dark"
                else ["#17171A", "#5C1A23", "#A9786A", "#6B6462", "#C9C1B6"])
    C["rest"] = "#7E3A44" if name == "dark" else "#DDD7CE"
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
                t = r.get("type", "bars")
                if t not in ("bars", "line", "donut"):
                    continue
                if t == "line" and len(r.get("series", [])) < 3:
                    continue
                if t != "line" and len(r.get("top", [])) < 5:
                    continue
                if r["id"] in BAD_DATA or any(b in (r["id"] + r["title"]).lower() for b in BANNED):
                    continue
                for x in r.get("top", []) + r.get("top10", []) + r.get("series", []) + r.get("series_all", []):
                    x["name"] = html.unescape(x["name"])
                r["fmt"] = t
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
FORMATS = ["bars", "line", "bars", "compare", "bars", "race", "bars", "donut"]  # чередование видов роликов


def compare_k(r):
    """Сколько следующих мест №1 перекрывает в одиночку (для ролика-сравнения)."""
    if r.get("type", "bars") != "bars" or r["unit"] not in ("usd", "t", "num") or is_asc(r):
        return 0
    v = [x["value"] for x in r["top"]]
    k, acc = 0, 0.0
    for x in v[1:7]:
        if acc + x >= v[0]:
            break
        acc += x
        k += 1
    return k


def variants(rankings):
    out = list(rankings)
    for r in rankings:
        if compare_k(r) >= 2:
            out.append(dict(r, id="cmp_" + r["id"], fmt="compare"))
        if r["fmt"] == "line" and all(len(x.get("points", [])) >= 5 for x in r.get("series_all", [])) and len(r.get("series_all", [])) >= 6:
            out.append(dict(r, id="race_" + r["id"], fmt="race"))
    return out


def topic(r):
    """Тема для разнообразия: у сырья общий товар (пшеница в рейтинге, долях и линиях одна тема)."""
    b = r["id"].removeprefix("cmp_").removeprefix("race_").removeprefix("line_")
    if r["block"] == "agro":
        tail = b.rsplit("_", 1)[-1]
        if tail.isdigit():
            return "agro:" + tail
    return b


def pick(rankings, st):
    """Вид ролика по кругу (рейтинг, линии, рейтинг, сравнение, рейтинг, гонка, рейтинг, доли).
    Блок не как у двух прошлых роликов, тема не повторяется 14 дней, рейтинг 90 дней."""
    now = dt.datetime.now(dt.timezone.utc)
    allv = variants(rankings)
    order = {r["id"]: i for i, r in enumerate(allv)}
    by_id = {r["id"]: r for r in allv}
    recent, near = set(), set()
    for p in st["posted"]:
        at = dt.datetime.fromisoformat(p["at"])
        if at > now - dt.timedelta(days=REPEAT_DAYS):
            recent.add(p["id"])
        if at > now - dt.timedelta(days=14):
            near.add(topic(by_id[p["id"]]) if p["id"] in by_id else p["id"])
    pool = [r for r in allv if r["id"] not in recent and topic(r) not in near]
    if not pool:
        return None
    auto = [p for p in st["posted"] if p.get("block") != "manual"]
    last_blocks = {p["block"] for p in auto[-2:]}
    n = len(auto)
    fp = []
    for j in range(len(FORMATS)):
        fp = [r for r in pool if r["fmt"] == FORMATS[(n + j) % len(FORMATS)]]
        fresh = [r for r in fp if r["block"] not in last_blocks]
        if fresh:
            fp = fresh
            break
    cand = fp
    for k in range(len(ORDER)):
        c = [r for r in fp if r["block"] == ORDER[(n + k) % len(ORDER)]]
        if c:
            cand = c
            break
    pri = {"mkt_world": 0, "mkt_sector": 1, "bil_ind": 1, "bil_country": 2, "mkt_country_cap": 2, "wdi": 0, "cis": 0}

    def score(r):
        b = r["id"].removeprefix("cmp_").removeprefix("race_").removeprefix("line_")
        return (next((v for k, v in pri.items() if b.startswith(k)), 3), order[r["id"]])
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
    i = r["id"].removeprefix("cmp_")
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


METRIC = (("bil_", "Состояние"), ("_rev", "Выручка за 12 мес."), ("_earn", "Прибыль за 12 мес."),
          ("_emp", "Сотрудники"), ("mkt_", "Капитализация"))


def sub_line(r):
    if r["block"] in ("companies", "billionaires"):
        i = r["id"].removeprefix("cmp_")
        m = next((v for k, v in METRIC if k in i), "")
        return f"{m} · {r['source']} · {r.get('note', '')}".lstrip(" ·")
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


def caption_bars(r, n):
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
        hook, CTA_TOP, rows, q, CTA_TEXT,
        f"Источник: {r['source_full']}" + (f", {r['note']}" if r["block"] in ("companies", "billionaires") else f", {r['year']} год")
        + ". Не индивидуальная инвестиционная рекомендация.",
        " ".join(tags[:12]),
    ]).replace(NB, " ")


# ---------- кадр ----------
# Без обложки: данные с первого кадра. Плашка Telegram вверху, где её не закрывает
# интерфейс Instagram; контент до y=1490; ниже только источник (зона подписи Instagram).
T_COV, T_EX = 0, 0
T_IT, T_FIN, T_END = int(3.0 * FPS), int(6.5 * FPS), int(3.0 * FPS)
TOP_CTA = (150, 290)
HEAD_Y = 322
BOTTOM = 1490
SRC_Y2 = 1508
ROWH = 1490


def chrome(im, d, n, total, src):
    d.rectangle([0, 0, int(W * n / (total - 1)), 8], fill=C["graphite"])
    y0, y1 = TOP_CTA
    d.rectangle([LX, y0, W - LX, y1], fill=C["graphite"])
    im.alpha_composite(ICON["tg_cta"], (LX + 26, (y0 + y1) // 2 - 36))
    d.text((LX + 122, y0 + 42), "Подписывайтесь в Telegram", font=F(32, 500), fill=C["blush"], anchor="lm")
    d.text((LX + 122, y0 + 96), "@osnovafin", font=F(62, 600), fill=C["bone"], anchor="lm")
    ff = F(22, 400)
    d.text((LX, SRC_Y2), src, font=ff, fill=C["smoke"])
    d.text((LX, SRC_Y2 + 28), "Не индивидуальная инвестиционная рекомендация.", font=ff, fill=C["smoke"])


def end_card(im, d, a):
    d.rectangle([0, TOP_CTA[1] + 10, W, BOTTOM], fill=hexa(C["bone"], a))
    d.rectangle([LX, TOP_CTA[1] + 40, W - LX, BOTTOM], fill=hexa(C["graphite"], a))
    im.alpha_composite(fade(ICON["tg_huge"], a), ((W - 220) // 2, 470))
    d.text((W / 2, 820), "@osnovafin", font=F(130, 600), fill=hexa(C["bone"], a), anchor="mm")
    d.text((W / 2, 930), "Telegram · OSNOVA Finance", font=F(40, 400), fill=hexa(C["blush"], a), anchor="mm")
    for i, l in enumerate(["Подписывайтесь:", "рейтинги, сделки инсайдеров,", "новости рынков каждый день"]):
        d.text((W / 2, 1080 + i * 72), l, font=F(50, 600 if i < 2 else 400),
               fill=hexa(C["bone"] if i < 2 else C["blush"], a), anchor="mm")


def draw_header(d, r, kick=None, sub=None, title=None):
    """Заголовок экрана; возвращает y, с которого начинается контент."""
    label(d, (LX, HEAD_Y), kick or kicker(r), 26, C["smoke"])
    title = title or r["title"]
    f = F(60, 600)
    lines = wrap(d, title, f, W - 2 * LX)
    if len(lines) > 1:
        f = F(52, 600)
        lines = wrap(d, title, f, W - 2 * LX)[:2]
    y = HEAD_Y + 36
    for l in lines:
        d.text((LX, y), l, font=f, fill=C["ink"])
        y += int(f.size * 1.14)
    sf = F(32, 400)
    for l in wrap(d, sub or sub_line(r), sf, W - 2 * LX)[:2]:
        d.text((LX, y + 4), l, font=sf, fill=C["smoke"])
        y += 40
    return y + 30


def punch_box(d, a, lines, y=1350):
    d.rectangle([LX, y, W - LX, BOTTOM], fill=hexa(C["graphite"], a))
    h = BOTTOM - y
    for j, l in enumerate(lines[:2]):
        fl = fit(d, l, 34, 400, W - 2 * LX - 56) if j == 0 else fit(d, l, 42, 600, W - 2 * LX - 56)
        d.text((LX + 28, y + h * (0.3 if j == 0 else 0.68)), l, font=fl, fill=hexa(C["bone"], a), anchor="lm")


def short(v, unit):
    """Подписи осей и бегущие значения."""
    if unit == "usd_pc":
        return "$" + f"{v:,.0f}".replace(",", NB)
    if unit == "pct":
        return num1(v) + "%"
    return fmt(v, unit)


def src_line(r):
    if r["block"] in ("companies", "billionaires"):
        return f"Источник: {r['source_full']}, {r['note']}."
    if r["fmt"] in ("line", "race"):
        return f"Источник: {r['source_full']}, {r['start']}-{r['year']}."
    return f"Источник: {r['source_full']}, {r['year']} год."


def end_phase(im, d, r, f, total, kick=None):
    draw_header(d, r, kick=kick)
    end_card(im, d, ease((f - (total - T_END)) / 6))


def table(im, d, rows, kind, y0, y1, a_fn, hl0=True, right=None):
    """Итоговая таблица на всю высоту: [(name, iso2, value, text)]."""
    n = len(rows)
    step = (y1 - y0) // n
    th = min(64, step - 20)
    vmax = max(v for _, _, v, _ in rows) or 1
    for i, (nm, iso, v, txt) in enumerate(rows):
        al = a_fn(i)
        y = y0 + i * step
        d.text((LX, y + step / 2 - 4), str(i + 1), font=F(36, 600), fill=hexa(C["smoke"], al), anchor="lm")
        tw = int(th * 2.4) if kind == "company" else int(th * 1.33)
        t = tile(kind, nm, iso, tw, th) if kind != "country" else flag(iso, th - 4)
        im.alpha_composite(fade(t, al), (LX + 56, int(y + step / 2 - th / 2 - 4)))
        tx = LX + 56 + tw + 22
        d.text((tx, y + 2), nm, font=fit(d, nm, 32, 500, W - LX - tx - (200 if right else 0), 16),
               fill=hexa(C["ink"], al), anchor="lt")
        if right:
            d.text((W - LX, y + 2), right[i], font=F(30, 600 if i == 0 else 400), fill=hexa(C["smoke"], al), anchor="rt")
        bw = int((W - LX - tx - 190) * abs(v) / vmax * ease(al))
        by = y + 42
        d.rectangle([tx, by, tx + max(bw, 3), y + step - 14], fill=hexa(C["graphite"] if (i == 0 and hl0) else C["bar"], al))
        d.text((tx + max(bw, 3) + 14, (by + y + step - 14) / 2), txt, font=F(32, 600), fill=hexa(C["ink"], al), anchor="lm")


# ---------- рейтинг: обратный отсчёт ----------
def make_frames(r):
    top = r["top"]
    n = len(top)
    kind = kind_of(r)
    st = story(r)
    asc = is_asc(r)
    vals = [abs(x["value"]) for x in top]
    total = n * T_IT + T_FIN + T_END

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
        if f < n * T_IT:  # обратный отсчёт: одно место на экране, крупно
            k, m = f // T_IT, f % T_IT
            idx = n - 1 - k
            x = top[idx]
            a = ease(m / 6)
            y0 = draw_header(d, r)
            # точки прогресса отсчёта
            for j in range(n):
                cx = LX + j * 52
                on = j >= idx
                d.rectangle([cx, y0, cx + 40, y0 + 10], fill=C["graphite"] if j == idx else (C["bar"] if on else C["line"]))
            y = y0 + 60
            nf = F(110, 600)
            ns = f"№{NB}{idx + 1}"
            d.text((LX, y), ns, font=nf, fill=hexa(C["smoke"], a))
            y += 140
            d.text((LX, y), x["name"], font=fit(d, x["name"], 76, 600, W - 2 * LX), fill=hexa(C["ink"], a))
            y += 110
            if kind == "company":
                t = tile(kind, x["name"], x["iso2"], W - 2 * LX, 230)
            elif kind == "country":
                t = flag(x["iso2"], 300)
            else:
                t = tile(kind, x["name"], x["iso2"], 300, 300)
            im.alpha_composite(fade(t, a), (LX, y))
            y += t.height + 30
            sl = ease((m - 3) / 12)
            d.text((LX - int(40 * (1 - sl)), y), x["text"], font=fit(d, x["text"], 170, 600, W - 2 * LX),
                   fill=hexa(C["graphite"], a * sl))
            y += 210
            info = []
            if kind != "country":
                info.append(country_ru(x["iso2"]))
            c = compare(idx)
            if c:
                info.append(c)
            for j, l in enumerate(wrap(d, " · ".join(info), F(44, 400), W - 2 * LX)[:2]):
                if y + j * 56 < BOTTOM - 40:
                    d.text((LX, y + j * 56), l, font=F(44, 400), fill=hexa(C["ink"], a))
        elif f < n * T_IT + T_FIN:  # итоговая таблица
            m = f - n * T_IT
            y0 = draw_header(d, r)
            table(im, d, [(x["name"], x["iso2"], x["value"], x["text"]) for x in top], kind, y0, 1330,
                  lambda i: ease((m - i * 2) / 8))
            punch_box(d, ease((m - 36) / 8), st["punch"])
        else:
            end_phase(im, d, r, f, total)
        chrome(im, d, f, total, src_line(r))
        return im.convert("RGB")
    return total, frame


# ---------- линии: как менялись лидеры ----------
def make_frames_line(r):
    ser = r["series"][:5]
    allr = r.get("series_all", ser)
    unit = r["unit"]
    hl = next((x for x in ser if x.get("hl")), ser[0])
    y0r, y1r = r["start"], r["year"]
    vmax = max(v for x in ser for _, v in x["points"]) * 1.08
    T_D, T_TB = int(20 * FPS), int(7.5 * FPS)
    total = T_D + T_TB + T_END
    order = sorted(range(len(ser)), key=lambda i: -ser[i]["value"])
    col = {i: (C["graphite"] if ser[i] is hl else C["seg"][1 + (k % 4)]) for k, i in enumerate(order)}
    sub = r["hook_text"]

    def upto(pts, t, X, Y):
        out = [(X(a), Y(b)) for a, b in pts if a <= t]
        nxt = next(((a, b) for a, b in pts if a > t), None)
        if out and nxt:
            a0, b0 = next((a, b) for a, b in reversed(pts) if a <= t)
            v = b0 + (nxt[1] - b0) * (t - a0) / (nxt[0] - a0)
            out.append((X(t), Y(v)))
            return out, v
        return out, (pts[-1][1] if out else None)

    def frame(f):
        im = Image.new("RGBA", (W, H), C["bone"])
        d = ImageDraw.Draw(im)
        if f < T_D:
            hy0 = draw_header(d, r, sub=sub)
            for k, i in enumerate(order):  # легенда в 2 колонки
                lx = LX + (k % 2) * ((W - 2 * LX) // 2)
                ly = hy0 + (k // 2) * 50
                d.rectangle([lx, ly + 18, lx + 34, ly + 28], fill=col[i])
                im.alpha_composite(flag(ser[i]["iso2"], 30), (lx + 46, ly + 4))
                d.text((lx + 98, ly + 23), ser[i]["name"], font=fit(d, ser[i]["name"], 32, 500, (W - 2 * LX) // 2 - 110, 14),
                       fill=C["ink"], anchor="lm")
            cx0, cx1 = LX, W - LX - 210
            cy0, cy1 = hy0 + ((len(ser) + 1) // 2) * 50 + 50, BOTTOM - 50

            def X(yr):
                return cx0 + (cx1 - cx0) * (yr - y0r) / max(1, y1r - y0r)

            def Y(v):
                return cy1 - (cy1 - cy0) * max(0, v) / vmax
            p = ease(min(1, f / (T_D - 2 * FPS)) ** 0.9) if f < T_D - 2 * FPS else 1
            t = y0r + (y1r - y0r) * p
            for k in range(5):
                v = vmax / 1.08 * k / 4
                y = Y(v)
                d.line([cx0, y, W - LX, y], fill=C["line"], width=2)
                if k:
                    d.text((cx0, y - 6), short(v, unit), font=F(26, 400), fill=C["smoke"], anchor="lb")
            for yr in (y0r, (y0r + y1r) // 2, y1r):
                d.text((X(yr), cy1 + 12), str(yr), font=F(30, 500), fill=C["smoke"], anchor="mt")
            d.text((cx0 + 4, cy0 - 10), str(int(t)), font=F(120, 600), fill=hexa(C["smoke"], 0.4), anchor="lt")
            heads = []
            for i in sorted(range(len(ser)), key=lambda i: ser[i] is hl):
                pts, v = upto(ser[i]["points"], t, X, Y)
                if len(pts) >= 2:
                    d.line(pts, fill=col[i], width=12 if ser[i] is hl else 7, joint="curve")
                if pts:
                    hx, hy = pts[-1]
                    d.ellipse([hx - 12, hy - 12, hx + 12, hy + 12], fill=col[i])
                    heads.append([hy, i, v, hx])
            heads.sort()
            for j in range(1, len(heads)):
                heads[j][0] = max(heads[j][0], heads[j - 1][0] + 48)
            for ly, i, v, hx in heads:
                lx = hx + 20
                im.alpha_composite(flag(ser[i]["iso2"], 30), (int(lx), int(ly - 17)))
                d.text((lx + 50, ly), short(v, unit), font=F(32, 600), fill=C["ink"], anchor="lm")
        elif f < T_D + T_TB:
            m = f - T_D
            yy = draw_header(d, r, sub=f"{y1r} год и рост с {y0r}")
            rows = [(x["name"], x["iso2"], x["value"], x["text"]) for x in allr]
            right = [x.get("growth") or (f"−{(1 - x['ratio']) * 100:.0f}%" if x.get("ratio", 1) < 1 else "") for x in allr]
            table(im, d, rows, "country", yy, 1330, lambda i: ease((m - i * 2) / 8), right=right)
            punch_box(d, ease((m - 36) / 8), ["Главное:", r["hook_text"]])
        else:
            end_phase(im, d, r, f, total)
        chrome(im, d, f, total, src_line(r))
        return im.convert("RGB")
    return total, frame


# ---------- доли: круговая диаграмма ----------
def make_frames_donut(r):
    segs = r["top"][:5]
    t10 = r.get("top10", r["top"])
    shares = [x["share"] for x in segs] + [r["rest"]]
    T_S, T_TB = int(2.8 * FPS), int(7 * FPS)
    total = len(segs) * T_S + int(2 * FPS) + T_TB + T_END
    R, RI = 360, 205
    SS = 2

    def donut(prog):
        S = (2 * R + 8) * SS
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        dd = ImageDraw.Draw(img)
        a0 = -90.0
        box = [4 * SS, 4 * SS, S - 4 * SS, S - 4 * SS]
        for i, sh in enumerate(shares):
            u = max(0, min(1, prog - i))
            if u <= 0:
                break
            dd.pieslice(box, a0, a0 + 360 * sh / 100 * ease(u),
                        fill=C["rest"] if i == len(segs) else C["seg"][i % 5])
            a0 += 360 * sh / 100
        c = S / 2
        dd.ellipse([c - RI * SS, c - RI * SS, c + RI * SS, c + RI * SS], fill=C["bone"])
        return img.resize((S // SS, S // SS), Image.LANCZOS)

    def frame(f):
        im = Image.new("RGBA", (W, H), C["bone"])
        d = ImageDraw.Draw(im)
        if f < total - T_TB - T_END:
            hy = draw_header(d, r, sub=r["hook_text"])
            CX, CY = W // 2, hy + R
            k = min(len(segs), f // T_S)
            u = (f - k * T_S) / (0.6 * T_S)
            prog = k + min(1, u) if k < len(segs) else len(segs) + min(1, (f - len(segs) * T_S) / FPS)
            dn = donut(prog)
            im.alpha_composite(dn, (CX - dn.width // 2, CY - dn.height // 2))
            if k < len(segs):
                x = segs[k]
                a = ease(u)
                im.alpha_composite(fade(flag(x["iso2"], 80), a), (CX - 55, CY - 150))
                d.text((CX, CY + 10), x["text"], font=F(110, 600), fill=hexa(C["graphite"], a), anchor="mm")
                d.text((CX, CY + 100), x["name"], font=fit(d, x["name"], 40, 500, 2 * RI - 40), fill=hexa(C["ink"], a), anchor="mm")
            else:
                d.text((CX, CY - 30), f"{num1(r['rest'])}%", font=F(110, 600), fill=C["graphite"], anchor="mm")
                d.text((CX, CY + 54), "все остальные", font=F(40, 500), fill=C["ink"], anchor="mm")
                d.text((CX, CY + 104), f"{r['countries'] - len(segs)} стран", font=F(36, 400), fill=C["smoke"], anchor="mm")
            ly0 = CY + R + 24
            for i in range(min(k, len(segs))):
                x = segs[i]
                cx = LX + (i % 2) * ((W - 2 * LX) // 2 + 10)
                y = ly0 + (i // 2) * 54
                d.rectangle([cx, y + 10, cx + 28, y + 38], fill=C["seg"][i % 5])
                im.alpha_composite(flag(x["iso2"], 30), (cx + 40, y + 4))
                d.text((cx + 92, y + 24), x["name"], font=fit(d, x["name"], 32, 500, 220, 14), fill=C["ink"], anchor="lm")
                d.text((cx + (W - 2 * LX) // 2 - 20, y + 24), x["text"], font=F(32, 600), fill=C["ink"], anchor="rm")
        elif f < total - T_END:
            m = f - (total - T_TB - T_END)
            yy = draw_header(d, r, sub=f"Топ-{len(t10)} экспортёров · {r['year']} год")
            table(im, d, [(x["name"], x["iso2"], x["share"], x["text"]) for x in t10], "country", yy, 1330,
                  lambda i: ease((m - i * 2) / 8))
            punch_box(d, ease((m - 36) / 8), [f"Топ-5 вместе: {num1(r['top_sum'])}%",
                                              f"Остальные {r['countries'] - len(segs)} стран: {num1(r['rest'])}%"])
        else:
            end_phase(im, d, r, f, total)
        chrome(im, d, f, total, src_line(r))
        return im.convert("RGB")
    return total, frame


# ---------- сравнение: №1 против следующих вместе ----------
def make_frames_compare(r):
    top = r["top"]
    k = compare_k(r)
    others = top[1:1 + k]
    v0 = top[0]["value"]
    acc = sum(x["value"] for x in others)
    unit = r["unit"]
    kind = kind_of(r)
    rng = f"№2–№{k + 1}"
    STEP = int(2.0 * FPS)
    T_B = int(1.2 * FPS) + k * STEP
    T_R = int(6 * FPS)
    total = T_B + T_R + T_END
    BW = W - 2 * LX
    kick = "СРАВНЕНИЕ · " + kicker(r).split(" · ")[1]
    sub = f"№1 против {k} следующих мест вместе"

    def frame(f):
        im = Image.new("RGBA", (W, H), C["bone"])
        d = ImageDraw.Draw(im)
        if f < total - T_END:
            y = draw_header(d, r, kick=kick, sub=sub) + 10
            a = ease(f / 8)
            tw = 170 if kind == "company" else 90
            im.alpha_composite(fade(tile(kind, top[0]["name"], top[0]["iso2"], tw, 68), a), (LX, y))
            d.text((LX + tw + 22, y + 34), f"№1 {top[0]['name']}", font=fit(d, f"№1 {top[0]['name']}", 48, 600, 500),
                   fill=hexa(C["ink"], a), anchor="lm")
            d.text((W - LX, y + 34), top[0]["text"], font=F(50, 600), fill=hexa(C["ink"], a), anchor="rm")
            bw = int(BW * ease(f / 24))
            d.rectangle([LX, y + 90, LX + max(bw, 3), y + 250], fill=C["graphite"])
            y2 = y + 300
            t0 = int(1.2 * FPS)
            shown = min(k, (f - t0) // STEP + 1) if f >= t0 else 0
            part = (f - t0 - (shown - 1) * STEP) / 12 if shown else 0
            cur = sum(x["value"] for x in others[:max(0, shown - 1)]) + (others[shown - 1]["value"] * ease(part) if shown else 0)
            d.text((LX, y2 + 34), f"{rng} вместе", font=F(48, 600), fill=C["ink"], anchor="lm")
            d.text((W - LX, y2 + 34), short(cur, unit) if shown else "", font=F(50, 600), fill=C["ink"], anchor="rm")
            x0 = LX
            for i in range(shown):
                w_ = BW * others[i]["value"] / v0 * (ease(part) if i == shown - 1 else 1)
                d.rectangle([int(x0), y2 + 90, max(int(x0), int(x0 + w_) - 4), y2 + 250], fill=C["seg"][1 + i % 4])
                x0 += w_
            d.rectangle([LX, y2 + 90, W - LX, y2 + 250], outline=C["line"], width=3)
            ly = y2 + 300
            if f < T_B:
                row = min(84, (BOTTOM - ly) // max(1, k))
                for i in range(shown):
                    x = others[i]
                    yy = ly + i * row
                    d.rectangle([LX, yy + 14, LX + 34, yy + 48], fill=C["seg"][1 + i % 4])
                    tw2 = 120 if kind == "company" else 64
                    im.alpha_composite(tile(kind, x["name"], x["iso2"], tw2, 48), (LX + 50, yy + 7))
                    nx = LX + 50 + tw2 + 18
                    d.text((nx, yy + 31), f"№{i + 2} {x['name']}", font=fit(d, f"№{i + 2} {x['name']}", 40, 500, W - LX - nx - 230),
                           fill=C["ink"], anchor="lm")
                    d.text((W - LX, yy + 31), x["text"], font=F(40, 600), fill=C["ink"], anchor="rm")
            else:
                b = ease((f - T_B) / 8)
                d.text((LX, ly), f"{top[0]['name']} больше,", font=fit(d, f"{top[0]['name']} больше,", 84, 600, BW),
                       fill=hexa(C["graphite"], b))
                d.text((LX, ly + 100), f"чем {rng} вместе", font=F(84, 600), fill=hexa(C["graphite"], b))
                d.text((LX, ly + 230), f"Разница: {short(v0 - acc, unit)}", font=F(56, 500), fill=hexa(C["ink"], b))
        else:
            end_phase(im, d, r, f, total, kick=kick)
        chrome(im, d, f, total, src_line(r))
        return im.convert("RGB")
    return total, frame


# ---------- гонка: как менялись места по годам ----------
def make_frames_race(r):
    ents = r["series_all"][:10]
    unit = r["unit"]
    y0r, y1r = r["start"], r["year"]
    nyrs = y1r - y0r
    PER = min(1.15, 25.0 / max(1, nyrs))
    T_RUN, T_HOLD, T_RES = int(nyrs * PER * FPS), int(1.2 * FPS), int(5 * FPS)
    total = T_RUN + T_HOLD + T_RES + T_END
    hl = next((x for x in ents if x.get("hl")), None)
    kick = f"ГОНКА · {y0r}-{y1r}"
    sub = f"{r['source']} · нынешняя десятка · кто выйдет вперёд?"

    def val(e, t):
        pts = e["points"]
        if t <= pts[0][0]:
            return pts[0][1] if t >= pts[0][0] - 0.01 else 0.0
        for (a, b), (c, d_) in zip(pts, pts[1:]):
            if a <= t <= c:
                return b + (d_ - b) * (t - a) / (c - a)
        return pts[-1][1]

    def ranks(yr):
        order = sorted(range(len(ents)), key=lambda i: -val(ents[i], yr))
        return {i: k for k, i in enumerate(order)}

    RK = {yr: ranks(yr) for yr in range(y0r, y1r + 1)}
    leader0 = ents[min(RK[y0r], key=RK[y0r].get)]
    leader1 = ents[min(RK[y1r], key=RK[y1r].get)]

    def board(im, d, t, top_y, bottom):
        ROW = (bottom - top_y) // len(ents)
        bh = ROW - 18
        NX, BX0, BX1 = LX, LX + 300, W - LX - 190
        yr = int(min(t, y1r - 1)) if t < y1r else y1r
        u = ease((t - yr) / 0.6) if t < y1r else 0
        ra, rb = RK[yr], RK[min(yr + 1, y1r)]
        vals = [val(e, t) for e in ents]
        vmax = max(vals) * 1.03 or 1
        for i, e in enumerate(ents):
            pos = ra[i] + (rb[i] - ra[i]) * u
            y = top_y + pos * ROW
            im.alpha_composite(flag(e["iso2"], 40), (NX, int(y + bh / 2 - 21)))
            d.text((NX + 68, y + bh / 2), e["name"], font=fit(d, e["name"], 34, 500, BX0 - NX - 78, 14), fill=C["ink"], anchor="lm")
            bw = int((BX1 - BX0) * vals[i] / vmax)
            colr = C["graphite"] if (e is hl or (hl is None and ra[i] == 0)) else C["bar"]
            d.rectangle([BX0, int(y), BX0 + max(bw, 3), int(y + bh)], fill=colr)
            d.text((BX0 + max(bw, 3) + 12, y + bh / 2), short(vals[i], unit), font=F(32, 600), fill=C["ink"], anchor="lm")

    def frame(f):
        im = Image.new("RGBA", (W, H), C["bone"])
        d = ImageDraw.Draw(im)
        if f < T_RUN + T_HOLD:
            ty = draw_header(d, r, kick=kick, sub=sub)
            t = y0r + min(1, f / T_RUN) * nyrs
            board(im, d, t, ty, 1370)
            # шкала времени под гонкой
            d.text((LX, 1478), str(int(t)), font=F(110, 600), fill=C["graphite"], anchor="ls")
            x0, x1, yy = LX + 300, W - LX, 1405
            d.line([x0, yy, x1, yy], fill=C["line"], width=6)
            d.line([x0, yy, x0 + (x1 - x0) * (t - y0r) / max(1, nyrs), yy], fill=C["graphite"], width=6)
            d.text((x0, yy + 18), str(y0r), font=F(26, 500), fill=C["smoke"], anchor="lt")
            d.text((x1, yy + 18), str(y1r), font=F(26, 500), fill=C["smoke"], anchor="rt")
        elif f < total - T_END:
            m = f - T_RUN - T_HOLD
            ty = draw_header(d, r, kick=kick, sub=sub)
            board(im, d, y1r, ty, 1320)
            first = (f"Лидер весь период: {leader1['name']}" if leader0 is leader1
                     else f"Лидер в {y0r}: {leader0['name']}, в {y1r}: {leader1['name']}")
            punch_box(d, ease(m / 8), [first, r["hook_text"]])
        else:
            end_phase(im, d, r, f, total, kick=kick)
        chrome(im, d, f, total, src_line(r))
        return im.convert("RGB")
    return total, frame


# ---------- подписи ----------
def tags_for(r, lead):
    tags, seen = [], set()
    for t in TAGS.get(r["block"], []) + [lead] + TAG_BASE:
        h = tag(t)
        if len(h) > 2 and h not in seen:
            seen.add(h)
            tags.append(h)
    return " ".join(tags[:12])


CTA_TOP = "Новые рейтинги каждый день в Telegram @osnovafin, ссылка в профиле."
CTA_TEXT = "Каждый день рынки, сделки инсайдеров из отчётов SEC и данные в Telegram @osnovafin, ссылка в профиле."


def caption(r, n):
    if r["fmt"] == "bars":
        return caption_bars(r, n)
    q = (QUESTIONS.get(r["block"]) or Q_DEFAULT)[n % 3]
    if r["fmt"] in ("line", "race"):
        hook = r["hook_text"] + "."
        rows = f"{r['title']}, {r['year']} год и рост с {r['start']}:\n" + "\n".join(
            f"{i + 1}. {x['flag']} {x['name']}: {x['text']}" + (f", рост {x['growth']}" if x.get("growth") else "")
            for i, x in enumerate(r.get("series_all", r["series"])))
        lead = next((x for x in r["series"] if x.get("hl")), r["series"][0])["name"]
    elif r["fmt"] == "donut":
        hook = r["hook_text"] + f". На остальные {r['countries'] - 5} стран приходится {num1(r['rest'])}%."
        rows = "Доли лидеров:\n" + "\n".join(f"{x['rank']}. {x['flag']} {x['name']}: {x['text']}" for x in r.get("top10", r["top"]))
        lead = r["top"][0]["name"]
    else:
        k = compare_k(r)
        top = r["top"]
        acc = sum(x["value"] for x in top[1:1 + k])
        hook = (f"{r['title']}: №1 {top[0]['name']}, {top[0]['text']}. Это больше, чем №2–№{k + 1} вместе "
                f"({short(acc, r['unit'])}), разница {short(top[0]['value'] - acc, r['unit'])}.")
        rows = "Топ-10:\n" + "\n".join(f"{x['rank']}. {x['flag']} {x['name']}: {x['text']}" for x in top)
        lead = top[0]["name"]
        q = "Кто, по-вашему, догонит №1?"
    src = src_line(r).replace("Источник: ", "Источник: ", 1)
    return "\n\n".join([hook, CTA_TOP, rows, q, CTA_TEXT, src + " Не индивидуальная инвестиционная рекомендация.",
                        tags_for(r, lead)]).replace(NB, " ")




# ---------- видео ----------
def tracks():
    return sorted(glob.glob(os.path.join(ASSETS, "music", "*.mp3")))


def render(r, out, n, theme=None):
    set_theme(theme or ("dark" if n % 5 in (1, 3) else "light"))  # bone и oxblood примерно 3:2
    total, frame = {"bars": make_frames, "line": make_frames_line, "donut": make_frames_donut,
                    "compare": make_frames_compare, "race": make_frames_race}[r.get("fmt", "bars")](r)
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
        "share_to_feed": "true", "thumb_offset": "1500", "access_token": token,
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
    auto = [p for p in st["posted"] if p.get("block") != "manual" and p.get("post") != "failed"]
    if auto and not dry and not want and "--force" not in args:
        gap = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(auto[-1]["at"])
        if gap < dt.timedelta(minutes=150):  # GitHub иногда запускает расписание с опозданием
            log(f"Пропуск: прошлый ролик вышел {int(gap.total_seconds() // 60)} мин назад")
            return 0
    r = next((x for x in variants(rankings) if x["id"] == want), None) if want else pick(rankings, st)
    if not r:
        log("Нет рейтинга для ролика: " + (f"{want} не найден" if want else "все публиковались за 90 дней"))
        return 1
    n = len([p for p in st["posted"] if p.get("block") != "manual"])
    for attempt in range(3):  # ошибка сборки не должна блокировать очередь
        try:
            music = render(r, out, n, theme)
            break
        except Exception as e:  # noqa: BLE001
            log(f"Ошибка сборки {r['id']}: {e!r}")
            if want or attempt == 2:
                raise
            st["posted"].append({"id": r["id"], "block": r["block"], "fmt": r["fmt"], "post": "failed",
                                 "at": dt.datetime.now(dt.timezone.utc).isoformat()})
            save_state(st)
            r = pick(rankings, st)
            if not r:
                return 1
    cap = caption(r, n)
    log(f"reels: {r['id']} ({r['block']}, {r['fmt']})\n---\n{cap}\n---")
    token = os.environ.get("IG_TOKEN", "")
    if dry or not token:
        log("Публикации нет: " + ("dry-run" if dry else "токен не задан"))
        save_state(st) if not os.path.exists(STATE) else None
        return 0
    # 08.11: Instagram дважды отклонил один и тот же ролик (ProcessingFailedError), очередь встала.
    # Теперь: одна повторная загрузка, затем ролик помечается failed и публикуется следующий рейтинг.
    pid = None
    for attempt in range(3):
        try:
            pid = publish_reel(token, out, cap)
            break
        except RuntimeError as e:
            log(f"Ошибка публикации {r['id']} (попытка {attempt + 1}): {e}")
            if want or attempt == 2:
                raise
            if attempt == 0:
                time.sleep(30)
                continue
            st["posted"].append({"id": r["id"], "block": r["block"], "fmt": r["fmt"], "post": "failed",
                                 "at": dt.datetime.now(dt.timezone.utc).isoformat()})
            save_state(st)
            r = pick(rankings, st)
            if not r:
                raise
            music = render(r, out, n, theme)
            cap = caption(r, n)
            log(f"reels (замена): {r['id']} ({r['block']}, {r['fmt']})")
    st["posted"].append({"id": r["id"], "block": r["block"], "fmt": r["fmt"], "at": dt.datetime.now(dt.timezone.utc).isoformat(),
                         "post": pid, "music": music})
    save_state(st)
    log(f"Опубликовано: {pid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
