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
                rep[key] = "нет поля logo"; continue
            fn = m.group(1).strip()
            info = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "query", "titles": "File:" + fn, "prop": "imageinfo",
                                "iiprop": "url", "iiurlwidth": 800, "format": "json"}, headers=H, timeout=30).json()
            ii = list(info["query"]["pages"].values())[0]["imageinfo"][0]
            url = ii.get("thumburl") or ii["url"]
            img = requests.get(url, headers=H, timeout=30)
            ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
            with open(os.path.join(out, f"{key}.{ext}"), "wb") as f:
                f.write(img.content)
            rep[key] = {"file": fn, "url": url, "bytes": len(img.content)}
        except Exception as e:  # noqa: BLE001
            rep[key] = f"ошибка: {e}"
    json.dump(rep, open(rp, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else open(os.path.join(OUTD, "request.txt")).read().split()[0]
    {"losers10y": losers10y, "spincheck": spincheck, "logos": logos}[task]()
