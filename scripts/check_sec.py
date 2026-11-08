"""Сверка годовой выручки и чистой прибыли из Yahoo (companies/data) с отчётами 10-K в SEC (XBRL companyfacts). v1
Печатает по каждой компании расхождение по годам; >2% помечается ПРОВЕРИТЬ. Только для компаний США."""
import json, sys, time
import requests

UA = {"User-Agent": "OSNOVA Finance maximenko.aleksander.p@gmail.com"}
REV = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
       "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueGoodsNet"]
NI = ["NetIncomeLoss", "NetIncomeLossAvailableToCommonStockholdersBasic", "ProfitLoss"]

def annual(facts, tags):
    best = {}
    for tag in tags:
        u = facts.get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", [])
        for x in u:
            if x.get("form") not in ("10-K", "10-K/A") or not x.get("start"):
                continue
            days = (time.mktime(time.strptime(x["end"], "%Y-%m-%d")) - time.mktime(time.strptime(x["start"], "%Y-%m-%d"))) / 86400
            if not 350 <= days <= 380:
                continue
            y = x["end"][:4]
            if y not in best or x["filed"] > best[y][1]:
                best[y] = (x["val"], x["filed"])
        if best:
            break
    return {y: v for y, (v, _) in best.items()}

tick = requests.get("https://www.sec.gov/files/company_tickers.json", headers=UA, timeout=30).json()
cik = {v["ticker"]: str(v["cik_str"]).zfill(10) for v in tick.values()}
bad = []
for t in sys.argv[1:]:
    try:
        y = json.load(open(f"companies/data/{t}.json"))
        f = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik[t]}.json", headers=UA, timeout=30).json()["facts"]
        r, n = annual(f, REV), annual(f, NI)
        line = []
        for k, sec, yh in (("выручка", r, y["revenue"]), ("прибыль", n, y["net_income"])):
            for yr in sorted(yh)[-4:]:
                if yr not in sec:
                    line.append(f"{k} {yr}: нет в SEC"); continue
                d = (yh[yr] - sec[yr]) / abs(sec[yr]) * 100 if sec[yr] else 0
                if abs(d) > 2:
                    line.append(f"{k} {yr}: Yahoo {yh[yr]/1e6:.0f} SEC {sec[yr]/1e6:.0f} ({d:+.1f}%) ПРОВЕРИТЬ")
        print(t, "OK" if not line else "; ".join(line), flush=True)
        if line: bad.append(t)
        time.sleep(0.3)
    except Exception as e:
        print(t, "ОШИБКА", e, flush=True); bad.append(t)
print("расхождения:", " ".join(bad) or "нет")
