"""Разовые выгрузки для роликов @aleksandr_markets. Запуск: push в am/research/request.txt (первая строка = задача).

losers10y  10 000 $ в ноябре 2016 -> сейчас, полная доходность (цены с учётом дивидендов и сплитов, yfinance auto_adjust),
           все компании S&P 500 + крупные бывшие участники. Итог: am/research/losers10y.json
"""
import datetime as dt
import json
import os
import sys

import requests
import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(ROOT, "am", "research")
SP500_CSV = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
EXTRA = {"PARA": "Paramount", "WBA": "Walgreens Boots Alliance", "VFC": "VF Corp", "LUMN": "Lumen Technologies", "M": "Macy's",
         "KSS": "Kohl's", "GPS": "Gap", "AAL": "American Airlines", "XRX": "Xerox", "MOS": "Mosaic", "WDC": "Western Digital",
         "IVZ": "Invesco", "HBI": "Hanesbrands", "NWL": "Newell Brands", "FL": "Foot Locker", "DISH": "DISH Network", "MAT": "Mattel",
         "WU": "Western Union", "CNC": "Centene", "BIIB": "Biogen", "INTC": "Intel", "BA": "Boeing", "MMM": "3M", "WBD": "Warner Bros. Discovery",
         "DXC": "DXC Technology", "LNC": "Lincoln National", "FOSL": "Fossil", "QRVO": "Qorvo", "ALK": "Alaska Air", "UAA": "Under Armour",
         "VIAV": "Viavi", "EL": "Estee Lauder", "PFE": "Pfizer", "VZ": "Verizon", "T": "AT&T", "KHC": "Kraft Heinz", "CVS": "CVS Health",
         "NKE": "Nike", "F": "Ford", "COTY": "Coty", "PRGO": "Perrigo", "TRIP": "Tripadvisor", "SIG": "Signet Jewelers",
         "AAP": "Advance Auto Parts", "SATS": "EchoStar", "GAP": "Gap", "FTR": "Frontier Communications", "NAVI": "Navient",
         "MAC": "Macerich", "SLG": "SL Green", "VNO": "Vornado", "MUR": "Murphy Oil", "WYNN": "Wynn Resorts", "NWSA": "News Corp",
         "FLR": "Fluor", "R": "Ryder", "JWN": "Nordstrom", "URBN": "Urban Outfitters", "TDC": "Teradata", "CHK": "Chesapeake",
         "RRC": "Range Resources", "AN": "AutoNation", "PVH": "PVH", "RL": "Ralph Lauren", "TAP": "Molson Coors", "LEG": "Leggett & Platt",
         "FMC": "FMC", "DLTR": "Dollar Tree", "MHK": "Mohawk", "WHR": "Whirlpool", "IPG": "Interpublic", "CMCSA": "Comcast", "UPS": "UPS", "DOW": "Dow", "SLB": "Schlumberger", "OXY": "Occidental", "APA": "APA", "HAL": "Halliburton"}


def universe():
    res = {}
    try:
        r = requests.get(SP500_CSV, timeout=30)
        for ln in r.text.strip().splitlines()[1:]:
            p = ln.split(",")
            res[p[0].strip().replace(".", "-")] = p[1].strip().strip('"')
    except Exception as e:  # noqa: BLE001
        print("список S&P 500:", e)
    for k, v in EXTRA.items():
        res.setdefault(k, v)
    return res


def losers10y():
    names = universe()
    start = dt.date(2016, 11, 14)
    df = yf.download(list(names), start="2016-11-01", end=dt.date.today().isoformat(), interval="1d",
                     auto_adjust=True, progress=False, group_by="ticker", threads=True)
    rows = []
    for t, n in names.items():
        try:
            s = df[t]["Close"].dropna()
        except Exception:  # noqa: BLE001
            continue
        if len(s) < 100:
            continue
        s0 = s[s.index.date >= start]
        if s0.empty or s.index[0].date() > start + dt.timedelta(days=10):
            continue  # нет истории на начало периода (IPO позже)
        p0, p1 = float(s0.iloc[0]), float(s.iloc[-1])
        rows.append({"ticker": t, "name": n, "start": str(s0.index[0].date()), "end": str(s.index[-1].date()),
                     "p0_adj": p0, "p1": p1, "value_10k": round(10000 * p1 / p0), "ret_pct": round((p1 / p0 - 1) * 100, 1),
                     "min_10k": round(10000 * float(s0.min()) / p0), "max_10k": round(10000 * float(s0.max()) / p0)})
    rows.sort(key=lambda r: r["value_10k"])
    try:
        caps = {}
        for r in rows[:40]:
            try:
                caps[r["ticker"]] = yf.Ticker(r["ticker"]).fast_info.get("marketCap")
            except Exception:  # noqa: BLE001
                pass
        for r in rows:
            r["mcap_now"] = caps.get(r["ticker"])
    except Exception:  # noqa: BLE001
        pass
    os.makedirs(OUTD, exist_ok=True)
    json.dump({"made": dt.datetime.utcnow().isoformat(), "universe": len(names), "computed": len(rows), "rows": rows},
              open(os.path.join(OUTD, "losers10y.json"), "w"), ensure_ascii=False, indent=1)
    for r in rows[:30]:
        print(r["ticker"], r["name"], r["value_10k"], r["ret_pct"])


def spincheck():
    """Проверка, учтены ли выделения (spin-off) в скорректированных ценах Yahoo."""
    out = {}
    cases = {"XRX": ("2016-12-20", "2017-01-12"), "VFC": ("2019-05-15", "2019-05-30"), "DXC": ("2018-05-25", "2018-06-08"),
             "CNDT": ("2016-12-28", "2017-01-12"), "KTB": ("2019-05-20", "2019-05-30"), "PCG": ("2016-11-10", "2016-11-20")}
    for t, (a, b) in cases.items():
        raw = yf.download(t, start=a, end=b, auto_adjust=False, progress=False)
        out[t] = {"rows": [[str(i.date()), float(r["Close"].iloc[0] if hasattr(r["Close"], "iloc") else r["Close"]),
                            float(r["Adj Close"].iloc[0] if hasattr(r["Adj Close"], "iloc") else r["Adj Close"])] for i, r in raw.iterrows()]}
        last = yf.download(t, period="5d", auto_adjust=False, progress=False)
        try:
            out[t]["last"] = float(last["Close"].iloc[-1].iloc[0]) if len(last) else None
        except Exception:  # noqa: BLE001
            out[t]["last"] = None
    json.dump(out, open(os.path.join(OUTD, "spincheck.json"), "w"), indent=1)
    print(json.dumps(out)[:3000])


LOGO_PAGES = {"adia": "Abu Dhabi Investment Authority", "kia": "Kuwait Investment Authority", "pif": "Public Investment Fund",
              "qia": "Qatar Investment Authority", "icd": "Investment Corporation of Dubai", "mubadala": "Mubadala Investment Company",
              "lia": "Libyan Investment Authority", "oia": "Oman Investment Authority", "adfd": "Abu Dhabi Fund for Development",
              "dif": "Dubai Investment Fund"}


def logos():
    """Логотипы фондов из инфобоксов Википедии (PNG 800 px) в am/research/logos/"""
    import re
    H = {"User-Agent": "osnova-research/1.0 (github.com/aleksandr-pm)"}
    import time
    out = os.path.join(OUTD, "logos"); os.makedirs(out, exist_ok=True)
    rp = os.path.join(out, "report.json")
    rep = json.load(open(rp)) if os.path.exists(rp) else {}
    for key, page in LOGO_PAGES.items():
        if isinstance(rep.get(key), dict):
            continue
        time.sleep(4)
        try:
            wt = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "parse", "page": page, "prop": "wikitext", "format": "json", "redirects": 1},
                              headers=H, timeout=30).json()["parse"]["wikitext"]["*"]
            m = re.search(r"\|\s*logo\s*=\s*(?:\[\[)?(?:File:|Image:)?([^\n|\]]+)", wt)
            if not m:
                rep[key] = "нет поля logo: " + " | ".join(l for l in wt.splitlines() if "logo" in l.lower() or "image" in l.lower())[:400]; continue
            fn = m.group(1).strip()
            info = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "query", "titles": "File:" + fn, "prop": "imageinfo",
                                "iiprop": "url", "iiurlwidth": 800, "format": "json"}, headers=H, timeout=30).json()
            pg = list(info["query"]["pages"].values())[0]
            if "imageinfo" not in pg:
                rep[key] = "нет файла: " + fn; continue
            ii = pg["imageinfo"][0]
            url = ii.get("thumburl") or ii["url"]
            img = requests.get(url.split("?")[0], headers=H, timeout=30)
            if img.content[:15].lower().startswith(b"<!doctype"):
                rep[key] = "html вместо картинки: " + url; continue
            ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
            with open(os.path.join(out, f"{key}.{ext}"), "wb") as f:
                f.write(img.content)
            rep[key] = {"file": fn, "url": url, "bytes": len(img.content)}
        except Exception as e:  # noqa: BLE001
            rep[key] = f"ошибка: {e}"
    # запасной путь: поиск файла логотипа в Commons и en.wikipedia
    for key, page in LOGO_PAGES.items():
        if isinstance(rep.get(key), dict):
            continue
        for site in ("https://commons.wikimedia.org/w/api.php", "https://en.wikipedia.org/w/api.php"):
            time.sleep(4)
            try:
                res = requests.get(site, params={"action": "query", "list": "search", "srsearch": (page if key != "oia" else "Oman Investment Authority OIA") + " logo", "srnamespace": 6, "srlimit": 5,
                                                 "format": "json"}, headers=H, timeout=30).json()["query"]["search"]
                hits = [h["title"] for h in res if "logo" in h["title"].lower()]
                if not hits:
                    continue
                info = requests.get(site, params={"action": "query", "titles": hits[0], "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 800,
                                                  "format": "json"}, headers=H, timeout=30).json()
                ii = list(info["query"]["pages"].values())[0]["imageinfo"][0]
                url = ii.get("thumburl") or ii["url"]
                img = requests.get(url.split("?")[0], headers=H, timeout=30)
                ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
                with open(os.path.join(out, f"{key}.{ext}"), "wb") as f:
                    f.write(img.content)
                rep[key] = {"file": hits[0], "url": url, "bytes": len(img.content), "via": "search"}
                break
            except Exception as e:  # noqa: BLE001
                rep[key] = f"поиск: {e}"
    json.dump(rep, open(rp, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))

BUILDING_Q = {
    "adia": ["ADIA Headquarters Abu Dhabi", "Abu Dhabi Investment Authority tower", "ADIA tower Corniche"],
    "kia": ["Kuwait Investment Authority building", "Kuwait City skyline", "Liberation Tower Kuwait"],
    "pif": ["PIF Tower Riyadh", "King Abdullah Financial District Riyadh", "Public Investment Fund tower"],
    "qia": ["Qatar Investment Authority headquarters", "Doha West Bay skyline", "Doha Corniche skyline"],
    "icd": ["ICD Brookfield Place Dubai", "Dubai International Financial Centre", "DIFC Gate Building"],
    "mubadala": ["Mubadala Tower Abu Dhabi", "Al Maryah Island towers", "Abu Dhabi Global Market Square"],
    "dif": ["Emirates Towers Dubai", "Dubai skyline Sheikh Zayed Road", "Dubai World Trade Centre tower"],
    "lia": ["Tripoli Tower Libya", "Tripoli Libya skyline", "Burj al Fateh Tripoli"],
    "oia": ["Oman Investment Authority building", "Muscat Oman city", "Muttrah Corniche Muscat"],
    "adfd": ["Abu Dhabi Fund for Development building", "Abu Dhabi Corniche skyline", "Abu Dhabi skyline"],
}


def extra():
    """Добор: точечные фото ADIA/Mubadala/ICD и логотип OIA с сайта фонда"""
    global BUILDING_Q
    BUILDING_Q = {"adia": ["ADIA Headquarters", "Abu Dhabi Investment Authority", "ADIA building Corniche Abu Dhabi"],
                  "mubadala": ["Mubadala Tower", "Al Sila Tower", "Al Maryah Island", "Sowwah Square Abu Dhabi"],
                  "icd": ["The Gate Dubai", "Gate Village DIFC", "DIFC Dubai gate"]}
    buildings(tag="extra")
    import re, time
    H = {"User-Agent": "Mozilla/5.0 (osnova-research)"}
    rep = {}
    for site in ("https://www.oia.gov.om/", "https://oia.gov.om/", "https://www.oia.om/"):
        try:
            time.sleep(2)
            r = requests.get(site, headers=H, timeout=30); html = r.text
            cands = re.findall(r'(?:src|href)=["\']([^"\']*logo[^"\']*\.(?:svg|png|jpg|webp))', html, re.I)
            rep[site] = {"status": r.status_code, "cands": cands[:10]}
            for i, c in enumerate(cands[:4]):
                u = requests.compat.urljoin(r.url, c)
                im = requests.get(u, headers=H, timeout=30)
                ext = u.rsplit(".", 1)[-1].lower()
                open(os.path.join(OUTD, "logos", f"oia_site{i}.{ext}"), "wb").write(im.content)
                rep[site].setdefault("saved", []).append([u, len(im.content)])
            if cands: break
        except Exception as e:  # noqa: BLE001
            rep[site] = str(e)
    json.dump(rep, open(os.path.join(OUTD, "logos", "oia_site.json"), "w"), ensure_ascii=False, indent=1)
    print(rep)


def salik():
    """Цена акции Salik (DFM) с IPO + логотип из Википедии"""
    import yfinance as yf, time, re
    out = os.path.join(OUTD, "salik"); os.makedirs(out, exist_ok=True)
    rep = {}
    for t in ("SALIK.AE",):
        try:
            h = yf.Ticker(t).history(period="max", interval="1d", auto_adjust=False)
            h = h[["Close", "Volume"]]; h.index = h.index.strftime("%Y-%m-%d")
            h.to_csv(os.path.join(out, "price.csv")); rep["price_rows"] = len(h); rep["last"] = [h.index[-1], float(h["Close"].iloc[-1])]
        except Exception as e:  # noqa: BLE001
            rep["yf_err"] = str(e)
    try:
        sc = requests.post("https://scanner.tradingview.com/uae/scan", json={"symbols": {"tickers": ["DFM:SALIK"]},
                           "columns": ["close", "market_cap_basic", "dividend_yield_recent", "Perf.Y", "Perf.YTD", "Perf.All", "price_earnings_ttm"]}, timeout=30).json()
        rep["tv"] = sc
    except Exception as e:  # noqa: BLE001
        rep["tv_err"] = str(e)
    H = {"User-Agent": "osnova-research/1.0 (github.com/aleksandr-pm)"}
    try:
        wt = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "parse", "page": "Salik (road toll)", "prop": "wikitext", "format": "json", "redirects": 1},
                          headers=H, timeout=30).json()["parse"]["wikitext"]["*"]
        m = re.search(r"\|\s*(?:logo|image)\s*=\s*(?:\[\[)?(?:File:|Image:)?([^\n|\]]+)", wt)
        rep["wiki_logo_field"] = m.group(1).strip() if m else None
        cands = [m.group(1).strip()] if m else []
        time.sleep(3)
        res = requests.get("https://commons.wikimedia.org/w/api.php", params={"action": "query", "list": "search", "srsearch": "Salik logo", "srnamespace": 6, "srlimit": 10, "format": "json"},
                           headers=H, timeout=30).json()["query"]["search"]
        rep["commons"] = [x["title"] for x in res]
        cands += [x["title"].replace("File:", "") for x in res if "salik" in x["title"].lower()]
        for i, fn in enumerate(cands[:3]):
            time.sleep(3)
            for site in ("https://en.wikipedia.org/w/api.php", "https://commons.wikimedia.org/w/api.php"):
                info = requests.get(site, params={"action": "query", "titles": "File:" + fn, "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 1000, "format": "json"}, headers=H, timeout=30).json()
                pg = list(info["query"]["pages"].values())[0]
                if "imageinfo" in pg:
                    u = (pg["imageinfo"][0].get("thumburl") or pg["imageinfo"][0]["url"]).split("?")[0]
                    open(os.path.join(out, f"logo{i}." + u.rsplit(".", 1)[-1].lower()), "wb").write(requests.get(u, headers=H, timeout=30).content)
                    rep.setdefault("logos", []).append([fn, u]); break
    except Exception as e:  # noqa: BLE001
        rep["logo_err"] = str(e)
    for site in ("https://www.salik.ae/en", "https://www.salik.ae/"):
        try:
            r = requests.get(site, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            c = re.findall(r'(?:src|href)=["\']([^"\']*logo[^"\']*\.(?:svg|png|webp|jpg))', r.text, re.I)
            rep["site"] = {"status": r.status_code, "cands": c[:8]}
            for i, cc in enumerate(c[:3]):
                u = requests.compat.urljoin(r.url, cc)
                open(os.path.join(out, f"site{i}." + u.rsplit(".", 1)[-1].lower()), "wb").write(requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).content)
            if c: break
        except Exception as e:  # noqa: BLE001
            rep["site_err"] = str(e)
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(rep)


def buildings(tag="report"):
    """Фото зданий фондов из Wikimedia Commons (JPEG 1600 px, до 2 на запрос) в am/research/buildings/ + логотип OIA через Wikidata"""
    import time
    H = {"User-Agent": "osnova-research/1.0 (github.com/aleksandr-pm)"}
    out = os.path.join(OUTD, "buildings"); os.makedirs(out, exist_ok=True)
    rep = {}
    api = "https://commons.wikimedia.org/w/api.php"
    for key, qs in BUILDING_Q.items():
        rep[key] = []; n = 0
        for q in qs:
            time.sleep(3)
            try:
                r = requests.get(api, params={"action": "query", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6,
                                              "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600,
                                              "format": "json"}, headers=H, timeout=30).json()
                pages = sorted(r.get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 99))
                got = 0
                for pg in pages:
                    ii = (pg.get("imageinfo") or [{}])[0]
                    if ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 1200:
                        continue
                    time.sleep(2)
                    img = requests.get(ii["thumburl"].split("?")[0], headers=H, timeout=60)
                    if img.content[:3] != b"\xff\xd8\xff":
                        continue
                    fn = f"{key}_{n}.jpg"; n += 1; got += 1
                    open(os.path.join(out, fn), "wb").write(img.content)
                    em = ii.get("extmetadata", {})
                    rep[key].append({"f": fn, "q": q, "title": pg["title"], "w": ii["width"], "h": ii["height"],
                                     "lic": em.get("LicenseShortName", {}).get("value"), "artist": em.get("Artist", {}).get("value", "")[:120]})
                    if got >= 2:
                        break
            except Exception as e:  # noqa: BLE001
                rep[key].append({"q": q, "err": str(e)})
    # логотип OIA: Wikidata P154, затем ar.wikipedia
    oia = {}
    try:
        time.sleep(3)
        s = requests.get("https://www.wikidata.org/w/api.php", params={"action": "wbsearchentities", "search": "Oman Investment Authority", "language": "en",
                                                                      "format": "json"}, headers=H, timeout=30).json()["search"]
        oia["ids"] = [x["id"] for x in s[:3]]
        for qid in oia["ids"]:
            time.sleep(3)
            ent = requests.get("https://www.wikidata.org/wiki/Special:EntityData/%s.json" % qid, headers=H, timeout=30).json()["entities"][qid]
            cl = ent.get("claims", {}).get("P154")
            if cl:
                fn = cl[0]["mainsnak"]["datavalue"]["value"]
                info = requests.get(api, params={"action": "query", "titles": "File:" + fn, "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 800,
                                                 "format": "json"}, headers=H, timeout=30).json()
                ii = list(info["query"]["pages"].values())[0]["imageinfo"][0]
                url = (ii.get("thumburl") or ii["url"]).split("?")[0]
                img = requests.get(url, headers=H, timeout=30)
                ext = url.rsplit(".", 1)[-1].lower()
                os.makedirs(os.path.join(OUTD, "logos"), exist_ok=True)
                open(os.path.join(OUTD, "logos", "oia." + ext), "wb").write(img.content)
                oia["logo"] = {"qid": qid, "file": fn, "url": url}
                break
    except Exception as e:  # noqa: BLE001
        oia["err"] = str(e)
    if "logo" not in oia:
        try:
            time.sleep(3)
            res = requests.get(api, params={"action": "query", "list": "search", "srsearch": "Oman Investment Authority", "srnamespace": 6, "srlimit": 10,
                                            "format": "json"}, headers=H, timeout=30).json()["query"]["search"]
            oia["commons_hits"] = [h["title"] for h in res]
        except Exception as e:  # noqa: BLE001
            oia["err2"] = str(e)
    rep["_oia_logo"] = oia
    json.dump(rep, open(os.path.join(out, tag + ".json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else open(os.path.join(OUTD, "request.txt")).read().split()[0]
    {"losers10y": losers10y, "spincheck": spincheck, "logos": logos, "buildings": buildings, "extra": extra, "salik": salik}[task]()
