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
        time.sleep(9)
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


def sobha():
    """Фото проектов Sobha (Commons) + логотип"""
    global BUILDING_Q
    BUILDING_Q = {"sobha": ["Sobha Hartland Dubai", "Sobha Realty", "Sobha One Dubai", "Mohammed Bin Rashid City Dubai", "Ras Al Khor Dubai skyline"]}
    buildings(tag="sobha")
    import re, time
    H = {"User-Agent": "osnova-research/1.0 (github.com/aleksandr-pm)"}; out = os.path.join(OUTD, "buildings"); rep = {}
    try:
        wt = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "parse", "page": "Sobha Realty", "prop": "wikitext", "format": "json", "redirects": 1}, headers=H, timeout=30).json()
        wt = wt.get("parse", {}).get("wikitext", {}).get("*", "")
        m = re.search(r"\|\s*logo\s*=\s*(?:\[\[)?(?:File:|Image:)?([^\n|\]]+)", wt); rep["field"] = m.group(1).strip() if m else None
        cands = [rep["field"]] if rep["field"] else []
        time.sleep(3)
        res = requests.get("https://commons.wikimedia.org/w/api.php", params={"action": "query", "list": "search", "srsearch": "Sobha logo", "srnamespace": 6, "srlimit": 10, "format": "json"}, headers=H, timeout=30).json()["query"]["search"]
        rep["commons"] = [x["title"] for x in res]; cands += [x["title"][5:] for x in res if "sobha" in x["title"].lower()]
        for i, fn in enumerate(cands[:3]):
            time.sleep(3)
            for site in ("https://en.wikipedia.org/w/api.php", "https://commons.wikimedia.org/w/api.php"):
                pg = list(requests.get(site, params={"action": "query", "titles": "File:" + fn, "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 1000, "format": "json"}, headers=H, timeout=30).json()["query"]["pages"].values())[0]
                if "imageinfo" in pg:
                    u = (pg["imageinfo"][0].get("thumburl") or pg["imageinfo"][0]["url"]).split("?")[0]
                    open(os.path.join(out, f"sobha_logo{i}." + u.rsplit(".", 1)[-1].lower()), "wb").write(requests.get(u, headers=H, timeout=30).content); rep.setdefault("logos", []).append(u); break
    except Exception as e:  # noqa: BLE001
        rep["err"] = str(e)
    json.dump(rep, open(os.path.join(out, "sobha_logo.json"), "w"), indent=1); print(rep)


def sobhasite():
    import re
    out = os.path.join(OUTD, "buildings"); rep = {}
    for u in ("https://sobharealty.com/", "https://www.sobharealty.com/"):
        try:
            r = requests.get(u, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept-Language": "en"}, timeout=40)
            svgs = re.findall(r"<svg[^>]*width=\"126\"[\s\S]*?</svg>", r.text)
            rep[u] = [r.status_code, len(r.text), len(svgs)]
            if svgs:
                open(os.path.join(out, "sobha_logo.svg"), "w").write(svgs[0]); break
        except Exception as e:  # noqa: BLE001
            rep[u] = str(e)
    json.dump(rep, open(os.path.join(out, "sobhasite.json"), "w")); print(rep)


def sobhaimgs():
    import re, time
    out = os.path.join(OUTD, "sobha_imgs"); os.makedirs(out, exist_ok=True); rep = {"pages": {}, "files": []}
    UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
    urls = []
    for pg in ("https://sobharealty.com/", "https://sobharealty.com/sobha-hartland", "https://sobharealty.com/sobha-hartland-ii", "https://sobharealty.com/sobha-one",
               "https://sobharealty.com/projects", "https://sobharealty.com/about-us"):
        try:
            r = requests.get(pg, headers=UA, timeout=40); found = re.findall(r'(/sites/default/files/[^"\'\s)]+?\.(?:jpg|jpeg|webp|png))', r.text, re.I)
            rep["pages"][pg] = [r.status_code, len(found)]
            for f in found:
                if any(k in f.lower() for k in ("logo", "icon", "ico_", "svg")): continue
                if f not in urls: urls.append(f)
        except Exception as e:  # noqa: BLE001
            rep["pages"][pg] = str(e)
        time.sleep(1)
    n = 0
    for f in urls:
        if n >= 40: break
        try:
            b = requests.get("https://sobharealty.com" + f, headers=UA, timeout=40).content
            if len(b) < 60000: continue
            ext = f.rsplit(".", 1)[-1].lower(); fn = f"s{n:02d}.{ext}"; open(os.path.join(out, fn), "wb").write(b)
            rep["files"].append([fn, f, len(b)]); n += 1
        except Exception as e:  # noqa: BLE001
            rep["files"].append([f, str(e)])
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1); print(rep["pages"], n)


def mcap():
    """Месячные цены и число акций для гонки капитализаций"""
    import yfinance as yf
    out = os.path.join(OUTD, "mcap"); os.makedirs(out, exist_ok=True); rep = {}
    T = {"ALDAR": "ALDAR.AD", "EMAAR": "EMAAR.AE", "FAB": "FAB.AD", "ENBD": "EMIRATESNBD.AE", "DU": "DU.AE", "EAND": "EAND.AD"}
    for k, t in T.items():
        try:
            tk = yf.Ticker(t)
            h = tk.history(start="2015-01-01", interval="1mo", auto_adjust=False)[["Close"]]
            h.index = h.index.strftime("%Y-%m-%d"); h.to_csv(os.path.join(out, k + ".csv"))
            info = {"rows": len(h), "first": h.index[0] if len(h) else None}
            try:
                fi = tk.fast_info; info["shares"] = fi.get("shares"); info["mcap"] = fi.get("market_cap"); info["currency"] = fi.get("currency")
            except Exception as e:  # noqa: BLE001
                info["fi_err"] = str(e)
            try:
                sf = tk.get_shares_full(start="2015-01-01")
                if sf is not None and len(sf):
                    sf.index = sf.index.strftime("%Y-%m-%d"); sf.to_csv(os.path.join(out, k + "_shares.csv"))
            except Exception as e:  # noqa: BLE001
                info["sf_err"] = str(e)
            rep[k] = info
        except Exception as e:  # noqa: BLE001
            rep[k] = {"err": str(e)}
    try:
        rep["tv"] = requests.post("https://scanner.tradingview.com/uae/scan", json={"symbols": {"tickers": ["ADX:ALDAR", "DFM:EMAAR", "ADX:FAB", "DFM:EMIRATESNBD", "DFM:DU", "ADX:EAND"]},
                                  "columns": ["close", "market_cap_basic", "total_shares_outstanding_fundamental"]}, timeout=30).json()
    except Exception as e:  # noqa: BLE001
        rep["tv_err"] = str(e)
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1, default=str); print(rep)


def tv_hist(symbol, n=200, interval="1M"):
    """Месячная история с TradingView через их websocket (как график на сайте)"""
    import websocket, random, string, re as _re
    def msg(func, params):
        b = json.dumps({"m": func, "p": params}, separators=(",", ":")); return "~m~%d~m~%s" % (len(b), b)
    rid = lambda p: p + "".join(random.choice(string.ascii_lowercase) for _ in range(12))
    ws = websocket.create_connection("wss://data.tradingview.com/socket.io/websocket", header=["Origin: https://www.tradingview.com"], timeout=20)
    cs = rid("cs_")
    for m in (msg("set_auth_token", ["unauthorized_user_token"]), msg("chart_create_session", [cs, ""]),
              msg("resolve_symbol", [cs, "symbol_1", '={"symbol":"%s","adjustment":"splits"}' % symbol]),
              msg("create_series", [cs, "s1", "s1", "symbol_1", interval, n])):
        ws.send(m)
    raw = ""
    for _ in range(200):
        r = ws.recv()
        if _re.match(r"~m~\d+~m~~h~\d+", r): ws.send(r); continue
        raw += r
        if "series_completed" in r or "symbol_error" in r: break
    ws.close()
    rows = []
    for part in _re.split(r"~m~\d+~m~", raw):
        if '"timescale_update"' in part or '"du"' in part:
            try:
                js = json.loads(part)
                for blk in js["p"][1].values():
                    for it in blk.get("s", []): rows.append(it["v"])
            except Exception:  # noqa: BLE001
                pass
    import datetime as _dt
    seen = {}
    for v in rows: seen[_dt.datetime.utcfromtimestamp(v[0]).strftime("%Y-%m-%d")] = v[4]
    return sorted(seen.items())


def mcap_tv():
    import subprocess, sys as _s
    subprocess.run([_s.executable, "-m", "pip", "install", "-q", "websocket-client"], check=False)
    out = os.path.join(OUTD, "mcap"); os.makedirs(out, exist_ok=True); rep = {}
    for k, sym in {"ALDAR": "ADX:ALDAR", "FAB": "ADX:FAB", "EAND": "ADX:EAND", "EMAAR": "DFM:EMAAR", "ENBD": "DFM:EMIRATESNBD", "DU": "DFM:DU"}.items():
        try:
            rows = tv_hist(sym)
            with open(os.path.join(out, k + "_tv.csv"), "w") as fh:
                fh.write("Date,Close\n"); [fh.write(f"{d},{c}\n") for d, c in rows]
            rep[k] = [len(rows), rows[0] if rows else None, rows[-1] if rows else None]
        except Exception as e:  # noqa: BLE001
            rep[k] = str(e)
    try:
        rep["scan"] = requests.post("https://scanner.tradingview.com/uae/scan", json={"symbols": {"tickers": ["ADX:EAND", "ADX:ALDAR", "ADX:FAB"]},
                                    "columns": ["close", "market_cap_basic", "total_shares_outstanding_fundamental"]}, timeout=30).json()
    except Exception as e:  # noqa: BLE001
        rep["scan_err"] = str(e)
    json.dump(rep, open(os.path.join(out, "report_tv.json"), "w"), indent=1, default=str); print(rep)


def reit():
    import subprocess, sys as _s
    subprocess.run([_s.executable, "-m", "pip", "install", "-q", "websocket-client"], check=False)
    out = os.path.join(OUTD, "mcap"); rep = {}
    try:
        rep["scan"] = requests.post("https://scanner.tradingview.com/uae/scan", json={"symbols": {"tickers": ["DFM:DUBAIRESI"]},
                                    "columns": ["close", "market_cap_basic", "total_shares_outstanding_fundamental", "dividend_yield_recent", "Perf.YTD", "price_book_ratio"]}, timeout=30).json()
    except Exception as e:  # noqa: BLE001
        rep["scan_err"] = str(e)
    try:
        rows = tv_hist("DFM:DUBAIRESI", n=400, interval="1D")
        with open(os.path.join(out, "DUBAIRESI_tv.csv"), "w") as fh:
            fh.write("Date,Close\n"); [fh.write(f"{d},{c}\n") for d, c in rows]
        rep["hist"] = [len(rows), rows[0] if rows else None, rows[-1] if rows else None]
    except Exception as e:  # noqa: BLE001
        rep["hist_err"] = str(e)
    json.dump(rep, open(os.path.join(out, "reit.json"), "w"), indent=1, default=str); print(rep)


def exch():
    """Логотипы крупнейших компаний DFM и ADX + сводка по биржам из скринера TradingView"""
    global LOGO_PAGES
    LOGO_PAGES = {"x_EMAAR": "Emaar Properties", "x_ENBD": "Emirates NBD", "x_DEWA": "Dubai Electricity and Water Authority", "x_DIB": "Dubai Islamic Bank",
                  "x_DU": "Du (telecommunications company)", "x_AIRARABIA": "Air Arabia", "x_TALABAT": "Talabat", "x_PARKIN": "Parkin (company)",
                  "x_IHC": "International Holding Company (UAE)", "x_ADNOCGAS": "ADNOC Gas", "x_FAB": "First Abu Dhabi Bank", "x_EAND": "e& (company)",
                  "x_ALDAR": "Aldar Properties", "x_ADCB": "Abu Dhabi Commercial Bank", "x_ADNOCDRILL": "ADNOC Drilling", "x_ADNOCDIST": "ADNOC Distribution",
                  "x_ADNOC": "ADNOC", "x_ADIB": "Abu Dhabi Islamic Bank"}
    logos()
    out = os.path.join(OUTD, "exch"); os.makedirs(out, exist_ok=True); rep = {}
    for ex in ("DFM", "ADX"):
        try:
            r = requests.post("https://scanner.tradingview.com/uae/scan", json={
                "filter": [{"left": "exchange", "operation": "equal", "right": ex}], "markets": ["uae"],
                "columns": ["name", "description", "market_cap_basic", "sector", "close", "type", "Value.Traded"],
                "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"}, "range": [0, 400]}, timeout=40).json()
            rep[ex] = r
        except Exception as e:  # noqa: BLE001
            rep[ex] = str(e)
    json.dump(rep, open(os.path.join(out, "scan.json"), "w"), indent=1, default=str)
    print({k: (v.get("totalCount") if isinstance(v, dict) else v) for k, v in rep.items()})


def sitelogos():
    import re, time
    UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept-Language": "en"}
    out = os.path.join(OUTD, "sitelogos"); os.makedirs(out, exist_ok=True); rep = {}
    sites = {"DEWA": ["https://www.dewa.gov.ae/en", "https://www.dewa.gov.ae/en/investor-relations"], "DU": ["https://www.du.ae/", "https://www.du.ae/personal"],
             "EAND": ["https://www.eand.com/en/index.html", "https://www.eand.com/"], "IHC": ["https://www.ihcuae.com/", "https://ihcuae.com/en"]}
    for k, urls in sites.items():
        rep[k] = []
        for u in urls:
            try:
                r = requests.get(u, headers=UA, timeout=40); html = r.text
                svgs = [m for m in re.findall(r"<svg[\s\S]*?</svg>", html) if "logo" in m[:400].lower()][:3]
                imgs = re.findall(r'(?:src|href|content)=["\']([^"\']*logo[^"\']*\.(?:svg|png|webp|jpg)[^"\']*)', html, re.I)[:8]
                rep[k].append({"u": u, "status": r.status_code, "len": len(html), "imgs": imgs, "svgs": len(svgs)})
                for i, sv in enumerate(svgs): open(os.path.join(out, f"{k}_inline{i}.svg"), "w").write(sv)
                for i, im in enumerate(imgs[:5]):
                    full = requests.compat.urljoin(r.url, im.split("?")[0])
                    b = requests.get(full, headers=UA, timeout=30).content
                    open(os.path.join(out, f"{k}_{i}." + full.rsplit(".", 1)[-1].lower()[:4]), "wb").write(b)
                if imgs or svgs: break
            except Exception as e:  # noqa: BLE001
                rep[k].append({"u": u, "err": str(e)})
            time.sleep(2)
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1); print(rep)


def logos3():
    import re, time
    H = {"User-Agent": "osnova-research/1.0 (github.com/aleksandr-pm)"}
    UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
    out = os.path.join(OUTD, "sitelogos"); rep = {}
    try:
        b = requests.get("https://www.dewa.gov.ae/-/media/Images/Header-and-Footer/Header/dewalogo2xhome.ashx", headers=UA, timeout=40)
        open(os.path.join(out, "DEWA_home.png"), "wb").write(b.content); rep["DEWA"] = [b.status_code, b.headers.get("content-type"), len(b.content)]
    except Exception as e:  # noqa: BLE001
        rep["DEWA"] = str(e)
    for key, titles in {"DU": ["Emirates Integrated Telecommunications Company", "Du (Emirati company)", "Du (telecom)"],
                        "IHC": ["International Holding Company PJSC", "International Holding Company (Abu Dhabi)", "International Holding Co"]}.items():
        rep[key] = []
        for t in titles:
            time.sleep(6)
            try:
                js = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "parse", "page": t, "prop": "wikitext", "format": "json", "redirects": 1}, headers=H, timeout=30).json()
                if "parse" not in js: rep[key].append([t, "нет страницы"]); continue
                wt = js["parse"]["wikitext"]["*"]
                m = re.search(r"\|\s*logo\s*=\s*(?:\[\[)?(?:File:|Image:)?([^\n|\]]+)", wt)
                if not m: rep[key].append([t, "нет logo"]); continue
                fn = m.group(1).strip(); time.sleep(4)
                for site in ("https://en.wikipedia.org/w/api.php", "https://commons.wikimedia.org/w/api.php"):
                    pg = list(requests.get(site, params={"action": "query", "titles": "File:" + fn, "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 800, "format": "json"}, headers=H, timeout=30).json()["query"]["pages"].values())[0]
                    if "imageinfo" in pg:
                        u = (pg["imageinfo"][0].get("thumburl") or pg["imageinfo"][0]["url"]).split("?")[0]
                        open(os.path.join(out, f"{key}_wiki." + u.rsplit(".", 1)[-1].lower()), "wb").write(requests.get(u, headers=H, timeout=30).content)
                        rep[key].append([t, fn, u]); break
                if rep[key] and len(rep[key][-1]) == 3: break
            except Exception as e:  # noqa: BLE001
                rep[key].append([t, str(e)])
    json.dump(rep, open(os.path.join(out, "report3.json"), "w"), indent=1); print(rep)


def dl():
    import time
    H = {"User-Agent": "osnova-research/1.0 (github.com/aleksandr-pm; contact via github)"}
    out = os.path.join(OUTD, "sitelogos"); rep = {}
    for k, u in {"DIB": "https://upload.wikimedia.org/wikipedia/en/8/8e/Dubai-Islamic-Bank-Logo.png", "ENBD": "https://upload.wikimedia.org/wikipedia/commons/3/39/Emirates_NBD_Logo.jpg", "TALABAT": "https://upload.wikimedia.org/wikipedia/commons/2/26/Talabat-logo.png"}.items():
        for attempt in range(6):
            time.sleep(40)
            b = requests.get(u, headers=H, timeout=40)
            if b.status_code == 200 and not b.content[:20].lower().startswith(b"<!doctype"):
                open(os.path.join(out, k + "_ok.png"), "wb").write(b.content); rep[k] = [u, len(b.content)]; break
            rep[k] = [u, b.status_code]
    json.dump(rep, open(os.path.join(out, "dl.json"), "w"), indent=1); print(rep)


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
                    if got >= (3 if tag == "sobha" else 2):
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
    {"losers10y": losers10y, "spincheck": spincheck, "logos": logos, "buildings": buildings, "extra": extra, "salik": salik, "sobha": sobha, "sobhasite": sobhasite, "sobhaimgs": sobhaimgs, "mcap": mcap, "mcap_tv": mcap_tv, "reit": reit, "exch": exch, "sitelogos": sitelogos, "logos3": logos3, "dl": dl}[task]()
