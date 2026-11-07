"""Рейтинги компаний (companiesmarketcap.com) и миллиардеров (Forbes Real-Time) для Threads и Instagram. v1

Вход: bank/raw_markets/*.csv, forbes_rtb.json (собирает scripts/fetch_markets.py).
Выход: bank/rankings_markets.json, карточки в bank/cards_markets/. Формат записей как у bank/rankings.json.
Блоки: companies, billionaires. Недвижимость не берём (правило проекта).
"""
import csv
import datetime as dt
import json
import os
import sys
import time

import pycountry

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fmt import fmt_value, flag  # noqa: E402
from render import render_card  # noqa: E402

RAW = "bank/raw_markets"
try:
    RE_SYMBOLS = {r["Symbol"] for r in csv.DictReader(open("bank/raw_markets/cmc_realestate.csv", encoding="utf-8"))}
except FileNotFoundError:
    RE_SYMBOLS = set()
OUT = "bank"
CARDS = "cards_markets"
TODAY = dt.date.today()
MON = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
ASOF = f"на {TODAY.day} {MON[TODAY.month - 1]} {TODAY.year}"
MON_N = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]

SPECIAL = {"United States": "US", "South Korea": "KR", "Taiwan": "TW", "Russia": "RU", "Hong Kong": "HK",
           "Czech Republic": "CZ", "Turkey": "TR", "Vietnam": "VN", "United Arab Emirates": "AE", "UAE": "AE",
           "Iran": "IR", "Macau": "MO", "Bermuda": "BM", "Cayman Islands": "KY", "Eswatini": "SZ"}
RU = {"US": "США", "CN": "Китая", "JP": "Японии", "IN": "Индии", "GB": "Великобритании", "DE": "Германии",
      "FR": "Франции", "CH": "Швейцарии", "SA": "Саудовской Аравии", "AE": "ОАЭ", "KR": "Южной Кореи",
      "TW": "Тайваня", "CA": "Канады", "BR": "Бразилии", "NL": "Нидерландов", "IT": "Италии", "ES": "Испании",
      "HK": "Гонконга", "AU": "Австралии", "SG": "Сингапура", "QA": "Катара", "KW": "Кувейта", "TR": "Турции",
      "ID": "Индонезии", "MX": "Мексики", "SE": "Швеции", "DK": "Дании", "NO": "Норвегии", "RU": "России",
      "KZ": "Казахстана", "IL": "Израиля", "ZA": "ЮАР", "PL": "Польши", "FI": "Финляндии", "BE": "Бельгии",
      "TH": "Таиланда", "MY": "Малайзии", "CZ": "Чехии", "AT": "Австрии"}
CIS = {"RU": "Россия", "KZ": "Казахстан", "UZ": "Узбекистан", "AZ": "Азербайджан", "GE": "Грузия", "AM": "Армения", "BY": "Беларусь"}


def iso(country):
    if country in SPECIAL:
        return SPECIAL[country]
    try:
        return pycountry.countries.lookup(country).alpha_2
    except LookupError:
        return ""


import re

STRIP = re.compile(r",?\s+(PJSC|P\.J\.S\.C\.|Public Joint Stock Company|Joint Stock Company|JSC|Inc\.?|Corp\.?|Corporation|Ltd\.?|Limited|plc|PLC|S\.A\.|AG|SE|N\.V\.)$")
REAL_ESTATE_WORDS = re.compile(r"Propert|Real Estate|REIT|Realty|Land\b|Estate|Emaar|Aldar|Damac|Developer|Vonovia|Prologis|Fudosan", re.I)


def short(name):
    m = re.match(r"^(.{3,}?)\s*\(([^)]{2,24})\)$", name)
    if m and len(name) > 26:
        name = m.group(2) if len(m.group(2)) >= 3 else m.group(1)
    if name.upper().startswith("JSC "):
        name = name[4:]
    for _ in range(2):
        name = STRIP.sub("", name).strip()
    return name


def read(name):
    p = os.path.join(RAW, name + ".csv")
    if not os.path.exists(p):
        return []
    out = []
    for r in csv.DictReader(open(p, encoding="utf-8")):
        if r.get("Symbol") in RE_SYMBOLS or REAL_ESTATE_WORDS.search(r.get("Name", "")):
            continue   # недвижимость не публикуем
        r["iso2"] = iso(r.get("country", ""))
        r["Name"] = short(r["Name"])
        out.append(r)
    return out


def record(rid, block, title, rows, unit, source, source_full, hook_tpl, note="", cis_pool=None, text=None):
    """rows: [(name, iso2, value)] уже отсортированы."""
    top = []
    for i, (name, iso2, v) in enumerate(rows[:10], 1):
        top.append({"iso2": iso2, "name": name, "value": v, "flag": flag(iso2) if iso2 else "🌐",
                    "text": text(v) if text else fmt_value(v, unit), "rank": i})
    cis = []
    for i, (name, iso2, v) in enumerate(cis_pool or [], 1):
        if iso2 in CIS and i > 10 and len(cis) < 2 and not any(c["iso"] == iso2 for c in cis):
            cis.append({"name": f"{name} ({CIS[iso2]})", "rank": i, "in_top10": False, "iso": iso2})
    lead = top[0]
    before, after = hook_tpl.split("[v]")
    before, after = before.replace("{L}", lead["name"]), after.replace("{L}", lead["name"])
    hook = [x for x in [[before.strip(), False], [lead["text"], True], [after.strip(), False]] if x[0]]
    return {"hook_tpl": hook_tpl, "id": rid, "block": block, "title": title, "unit": unit, "year": TODAY.year, "source": source,
            "source_full": source_full, "note": note or ASOF, "countries": len(rows), "top": top, "cis": cis,
            "hook": hook, "hook_text": (before + lead["text"] + after).strip(), "type": "bars",
            "period": f"{MON_N[TODAY.month - 1]} {TODAY.year}",
            "card": f"{CARDS}/{rid}.png"}


def employees(v):
    return (f"{v / 1e6:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " млн чел.") if v >= 1e6 else \
        (f"{v / 1e3:.0f}" + " тыс. чел.")


def companies():
    recs = []
    src, full = "CompaniesMarketCap", "companiesmarketcap.com"
    allc = read("cmc_all")
    val = lambda rows, k: [(r["Name"], r["iso2"], float(r[k])) for r in rows if r.get(k) not in (None, "", "0")]
    world = [
        ("cmc_all", "marketcap", "mkt_world_cap", "Самые дорогие компании мира по капитализации", "usd", "Самая дорогая компания мира: {L}, [v]"),
        ("cmc_revenue", "revenue_ttm", "mkt_world_rev", "Крупнейшие компании мира по выручке за 12 месяцев", "usd", "{L}: выручка [v] за год"),
        ("cmc_earnings", "earnings_ttm", "mkt_world_earn", "Самые прибыльные компании мира за 12 месяцев", "usd", "{L} заработала [v] за год"),
        ("cmc_employees", "employees_count", "mkt_world_emp", "Крупнейшие работодатели мира", "num", "В {L} работают [v]"),
    ]
    for f, k, rid, title, unit, hook in world:
        rows = sorted(val(read(f), k), key=lambda x: -x[2])
        if len(rows) >= 10:
            recs.append(record(rid, "companies", title, rows, unit, src, full, hook, cis_pool=rows,
                               text=employees if unit == "num" else None))
    # по странам: капитализация
    by = {}
    for name, iso2, v in sorted(val(allc, "marketcap"), key=lambda x: -x[2]):
        by.setdefault(iso2, []).append((name, iso2, v))
    for c in RU:
        rows = by.get(c, [])
        if len(rows) >= (5 if c in ("KZ", "RU") else 10):
            recs.append(record(f"mkt_country_cap_{c.lower()}", "companies", f"Самые дорогие компании {RU[c]}",
                               rows, "usd", src, full, "№1: {L}, [v]"))
    # по странам: прибыль
    byp = {}
    for name, iso2, v in sorted(val(read("cmc_earnings"), "earnings_ttm"), key=lambda x: -x[2]):
        byp.setdefault(iso2, []).append((name, iso2, v))
    for c in ("US", "CN", "IN", "SA", "AE", "JP", "GB", "DE", "RU", "KZ", "KR", "CH", "FR", "BR", "CA"):
        rows = byp.get(c, [])
        if len(rows) >= (5 if c in ("KZ", "RU", "AE") else 10):
            recs.append(record(f"mkt_country_earn_{c.lower()}", "companies", f"Самые прибыльные компании {RU[c]}",
                               rows, "usd", src, full, "{L}: прибыль [v] за год"))
    # отрасли
    SECT = [("cmc_tech", "Крупнейшие технологические компании"), ("cmc_banks", "Крупнейшие банки мира"),
            ("cmc_oil", "Крупнейшие нефтегазовые компании"), ("cmc_semis", "Крупнейшие производители чипов"),
            ("cmc_pharma", "Крупнейшие фармкомпании"), ("cmc_auto", "Самые дорогие автопроизводители"),
            ("cmc_airlines", "Самые дорогие авиакомпании"), ("cmc_insurance", "Крупнейшие страховые компании"),
            ("cmc_food", "Крупнейшие производители еды"), ("cmc_retail", "Крупнейшие ритейлеры"),
            ("cmc_telecom", "Крупнейшие телеком-операторы"), ("cmc_mining", "Крупнейшие горнодобывающие компании"),
            ("cmc_ai", "Крупнейшие компании в сфере ИИ"), ("cmc_beverages", "Крупнейшие производители напитков"),
            ("cmc_gaming", "Крупнейшие компании видеоигр")]
    for f, title in SECT:
        rows = sorted(val(read(f), "marketcap"), key=lambda x: -x[2])
        if len(rows) >= 10:
            recs.append(record(f"mkt_sector_{f[4:]}", "companies", title + " по капитализации", rows, "usd",
                               src, full, "№1: {L}, [v]", cis_pool=rows))
    # дивиденды среди компаний дороже $10 млрд
    cap = {r["Symbol"]: float(r["marketcap"] or 0) for r in allc}
    div = [(r["Name"], r["iso2"], float(r["dividend_yield_ttm"])) for r in read("cmc_dividend")
           if r.get("dividend_yield_ttm") and cap.get(r["Symbol"], 0) >= 1e10 and 0 < float(r["dividend_yield_ttm"]) <= 25]
    div.sort(key=lambda x: -x[2])
    if len(div) >= 10:
        recs.append(record("mkt_world_div", "companies", "Самая высокая дивидендная доходность среди компаний дороже $10 млрд",
                           div, "pct", src, full, "{L}: [v] годовых дивидендами"))
    return recs


FORBES_IND = {"Technology": "технологий", "Finance & Investments": "финансов и инвестиций", "Fashion & Retail": "моды и ритейла",
              "Food & Beverage": "еды и напитков", "Energy": "энергетики", "Healthcare": "медицины и фармы",
              "Metals & Mining": "металлов и добычи", "Media & Entertainment": "медиа и развлечений", "Automotive": "автопрома",
              "Logistics": "логистики", "Sports": "спорта", "Telecom": "телекома", "Gambling & Casinos": "казино и ставок",
              "Manufacturing": "промышленности", "Diversified": "диверсифицированного бизнеса"}


def billionaires():
    p = os.path.join(RAW, "forbes_rtb.json")
    if not os.path.exists(p):
        return []
    people = json.load(open(p))["personList"]["personsLists"]
    rows_all = []
    for x in people:
        if not x.get("finalWorth") or "Real Estate" in (x.get("industries") or []) or \
                re.search(r"Alabbar|Sajwani|Emaar|Damac|Sobha", (x.get("personName") or "") + " " + (x.get("source") or "")):
            continue
        rows_all.append((x["personName"].replace(" & family", " с семьёй"), iso(x.get("countryOfCitizenship", "")),
                         x["finalWorth"] * 1e6, x.get("industries") or []))
    rows_all.sort(key=lambda r: -r[2])
    src, full = "Forbes", "Forbes Real-Time Billionaires"
    recs = [record("bil_world", "billionaires", "Самые богатые люди мира", [r[:3] for r in rows_all], "usd", src, full,
                   "№1 в мире: {L}, [v]", cis_pool=[r[:3] for r in rows_all])]
    by = {}
    for r in rows_all:
        by.setdefault(r[1], []).append(r[:3])
    for c in ("US", "CN", "IN", "RU", "DE", "FR", "GB", "AE", "KZ", "CA", "HK", "TW", "IT", "BR", "SE", "CH", "JP", "AU", "IL", "SA", "KR"):
        rows = by.get(c, [])
        if len(rows) >= (3 if c in ("KZ", "AE", "SA") else 10):
            recs.append(record(f"bil_country_{c.lower()}", "billionaires", f"Самые богатые люди {RU.get(c, c)}", rows, "usd",
                               src, full, "№1: {L}, [v]"))
    for ind, ru in FORBES_IND.items():
        rows = [r[:3] for r in rows_all if ind in r[3]]
        if len(rows) >= 10:
            recs.append(record(f"bil_ind_{ind.split()[0].lower()}", "billionaires", f"Самые богатые люди из сферы {ru}", rows,
                               "usd", src, full, "№1: {L}, [v]", cis_pool=rows))
    return recs


# ───────── русские названия: Wikidata (метка ru), кеш bank/raw_markets/ru_names.json ─────────
RU_CACHE = os.path.join(RAW, "ru_names.json")
PERSON = re.compile(r"business|entrepreneur|investor|billionaire|executive|heir|founder|magnate|oligarch|engineer|philanthrop|banker|industrialist|manager|CEO", re.I)
COMPANY = re.compile(r"company|bank|corporation|manufacturer|conglomerate|operator|airline|enterprise|group|firm|insurer|retailer|producer|holding|brand|maker|chain|developer of|software|semiconductor|telecom|pharmaceutical|exchange|carrier|utility|automaker", re.I)
CYR = re.compile(r"[А-Яа-яЁё]")


def wikidata_ru(name, person):
    import requests
    H = {"User-Agent": "OSNOVA-Finance-ranking/1.0 (data bank; contact via github aleksandr-pm)"}
    try:
        r = requests.get("https://www.wikidata.org/w/api.php", params={"action": "wbsearchentities", "search": name, "language": "en",
                         "type": "item", "limit": 5, "format": "json"}, headers=H, timeout=20).json()
        for hit in r.get("search", []):
            desc = hit.get("description", "")
            if not (PERSON if person else COMPANY).search(desc):
                continue
            e = requests.get("https://www.wikidata.org/w/api.php", params={"action": "wbgetentities", "ids": hit["id"], "props": "labels",
                             "languages": "ru", "format": "json"}, headers=H, timeout=20).json()
            lab = e["entities"][hit["id"]].get("labels", {}).get("ru", {}).get("value", "")
            return lab if CYR.search(lab) else ""
    except Exception:
        return None
    return ""


def russify(recs):
    try:
        cache = json.load(open(RU_CACHE, encoding="utf-8"))
    except Exception:
        cache = {}
    online = os.environ.get("GITHUB_ACTIONS") == "true"
    asked = 0
    for r in recs:
        person = r["block"] == "billionaires"
        for row in r["top"] + r.get("cis", []):
            base, fam = row["name"], ""
            m = re.match(r"^(.*?)( с семьёй)$", base)
            if m:
                base, fam = m.group(1), m.group(2)
            m2 = re.match(r"^(.*) \(([^)]+)\)$", base) if not person else None   # «Sberbank (Россия)» из строки СНГ
            tail = ""
            if m2 and m2.group(2) in CIS.values():
                base, tail = m2.group(1), f" ({m2.group(2)})"
            key = ("p:" if person else "c:") + base
            if key not in cache and online and asked < 1500:
                v = wikidata_ru(base, person)
                asked += 1
                if v is not None:
                    cache[key] = v
                time.sleep(0.2)
            ru = cache.get(key) or ""
            if ru:
                ru = re.sub(r"\s*\(.*?\)$", "", ru).strip()          # «Тинькофф (банк)» → «Тинькофф»
                if person:   # «Маск, Илон» → «Илон Маск»
                    if "," in ru:
                        a, b = [x.strip() for x in ru.split(",", 1)]
                        ru = f"{b} {a}"
                    ru = " ".join(ru.split()[:3])
                row["name"] = ru + fam + tail
    json.dump(cache, open(RU_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for r in recs:   # вывод в карточке и тексте под новое имя лидера
        lead = r["top"][0]
        r["hook"] = [[seg[0].replace(seg[0], seg[0]), seg[1]] for seg in r["hook"]]
        r["hook_text"] = r["hook_text"]
    print("Wikidata запросов:", asked, "· в кеше:", len(cache))


def main():
    recs = companies() + billionaires()
    russify(recs)
    for r in recs:   # хук пересобираем с русским именем лидера
        tpl = r.pop("hook_tpl")
        lead = r["top"][0]
        before, after = tpl.split("[v]")
        before, after = before.replace("{L}", lead["name"]), after.replace("{L}", lead["name"])
        r["hook"] = [x for x in [[before.strip(), False], [lead["text"], True], [after.strip(), False]] if x[0]]
        r["hook_text"] = (before + lead["text"] + after).strip()
    os.makedirs(os.path.join(OUT, CARDS), exist_ok=True)
    for i, r in enumerate(recs):
        p = os.path.join(OUT, r["card"])
        render_card(r, p, theme=i % 3)
    json.dump(recs, open(os.path.join(OUT, "rankings_markets.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("рейтингов:", len(recs), "· компании:", sum(r["block"] == "companies" for r in recs),
          "· миллиардеры:", sum(r["block"] == "billionaires" for r in recs))


if __name__ == "__main__":
    main()
