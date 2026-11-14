"""Утренние сторис для Instagram @aleksandr_markets: итоги торгов ОАЭ и США. v1 (14.11.2026)

python scripts/am_stories.py probe     проверить источники данных, итог в am/probe.json
python scripts/am_stories.py render    собрать данные и нарисовать сторис в am/out/, план в am/out/today.json
python scripts/am_stories.py publish   опубликовать сторис из am/out/today.json (нужен коммит картинок до запуска)

Данные:
  ОАЭ: публичный скринер TradingView (scanner.tradingview.com/uae/scan), без ключа.
       Лидеры только среди компаний с капитализацией от 5 млрд AED.
  США: Yahoo Finance (yfinance), лидеры среди компаний S&P 500.

Публикация (раздел 5 инструкции Instagram_autopublish_guide.md):
  - публикуется, только если есть файл am/LIVE и секреты IG_TOKEN_AM (или IG_TOKEN) и IG_USER_ID_AM;
  - пауза: дата в am/pause_until.txt;
  - любая ошибка после создания контейнера: сторис помечается как использованная, повтора нет.
Подпись в кадре без фамилии и без упоминания работодателя.
"""
import datetime as dt
import io
import json
import os
import sys
import time

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AM = os.path.join(ROOT, "am")
OUT = os.path.join(AM, "out")
BG = os.path.join(AM, "bg")
FONTS = os.path.join(ROOT, "fonts")
REPO = os.environ.get("GITHUB_REPOSITORY", "aleksandr-pm/osnova-finance-data")
IG = "https://graph.facebook.com/v25.0"
DXB = dt.timezone(dt.timedelta(hours=4))
TV_UAE = "https://scanner.tradingview.com/uae/scan"
TV_GLOBAL = "https://scanner.tradingview.com/global/scan"
UA = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
MIN_CAP_AED = 5e9
EXCLUDE = {"ORDS", "GFH", "SALAM_BAH", "ALSALAMBAH", "NIND", "NDAQ"}  # иностранные эмитенты на ADX/DFM (правило инструкции)

# Индексы ОАЭ: (символ TradingView, подпись). Символ индекса недвижимости уточняется в probe.
UAE_INDICES = [("ADX:FADGI", "FTSE ADX General"), ("DFM:DFMGI", "DFM General"), ("DFM:DFMREI", "DFM Real Estate")]
US_INDICES = [("^GSPC", "S&P 500"), ("^NDX", "Nasdaq 100"), ("^DJI", "Dow Jones")]
EXTRA_US = [("BZ=F", "BRENT", "usd"), ("^TNX", "UST 10 ЛЕТ", "yield"), ("GC=F", "ЗОЛОТО", "usd"), ("EURUSD=X", "EUR/USD", "fx")]
EXTRA_UAE = [("BZ=F", "BRENT", "usd"), ("GC=F", "ЗОЛОТО", "usd")]
SP500_CSV = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"

# Короткие имена компаний ОАЭ (по тикеру TradingView); остальные из описания скринера
UAE_NAMES = {"ETISALAT": "e&", "2POINTZERO": "2PointZero", "NBQ": "Bank of Umm Al Qaiwain", "ALANSARI": "Al Ansari",
             "TABREED": "Tabreed", "ADNH": "AD National Hotels", "RAKBANK": "RAKBANK", "CBD": "Commercial Bank Dubai",
             "AMANAT": "Amanat", "ALDAR_": "Aldar", "EMSTEEL": "Emsteel", "ESHRAQ": "Eshraq", "RAKPROP": "RAK Properties",
             "EMAAR": "Emaar Properties", "EMAARDEV": "Emaar Development", "ALDAR": "Aldar", "FAB": "FAB", "ENBD": "Emirates NBD",
             "ADCB": "ADCB", "ADIB": "ADIB", "DIB": "Dubai Islamic Bank", "IHC": "IHC", "ADNOCGAS": "ADNOC Gas",
             "ADNOCDRILL": "ADNOC Drilling", "ADNOCDIST": "ADNOC Distribution", "ADNOCLS": "ADNOC L&S", "EAND": "e&", "DU": "du",
             "SALIK": "Salik", "PARKIN": "Parkin", "TALABAT": "Talabat", "AIRARABIA": "Air Arabia", "DEWA": "DEWA",
             "TAQA": "TAQA", "ADPORTS": "AD Ports", "MASQ": "Mashreq", "ALPHADHABI": "Alpha Dhabi", "BOROUGE": "Borouge",
             "FERTIGLB": "Fertiglobe", "MULTIPLY": "Multiply", "PUREHEALTH": "PureHealth", "DFM": "DFM", "EMIRATESNBD": "Emirates NBD",
             "SPINNEYS": "Spinneys", "TECOM": "TECOM", "EMPOWER": "Empower", "DIC": "Dubai Investments", "ALEC": "ALEC",
             "AMR": "Americana", "AGTHIA": "Agthia", "NMDC": "NMDC", "ADX": "ADX", "PRESIGHT": "Presight", "SPACE42": "Space42",
             "ALDARHOLD": "Aldar", "MODON": "Modon", "LULU": "Lulu", "DNIN": "Dubai National Ins.", "GHITHA": "Ghitha"}
NB = " "
MINUS = "−"
WD = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
MON = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]


def log(*a):
    print(*a, flush=True)


# ───────── данные ─────────

def tv_post(url, body):
    r = requests.post(url, data=json.dumps(body), headers=UA, timeout=30)
    r.raise_for_status()
    return r.json()


def uae_stocks():
    body = {"filter": [{"left": "type", "operation": "equal", "right": "stock"}],
            "columns": ["name", "description", "close", "change", "market_cap_basic", "exchange", "currency", "volume"],
            "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"}, "range": [0, 400]}
    js = tv_post(TV_UAE, body)
    rows = []
    for x in js.get("data", []):
        n, desc, close, ch, cap, exch, cur, vol = x["d"]
        rows.append({"symbol": x["s"], "ticker": n, "desc": desc, "close": close, "change": ch, "cap": cap,
                     "exchange": exch, "currency": cur, "volume": vol})
    return rows


def tv_symbols(tickers, cols=("close", "change", "description")):
    js = tv_post(TV_GLOBAL, {"symbols": {"tickers": list(tickers)}, "columns": list(cols)})
    return {x["s"]: dict(zip(cols, x["d"])) for x in js.get("data", [])}


def uae_index_candidates():
    """Все индексы в скринере ОАЭ: чтобы найти точный символ индекса недвижимости DFM."""
    body = {"filter": [{"left": "type", "operation": "equal", "right": "index"}],
            "columns": ["name", "description", "close", "change"], "range": [0, 200]}
    try:
        js = tv_post(TV_UAE, body)
        return [{"s": x["s"], **dict(zip(["name", "description", "close", "change"], x["d"]))} for x in js.get("data", [])]
    except Exception as e:  # noqa: BLE001
        return [{"error": str(e)}]


STOP = {"of", "and", "&", "the", "for", "de"}


def shorten(name, maxc=20):
    out = ""
    for w in name.split():
        if len((out + " " + w).strip()) > maxc:
            break
        out = (out + " " + w).strip()
    words = out.split()
    while words and words[-1].lower() in STOP:
        words.pop()
    return " ".join(words) or name[:maxc]


def nice_name(r):
    if r["ticker"] in UAE_NAMES:
        return UAE_NAMES[r["ticker"]]
    d = (r["desc"] or r["ticker"]).replace(" PJSC", "").replace(" P.J.S.C.", "").replace(" P.J.S.C", "").replace(" COMPANY", "")
    for suf in ("(P.J.S.C)", "(P.J.S.C.)", "PJSC", "P.J.S.C.", "PSC", "plc", "PLC", "Company", "Co."):
        d = d.replace(suf, "")
    d = d.title() if d.isupper() else d
    return shorten(d.strip())


def uae_data():
    rows = [r for r in uae_stocks() if r["close"] and r["change"] is not None]
    big = [r for r in rows if (r["cap"] or 0) >= MIN_CAP_AED and r["symbol"].split(":")[0] in ("ADX", "DFM")
           and r["ticker"] not in EXCLUDE and r["currency"] == "AED"
           and not any(w in (r["desc"] or "").upper() for w in ("BAHRAIN", "B.S.C", "QATAR", "OOREDOO", "Q.P.S.C", "K.S.C"))]
    if len(big) < 10:
        raise RuntimeError(f"ОАЭ: мало крупных бумаг ({len(big)})")
    if all(abs(r["change"]) < 1e-9 for r in big):
        raise RuntimeError("ОАЭ: все изменения нулевые, похоже на выходной")
    big.sort(key=lambda r: r["change"], reverse=True)
    gain = [(nice_name(r), r["change"]) for r in big[:5] if r["change"] > 0]
    lose = [(nice_name(r), r["change"]) for r in reversed(big[-5:]) if r["change"] < 0]
    idx = tv_symbols([s for s, _ in UAE_INDICES])
    indices = [(label, idx[s]["close"], idx[s]["change"]) for s, label in UAE_INDICES if s in idx and idx[s]["close"]]
    return {"indices": indices, "gain": gain, "lose": lose, "universe": len(big)}


def yf_closes(tickers, period="10d"):
    import yfinance as yf
    df = yf.download(tickers, period=period, interval="1d", progress=False, auto_adjust=False, group_by="ticker", threads=True)
    out = {}
    for t in tickers:
        try:
            s = (df[t]["Close"] if len(tickers) > 1 else df["Close"]).dropna()
            s = s[s.index.dayofweek < 5]  # фьючерсы и валюты дают строку за выходной с той же ценой
            s = s[s.index.normalize() <= s.index.normalize().max()]
            if len(s) >= 2:
                out[t] = s
        except Exception:  # noqa: BLE001
            pass
    return out


def sp500():
    try:
        r = requests.get(SP500_CSV, timeout=30)
        r.raise_for_status()
        lines = r.text.strip().splitlines()[1:]
        res = {}
        for ln in lines:
            parts = ln.split(",")
            sym = parts[0].strip().replace(".", "-")
            name = parts[1].strip().strip('"')
            res[sym] = name
        if len(res) > 400:
            return res
    except Exception as e:  # noqa: BLE001
        log("S&P 500 список не загрузился:", e)
    return {}


US_SHORT = {"Advanced Micro Devices": "AMD", "Fidelity National Information Services": "FIS", "Charter Communications": "Charter",
            "International Business Machines": "IBM", "Alphabet (Class A)": "Alphabet", "Alphabet (Class C)": "Alphabet C",
            "Berkshire Hathaway": "Berkshire", "JPMorgan Chase": "JPMorgan", "Thermo Fisher Scientific": "Thermo Fisher",
            "Texas Instruments": "Texas Instruments", "Hewlett Packard Enterprise": "HPE", "Taiwan Semiconductor": "TSMC"}


def short_us(name):
    for suf in (", Inc.", " Inc.", " Corporation", " Corp.", " Incorporated", " Company", " Co.", " plc", " Ltd.", " Holdings", " Group", " (Class A)", " (Class B)", " (Class C)"):
        name = name.replace(suf, "")
    return US_SHORT.get(name.strip(), shorten(name.strip()))


def us_data():
    names = sp500()
    tick = [t for t, _ in US_INDICES] + [t for t, _, _ in EXTRA_US]
    base = yf_closes(tick)
    ref = base.get("^GSPC")
    if ref is None:
        raise RuntimeError("США: нет данных по S&P 500")
    day = ref.index[-1].date()
    indices = []
    for t, label in US_INDICES:
        s = base.get(t)
        if s is not None:
            indices.append((label, float(s.iloc[-1]), (float(s.iloc[-1]) / float(s.iloc[-2]) - 1) * 100))
    extra = []
    for t, label, kind in EXTRA_US:
        s = base.get(t)
        if s is None:
            continue
        s = s[s.index.date <= day]
        if len(s) < 2:
            continue
        p, q = float(s.iloc[-1]), float(s.iloc[-2])
        extra.append((label, p, q, kind))
    movers = []
    if names:
        st = yf_closes(list(names.keys()), period="7d")
        for t, s in st.items():
            if s.index[-1].date() != day:
                continue
            movers.append((short_us(names[t]), (float(s.iloc[-1]) / float(s.iloc[-2]) - 1) * 100))
    movers.sort(key=lambda x: x[1], reverse=True)
    gain = [m for m in movers[:5] if m[1] > 0]
    lose = [m for m in reversed(movers[-5:]) if m[1] < 0]
    return {"day": day.isoformat(), "indices": indices, "extra": extra, "gain": gain, "lose": lose, "universe": len(movers)}


def extras_uae():
    base = yf_closes([t for t, _, _ in EXTRA_UAE])
    out = []
    for t, label, kind in EXTRA_UAE:
        s = base.get(t)
        if s is not None:
            out.append((label, float(s.iloc[-1]), float(s.iloc[-2]), kind))
    return out


def prev_uae_day(now):
    d = now.date() - dt.timedelta(days=1)
    while d.weekday() >= 5:  # ОАЭ торгуют пн-пт
        d -= dt.timedelta(days=1)
    return d


# ───────── форматирование ─────────

def num(v, d=2):
    s = f"{abs(v):,.{d}f}".replace(",", NB).replace(".", ",")
    return (MINUS if v < 0 else "") + s


def pct(v):
    return ("+" if v >= 0 else MINUS) + num(abs(v), 2) + "%"


def extra_cells(extra):
    cells = []
    for label, p, q, kind in extra:
        if kind == "yield":
            bp = round((p - q) * 100)
            ch = ("+" if bp > 0 else MINUS if bp < 0 else "") + f"{abs(bp)} б.п."
            cells.append((label, num(p, 2) + "%", ch, bp < 0))
        elif kind == "fx":
            c = (p / q - 1) * 100
            cells.append((label, num(p, 4), pct(c).replace(",00", ",0"), c < 0))
        else:
            c = (p / q - 1) * 100
            cells.append((label, num(p, 2 if p < 1000 else 0) + " $", ("+" if c >= 0 else MINUS) + num(abs(c), 1) + "%", c < 0))
    return cells


def date_ru(d):
    return f"{WD[d.weekday()]}, {d.day} {MON[d.month - 1]}"


# ───────── отрисовка ─────────

W, H = 1080, 1920
INK = (14, 24, 38); NAVY = (27, 47, 74); SAND = (201, 178, 138); STONE = (236, 231, 221); STONE2 = (214, 206, 192)
WHITE = (255, 255, 255); GREY = (184, 194, 207); RED = (226, 120, 100); BRICK = (154, 63, 48)
M = 64
SIG = "@aleksandr_markets · WhatsApp +971 58 508 5260"
TH = {"navy": dict(bg=INK, tile=NAVY, tx=WHITE, mut=GREY, up=SAND, upt=INK, dn=BRICK, dnt=WHITE, line=(44, 58, 84), uptx=SAND, dntx=RED, ov=0.74),
      "stone": dict(bg=STONE, tile=WHITE, tx=INK, mut=(95, 105, 120), up=NAVY, upt=WHITE, dn=BRICK, dnt=WHITE, line=STONE2, uptx=NAVY, dntx=BRICK, ov=0.84)}
FW = {400: "Rubik_400Regular.ttf", 500: "Rubik_500Medium.ttf", 600: "Rubik_600SemiBold.ttf", 700: "Rubik_700Bold.ttf"}
_fc = {}


def font(w, s):
    k = (w, s)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(os.path.join(FONTS, FW[w]), s)
    return _fc[k]


def tw(d, s, f):
    return d.textlength(s, font=f)


def fit(d, s, w, size, maxw):
    while size > 22 and tw(d, s, font(w, size)) > maxw:
        size -= 2
    return font(w, size)


def T(d, xy, s, f, c, anchor="la"):
    d.text(xy, s, font=f, fill=c, anchor=anchor)


def background(prefix, theme, day):
    files = sorted(f for f in os.listdir(BG) if f.startswith(prefix)) if os.path.isdir(BG) else []
    t = TH[theme]
    if not files:
        return Image.new("RGB", (W, H), t["bg"])
    im = Image.open(os.path.join(BG, files[day.toordinal() % len(files)])).convert("RGB")
    r = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(2))
    return Image.blend(im, Image.new("RGB", (W, H), t["bg"]), t["ov"])


def chip(d, xr, yc, v, t, size=52, h=80):
    s = pct(v)
    f = font(700, size)
    w = tw(d, s, f) + 40
    d.rectangle([xr - w, yc - h / 2, xr, yc + h / 2], fill=t["up"] if v >= 0 else t["dn"])
    T(d, (xr - 20, yc), s, f, t["upt"] if v >= 0 else t["dnt"], anchor="rm")


def story(theme, bg_prefix, day, kick, date, indices, gain, lose, cells, source):
    t = TH[theme]
    img = background(bg_prefix, theme, day)
    d = ImageDraw.Draw(img)
    T(d, (M, 240), kick, font(600, 34), t["mut"])
    T(d, (M, 290), date, fit(d, date, 700, 84, W - 2 * M), t["tx"])
    y, th = 410, 160
    for name, lvl, ch in indices:
        d.rectangle([M, y, W - M, y + th - 14], fill=t["tile"])
        T(d, (M + 30, y + 20), name, font(600, 36), t["mut"])
        T(d, (M + 30, y + th - 32), num(lvl, 2), font(700, 60), t["tx"], anchor="ls")
        chip(d, W - M - 26, y + (th - 14) / 2, ch, t)
        y += th
    y += 26
    cw, rh = (W - 2 * M - 28) // 2, 84
    for col, (title, rows, isup) in enumerate([("ВЫРОСЛИ", gain, True), ("УПАЛИ", lose, False)]):
        x = M + col * (cw + 28)
        d.rectangle([x, y, x + cw, y + 60], fill=t["up"] if isup else t["dn"])
        T(d, (x + 22, y + 30), title, font(700, 34), t["upt"] if isup else t["dnt"], anchor="lm")
        yy = y + 60
        for nm, ch in rows:
            d.line([(x, yy + rh), (x + cw, yy + rh)], fill=t["line"], width=2)
            T(d, (x + 4, yy + rh / 2), nm, fit(d, nm, 600, 38, cw - 185), t["tx"], anchor="lm")
            T(d, (x + cw - 4, yy + rh / 2), pct(ch), font(700, 42), t["uptx"] if isup else t["dntx"], anchor="rm")
            yy += rh
        if not rows:
            T(d, (x + 4, yy + rh / 2), "нет", font(500, 36), t["mut"], anchor="lm")
    y = y + 60 + 5 * rh + 26
    if cells:
        n = len(cells)
        gw = (W - 2 * M - (n - 1) * 16) / n
        for i, (nm, val, ch, neg) in enumerate(cells):
            x = M + i * (gw + 16)
            d.rectangle([x, y, x + gw, y + 150], fill=t["tile"])
            T(d, (x + 18, y + 20), nm, font(600, 28), t["mut"])
            T(d, (x + 18, y + 64), val, fit(d, val, 700, 44, gw - 30), t["tx"])
            T(d, (x + 18, y + 112), ch, font(600, 30), t["dntx"] if neg else t["uptx"])
    disc = "Информационные материалы, не является инвестиционной рекомендацией"
    T(d, (M, H - 250), source, fit(d, source, 400, 26, W - 2 * M), t["mut"])
    T(d, (M, H - 212), disc, fit(d, disc, 400, 26, W - 2 * M), t["mut"])
    T(d, (M, H - 170), SIG, font(600, 30), t["tx"])
    return img


# ───────── режимы ─────────

def probe():
    res = {"at": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        rows = uae_stocks()
        res["uae_rows"] = len(rows)
        res["uae_top_by_cap"] = rows[:25]
        res["uae_big"] = len([r for r in rows if (r["cap"] or 0) >= MIN_CAP_AED])
    except Exception as e:  # noqa: BLE001
        res["uae_error"] = str(e)
    res["uae_index_candidates"] = uae_index_candidates()
    try:
        res["uae_indices"] = tv_symbols(["ADX:FADGI", "DFM:DFMGI", "DFM:DFMREI", "DFM:DFMRE", "DFM:DFMRES", "DFM:REAL ESTATE"])
    except Exception as e:  # noqa: BLE001
        res["uae_indices_error"] = str(e)
    try:
        u = us_data()
        res["us"] = {k: (v if k != "extra" else [list(x) for x in v]) for k, v in u.items()}
    except Exception as e:  # noqa: BLE001
        res["us_error"] = str(e)
    os.makedirs(AM, exist_ok=True)
    with open(os.path.join(AM, "probe.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    log(json.dumps(res, ensure_ascii=False, default=str)[:3000])


def render():
    now = dt.datetime.now(DXB)
    os.makedirs(OUT, exist_ok=True)
    plan = {"made_at": now.isoformat(), "stories": []}
    # ОАЭ
    try:
        u = uae_data()
        uday = prev_uae_day(now)
        cells = [(l, v, c, n) for l, v, c, n in extra_cells(extras_uae())] + [("USD/AED", "3,6725", "привязка", False)]
        img = story("navy", "uae", uday, "ИТОГИ ТОРГОВ · ОАЭ", date_ru(uday), u["indices"], u["gain"], u["lose"], cells,
                    f"Закрытие торгов ADX и DFM, {uday.strftime('%d.%m.%Y')}. Лидеры среди компаний дороже 5 млрд AED")
        p = f"am/out/{uday.isoformat()}_uae.png"
        img.save(os.path.join(ROOT, p))
        plan["stories"].append({"id": f"uae-{uday.isoformat()}", "path": p})
        log(f"ОАЭ: {p}, бумаг в выборке {u['universe']}, индексов {len(u['indices'])}")
    except Exception as e:  # noqa: BLE001
        log("ОАЭ не собрана:", e)
    # США
    try:
        s = us_data()
        sday = dt.date.fromisoformat(s["day"])
        if (now.date() - sday).days > 4:
            raise RuntimeError(f"данные устарели: {sday}")
        img = story("stone", "us", sday, "ИТОГИ ТОРГОВ · США", date_ru(sday), s["indices"], s["gain"], s["lose"], extra_cells(s["extra"]),
                    f"Закрытие торгов NYSE и Nasdaq, {sday.strftime('%d.%m.%Y')}. Лидеры среди компаний S&P 500")
        p = f"am/out/{sday.isoformat()}_us.png"
        img.save(os.path.join(ROOT, p))
        plan["stories"].append({"id": f"us-{sday.isoformat()}", "path": p})
        log(f"США: {p}, бумаг в выборке {s['universe']}")
    except Exception as e:  # noqa: BLE001
        log("США не собраны:", e)
    with open(os.path.join(OUT, "today.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)
    # чистим картинки старше 21 дня
    cutoff = (now.date() - dt.timedelta(days=21)).isoformat()
    for fn in os.listdir(OUT):
        if fn.endswith(".png") and fn[:10] < cutoff:
            os.remove(os.path.join(OUT, fn))


def check(resp, what):
    try:
        js = resp.json()
    except Exception:  # noqa: BLE001
        js = {"raw": resp.text[:300]}
    if resp.status_code != 200 or "error" in js:
        raise RuntimeError(f"{what}: HTTP {resp.status_code} {json.dumps(js.get('error', js), ensure_ascii=False)[:400]}")
    return js


def paused():
    try:
        until = dt.datetime.fromisoformat(open(os.path.join(AM, "pause_until.txt")).read().strip())
        if until.tzinfo is None:
            until = until.replace(tzinfo=DXB)
        return until if dt.datetime.now(dt.timezone.utc) < until else None
    except Exception:  # noqa: BLE001
        return None


def load_state():
    p = os.path.join(AM, "state_stories.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"posted": []}


def save_state(st):
    with open(os.path.join(AM, "state_stories.json"), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def publish():
    dry = os.environ.get("DRY_RUN", "").lower() in ("yes", "1", "true")
    live = os.path.exists(os.path.join(AM, "LIVE"))
    token = os.environ.get("IG_TOKEN_AM") or os.environ.get("IG_TOKEN", "")
    uid = os.environ.get("IG_USER_ID_AM", "")
    sha = os.environ.get("PUBLISH_SHA") or os.environ.get("GITHUB_SHA", "main")
    plan = json.load(open(os.path.join(OUT, "today.json"), encoding="utf-8"))
    st = load_state()
    done = {p["id"] for p in st["posted"]}
    todo = [s for s in plan["stories"] if s["id"] not in done]
    for s in todo:
        log(f"{s['id']}: https://raw.githubusercontent.com/{REPO}/{sha}/{s['path']}")
    if not todo:
        log("Новых сторис нет")
        return 0
    if dry or not live or not token or not uid:
        log("Публикации нет: " + ("dry-run" if dry else "нет файла am/LIVE" if not live else "нет секрета IG_USER_ID_AM или токена"))
        return 0
    if paused():
        log(f"Пауза до {paused().isoformat()}")
        return 0
    for s in todo:
        url = f"https://raw.githubusercontent.com/{REPO}/{sha}/{s['path']}"
        entry = {"id": s["id"], "at": dt.datetime.now(dt.timezone.utc).isoformat()}
        try:
            c = check(requests.post(f"{IG}/{uid}/media", data={"image_url": url, "media_type": "STORIES", "access_token": token}, timeout=60),
                      "контейнер")
            for _ in range(24):
                time.sleep(5)
                stt = check(requests.get(f"{IG}/{c['id']}", params={"fields": "status_code", "access_token": token}, timeout=30), "статус")
                if stt.get("status_code") in ("FINISHED", "ERROR", "EXPIRED"):
                    break
            if stt.get("status_code") != "FINISHED":
                raise RuntimeError(f"контейнер {stt}")
            p = check(requests.post(f"{IG}/{uid}/media_publish", data={"creation_id": c["id"], "access_token": token}, timeout=60), "публикация")
            entry["post"] = p["id"]
            log(f"Опубликовано {s['id']}: {p['id']}")
        except Exception as e:  # noqa: BLE001
            # Правило из инструкции: после ошибки сторис не повторяем (Instagram мог её всё же опубликовать)
            entry["post"] = "error"
            entry["error"] = str(e)[:300]
            log(f"Ошибка {s['id']}: {e}")
        st["posted"].append(entry)
        save_state(st)
        time.sleep(20)
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "render"
    sys.exit({"probe": probe, "render": render, "publish": publish}[mode]() or 0)
