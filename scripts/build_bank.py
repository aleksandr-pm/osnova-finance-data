"""OSNOVA Finance: сборка банка рейтингов из открытых данных.

Источники: World Bank WDI (API), FAOSTAT (bulk-выгрузки).
Результат:
  bank/rankings.json   все рейтинги
  bank/threads.md      готовые тексты Threads
  bank/cards/*.png     карточки 1080x1350
"""
import io
import json
import os
import sys
import time
import zipfile
from collections import defaultdict

import pandas as pd
import pycountry
import requests
from babel import Locale

sys.path.insert(0, os.path.dirname(__file__))
from fmt import fmt_value, flag  # noqa: E402
from render import render_card  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "bank")
CACHE = os.path.join(ROOT, ".cache")
os.makedirs(os.path.join(OUT, "cards"), exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

MIN_YEAR = 2022  # старее данные в банк не берём
UA = {"User-Agent": "osnova-finance-data-builder/1.0"}

# ---------------------------------------------------------------- страны
RU_NAMES = Locale("ru").territories
OVERRIDE = {
    "US": "США", "GB": "Великобритания", "AE": "ОАЭ", "RU": "Россия",
    "KR": "Южная Корея", "KP": "КНДР", "CD": "ДР Конго", "CG": "Республика Конго",
    "HK": "Гонконг", "MO": "Макао", "TW": "Тайвань", "CZ": "Чехия",
    "BA": "Босния и Герцеговина", "CI": "Кот-д’Ивуар", "MM": "Мьянма",
    "VN": "Вьетнам", "LA": "Лаос", "IR": "Иран", "SY": "Сирия", "TZ": "Танзания",
    "BO": "Боливия", "VE": "Венесуэла", "MK": "Северная Македония",
    "MD": "Молдова", "PS": "Палестина", "DO": "Доминиканская Республика",
    "CF": "ЦАР", "SA": "Саудовская Аравия", "NZ": "Новая Зеландия",
    "ZA": "ЮАР", "PG": "Папуа-Новая Гвинея",
    "TL": "Восточный Тимор", "XK": "Косово", "CV": "Кабо-Верде",
    "SZ": "Эсватини", "TR": "Турция", "KG": "Киргизия", "BY": "Беларусь",
}
# аудитория: страны, чьё место показываем отдельной строкой
CIS_HOOK = ["RU", "KZ", "UZ", "BY", "AZ", "AM", "GE", "KG", "TJ", "MD", "TM"]
EX_USSR = ["RU", "UA", "BY", "MD", "KZ", "UZ", "KG", "TJ", "TM",
           "AZ", "AM", "GE", "LT", "LV", "EE"]


def ru_name(iso2, fallback=""):
    if iso2 in OVERRIDE:
        return OVERRIDE[iso2]
    return RU_NAMES.get(iso2, fallback or iso2)


def m49_to_iso2(m49):
    m49 = str(m49).strip().strip("'").zfill(3)
    c = pycountry.countries.get(numeric=m49)
    return c.alpha_2 if c else None


# ---------------------------------------------------------------- утилиты
def log(*a):
    print(*a, flush=True)


def get(url, **kw):
    for attempt in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=kw.pop("timeout", 120), **kw)
            if r.status_code == 200:
                return r
            log(f"  HTTP {r.status_code} {url}")
        except Exception as e:  # noqa: BLE001
            log(f"  ошибка {e} {url}")
        time.sleep(5 * (attempt + 1))
    return None


def pick_year(by_year):
    """Последний год, где стран не меньше 70% от максимума за период."""
    if not by_year:
        return None
    mx = max(len(v) for v in by_year.values())
    for y in sorted(by_year, reverse=True):
        if len(by_year[y]) >= 0.7 * mx and len(by_year[y]) >= 10:
            return y
    return None


def make_ranking(rid, block, title, unit, year, source, source_full, values,
                 asc=False, note="", hook=True):
    """values: dict iso2 -> number (или name -> number при отсутствии iso)."""
    rows = sorted(values.items(), key=lambda kv: kv[1], reverse=not asc)
    full = [{"iso2": k, "name": ru_name(k), "value": v, "flag": flag(k),
             "text": fmt_value(v, unit)} for k, v in rows]
    for i, r in enumerate(full, 1):
        r["rank"] = i
    cis = []
    if hook:
        for r in full[5:60]:
            if r["iso2"] in CIS_HOOK:
                cis.append({"name": r["name"], "rank": r["rank"], "in_top10": r["rank"] <= 10})
            if len(cis) == 3:
                break
    return {
        "id": rid, "block": block, "title": title, "unit": unit, "year": int(year),
        "source": source, "source_full": source_full, "note": note,
        "countries": len(full), "top": full[:10], "cis": cis,
    }


# ---------------------------------------------------------------- World Bank
WDI = [
    # код, блок, заголовок, единица, asc, фильтр населения
    ("NY.GDP.MKTP.CD", "economy", "Крупнейшие экономики мира по ВВП", "usd", False, False),
    ("NY.GDP.MKTP.PP.CD", "economy", "Крупнейшие экономики по ВВП с учётом паритета покупательной способности", "usd", False, False),
    ("NY.GDP.PCAP.CD", "economy", "Самый высокий ВВП на душу населения", "usd_pc", False, True),
    ("NY.GDP.MKTP.KD.ZG", "economy", "Самый быстрый рост экономики", "pct", False, True),
    ("SL.UEM.TOTL.ZS", "economy", "Самая высокая безработица", "pct", False, True),
    ("SL.UEM.TOTL.ZS", "economy", "Самая низкая безработица", "pct", True, True),
    ("NY.GNS.ICTR.ZS", "economy", "Больше всех сберегают: валовые сбережения в % от ВВП", "pct", False, True),
    ("GC.TAX.TOTL.GD.ZS", "economy", "Самая высокая налоговая нагрузка: налоги в % от ВВП", "pct", False, True),
    ("FI.RES.TOTL.CD", "money", "Крупнейшие резервы страны, включая золото", "usd", False, False),
    ("CM.MKT.LCAP.CD", "money", "Крупнейшие фондовые рынки по капитализации компаний", "usd", False, False),
    ("BX.KLT.DINV.CD.WD", "money", "Больше всего прямых иностранных инвестиций", "usd", False, False),
    ("BX.TRF.PWKR.CD.DT", "money", "Больше всего денег получают от мигрантов", "usd", False, False),
    ("BM.TRF.PWKR.CD.DT", "money", "Больше всего денег мигранты отправляют из этих стран", "usd", False, False),
    ("BX.TRF.PWKR.DT.GD.ZS", "money", "Переводы мигрантов в % от ВВП: самые зависимые экономики", "pct", False, True),
    ("NE.EXP.GNFS.CD", "economy", "Крупнейшие экспортёры товаров и услуг", "usd", False, False),
    ("TX.VAL.TECH.CD", "economy", "Крупнейшие экспортёры высоких технологий", "usd", False, False),
    ("BN.CAB.XOKA.GD.ZS", "economy", "Самый большой профицит внешней торговли и доходов, % ВВП", "pct", False, True),
]
WDI_CIS = [
    ("NY.GDP.PCAP.CD", "Страны бывшего СССР: ВВП на душу населения", "usd_pc"),
    ("NY.GDP.MKTP.CD", "Страны бывшего СССР: размер экономики", "usd"),
    ("FP.CPI.TOTL.ZG", "Страны бывшего СССР: инфляция", "pct"),
    ("NY.GDP.MKTP.KD.ZG", "Страны бывшего СССР: рост экономики", "pct"),
    ("BX.TRF.PWKR.DT.GD.ZS", "Страны бывшего СССР: переводы мигрантов в % от ВВП", "pct"),
    ("BX.KLT.DINV.CD.WD", "Страны бывшего СССР: прямые иностранные инвестиции", "usd"),
    ("FI.RES.TOTL.CD", "Страны бывшего СССР: резервы, включая золото", "usd"),
    ("SL.UEM.TOTL.ZS", "Страны бывшего СССР: безработица", "pct"),
]


def wdi_countries():
    r = get("https://api.worldbank.org/v2/country?format=json&per_page=400")
    data = r.json()[1]
    return {c["iso2Code"] for c in data if c["region"]["value"] != "Aggregates"}


def wdi_series(code, real):
    r = get(f"https://api.worldbank.org/v2/country/all/indicator/{code}"
            f"?format=json&per_page=20000&date=2014:2025")
    if r is None:
        return {}
    js = r.json()
    if len(js) < 2 or js[1] is None:
        log(f"  WDI {code}: пусто")
        return {}
    by_year = defaultdict(dict)
    for row in js[1]:
        iso = row["country"]["id"]
        if iso in real and row["value"] is not None:
            by_year[int(row["date"])][iso] = float(row["value"])
    return by_year


def build_wdi():
    out = []
    real = wdi_countries()
    log(f"WDI: стран {len(real)}")
    pop_y = wdi_series("SP.POP.TOTL", real)
    py = max(pop_y) if pop_y else None
    pop = pop_y.get(py, {})
    cache = {}
    for code, block, title, unit, asc, popf in WDI:
        by_year = cache.setdefault(code, wdi_series(code, real))
        y = pick_year(by_year)
        if not y or y < MIN_YEAR:
            log(f"  WDI {code}: нет свежего года ({y})")
            continue
        vals = by_year[y]
        note = ""
        if popf:
            vals = {k: v for k, v in vals.items() if pop.get(k, 0) >= 1_000_000}
            note = "страны с населением от 1 млн"
        rid = f"wdi_{code}_{'asc' if asc else 'desc'}".replace(".", "_").lower()
        out.append(make_ranking(rid, block, title, unit, y, "World Bank",
                                "World Bank, World Development Indicators", vals,
                                asc=asc, note=note))
        log(f"  {rid}: {y}, стран {len(vals)}")
    for code, title, unit in WDI_CIS:
        by_year = cache.setdefault(code, wdi_series(code, real))
        # год, где есть данные хотя бы по 10 из 15
        y = None
        for yy in sorted(by_year, reverse=True):
            if sum(1 for k in EX_USSR if k in by_year[yy]) >= 10:
                y = yy
                break
        if not y or y < MIN_YEAR:
            log(f"  CIS {code}: нет свежего года ({y})")
            continue
        vals = {k: by_year[y][k] for k in EX_USSR if k in by_year[y]}
        rid = f"cis_{code}".replace(".", "_").lower()
        out.append(make_ranking(rid, "cis", title, unit, y, "World Bank",
                                "World Bank, World Development Indicators", vals,
                                hook=False))
        log(f"  {rid}: {y}, стран {len(vals)}")
    return out


# ---------------------------------------------------------------- FAOSTAT
# код товара FAO: родительный падеж
FAO_PROD = {
    15: "пшеницы", 56: "кукурузы", 27: "риса", 44: "ячменя", 236: "соевых бобов",
    656: "кофе", 661: "какао-бобов", 667: "чая", 156: "сахарного тростника",
    116: "картофеля", 515: "яблок", 486: "бананов", 560: "винограда",
    388: "томатов", 267: "подсолнечника", 270: "рапса", 257: "пальмового масла",
    261: "оливкового масла", 564: "вина", 867: "говядины", 1058: "курятины",
    882: "коровьего молока", 1062: "куриных яиц", 767: "хлопка", 572: "авокадо",
    490: "апельсинов", 1182: "мёда", 403: "лука", 221: "миндаля", 225: "фундука",
    223: "фисташек", 268: "подсолнечного масла", 1035: "свинины",
}
FAO_TRADE = {
    15: "пшеницы", 56: "кукурузы", 31: "риса", 44: "ячменя", 236: "соевых бобов",
    656: "кофе", 661: "какао-бобов", 667: "чая", 162: "сахара-сырца",
    268: "подсолнечного масла", 257: "пальмового масла", 261: "оливкового масла",
    564: "вина", 486: "бананов", 515: "яблок", 572: "авокадо",
    767: "хлопка", 270: "рапса",
}
FAO_FILES = {
    "QCL": "https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip",
    "TCL": "https://bulks-faostat.fao.org/production/Trade_CropsLivestock_E_All_Data_(Normalized).zip",
}


def fao_url(code):
    r = get("https://fenixservices.fao.org/faostat/static/bulkdownloads/datasets_E.json")
    if r is not None:
        def walk(o):
            if isinstance(o, dict):
                if o.get("DatasetCode") == code and o.get("FileLocation"):
                    return o["FileLocation"]
                for v in o.values():
                    x = walk(v)
                    if x:
                        return x
            elif isinstance(o, list):
                for v in o:
                    x = walk(v)
                    if x:
                        return x
            return None
        try:
            u = walk(r.json())
            if u:
                return u
        except Exception as e:  # noqa: BLE001
            log(f"  datasets_E.json: {e}")
    return FAO_FILES[code]


def fao_load(code, items, elements):
    path = os.path.join(CACHE, f"{code}.zip")
    if not os.path.exists(path):
        url = fao_url(code)
        log(f"FAO {code}: скачиваю {url}")
        with requests.get(url, headers=UA, stream=True, timeout=900) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for ch in r.iter_content(1 << 20):
                    f.write(ch)
    log(f"FAO {code}: {os.path.getsize(path) // (1 << 20)} МБ")
    zf = zipfile.ZipFile(path)
    name = max((n for n in zf.namelist() if n.endswith(".csv")),
               key=lambda n: zf.getinfo(n).file_size)
    cols = ["Area Code", "Area Code (M49)", "Area", "Item Code", "Item",
            "Element Code", "Year", "Value"]
    parts = []
    for ch in pd.read_csv(zf.open(name), usecols=cols, chunksize=2_000_000,
                          encoding="utf-8", encoding_errors="replace",
                          dtype={"Area Code (M49)": str}, low_memory=False):
        ch = ch[ch["Item Code"].isin(items) & ch["Element Code"].isin(elements)
                & (ch["Year"] >= 2015) & (ch["Area Code"] < 5000)
                & (ch["Area Code"] != 351)]
        parts.append(ch)
    df = pd.concat(parts)
    log(f"FAO {code}: строк после фильтра {len(df)}")
    names = df.groupby("Item Code")["Item"].first().to_dict()
    for k in sorted(names):
        log(f"    товар {k}: {names[k]}")
    return df


def fao_rankings(df, element, mapping, kind, unit, mult):
    out = []
    for item, gen in mapping.items():
        d = df[(df["Item Code"] == item) & (df["Element Code"] == element)
               & (df["Value"] > 0)]
        if d.empty:
            log(f"  FAO {kind} {item}: нет данных")
            continue
        by_year = defaultdict(dict)
        for m49, y, v in zip(d["Area Code (M49)"], d["Year"], d["Value"]):
            iso = m49_to_iso2(m49)
            if iso:
                by_year[int(y)][iso] = by_year[int(y)].get(iso, 0) + float(v) * mult
        y = pick_year(by_year)
        if not y:
            continue
        title = {"prod": f"Крупнейшие производители {gen}",
                 "exp": f"Крупнейшие экспортёры {gen}",
                 "imp": f"Крупнейшие импортёры {gen}"}[kind]
        rk = make_ranking(f"fao_{kind}_{item}", "agro", title, unit, y,
                          "FAOSTAT", "FAOSTAT, ФАО ООН", by_year[y])
        rk["hook_tpl"] = {"prod": f"{{L}} производит больше всех {gen}: [v]",
                          "exp": f"{{L}} продаёт больше всех {gen}: [v]",
                          "imp": f"{{L}} покупает больше всех {gen}: [v]"}[kind]
        out.append(rk)
        log(f"  fao_{kind}_{item}: {y}, стран {len(by_year[y])}")
    return out


def build_fao():
    out = []
    try:
        q = fao_load("QCL", list(FAO_PROD), [5510])
        out += fao_rankings(q, 5510, FAO_PROD, "prod", "t", 1)
        del q
    except Exception as e:  # noqa: BLE001
        log(f"FAO QCL ошибка: {e}")
    try:
        t = fao_load("TCL", list(FAO_TRADE), [5922, 5622])
        out += fao_rankings(t, 5922, FAO_TRADE, "exp", "usd", 1000)
        out += fao_rankings(t, 5622, FAO_TRADE, "imp", "usd", 1000)
    except Exception as e:  # noqa: BLE001
        log(f"FAO TCL ошибка: {e}")
    return out


# ---------------------------------------------------------------- крючки
# {L} страна №1, [v] выделенная цифра
HOOKS = {
    "wdi_ny_gdp_mktp_cd_desc": "{L}: ВВП [v], первое место в мире",
    "wdi_ny_gdp_mktp_pp_cd_desc": "{L}: ВВП по паритету покупательной способности [v], №1 в мире",
    "wdi_ny_gdp_pcap_cd_desc": "{L}: [v] ВВП на человека, больше всех в мире",
    "wdi_ny_gdp_mktp_kd_zg_desc": "{L}: экономика выросла на [v] за год, быстрее всех",
    "wdi_sl_uem_totl_zs_desc": "{L}: безработица [v], самая высокая в мире",
    "wdi_sl_uem_totl_zs_asc": "{L}: безработица всего [v], самая низкая в мире",
    "wdi_ny_gns_ictr_zs_desc": "{L} сберегает [v] ВВП, больше всех в мире",
    "wdi_gc_tax_totl_gd_zs_desc": "{L}: налоги забирают [v] ВВП, больше всех в мире",
    "wdi_fi_res_totl_cd_desc": "{L}: резервы [v], больше всех в мире",
    "wdi_cm_mkt_lcap_cd_desc": "{L}: компании на бирже стоят [v], №1 в мире",
    "wdi_bx_klt_dinv_cd_wd_desc": "{L}: [v] прямых иностранных инвестиций за год, №1 в мире",
    "wdi_bx_trf_pwkr_cd_dt_desc": "{L}: мигранты прислали домой [v] за год, больше всех в мире",
    "wdi_bm_trf_pwkr_cd_dt_desc": "{L}: мигранты отправили отсюда [v] за год, №1 в мире",
    "wdi_bx_trf_pwkr_dt_gd_zs_desc": "{L}: переводы мигрантов равны [v] ВВП, больше всех в мире",
    "wdi_ne_exp_gnfs_cd_desc": "{L}: экспорт [v] за год, №1 в мире",
    "wdi_tx_val_tech_cd_desc": "{L}: экспорт высоких технологий [v], №1 в мире",
    "wdi_bn_cab_xoka_gd_zs_desc": "{L}: профицит [v] ВВП, №1 в мире",
    "cis_ny_gdp_pcap_cd": "{L}: [v] ВВП на человека, №1",
    "cis_ny_gdp_mktp_cd": "{L}: ВВП [v], №1",
    "cis_fp_cpi_totl_zg": "{L}: инфляция [v], самая высокая",
    "cis_ny_gdp_mktp_kd_zg": "{L}: рост экономики [v], быстрее всех",
    "cis_bx_trf_pwkr_dt_gd_zs": "{L}: переводы мигрантов равны [v] ВВП, больше всех",
    "cis_bx_klt_dinv_cd_wd": "{L}: [v] прямых иностранных инвестиций, №1",
    "cis_fi_res_totl_cd": "{L}: резервы [v], №1",
    "cis_sl_uem_totl_zs": "{L}: безработица [v], самая высокая",
}


def make_hook(r):
    tpl = r.pop("hook_tpl", None) or HOOKS.get(r["id"]) or (r["title"] + ": №1 {L}, [v]")
    lead = r["top"][0]
    before, after = tpl.split("[v]")
    before = before.replace("{L}", lead["name"])
    after = after.replace("{L}", lead["name"])
    r["hook"] = [[before.strip(), False], [lead["text"], True], [after.strip(), False]]
    r["hook"] = [x for x in r["hook"] if x[0]]
    r["hook_text"] = (before + lead["text"] + after).strip()


# ---------------------------------------------------------------- тексты
QUESTIONS = [
    "Кто удивил в этом списке?",
    "Кого не хватает в топе, по-вашему?",
    "Кто поднимется выше через 5 лет?",
]


def cis_line(items):
    parts = [f"{c['name']} на {c['rank']}-м" for c in items]
    return parts[0] + " месте" + "".join(", " + p for p in parts[1:]) + "."


def threads_text(r, i):
    lines = [r["hook_text"] + ".", "", f"{r['title']} · {r['year']}"]
    for row in r["top"][:5]:
        lines.append(f"{row['rank']}. {flag(row['iso2'])} {row['name']} · {row['text']}")
    lines.append("")
    hook = [c for c in r["cis"] if c["rank"] > 5]
    if hook:
        lines.append(cis_line(hook))
    lines.append(QUESTIONS[i % len(QUESTIONS)])
    lines.append("")
    lines.append("Полный топ-10 и график в Telegram, ссылка в ответе.")
    lines.append(f"{r['source']} · #данные")
    text = "\n".join(lines)
    if len(text) > 500:
        text = text.replace("\n" + QUESTIONS[i % len(QUESTIONS)], "")
    return text


# ---------------------------------------------------------------- main
def main():
    rankings = []
    rankings += build_wdi()
    rankings += build_fao()
    log(f"Итого рейтингов: {len(rankings)}")
    for i, r in enumerate(rankings):
        make_hook(r)
        r["threads"] = threads_text(r, i)
        r["threads_len"] = len(r["threads"])
        r["card"] = f"cards/{r['id']}.png"
        try:
            render_card(r, os.path.join(OUT, r["card"]), theme=i % 3)
        except Exception as e:  # noqa: BLE001
            log(f"  карточка {r['id']}: {e}")
    with open(os.path.join(OUT, "rankings.json"), "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "threads.md"), "w", encoding="utf-8") as f:
        for r in rankings:
            f.write(f"## {r['id']} ({r['threads_len']} симв.)\n\n{r['threads']}\n\n")
    blocks = defaultdict(int)
    for r in rankings:
        blocks[r["block"]] += 1
    log("По блокам: " + ", ".join(f"{k} {v}" for k, v in sorted(blocks.items())))


if __name__ == "__main__":
    main()
