"""Рыночные посты для Telegram @osnovafin. v1 (06.11.2026)

Режимы (python scripts/market.py <режим>):
  evening   итоги дня: индексы мира, сырьё, биткоин, доходность UST 10Y (после закрытия США)
  calendar  экономический календарь дня (утро, время по Дубаю)
  chart     график дня: актив с самым сильным движением за день, линия за 6 месяцев
  alerts    алерт: индекс или крупная бумага США за день −5% и сильнее (рост +7% и сильнее)

Картинка → tg/img/<id>.png, запись → tg/outbox.json. Публикует воркер osnova-finance-feed
(у него BOT_TOKEN): раз в минуту читает outbox.json с GitHub и отправляет новые записи.
Данные: Yahoo Finance (yfinance), календарь: ForexFactory (faireconomy.media).
"""
import datetime as dt
import json
import os
import re
import sys
import time

import requests
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import font, tw, spaced, ring, plane, M  # noqa: E402

W, H = 1080, 1350
T = {"bg": "#17171A", "brand": "#F2EFEA", "head": "#EFE4E0", "sub": "#AC8C8A", "text": "#EFE4E0",
     "muted": "#8E8486", "line": "#2E2A2C", "row": "#1F1D20", "cta": "#E2B8A4",
     "up": "#4FA36B", "down": "#D9534F", "flat": "#AC8C8A", "chart": "#E2B8A4"}
DXB = dt.timezone(dt.timedelta(hours=4))
NB = " "
MINUS = "−"
MON = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
WD = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]

INDICES = [("^GSPC", "S&P 500", "🇺🇸"), ("^IXIC", "Nasdaq", "🇺🇸"), ("^DJI", "Dow Jones", "🇺🇸"),
           ("^GDAXI", "DAX", "🇩🇪"), ("^FTSE", "FTSE 100", "🇬🇧"), ("^N225", "Nikkei 225", "🇯🇵"),
           ("^HSI", "Hang Seng", "🇭🇰"), ("000001.SS", "Шанхай", "🇨🇳")]
COMMOD = [("BZ=F", "Нефть Brent", "$"), ("GC=F", "Золото", "$"), ("SI=F", "Серебро", "$"), ("HG=F", "Медь", "$")]
OTHER = [("BTC-USD", "Биткоин", "$"), ("^TNX", "UST 10 лет", "%")]
# Крупнейшие бумаги США для графика дня и алертов
BIG = ("AAPL MSFT NVDA AMZN GOOGL META TSLA AVGO BRK-B LLY JPM V MA UNH XOM WMT JNJ PG HD COST ORCL ABBV BAC KO "
       "MRK CVX NFLX CRM AMD PEP ADBE MCD CSCO WFC ABT DIS INTU IBM QCOM CAT TXN GS MS PLTR UBER AMAT BA INTC "
       "MU PANW CRWD COIN MSTR HOOD SMCI ARM DELL SHOP SNOW NOW TSM ASML BABA PDD").split()
NAMES = {"AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "AMZN": "Amazon", "GOOGL": "Alphabet", "META": "Meta",
         "TSLA": "Tesla", "AVGO": "Broadcom", "BRK-B": "Berkshire Hathaway", "LLY": "Eli Lilly", "JPM": "JPMorgan",
         "V": "Visa", "MA": "Mastercard", "UNH": "UnitedHealth", "XOM": "ExxonMobil", "WMT": "Walmart", "JNJ": "Johnson & Johnson",
         "PG": "Procter & Gamble", "HD": "Home Depot", "COST": "Costco", "ORCL": "Oracle", "ABBV": "AbbVie", "BAC": "Bank of America",
         "KO": "Coca-Cola", "MRK": "Merck", "CVX": "Chevron", "NFLX": "Netflix", "CRM": "Salesforce", "AMD": "AMD", "PEP": "PepsiCo",
         "ADBE": "Adobe", "MCD": "McDonald's", "CSCO": "Cisco", "WFC": "Wells Fargo", "ABT": "Abbott", "DIS": "Disney",
         "INTU": "Intuit", "IBM": "IBM", "QCOM": "Qualcomm", "CAT": "Caterpillar", "TXN": "Texas Instruments", "GS": "Goldman Sachs",
         "MS": "Morgan Stanley", "PLTR": "Palantir", "UBER": "Uber", "AMAT": "Applied Materials", "BA": "Boeing", "INTC": "Intel",
         "MU": "Micron", "PANW": "Palo Alto Networks", "CRWD": "CrowdStrike", "COIN": "Coinbase", "MSTR": "Strategy",
         "HOOD": "Robinhood", "SMCI": "Super Micro", "ARM": "Arm", "DELL": "Dell", "SHOP": "Shopify", "SNOW": "Snowflake",
         "NOW": "ServiceNow", "TSM": "TSMC", "ASML": "ASML", "BABA": "Alibaba", "PDD": "PDD (Temu)",
         "BTC-USD": "Биткоин", "GC=F": "Золото", "BZ=F": "Нефть Brent", "SI=F": "Серебро", "^GSPC": "S&P 500", "^IXIC": "Nasdaq"}

OUTBOX = "tg/outbox.json"
STATE = "tg/state.json"


# ───────── форматирование ─────────

def num(v, d=2):
    s = f"{abs(v):,.{d}f}".replace(",", NB).replace(".", ",")
    if "," in s:
        s = s.rstrip("0").rstrip(",") if d > 0 else s
    return (MINUS if v < 0 else "") + s


def price(v):
    return num(v, 0 if abs(v) >= 1000 else 2)


def pct(v):
    s = f"{abs(v):.2f}".replace(".", ",")
    return ("+" if v > 0 else MINUS if v < 0 else "") + s + "%"


def col(v):
    return T["up"] if v > 0.004 else T["down"] if v < -0.004 else T["flat"]


def day_ru(d):
    return f"{d.day} {MON[d.month - 1]}"


# ───────── данные ─────────

def closes(tickers, period="10d"):
    import yfinance as yf
    df = yf.download(tickers, period=period, interval="1d", progress=False, auto_adjust=False, group_by="ticker", threads=False)
    out = {}
    for t in tickers:
        try:
            s = (df[t]["Close"] if len(tickers) > 1 else df["Close"]).dropna()
            if len(s) >= 2:
                out[t] = s
        except Exception:
            pass
    return out


def last_change(s):
    a, b = float(s.iloc[-2]), float(s.iloc[-1])
    return b, (b / a - 1) * 100, b - a


# ───────── общие части карточки ─────────

def canvas(title, subtitle):
    im = Image.new("RGB", (W, H), T["bg"])
    _IM["im"] = im
    d = ImageDraw.Draw(im)
    ring(d, M + 16, 96, 16, T["brand"], T["bg"])
    spaced(d, M + 46, 85, "OSNOVA FINANCE", font(20, 500), T["brand"], 4)
    d.text((M, 150), title, font=font(64, 700), fill=T["head"])
    d.text((M, 236), subtitle, font=font(28), fill=T["sub"])
    return im, d


def footer(d, source):
    y = H - 150
    d.rectangle([M, y, W - M, y], fill=T["line"])
    d.text((M, y + 30), "Источник: " + source, font=font(22), fill=T["muted"])
    cy = y + 92
    d.text((M, cy), "Рынки и данные 24/7 в Telegram @osnovafin", font=font(30, 600), fill=T["cta"], anchor="lm")
    plane(d, W - M - 52, cy, 52, T["cta"], T["bg"])


def section(d, y, name):
    spaced(d, M, y, name.upper(), font(21, 600), T["sub"], 3)
    return y + 40


EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_IM = {}


def emoji(d, x, y, ch, size=34):
    """Цветной эмодзи (флаг): Noto Color Emoji рисуется только в 109 px, затем масштабируется."""
    from PIL import ImageFont
    im = _IM.get("im")
    if im is None or not os.path.exists(EMOJI_FONT):
        return
    tile = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((0, 0), ch, font=ImageFont.truetype(EMOJI_FONT, 109), embedded_color=True)
    bb = tile.getbbox()
    if not bb:
        return
    tile = tile.crop(bb)
    k = size / tile.height
    tile = tile.resize((max(1, int(tile.width * k)), size), Image.LANCZOS)
    im.paste(tile, (int(x), int(y)), tile)


def row(d, y, label, value, change, change_txt=None, flag=""):
    f = font(30, 500)
    if flag:
        emoji(d, M, y + 3, flag, 30)
        d.text((M + 52, y), label, font=f, fill=T["text"])
    else:
        d.text((M, y), label, font=f, fill=T["text"])
    d.text((W - M - 230, y), value, font=f, fill=T["muted"], anchor="ra")
    d.text((W - M, y), change_txt or pct(change), font=font(30, 600), fill=col(change), anchor="ra")
    d.rectangle([M, y + 46, W - M, y + 46], fill=T["line"])
    return y + 54


# ───────── outbox ─────────

def load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def push_out(item_id, img_path, caption):
    os.makedirs("tg", exist_ok=True)
    if os.environ.get("DRY_RUN") == "yes":
        print("DRY:", item_id, img_path, "\n" + caption)
        return True
    box = load(OUTBOX, [])
    if any(x["id"] == item_id for x in box):
        print("уже в очереди:", item_id)
        return False
    repo = os.environ.get("GITHUB_REPOSITORY", "aleksandr-pm/osnova-finance-data")
    entry = {"id": item_id, "caption": caption[:1000], "t": int(time.time())}
    if img_path:
        entry["photo"] = f"https://raw.githubusercontent.com/{repo}/main/{img_path}"
    box = (box + [entry])[-30:]
    json.dump(box, open(OUTBOX, "w"), ensure_ascii=False, indent=1)
    print("в очередь:", item_id)
    return True


# ───────── 1. итоги дня ─────────

def evening():
    tick = [t for t, _, _ in INDICES + COMMOD + OTHER]
    data = closes(tick)
    now = dt.datetime.now(DXB)
    us_day = (now - dt.timedelta(hours=12)).date()  # торговый день США, закрытие около 01:00 по Дубаю
    im, d = canvas("Итоги дня", f"{day_ru(us_day)}, {WD[us_day.weekday()]} · изменение к прошлому закрытию")
    y = 290
    y = section(d, y, "Индексы")
    lines = []
    for t, name, fl in INDICES:
        if t in data:
            p, c, _ = last_change(data[t])
            y = row(d, y, name, price(p), c, flag=fl)
            if t in ("^GSPC", "^IXIC", "^DJI"):
                lines.append(f"{name} {pct(c)}")
    y += 12
    y = section(d, y, "Сырьё")
    com = []
    for t, name, _ in COMMOD:
        if t in data:
            p, c, _ = last_change(data[t])
            y = row(d, y, name, "$" + price(p), c)
            if t in ("BZ=F", "GC=F"):
                com.append(f"{name} {pct(c)}")
    y += 12
    y = section(d, y, "Биткоин и облигации")
    for t, name, unit in OTHER:
        if t in data:
            p, c, dv = last_change(data[t])
            if unit == "%":
                bp = round(dv * 100)
                y = row(d, y, name, num(p, 2) + "%", dv, change_txt=(("+" if bp > 0 else MINUS if bp < 0 else "") + f"{abs(bp)} б.п."))
            else:
                y = row(d, y, name, "$" + price(p), c)
    footer(d, "Yahoo Finance, цены закрытия")
    os.makedirs("tg/img", exist_ok=True)
    item = f"evening-{us_day.isoformat()}"
    path = f"tg/img/{item}.png"
    im.save(path)
    cap = f"📈 <b>Итоги дня {day_ru(us_day)}</b>\n\n" + ", ".join(lines)
    if com:
        cap += "\n" + ", ".join(com)
    cap += "\n\n#итогидня"
    return push_out(item, path, cap)


# ───────── 2. экономический календарь ─────────

FLAGS = {"USD": ("🇺🇸", "США"), "EUR": ("🇪🇺", "Еврозона"), "GBP": ("🇬🇧", "Британия"), "CNY": ("🇨🇳", "Китай"),
         "JPY": ("🇯🇵", "Япония"), "CAD": ("🇨🇦", "Канада"), "AUD": ("🇦🇺", "Австралия"), "CHF": ("🇨🇭", "Швейцария")}
SKIP = re.compile(r"Home|Housing|Building Permits|Mortgage|HPI|House|Construction", re.I)
TR = [
    (r"^Core CPI m/m", "Базовая инфляция (CPI), м/м"), (r"^Core CPI y/y", "Базовая инфляция (CPI), г/г"),
    (r"^CPI m/m", "Инфляция (CPI), м/м"), (r"^CPI y/y", "Инфляция (CPI), г/г"), (r"^CPI q/q", "Инфляция (CPI), кв/кв"),
    (r"^Flash CPI y/y|^CPI Flash Estimate y/y", "Инфляция, предварительно, г/г"),
    (r"^Core CPI Flash Estimate y/y", "Базовая инфляция, предварительно, г/г"),
    (r"^Core PCE Price Index m/m", "Базовый индекс цен PCE, м/м"), (r"^Core PCE Price Index y/y", "Базовый индекс цен PCE, г/г"),
    (r"^Core PPI m/m", "Базовые цены производителей (PPI), м/м"), (r"^PPI m/m", "Цены производителей (PPI), м/м"),
    (r"^PPI y/y", "Цены производителей (PPI), г/г"),
    (r"^ADP Non-Farm Employment Change", "Занятость по данным ADP"),
    (r"^Non-Farm Employment Change", "Новые рабочие места вне сельского хозяйства (NFP)"),
    (r"^Unemployment Claims", "Заявки на пособие по безработице"), (r"^Unemployment Rate", "Уровень безработицы"),
    (r"^Average Hourly Earnings m/m", "Средняя почасовая зарплата, м/м"), (r"^JOLTS Job Openings", "Вакансии (JOLTS)"),
    (r"^Core Retail Sales m/m", "Базовые розничные продажи, м/м"), (r"^Retail Sales m/m", "Розничные продажи, м/м"),
    (r"^Retail Sales y/y", "Розничные продажи, г/г"),
    (r"^ISM Manufacturing PMI", "Деловая активность в промышленности (ISM)"), (r"^ISM Services PMI", "Деловая активность в услугах (ISM)"),
    (r"^Flash Manufacturing PMI", "Деловая активность в промышленности (PMI), предварительно"),
    (r"^Flash Services PMI", "Деловая активность в услугах (PMI), предварительно"),
    (r"^Caixin Manufacturing PMI", "Деловая активность в промышленности (Caixin)"),
    (r"^Caixin Services PMI", "Деловая активность в услугах (Caixin)"),
    (r"^Manufacturing PMI", "Деловая активность в промышленности (PMI)"), (r"^Services PMI", "Деловая активность в услугах (PMI)"),
    (r"^(Advance|Prelim|Final)? ?GDP q/q", "ВВП, кв/кв"), (r"^GDP y/y", "ВВП, г/г"), (r"^GDP m/m", "ВВП, м/м"),
    (r"^Federal Funds Rate", "Решение ФРС по ставке"), (r"^FOMC Statement", "Заявление ФРС"),
    (r"^FOMC Press Conference", "Пресс-конференция ФРС"), (r"^FOMC Meeting Minutes", "Протокол заседания ФРС"),
    (r"^FOMC Economic Projections", "Прогнозы ФРС"),
    (r"^Fed Chair (.+) Speaks", r"Выступление главы ФРС (\1)"), (r"^FOMC Member (.+) Speaks", r"Выступление члена ФРС (\1)"),
    (r"^Main Refinancing Rate", "Решение ЕЦБ по ставке"), (r"^ECB Press Conference", "Пресс-конференция ЕЦБ"),
    (r"^ECB President (.+) Speaks", r"Выступление главы ЕЦБ (\1)"),
    (r"^Official Bank Rate", "Решение Банка Англии по ставке"), (r"^BOJ Policy Rate", "Решение Банка Японии по ставке"),
    (r"^Overnight Rate", "Решение Банка Канады по ставке"), (r"^Cash Rate", "Решение РБА по ставке"),
    (r"^Prelim UoM Consumer Sentiment", "Настроения потребителей (Мичиган), предварительно"),
    (r"^Revised UoM Consumer Sentiment", "Настроения потребителей (Мичиган), итог"),
    (r"^Prelim UoM Inflation Expectations", "Инфляционные ожидания (Мичиган)"),
    (r"^CB Consumer Confidence", "Доверие потребителей (Conference Board)"),
    (r"^Crude Oil Inventories", "Запасы нефти в США"), (r"^Natural Gas Storage", "Запасы газа в США"),
    (r"^Core Durable Goods Orders m/m", "Базовые заказы товаров длительного пользования, м/м"),
    (r"^Durable Goods Orders m/m", "Заказы товаров длительного пользования, м/м"),
    (r"^Trade Balance", "Торговый баланс"), (r"^Empire State Manufacturing Index", "Промышленность штата Нью-Йорк (Empire State)"),
    (r"^Philly Fed Manufacturing Index", "Промышленность Филадельфии (Philly Fed)"),
    (r"^Industrial Production m/m", "Промышленное производство, м/м"), (r"^Industrial Production y/y", "Промышленное производство, г/г"),
    (r"^German (.+)", None), (r"^French (.+)", None), (r"^Italian (.+)", None), (r"^Spanish (.+)", None),
    (r"^(\d+)-y Bond Auction", r"Аукцион \1-летних гособлигаций"),
    (r"^Treasury Currency Report", "Валютный отчёт Минфина США"),
    (r"^Bank Holiday", None),
]
COUNTRY_PREFIX = {"German": "Германия: ", "French": "Франция: ", "Italian": "Италия: ", "Spanish": "Испания: "}


def tr(title):
    m = re.match(r"^(German|French|Italian|Spanish) (.+)$", title)
    if m:
        inner = tr(m.group(2))
        return COUNTRY_PREFIX[m.group(1)] + inner if inner else None
    for pat, ru in TR:
        mm = re.match(pat, title)
        if mm:
            return mm.expand(ru) if ru else None
    return None


def ru_val(v):
    """6.5% → 6,5%; 65K → 65 тыс.; 1.2M → 1,2 млн; −0.3% остаётся числом с минусом"""
    if not v:
        return ""
    v = v.replace(".", ",").replace("-", MINUS)
    return re.sub(r"(\d)([KMBT])$", lambda m: m.group(1) + NB + {"K": "тыс.", "M": "млн", "B": "млрд", "T": "трлн"}[m.group(2)], v)


def calendar():
    r = requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json", timeout=30,
                     headers={"User-Agent": "Mozilla/5.0 (compatible; OSNOVAFinance/1.0)"})
    r.raise_for_status()
    today = dt.datetime.now(DXB).date()
    rows, skipped = [], []
    for e in r.json():
        if e.get("impact") not in ("High", "Medium") or e.get("country") not in FLAGS:
            continue
        if e.get("impact") == "Medium" and e.get("country") not in ("USD", "EUR", "CNY"):
            continue
        if SKIP.search(e.get("title", "")):
            continue
        try:
            t = dt.datetime.fromisoformat(e["date"]).astimezone(DXB)
        except Exception:
            continue
        if t.date() != today:
            continue
        name = tr(e["title"])
        if not name:
            skipped.append(e["title"])
            continue
        rows.append((t, e["country"], name, e.get("impact"), ru_val(e.get("forecast") or ""), ru_val(e.get("previous") or "")))
    print("без перевода, пропущено:", skipped)
    if not rows:
        print("важных событий сегодня нет")
        return False
    rows.sort(key=lambda x: x[0])
    rows = rows[:13]
    im, d = canvas("Календарь дня", f"{day_ru(today)}, {WD[today.weekday()]} · время по Дубаю")
    y = 300
    d.text((M, y), "ВРЕМЯ", font=font(20, 600), fill=T["sub"])
    d.text((M + 120, y), "СОБЫТИЕ", font=font(20, 600), fill=T["sub"])
    d.text((W - M - 150, y), "ПРОГНОЗ", font=font(20, 600), fill=T["sub"], anchor="ra")
    d.text((W - M, y), "ПРЕД.", font=font(20, 600), fill=T["sub"], anchor="ra")
    y += 46
    maxw = W - 2 * M - 120 - 330
    for t, c, name, imp, fc, pv in rows:
        flag, _ = FLAGS[c]
        tf = font(30, 600 if imp == "High" else 500)
        d.text((M, y), t.strftime("%H:%M"), font=tf, fill=T["cta"] if imp == "High" else T["text"])
        emoji(d, M + 120, y + 2, flag, 28)
        nf = font(27, 600 if imp == "High" else 400)
        words, linesn, cur = name.split(), [], ""
        for w_ in words:
            test = (cur + " " + w_).strip()
            if tw(d, test, nf) <= maxw - 50:
                cur = test
            else:
                linesn.append(cur)
                cur = w_
        linesn.append(cur)
        linesn = linesn[:2]
        for i, ln in enumerate(linesn):
            d.text((M + 170, y + i * 34), ln, font=nf, fill=T["text"])
        d.text((W - M - 150, y), fc or "·", font=font(27, 500), fill=T["text"], anchor="ra")
        d.text((W - M, y), pv or "·", font=font(27), fill=T["muted"], anchor="ra")
        y += 34 * len(linesn) + 26
        d.rectangle([M, y - 13, W - M, y - 13], fill=T["line"])
        if y > H - 200:
            break
    footer(d, "ForexFactory · выделены главные события дня")
    os.makedirs("tg/img", exist_ok=True)
    item = f"calendar-{today.isoformat()}"
    path = f"tg/img/{item}.png"
    im.save(path)
    top = [f"{t.strftime('%H:%M')} {FLAGS[c][0]} {n}" for t, c, n, imp, _, _ in rows if imp == "High"][:5]
    cap = f"🗓 <b>Экономический календарь на {day_ru(today)}</b>\n\n"
    cap += ("Главное:\n" + "\n".join(top)) if top else "Главных событий нет, на графике второстепенные"
    cap += "\n\nВремя по Дубаю · #календарь"
    return push_out(item, path, cap)


# ───────── 3. график дня ─────────

def chart():
    import yfinance as yf
    pool = BIG + ["BTC-USD", "GC=F", "BZ=F", "SI=F"]
    data = closes(pool, period="7d")
    moves = sorted(((abs(last_change(s)[1]), t) for t, s in data.items()), reverse=True)
    st = load(STATE, {})
    used = st.get("chart_used", [])
    pick = next((t for _, t in moves if t not in used[-6:]), moves[0][1])
    hist = yf.download(pick, period="6mo", interval="1d", progress=False, auto_adjust=False)["Close"].dropna()
    hist = hist.iloc[:, 0] if hasattr(hist, "columns") else hist
    p, c, _ = last_change(data[pick])
    half = (float(hist.iloc[-1]) / float(hist.iloc[0]) - 1) * 100
    name = NAMES.get(pick, pick)
    tick = "" if pick in ("BTC-USD", "GC=F", "BZ=F", "SI=F") or name == pick else f" ({pick})"
    im, d = canvas(name + tick, f"Цена за 6 месяцев · за день {pct(c)}, за полгода {pct(half)}")
    # линия
    x0, x1, y0, y1 = M, W - M - 120, 330, H - 260
    vals = [float(v) for v in hist.values]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.08 or 1
    lo, hi = lo - pad, hi + pad
    for k in range(5):
        gy = y0 + (y1 - y0) * k / 4
        d.rectangle([x0, gy, x1, gy], fill=T["line"])
        gv = hi - (hi - lo) * k / 4
        d.text((x1 + 14, gy), price(gv), font=font(22), fill=T["muted"], anchor="lm")
    pts = [(x0 + (x1 - x0) * i / (len(vals) - 1), y1 - (y1 - y0) * (v - lo) / (hi - lo)) for i, v in enumerate(vals)]
    d.line(pts, fill=T["chart"], width=5, joint="curve")
    lx, ly = pts[-1]
    d.ellipse([lx - 9, ly - 9, lx + 9, ly + 9], fill=col(c))
    lab = ("$" if pick != "^TNX" else "") + price(vals[-1])
    lf = font(30, 700)
    bw = tw(d, lab, lf) + 28
    bx = min(lx - bw / 2, x1 - bw)
    by = ly - 66 if ly - 66 > y0 else ly + 22
    d.rectangle([bx, by, bx + bw, by + 46], fill=col(c))
    d.text((bx + bw / 2, by + 23), lab, font=lf, fill=T["bg"], anchor="mm")
    # месяцы по оси
    idx = hist.index
    seen = set()
    for i, ts in enumerate(idx):
        key = (ts.year, ts.month)
        if key in seen or i == 0:
            seen.add(key)
            continue
        seen.add(key)
        x = x0 + (x1 - x0) * i / (len(vals) - 1)
        d.text((x, y1 + 30), MON[ts.month - 1][:3], font=font(24), fill=T["muted"], anchor="mm")
    footer(d, "Yahoo Finance, цены закрытия")
    os.makedirs("tg/img", exist_ok=True)
    today = dt.datetime.now(DXB).date()
    item = f"chart-{today.isoformat()}-{pick.replace('^', '').replace('=', '')}"
    path = f"tg/img/{item}.png"
    im.save(path)
    word = "выросла" if c > 0 else "упала"
    if pick in ("BTC-USD", "GC=F", "BZ=F", "SI=F"):
        head = f"<b>{name}</b> {pct(c)} за день"
    else:
        head = f"Акции <b>{name}</b> {'выросли' if c > 0 else 'упали'} на {pct(abs(c)).lstrip('+')} за день"
    cap = f"📊 {head}\nЗа полгода: {pct(half)}, цена ${price(vals[-1])}\n\n#графикдня"
    ok = push_out(item, path, cap)
    st["chart_used"] = (used + [pick])[-20:]
    json.dump(st, open(STATE, "w"), ensure_ascii=False, indent=1)
    return ok


# ───────── 4. алерты ─────────

def alerts():
    idx = [t for t, _, _ in INDICES]
    data = closes(idx + BIG, period="5d")
    today = dt.datetime.now(DXB).date().isoformat()
    st = load(STATE, {})
    sent = st.get("alerts", {})
    sent = {k: v for k, v in sent.items() if v == today}
    names = {t: n for t, n, _ in INDICES}
    out = 0
    for t, s in data.items():
        p, c, _ = last_change(s)
        is_idx = t in names
        if not (c <= -5 or (c >= 7 and not is_idx) or (is_idx and c >= 5)):
            continue
        key = f"{t}:{'down' if c < 0 else 'up'}"
        if key in sent:
            continue
        name = names.get(t) or NAMES.get(t, t)
        what = f"Индекс <b>{name}</b>" if is_idx else f"<b>{name}</b> ({t})"
        arrow = "🔻" if c < 0 else "🚀"
        cap = f"⚡️{arrow} {what} {pct(c)} за день, {('' if is_idx else '$')}{price(p)}\n\n#алерт"
        if push_out(f"alert-{today}-{t.replace('^', '')}-{'d' if c < 0 else 'u'}", None, cap):
            sent[key] = today
            out += 1
    st["alerts"] = sent
    json.dump(st, open(STATE, "w"), ensure_ascii=False, indent=1)
    print("алертов:", out)
    return out > 0


if __name__ == "__main__":
    mode = sys.argv[1]
    ok = {"evening": evening, "calendar": calendar, "chart": chart, "alerts": alerts}[mode]()
    print("готово:", mode, ok)
