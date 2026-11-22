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


def dtclogo():
    import re as _re
    H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
    out = os.path.join(OUTD, "px"); os.makedirs(out, exist_ok=True); rep = {}
    for site in ("https://www.dubaitaxi.ae/en", "https://www.dubaitaxi.ae/", "https://ir.dubaitaxi.ae/"):
        try:
            h = requests.get(site, headers=H, timeout=30).text
            open(os.path.join(out, "dtc_home_%d.html" % len(rep)), "w").write(h)
            cands = sorted(set(_re.findall(r'(?:src|href|data-src)=["\']([^"\']*(?:logo|Logo|LOGO)[^"\']*)["\']', h)))
            rep[site] = cands[:30]
            for i, c in enumerate(cands[:12]):
                u = requests.compat.urljoin(site, c)
                b = requests.get(u, headers=H, timeout=30)
                if b.status_code == 200 and len(b.content) > 300:
                    ext = (c.split("?")[0].rsplit(".", 1)[-1] or "bin")[:4]
                    open(os.path.join(out, "dtclogo_%d_%d.%s" % (len(rep), i, ext)), "wb").write(b.content)
        except Exception as e:  # noqa: BLE001
            rep[site] = str(e)
    json.dump(rep, open(os.path.join(out, "dtclogo.json"), "w"), indent=1); print(rep)


def dtcimg():
    H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
    out = os.path.join(OUTD, "px", "img"); os.makedirs(out, exist_ok=True); rep = {}
    base = "https://cdn.prod.website-files.com/656e39bd8b07a811ace24224/"
    for i, f in enumerate(["656e39bd8b07a811ace24624_taxi.webp", "656e39bd8b07a811ace2453a_DTC%20md.webp", "6ae2f9b724f9b9545ad63796_5Y6A444444391.jpg",
                           "6af5a0d37c3df613b283adda_Web-BannerQ3-2026.jpg", "69ccece33dc9e78c0796ab70_normal%20screen02.jpg", "656e39bd8b07a811ace24533_rl.webp",
                           "656e39bd8b07a811ace24534_al.webp", "656e39bd8b07a811ace24535_ls.webp", "656e39bd8b07a811ace2462a_falt.webp", "656e39bd8b07a811ace2462c_ishh.webp"]):
        b = requests.get(base + f, headers=H, timeout=40)
        rep[f] = [b.status_code, len(b.content)]
        if b.status_code == 200: open(os.path.join(out, "%02d_%s" % (i, f.split("_", 1)[1].replace("%20", "_"))), "wb").write(b.content)
    for u in ["https://cdn.prod.website-files.com/656e39bd8b07a811ace241f7/699d5c43904ab65c6cc79e3a_website-banner---update.jpg"]:
        b = requests.get(u, headers=H, timeout=40); rep[u] = [b.status_code, len(b.content)]
        if b.status_code == 200: open(os.path.join(out, "99_banner.jpg"), "wb").write(b.content)
    json.dump(rep, open(os.path.join(out, "rep.json"), "w"), indent=1); print(rep)


def series():
    """Серия «Как зарабатывает компания»: цены (TradingView), годовая отчётность США (yfinance), логотипы (Wikidata P154)."""
    import subprocess, sys as _s, time
    subprocess.run([_s.executable, "-m", "pip", "install", "-q", "websocket-client"], check=False)
    out = os.path.join(OUTD, "series"); os.makedirs(out, exist_ok=True); rep = {}
    extra = [l.strip() for l in open(os.path.join(OUTD, "request.txt"), encoding="utf-8").read().splitlines()[2:] if ":" in l]
    if extra:
        us = {x.split(":")[1]: x for x in extra}
    else: us = {"KO": "NYSE:KO", "MCD": "NYSE:MCD", "COST": "NASDAQ:COST", "AAPL": "NASDAQ:AAPL", "AMZN": "NASDAQ:AMZN", "V": "NYSE:V",
          "SBUX": "NASDAQ:SBUX", "RACE": "NYSE:RACE", "WDFC": "NASDAQ:WDFC", "TKO": "NYSE:TKO"}
    for k, sym in us.items():
        try:
            rows = tv_hist(sym, 600, "1W")
            with open(os.path.join(out, k + "_w.csv"), "w") as fh:
                fh.write("Date,Close\n"); [fh.write(f"{d},{c}\n") for d, c in rows]
            rep["px_" + k] = [len(rows), rows[0], rows[-1]]
        except Exception as e:  # noqa: BLE001
            rep["px_" + k] = str(e)
        try:
            import yfinance as yf
            t = yf.Ticker(k)
            inc = t.income_stmt
            fin = {}
            for col in inc.columns:
                y = str(col)[:10]
                fin[y] = {r: (None if str(inc.loc[r, col]) == "nan" else float(inc.loc[r, col])) for r in ("Total Revenue", "Net Income", "Operating Income", "Gross Profit") if r in inc.index}
            info = t.info
            fin["_info"] = {f: info.get(f) for f in ("marketCap", "dividendRate", "dividendYield", "trailingPE", "currentPrice", "sharesOutstanding", "fullTimeEmployees", "longBusinessSummary")}
            json.dump(fin, open(os.path.join(out, k + "_fin.json"), "w"), indent=1, default=str)
            rep["fin_" + k] = "ok"
        except Exception as e:  # noqa: BLE001
            rep["fin_" + k] = str(e)
    H = {"User-Agent": "osnova-research/1.0 (github.com/aleksandr-pm; research bot)"}
    titles = {"PARKIN": "Parkin Company", "SALIK": "Salik (road toll)", "KO": "The Coca-Cola Company", "MCD": "McDonald's", "COST": "Costco",
              "AAPL": "Apple Inc.", "AMZN": "Amazon (company)", "V": "Visa Inc.", "SBUX": "Starbucks", "RACE": "Ferrari", "WDFC": "WD-40",
              "TKO": "TKO Group Holdings", "WWE": "WWE", "LULU": "Lulu Hypermarket", "TALABAT": "Talabat", "AIRARABIA": "Air Arabia",
              "EMAAR": "Emaar Properties", "ENBD": "Emirates NBD", "ALDAR": "Aldar Properties", "ADNOCGAS": "ADNOC Gas", "DEWA": "Dubai Electricity and Water Authority"}
    if extra: titles = {}
    lg = os.path.join(out, "logos"); os.makedirs(lg, exist_ok=True)
    for k, tt in titles.items():
        try:
            j = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "query", "prop": "pageprops", "titles": tt, "redirects": 1, "format": "json"}, headers=H, timeout=30).json()
            qid = list(j["query"]["pages"].values())[0].get("pageprops", {}).get("wikibase_item")
            if not qid: rep["logo_" + k] = "no qid"; continue
            w = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json", headers=H, timeout=30).json()
            cl = w["entities"][qid]["claims"].get("P154") or w["entities"][qid]["claims"].get("P18")
            if not cl: rep["logo_" + k] = "no P154"; continue
            fn = cl[0]["mainsnak"]["datavalue"]["value"]
            for att in range(4):
                time.sleep(20)
                b = requests.get("https://commons.wikimedia.org/wiki/Special:FilePath/" + fn.replace(" ", "_"), params={"width": 1000}, headers=H, timeout=40)
                if b.status_code == 200 and b.content[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1", b"\xff\xd8\xff\xdb") or (b.status_code == 200 and b.content[:3] == b"GIF"):
                    open(os.path.join(lg, k + (".png" if b.content[:4] == b"\x89PNG" else ".jpg")), "wb").write(b.content); rep["logo_" + k] = [fn, len(b.content)]; break
                rep["logo_" + k] = [fn, b.status_code, b.content[:15].hex()]
        except Exception as e:  # noqa: BLE001
            rep["logo_" + k] = str(e)
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1, default=str); print(rep)


def logos4():
    import re as _re
    H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
    out = os.path.join(OUTD, "series", "sitelogos"); os.makedirs(out, exist_ok=True); rep = {}
    for k, site in {"PARKIN": "https://www.parkin.ae/", "ENBD": "https://www.emiratesnbd.com/en", "ADNOCGAS": "https://www.adnocgas.ae/"}.items():
        try:
            h = requests.get(site, headers=H, timeout=30).text
            open(os.path.join(out, k + ".html"), "w").write(h)
            c = sorted(set(_re.findall(r'(?:src|href|data-src)=["\']([^"\']*(?:logo|Logo|LOGO)[^"\']*\.(?:svg|png|webp|jpg)[^"\']*)["\']', h)))
            rep[k] = c[:15]
            for i, u in enumerate(c[:8]):
                b = requests.get(requests.compat.urljoin(site, u), headers=H, timeout=30)
                if b.status_code == 200 and len(b.content) > 300:
                    open(os.path.join(out, f"{k}_{i}.{u.split('?')[0].rsplit('.', 1)[-1][:4]}"), "wb").write(b.content)
        except Exception as e:  # noqa: BLE001
            rep[k] = str(e)
    json.dump(rep, open(os.path.join(out, "rep.json"), "w"), indent=1); print(rep)


def commons():
    """Фото со свободной лицензией с Wikimedia Commons по запросам из строк 3+ request.txt (запрос|кол-во)"""
    import time
    H = {"User-Agent": "osnova-research/1.0 (github.com/aleksandr-pm; research bot)"}
    out = os.path.join(OUTD, "commons"); os.makedirs(out, exist_ok=True); rep = []
    qs = [l.strip() for l in open(os.path.join(OUTD, "request.txt"), encoding="utf-8").read().splitlines()[2:] if "|" in l]
    for ln in qs:
        q, n = ln.split("|"); n = int(n)
        if q.startswith("file:"):  # прямой файл (логотип SVG и т.п.) в PNG 1200 px
            fn = q[5:]; time.sleep(10)
            b = requests.get("https://commons.wikimedia.org/wiki/Special:FilePath/" + fn.replace(" ", "_"), params={"width": 1200}, headers=H, timeout=60)
            if b.status_code == 200 and b.content[:4] == b"\x89PNG":
                open(os.path.join(out, "file_" + "".join(ch if ch.isalnum() else "_" for ch in fn)[:40] + ".png"), "wb").write(b.content); rep.append({"file": fn, "license": "logo"})
            else: rep.append({"file": fn, "error": b.status_code})
            continue
        j = requests.get("https://commons.wikimedia.org/w/api.php", params={"action": "query", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6,
                         "gsrlimit": 25, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 1600, "format": "json"}, headers=H, timeout=40).json()
        pages = sorted(j.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
        got = 0
        for pg in pages:
            ii = pg.get("imageinfo", [{}])[0]
            if ii.get("width", 0) < 1200: continue
            md = ii.get("extmetadata", {}); lic = md.get("LicenseShortName", {}).get("value", "")
            if not any(x in lic for x in ("CC BY", "CC0", "Public domain", "CC-BY")): continue
            time.sleep(8)
            b = requests.get(ii.get("thumburl") or ii["url"], headers=H, timeout=60)
            if b.status_code != 200 or b.content[:3] != b"\xff\xd8\xff": continue
            slug = "".join(ch if ch.isalnum() else "_" for ch in q.lower())[:30]
            fn = f"{slug}_{got + 1}.jpg"; open(os.path.join(out, fn), "wb").write(b.content); got += 1
            rep.append({"file": fn, "title": pg["title"], "license": lic, "author": md.get("Artist", {}).get("value", "")[:120]})
            if got >= n: break
    json.dump(rep, open(os.path.join(out, "manifest.json"), "w"), indent=1, ensure_ascii=False); print(len(rep))


def px():
    """Дневные цены и ключевые показатели для серии роликов про компании"""
    import subprocess, sys as _s
    subprocess.run([_s.executable, "-m", "pip", "install", "-q", "websocket-client"], check=False)
    out = os.path.join(OUTD, "px"); os.makedirs(out, exist_ok=True); rep = {}
    syms = ["DFM:DTC", "DFM:SALIK", "DFM:PARKIN", "DFM:TALABAT", "DFM:EMAAR", "DFM:DEWA", "DFM:AIRARABIA", "DFM:EMIRATESNBD", "ADX:ALDAR", "ADX:ADNOCGAS", "ADX:LULU", "ADX:ADNOCDRILL"]
    for sym in syms:
        k = sym.split(":")[1]
        try:
            rows = tv_hist(sym, 1500, "1D")
            with open(os.path.join(out, k + ".csv"), "w") as fh:
                fh.write("Date,Close\n"); [fh.write(f"{d},{c}\n") for d, c in rows]
            rep[k] = [len(rows), rows[0] if rows else None, rows[-1] if rows else None]
        except Exception as e:  # noqa: BLE001
            rep[k] = str(e)
    cols = ["close", "market_cap_basic", "dividend_yield_recent", "price_earnings_ttm", "total_debt", "total_revenue", "net_income", "total_shares_outstanding_fundamental", "description", "sector"]
    try:
        rep["scan"] = {"cols": cols, "data": requests.post("https://scanner.tradingview.com/uae/scan", json={"symbols": {"tickers": syms}, "columns": cols}, timeout=30).json()}
    except Exception as e:  # noqa: BLE001
        rep["scan_err"] = str(e)
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1, default=str); print({k: v for k, v in rep.items() if k != "scan"})


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

def brkcash():
    """Деньги Berkshire: SEC XBRL (2009+), годовые отчёты PDF (1994-2010), страницы-агрегаторы."""
    import io, re as _re
    out = os.path.join(OUTD, "brkcash"); os.makedirs(out, exist_ok=True)
    UA = {"User-Agent": os.environ.get("SEC_UA", "OSNOVA Finance research bot (github.com/aleksandr-pm)")}
    rep = {}
    try:
        f = requests.get("https://data.sec.gov/api/xbrl/companyfacts/CIK0001067983.json", headers=UA, timeout=60).json()
        keep = {}
        for ns, d in f.get("facts", {}).items():
            for tag, v in d.items():
                if _re.search(r"Cash|Treasur|ShortTerm", tag):
                    keep[ns + ":" + tag] = [{"end": x["end"], "val": x["val"], "form": x.get("form"), "fy": x.get("fy"), "fp": x.get("fp")}
                                            for x in v.get("units", {}).get("USD", []) if not x.get("start")]
        json.dump(keep, open(os.path.join(out, "sec_facts.json"), "w"))
        rep["sec_tags"] = list(keep)
    except Exception as e:  # noqa: BLE001
        rep["sec_err"] = str(e)
    for u in ["https://usmacro.com/indicator/brka_cash", "https://www.macrotrends.net/stocks/charts/BRK.A/berkshire-hathaway/cash-on-hand"]:
        try:
            r = requests.get(u, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}, timeout=40)
            open(os.path.join(out, u.split("/")[2] + ".html"), "w").write(r.text); rep[u] = r.status_code
        except Exception as e:  # noqa: BLE001
            rep[u] = str(e)
    from pypdf import PdfReader
    for y in range(int(os.environ.get("Y0", 2011)), int(os.environ.get("Y1", 2018))):
        hits = []
        for u in [f"https://www.berkshirehathaway.com/{y}ar/{y}ar.pdf", f"https://www.berkshirehathaway.com/{y}ar/{y}.pdf"]:
            try:
                r = requests.get(u, headers=UA, timeout=90)
                if r.status_code != 200 or r.content[:4] != b"%PDF":
                    continue
                rd = PdfReader(io.BytesIO(r.content))
                for i, pg in enumerate(rd.pages):
                    t = pg.extract_text() or ""
                    for ln in t.splitlines():
                        if _re.search(r"[Cc]ash and cash equivalents|[Cc]ash equivalents|Treasury [Bb]ills|billion of cash|cash and equivalents", ln):
                            hits.append(f"p{i+1}: {ln.strip()}")
                rep[str(y)] = u; break
            except Exception as e:  # noqa: BLE001
                rep[str(y) + "_err"] = str(e)
        open(os.path.join(out, f"ar{y}.txt"), "w").write("\n".join(hits))
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))

def cashtop():
    """Топ компаний мира по деньгам: наличные + краткосрочные вложения, последний квартал (yfinance)."""
    import yfinance as yf
    out = os.path.join(OUTD, "cashtop"); os.makedirs(out, exist_ok=True)
    tick = ["BRK-B", "GOOGL", "MSFT", "AAPL", "AMZN", "META", "NVDA", "TSM", "AVGO", "ORCL", "TSLA", "NFLX", "CSCO", "JNJ", "PFE", "MRK", "LLY",
            "ABBV", "UNH", "WMT", "XOM", "CVX", "COST", "BABA", "PDD", "JD", "BIDU", "QCOM", "INTC", "AMD", "ADBE", "CRM", "NVO", "ASML", "SAP",
            "TM", "SONY", "7203.T", "6758.T", "9984.T", "005930.KS", "000660.KS", "0700.HK", "9988.HK", "1810.HK", "3690.HK", "1211.HK", "2222.SR",
            "ROG.SW", "NESN.SW", "NOVN.SW", "MC.PA", "TTE", "SHEL", "BP", "AZN", "GSK", "VOW3.DE", "MBG.DE", "BMW.DE", "SIE.DE", "DTE.DE",
            "RELIANCE.NS", "TCS.NS", "VALE", "PBR", "BHP", "RIO", "GM", "F", "IBM", "TXN", "KO", "PEP", "PG", "MCD", "DIS", "T", "VZ", "CMCSA",
            "HD", "NKE", "V", "MA", "UBER", "PLTR", "ARM", "601857.SS", "600519.SS", "0941.HK", "0883.HK", "2318.HK"]
    fx = {}
    rows = []
    for t in tick:
        try:
            tk = yf.Ticker(t)
            bs = tk.quarterly_balance_sheet
            if bs is None or bs.empty: rows.append({"t": t, "err": "no bs"}); continue
            col = bs.columns[0]; r = {"t": t, "date": str(col)[:10]}
            for k in ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents", "Other Short Term Investments", "Total Assets"]:
                if k in bs.index:
                    v = bs.loc[k, col]
                    r[k] = None if v != v else float(v)
            inf = tk.info; cur = inf.get("financialCurrency") or inf.get("currency") or "USD"
            r.update(cur=cur, name=inf.get("longName") or inf.get("shortName"), sector=inf.get("sector"), industry=inf.get("industry"), mcap=inf.get("marketCap"),
                     mcur=inf.get("currency"))
            if cur != "USD":
                if cur not in fx:
                    h = yf.Ticker(f"{cur}USD=X").history(period="5d")["Close"]
                    fx[cur] = float(h.iloc[-1]) if len(h) else None
                r["fx"] = fx[cur]
            rows.append(r); time.sleep(0.3)
        except Exception as e:  # noqa: BLE001
            rows.append({"t": t, "err": str(e)})
    for r in rows:
        c = r.get("Cash Cash Equivalents And Short Term Investments") or r.get("Cash And Cash Equivalents")
        if c and (r.get("cur") == "USD" or r.get("fx")): r["cash_usd_bn"] = round(c * (r.get("fx") or 1) / 1e9, 1)
    rows.sort(key=lambda r: -(r.get("cash_usd_bn") or 0))
    json.dump(rows, open(os.path.join(out, "cashtop.json"), "w"), ensure_ascii=False, indent=1)
    for r in rows[:30]: print(r.get("t"), r.get("name"), r.get("cash_usd_bn"), r.get("date"), r.get("sector"))

def wplogos():
    """Логотипы из инфобоксов Википедии: строки 3+ request.txt = КЛЮЧ|Название статьи"""
    import re as _re, time
    H = {"User-Agent": "osnova-research/1.0 (github.com/aleksandr-pm; research bot)"}
    out = os.path.join(OUTD, "wplogos"); os.makedirs(out, exist_ok=True); rep = {}
    for ln in open(os.path.join(OUTD, "request.txt"), encoding="utf-8").read().splitlines()[2:]:
        if "|" not in ln: continue
        k, page = ln.split("|", 1)
        try:
            wt = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "parse", "page": page, "prop": "wikitext", "format": "json", "redirects": 1},
                              headers=H, timeout=30).json()["parse"]["wikitext"]["*"]
            m = _re.search(r"\|\s*logo\s*=\s*(?:\[\[(?:File|Image):)?\s*([^|\]\n{}]+\.(?:svg|png|jpg))", wt, _re.I)
            if not m: rep[k] = "no logo field"; continue
            fn = m.group(1).strip(); time.sleep(4)
            b = requests.get("https://commons.wikimedia.org/wiki/Special:FilePath/" + fn.replace(" ", "_"), params={"width": 1200}, headers=H, timeout=60)
            if b.status_code != 200:
                b = requests.get("https://en.wikipedia.org/wiki/Special:FilePath/" + fn.replace(" ", "_"), params={"width": 1200}, headers=H, timeout=60)
            ext = "png" if b.content[:4] == b"\x89PNG" else "jpg" if b.content[:3] == b"\xff\xd8\xff" else "bin"
            open(os.path.join(out, f"{k}.{ext}"), "wb").write(b.content); rep[k] = [fn, b.status_code, ext]
        except Exception as e:  # noqa: BLE001
            rep[k] = str(e)
    json.dump(rep, open(os.path.join(out, "rep.json"), "w"), indent=1); print(rep)


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else open(os.path.join(OUTD, "request.txt")).read().split()[0]
    {"losers10y": losers10y, "spincheck": spincheck, "logos": logos, "buildings": buildings, "extra": extra, "salik": salik, "sobha": sobha, "sobhasite": sobhasite, "sobhaimgs": sobhaimgs, "mcap": mcap, "mcap_tv": mcap_tv, "reit": reit, "exch": exch, "sitelogos": sitelogos, "logos3": logos3, "dl": dl, "px": px, "dtclogo": dtclogo, "dtcimg": dtcimg, "series": series, "logos4": logos4, "commons": commons, "brkcash": brkcash, "cashtop": cashtop, "wplogos": wplogos}[task]()
