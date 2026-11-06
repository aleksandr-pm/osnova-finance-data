"""Сырые данные для рейтингов компаний и миллиардеров → bank/raw_markets/. v1"""
import os, time, requests
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
     "Accept": "text/html,application/json,text/csv,*/*"}
OUT = "bank/raw_markets"
os.makedirs(OUT, exist_ok=True)
CMC = "https://companiesmarketcap.com/"
PAGES = {
    "cmc_all": "?download=csv",
    "cmc_revenue": "largest-companies-by-revenue/?download=csv",
    "cmc_earnings": "most-profitable-companies/?download=csv",
    "cmc_employees": "largest-companies-by-number-of-employees/?download=csv",
    "cmc_dividend": "top-companies-by-dividend-yield/?download=csv",
    "cmc_pe": "top-companies-by-pe-ratio/?download=csv",
    "cmc_tech": "tech/largest-tech-companies-by-market-cap/?download=csv",
    "cmc_banks": "banks/largest-banks-by-market-cap/?download=csv",
    "cmc_oil": "oil-gas/largest-oil-and-gas-companies-by-market-cap/?download=csv",
    "cmc_semis": "semiconductors/largest-semiconductor-companies-by-market-cap/?download=csv",
    "cmc_pharma": "pharmaceuticals/largest-pharmaceutical-companies-by-market-cap/?download=csv",
    "cmc_auto": "automakers/largest-automakers-by-market-cap/?download=csv",
    "cmc_airlines": "airlines/largest-airlines-by-market-cap/?download=csv",
    "cmc_insurance": "insurance/largest-insurance-companies-by-market-cap/?download=csv",
    "cmc_food": "food/largest-food-companies-by-market-cap/?download=csv",
    "cmc_retail": "retail/largest-retail-companies-by-market-cap/?download=csv",
    "cmc_telecom": "telecommunication/largest-telecommunication-companies-by-market-cap/?download=csv",
    "cmc_mining": "mining/largest-mining-companies-by-market-cap/?download=csv",
    "cmc_luxury": "luxury/largest-luxury-companies-by-market-cap/?download=csv",
    "cmc_crypto": "cryptocurrency/largest-cryptocurrency-companies-by-market-cap/?download=csv",
    "cmc_ai": "artificial-intelligence/largest-ai-companies-by-marketcap/?download=csv",
    "cmc_defense": "defense-contractors/largest-defense-contractors-by-market-cap/?download=csv",
    "cmc_beverages": "beverages/largest-beverage-companies-by-market-cap/?download=csv",
    "cmc_sports": "sports/largest-sports-companies-by-market-cap/?download=csv",
    "cmc_gaming": "video-games/largest-video-game-companies-by-market-cap/?download=csv",
    "cmc_realestate": "real-estate/largest-real-estate-companies-by-market-cap/?download=csv",
}
for k, path in PAGES.items():
    try:
        r = requests.get(CMC + path, headers=H, timeout=40)
        ok = r.status_code == 200 and r.text[:200].count(",") >= 3 and "<html" not in r.text[:200].lower()
        print(k, r.status_code, len(r.text), "CSV" if ok else "NOT CSV", r.text[:80].replace("\n", " | "))
        if ok:
            open(f"{OUT}/{k}.csv", "w").write(r.text)
    except Exception as e:
        print(k, "ERR", e)
    time.sleep(1.5)
# миллиардеры
for k, u in {
    "bloomberg": "https://www.bloomberg.com/billionaires/",
    "forbes_rtb": "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json?fields=rank,uri,personName,lastName,gender,source,industries,countryOfCitizenship,birthDate,finalWorth,date,timestamp&limit=3000",
}.items():
    try:
        r = requests.get(u, headers=H, timeout=40)
        print(k, r.status_code, len(r.text), r.text[:120].replace("\n", " "))
        if r.status_code == 200:
            open(f"{OUT}/{k}.{'json' if 'json' in u else 'html'}", "w").write(r.text)
    except Exception as e:
        print(k, "ERR", e)
