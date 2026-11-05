"""Годовая отчётность публичных компаний из Yahoo Finance (yfinance) → companies/data/<ticker>.json. v1"""
import json, os, sys
import yfinance as yf

TICKERS = sys.argv[1:] or """SALIK.AE EMPOWER.AE EMAAR.AE DEWA.AE PARKIN.AE TALABAT.AE ADNOCGAS.AE ALDAR.AE
EAND.AE DU.AE ADPORTS.AE AIRARABIA.AE EMIRATESNBD.AE FAB.AE ADNOCDIST.AE ADNOCDRILL.AE TAQA.AE
DEYAAR.AE SPINNEYS.AE ALPHADHABI.AE PUREHEALTH.AE BURJEEL.AE AMANAT.AE ADIB.AE DIB.AE GFH.AE AMLAK.AE
ADNOCLS.AE TECOM.AE DFM.AE""".split()

ROWS = {
    "revenue": ["Total Revenue", "Operating Revenue"],
    "net_income": ["Net Income Common Stockholders", "Net Income"],
    "operating_income": ["Operating Income"],
    "ebitda": ["EBITDA", "Normalized EBITDA"],
}
BS = {"total_debt": ["Total Debt"], "cash": ["Cash And Cash Equivalents"], "equity": ["Stockholders Equity", "Total Equity Gross Minority Interest"]}

def pick(df, names):
    out = {}
    if df is None or df.empty:
        return out
    for n in names:
        if n in df.index:
            for col, v in df.loc[n].items():
                if v == v:  # not NaN
                    out[str(col.year)] = float(v)
            if out:
                return out
    return out

os.makedirs("companies/data", exist_ok=True)
for t in TICKERS:
    try:
        tk = yf.Ticker(t)
        info = tk.info or {}
        inc, bal = tk.income_stmt, tk.balance_sheet
        rec = {"ticker": t, "name": info.get("longName") or info.get("shortName"), "currency": info.get("financialCurrency") or info.get("currency"),
               "sector": info.get("sector"), "industry": info.get("industry"), "summary": (info.get("longBusinessSummary") or "")[:1500],
               "market_cap": info.get("marketCap"), "price": info.get("currentPrice") or info.get("regularMarketPrice"),
               "dividend_yield": info.get("dividendYield"), "employees": info.get("fullTimeEmployees"), "source": "Yahoo Finance"}
        for k, n in ROWS.items(): rec[k] = pick(inc, n)
        for k, n in BS.items(): rec[k] = pick(bal, n)
        ok = bool(rec["revenue"])
        print(("OK " if ok else "EMPTY ") + t, rec["name"], rec["currency"], sorted(rec["revenue"]), flush=True)
        with open(f"companies/data/{t}.json", "w") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
    except Exception as e:
        print("ERR", t, e, flush=True)
