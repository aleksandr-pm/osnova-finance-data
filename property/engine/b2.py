"""Batch 2 (21 Nov 2026): 15 reels. Proven formats (race, dumbbell, ranking) + new (slope, multiline, countdown, quiz).
DB = OSNOVA DLD/Ejari aggregates; SITE = osnova.property pages read 16 Nov 2026."""
import sys; sys.path.insert(0, '/home/claude/prop'); sys.path.insert(0, '/home/claude/en1')
import pandas as pd, numpy as np
from data import SER as PRICE, YRS
FOOT = "Market statistics, not an offer or investment advice."
TAGS = "#dubaioffice #dubaicommercialproperty #dubairealestate #dubaiinvestment #officespace"
i0 = lambda v: f"{v:,.0f}"; p1 = lambda v: f"{v:.1f}%"
s = pd.read_csv('/home/claude/inv/sales_area.csv'); b = pd.read_csv('/home/claude/inv/sales_bld.csv'); r = pd.read_csv('/home/claude/inv/rent_area.csv')
DB_SALES = "Source: Dubai Land Department sales, office units, OSNOVA aggregates"
B = {}
def add(id_, fmt, word, line, cfg, cap, tags=""):
    B[id_] = dict(fmt=fmt, word=word, line=line, cfg=cfg,
                  caption=cap.strip() + f"\n\nFull data on osnova.property, link in bio. Or comment {word} and we will send it to you.\n\n{cfg['src']}. {FOOT}\n\n{TAGS}{(' ' + tags) if tags else ''}")

def clean(v, yrs):
    v = pd.Series(v, index=yrs, dtype=float)
    for y in yrs[1:-1]:
        if v[y] < 0.6 * min(v[y - 1], v[y + 1]): v[y] = np.nan
    return [round(x) for x in v.interpolate(limit_direction='both')]

# 1. race: where offices trade most (deals)
AR = {"Business Bay": "Business Bay", "Al Thanyah Fifth": "JLT", "Al Hebiah First": "Motor City", "Al Thanyah First": "Barsha Heights",
      "Al Barsha South Fourth": "JVC", "Al Hebiah Fourth": "Sports City", "Nadd Hessa": "Silicon Oasis", "Dubai Investment Park First": "DIP",
      "Al Barshaa South Third": "Arjan", "Al Warsan First": "Al Warsan", "Marsa Dubai": "Dubai Marina", "Burj Khalifa": "Downtown"}
d = s[s.segment == 'Office'].groupby(['area_name', 'year']).deals.sum().unstack().fillna(0)
Y16 = list(range(2016, 2026)); DEALS = {AR[a]: [int(d.loc[a, y]) for y in Y16] for a in AR}
add("b2_race_deals", "race", "DATA", "for the full research", dict(series=DEALS, years=Y16, kick="WHERE OFFICES TRADE",
    title="Office deals per year, by district", sub="Registered office sales, DLD", fmt=i0, rh=68,
    hook=("1,430", "office deals in one district in 2025. Which?"), events=[(2020.0, 2021.2, "2020", "The market bottom: 912 deals in all Dubai")],
    end=("2025 · TOP", "Business Bay 1,430"), summary=None, src=DB_SALES + ", 2016–2025"),
    """1,430 office deals in Business Bay in 2025. JLT is second with 1,092.

Registered office sales by district:
Business Bay: 447 (2020) to 1,430 (2025)
JLT: 294 to 1,092
Motor City: 9 to 321
JVC: 8 to 271

The new names on the list are Motor City, JVC and Sports City: off-plan towers moved the market out of the core.""", "#businessbay #jlt")

# 2-3. race: towers of Business Bay and JLT, AED/sq ft
def towers(area, names, pretty):
    x = b[(b.segment == 'Office') & (b.area_name == area) & (b.building_name.isin(names)) & (b.year.between(2018, 2025))]
    pv = x.pivot(index='building_name', columns='year', values='median_psf'); yrs = list(range(2018, 2026))
    return {pretty[n]: clean([pv.loc[n, y] for y in yrs], yrs) for n in names}, yrs
BBN = {'Tamani Arts Office': 'Tamani Arts', 'Churchill Tower 1-Commercial': 'Churchill', 'Park Lane': 'Park Lane', 'THE BINARY BY OMNIYAT': 'The Binary',
       'B2B': 'B2B Tower', 'BURLINGTON TOWER': 'Burlington', 'The Opus By Omniyat': 'The Opus', 'Citadel Tower': 'Citadel', 'BAYSWATER BAY BY OMNIYAT': 'Bayswater', 'WESTBURRY TOWER 1': 'Westburry 1'}
BB, Y18 = towers('Business Bay', list(BBN), BBN)
add("b2_race_bb_towers", "race", "PRICE", "for prices by building", dict(series=BB, years=Y18, base_idx=2, kick="BUSINESS BAY · TOWERS",
    title="Business Bay towers, price per sq ft", sub="Median office sale price, AED, DLD", fmt=i0, rh=80,
    hook=("4,365", "AED per sq ft in one Business Bay tower. Which?"), events=[(2020.0, 2021.2, "2020", "Most towers below 1,000")],
    end=("2025 · TOP", "The Opus 4,365"), summary=dict(kick="BUSINESS BAY · 2020 TO 2025", title="Growth since 2020", sub="Median AED per sq ft, 2020 vs 2025",
    take="The Binary: x4.8 in five years"), src=DB_SALES + ", 2018–2025. Years with under 5 deals interpolated"),
    """4,365 AED per sq ft. The Opus by Omniyat is the most expensive of the ten most traded office towers in Business Bay.

Median price paid, 2020 to 2025:
The Binary by Omniyat: 657 to 3,174 (x4.8)
B2B Tower: 728 to 2,295
Tamani Arts: 720 to 2,035, the most traded tower with 1,045 deals since 2018
Park Lane: 705 to 1,710

Same district, 2.5x difference between towers.""", "#businessbay")
JLN = {'MAZAYA BUSINESS AVENUE AA1': 'Mazaya AA1', 'MAZAYA BUSINESS AVENUE BB2': 'Mazaya BB2', 'Silver Tower': 'Silver Tower', 'Dubai Star': 'Dubai Star',
       'HDS BUSINESS CENTRE': 'HDS Business Ctr', 'HDS Tower': 'HDS Tower', 'ALMAS TOWER': 'Almas Tower', 'Gold Tower': 'Gold Tower', 'PLATINUM TOWER': 'Platinum Tower', 'JUMAIRAH BAY TOWER-X3': 'Jumeirah Bay X3'}
JL, _ = towers('Al Thanyah Fifth', list(JLN), JLN)
add("b2_race_jlt_towers", "race", "PRICE", "for prices by building", dict(series=JL, years=Y18, base_idx=2, kick="JLT · TOWERS",
    title="JLT towers, price per sq ft", sub="Median office sale price, AED, DLD", fmt=i0, rh=80,
    hook=("4,000", "AED per sq ft in one JLT tower. Which?"), events=[(2020.0, 2021.2, "2020", "Dubai Star at 430")],
    end=("2025 · TOP", "Almas Tower 4,000"), summary=dict(kick="JLT · 2020 TO 2025", title="Growth since 2020", sub="Median AED per sq ft, 2020 vs 2025",
    take="Gold Tower: x3.8 in five years"), src=DB_SALES + ", 2018–2025. Years with under 5 deals interpolated"),
    """Almas Tower 4,000 AED per sq ft. Mazaya BB2 1,184. Same lake, 3.4x apart.

Median price paid in JLT towers, 2020 to 2025:
Gold Tower: 666 to 2,532 (x3.8)
Mazaya AA1: 409 to 1,459
Dubai Star: 430 to 1,298
HDS Tower: 478 to 1,302""", "#jlt")

# 4. race: warehouse rent by area (Ejari)
WA = {"Dubai Investment Park Second": "DIP 2", "Dubai Investment Park First": "DIP 1", "Ras Al Khor Industrial First": "Ras Al Khor 1",
      "Jabal Ali Industrial First": "Jebel Ali Ind 1", "Ras Al Khor Industrial Second": "Ras Al Khor 2", "Al Qusais Industrial First": "Al Qusais 1",
      "Um Ramool": "Umm Ramool", "Al Qusais Industrial Second": "Al Qusais 2", "Saih Shuaib 4": "Industrial City", "Al Goze Industrial First": "Al Quoz 1"}
w = r[(r.segment == 'Warehouse') & (r.version == 'New')]; Y18b = list(range(2018, 2026)); WH = {}
for a, n in WA.items():
    q = w[w.area_name == a].set_index('year')
    WH[n] = clean([q.median_psf[y] if y in q.index and q.contracts_physical[y] >= 15 else np.nan for y in Y18b], Y18b)
add("b2_race_wh_rent", "race", "RENT", "for warehouse rents", dict(series=WH, years=Y18b, base_idx=2, kick="WAREHOUSES · EJARI",
    title="Warehouse rent per sq ft a year", sub="Median new lease by area, AED", fmt=i0, rh=80,
    hook=("+%d%%" % round((max(WH.values(), key=lambda v: v[-1] / v[2])[-1] / max(WH.values(), key=lambda v: v[-1] / v[2])[2] - 1) * 100),
          "Warehouse rent growth in one Dubai area since 2020"),
    events=[(2022.0, 2023.2, "2022", "Logistics demand picks up")], end=("2025 · TOP", f"{max(WH, key=lambda k: WH[k][-1])} {WH[max(WH, key=lambda k: WH[k][-1])][-1]}"),
    summary=dict(kick="WAREHOUSES · 2020 TO 2025", title="Rent growth since 2020", sub="Median new-lease AED per sq ft, 2020 vs 2025",
                 take="Industrial rents rose in every area"), src="Source: Ejari new lease contracts (DLD), warehouse units, 2018–2025"),
    "Warehouse rents in Dubai, median new lease per sq ft a year, 2018 to 2025:\n" +
    "\n".join(f"{k}: {v[2]} (2020) to {v[-1]} (2025)" for k, v in sorted(WH.items(), key=lambda kv: -kv[1][-1])[:5]), "#warehouse #logistics")

# 5. dumbbell: warehouses asked vs paid (SITE)
add("b2_wh_dumbbell", "dumbbell", "RENT", "for 9 industrial areas", dict(kick="ASKED VS PAID · WAREHOUSES", title="Asked is an opinion. Paid is a fact.",
    sub="Warehouse rent, AED per sq ft a year", rows=[("Al Quoz", 100, 55), ("Al Qusais", 74, 61), ("Umm Ramool", 70, 58), ("DIP", 68, 51),
    ("Ras Al Khor", 68, 60), ("Al Warsan", 65, 65), ("Industrial City", 62, 50), ("Jebel Ali, JAFZA", 49, 50)], fmt=i0, lo=30, rh=96,
    paid_lab="Paid (Ejari 2026)", ask_lab="Asked (listings)", hook=("+82%", "How far Al Quoz warehouse listings ask above leases"),
    take=("WHAT IT MEANS", "Al Quoz: widest gap. Jebel Ali: leases match listings"), src="Source: portal listings Nov 2026 · Ejari new leases, 2026 YTD · osnova.property"),
    """Al Quoz warehouse listings ask 100 AED per sq ft a year. Tenants sign at 55.

Warehouse rent, asked vs paid (Ejari 2026):
Al Quoz 100 vs 55
DIP 68 vs 51
Industrial City 62 vs 50
Jebel Ali and JAFZA 49 vs 50, the only area where listings match leases""", "#warehouse")

# 6. ranking: shop yields (SITE)
add("b2_rank_shop_yield", "bars", "YIELD", "for yields by district", dict(kick="SHOPS · YIELD 2026", title="Shop gross yield by district",
    sub="Ejari rent ÷ price paid for ready shops, 2026", rows=[("Liwan", 16.4, "1,400 paid · 229 rent"), ("Dubai Marina", 10.8, "2,146 · 232"),
    ("Arjan", 10.0, "1,652 · 165"), ("JVC", 9.5, "2,449 · 232"), ("International City", 9.2, "1,037 · 95"), ("JLT", 9.2, "1,976 · 181"),
    ("Jebel Ali First", 8.8, "2,600 · 229"), ("Majan", 7.6, "2,355 · 179"), ("Meydan Avenue", 7.3, "3,464 · 254"), ("Business Bay", 7.2, "2,944 · 212"),
    ("Meydan / Sobha", 6.4, "4,997 · 321"), ("Al Jaddaf", 5.1, "4,049 · 207")], fmt=p1, hl=[0], rh=72,
    hook=("16.4%", "gross yield on shops in one Dubai district"), take=("RETAIL BEATS OFFICES", "Most districts yield more on shops than on offices"),
    src="Source: DLD ready shop sales and Ejari new leases, 2026 YTD · osnova.property"),
    """16.4% gross yield on shops in Liwan. 5.1% in Al Jaddaf.

Shop gross yield = Ejari rent ÷ price paid for ready shops, 2026:
Liwan 16.4%
Dubai Marina 10.8%
Arjan 10.0%
JVC 9.5%
Business Bay 7.2%

Gross, before service charge and vacancy.""", "#dubairetail")

# 7. ranking: most expensive office buildings 2025 (DB)
EX = [("ENARA by Omniyat", 5855, "Business Bay · 16 deals"), ("HQ by ROVE", 4565, "Business Bay · 96"), ("The Opus", 4365, "Business Bay · 32"),
      ("Almas Tower", 4000, "JLT · 25"), ("Burj Capital", 3769, "Business Bay · 82"), ("31 Above", 3724, "Maritime City · 26"),
      ("ME DO RE", 3689, "JLT · 21"), ("The Onyx 2", 3411, "The Greens · 10"), ("The Binary", 3174, "Business Bay · 47"),
      ("Anantara Business", 3168, "Business Bay · 11"), ("Bay Square 12", 2824, "Business Bay · 12"), ("Vision Tower 1", 2755, "Business Bay · 19")]
add("b2_rank_expensive", "bars", "PRICE", "for prices by building", dict(kick="TOP OF THE MARKET · 2025", title="Most expensive office buildings",
    sub="Median price paid, AED per sq ft, 10+ deals in 2025", rows=EX, fmt=i0, hl=[0], rh=72,
    hook=("5,855", "AED per sq ft. Dubai's most expensive office building"), take=("BUSINESS BAY", "8 of the 12 most expensive office buildings are in Business Bay"),
    src=DB_SALES + ", 2025, buildings with 10+ deals"),
    """5,855 AED per sq ft. ENARA by Omniyat was the most expensive office building traded in Dubai in 2025.

Median price paid, buildings with 10+ deals in 2025:
ENARA by Omniyat 5,855
HQ by ROVE 4,565
The Opus by Omniyat 4,365
Almas Tower, JLT 4,000
Burj Capital 3,769

8 of the top 12 are in Business Bay.""", "#businessbay #omniyat")

# 8. ranking: most traded office buildings 2025 (DB)
TR = [("Capital One", 356, "Motor City / JVC · 1,829"), ("ASPIRZ by Danube", 189, "Sports City · 2,401"), ("I-Rise Tower", 140, "Barsha Heights · 1,829"),
      ("Tamani Arts", 123, "Business Bay · 2,035"), ("Samana Barari Ave", 107, "Majan · 1,730"), ("HQ by ROVE", 96, "Business Bay · 4,565"),
      ("Cove Boulevard", 94, "DLRC · 1,412"), ("Schon Business Park", 90, "DIP · 595"), ("Burj Capital", 82, "Business Bay · 3,769"),
      ("Churchill Tower", 79, "Business Bay · 1,767"), ("Park Lane", 75, "Business Bay · 1,710"), ("Mazaya BB1", 73, "JLT · 1,200")]
add("b2_rank_traded", "bars", "PRICE", "for prices by building", dict(kick="MOST TRADED · 2025", title="Most traded office buildings",
    sub="Registered office sales in 2025 · district · AED per sq ft", rows=TR, fmt=i0, hl=[0], rh=72,
    hook=("356", "offices sold in one Dubai building in 2025"), take=("OFF-PLAN LEADS", "The top 2 are off-plan towers outside the core"),
    src=DB_SALES + ", 2025"),
    """356 offices sold in one building in 2025. Capital One is the most traded office building in Dubai.

Registered office sales in 2025, median price paid:
Capital One: 356 deals, 1,829 AED per sq ft
ASPIRZ by Danube, Sports City: 189, 2,401
I-Rise Tower, Barsha Heights: 140, 1,829
Tamani Arts, Business Bay: 123, 2,035
Schon Business Park, DIP: 90, 595""", "#danube")

# 9. slope: price 2020 -> 2025 (DB)
SL = ["Downtown", "The Greens", "Dubai Marina", "Business Bay", "Barsha Heights", "JLT", "JVC", "Motor City", "Silicon Oasis", "DIP"]
add("b2_slope_price", "slope", "PRICE", "for prices by district", dict(kick="2020 VS 2025", title="Office price per sq ft, 2020 and 2025",
    sub="Median sale price, ready offices, AED", rows=[(k, PRICE[k][4], PRICE[k][-1]) for k in SL], fmt=i0, left="2020", right="2025",
    hook=("+220%", "One district tripled. Which line is it?"), take=("THE STEEPEST LINE", "JVC: 418 to 1,339 AED per sq ft, +220%"),
    src=DB_SALES + ", ready offices, 2020 and 2025"),
    "Office prices per sq ft, 2020 vs 2025, ready offices (DLD):\n" + "\n".join(f"{k}: {PRICE[k][4]:,} to {PRICE[k][-1]:,} (+{(PRICE[k][-1] / PRICE[k][4] - 1) * 100:.0f}%)" for k in SL[:6]))

# 10. slope: rent 2020 -> 2025 (DB)
RA = {"Downtown": "Burj Khalifa", "The Greens": "Al Thanyah Third", "Dubai Marina": "Marsa Dubai", "Business Bay": "Business Bay", "Barsha Heights": "Al Thanyah First",
      "JLT": "Al Thanyah Fifth", "JVC": "Al Barsha South Fourth", "Motor City": "Al Hebiah First", "Silicon Oasis": "Nadd Hessa", "DIP": "Dubai Investment Park First"}
o = r[(r.segment == 'Office') & (r.version == 'New')].set_index(['area_name', 'year'])
RN = {k: (round(o.loc[(v, 2020)].median_psf), round(o.loc[(v, 2025)].median_psf)) for k, v in RA.items()}
add("b2_slope_rent", "slope", "RENT", "for rents by district", dict(kick="2020 VS 2025", title="Office rent per sq ft, 2020 and 2025",
    sub="Median new lease, AED a year, Ejari", rows=[(k, a, z) for k, (a, z) in RN.items()], fmt=i0, left="2020", right="2025",
    hook=("x2.9", "Office rents in one district since 2020"), take=("RENTS FOLLOWED PRICES", "Every district on the chart at least doubled its rent"),
    src="Source: Ejari new lease contracts (DLD), office units, 2020 and 2025"),
    "Office rent per sq ft a year, Ejari new leases, 2020 vs 2025:\n" + "\n".join(f"{k}: {a} to {z} (+{(z / a - 1) * 100:.0f}%)" for k, (a, z) in list(RN.items())[:6]))

# 11. multiline: Business Bay vs JLT vs Downtown (DB)
ML = {k: PRICE[k] for k in ("Downtown", "Business Bay", "JLT")}
add("b2_multiline", "multiline", "PRICE", "for prices by district", dict(kick="THREE DISTRICTS · 10 YEARS", title="Office price per sq ft, 2016–2025",
    sub="Median sale price, ready offices, AED", series=ML, years=YRS, fmt=i0, grid=[1000, 2000, 3000, 4000, 5000],
    hook=("x2.2", "the gap between Downtown and Business Bay"), take=("2025", "Downtown 5,110 · Business Bay 1,820 · JLT 1,425"),
    src=DB_SALES + ", ready offices, 2016–2025"),
    """Downtown, Business Bay, JLT: ten years of office prices on one chart.

Median price paid for ready offices, AED per sq ft:
Downtown: 2,876 (2016) to 5,110 (2025)
Business Bay: 1,058 to 1,820
JLT: 895 to 1,425

All three bottomed in 2020 and broke their 2016 level only after 2023.""", "#businessbay #jlt")

# 12. countdown: top 10 growth since 2020 (DB)
GR = sorted(((k, (v[-1] / v[4] - 1) * 100, f"{v[4]:,} to {v[-1]:,} AED per sq ft") for k, v in PRICE.items()), key=lambda z: -z[1])[:10][::-1]
add("b2_count_growth", "countdown", "PRICE", "for prices by district", dict(kick="TOP 10 · GROWTH SINCE 2020", hook=(f"+{GR[-1][1]:.0f}%", "The #1 office district in Dubai since 2020. Countdown"),
    rows=GR, fmt=lambda v: f"+{v:.0f}%", sum_title="Top 10 since 2020", src=DB_SALES + ", ready offices, 2020 vs 2025"),
    "Top 10 Dubai office districts by price growth, 2020 to 2025 (ready offices, DLD):\n" + "\n".join(f"{i + 1}. {k}: +{g:.0f}%" for i, (k, g, _) in enumerate(GR[::-1][:5])))

# 13. countdown: 10 cheapest districts for a ready office, 2025 (DB)
q = s[(s.segment == 'Office') & (s.reg_type == 'ready') & (s.year == 2025) & (s.deals >= 10)].sort_values('median_psf')
NM = {"Dubai Investment Park First": "DIP", "Al Warsan First": "International City", "Nadd Hessa": "Silicon Oasis", "Al Barshaa South Third": "Arjan",
      "Al Hebiah First": "Motor City", "Al Barsha South Fourth": "JVC", "Al Thanyah Fifth": "JLT", "Port Saeed": "Port Saeed", "Al Thanyah First": "Barsha Heights",
      "Business Bay": "Business Bay", "Al Hebiah Fourth": "Sports City", "Wadi Al Safa 3": "Majan", "Wadi Al Safa 5": "DLRC", "Al Jadaf": "Al Jaddaf", "Nad Al Shiba First": "Nad Al Shiba"}
CH = [(NM.get(a, a), p, f"{int(n):,} ready deals in 2025") for a, p, n in zip(q.area_name, q.median_psf, q.deals)][:10][::-1]
add("b2_count_cheapest", "countdown", "PRICE", "for prices by district", dict(kick="10 CHEAPEST · READY OFFICES", hook=(f"{CH[-1][1]:,.0f} AED", "per sq ft. The cheapest office district in Dubai"),
    rows=CH, fmt=lambda v: f"{v:,.0f}", sum_title="Cheapest per sq ft, 2025", src=DB_SALES + ", ready offices, 2025, districts with 10+ deals"),
    "The 10 cheapest districts to buy a ready office in Dubai, median AED per sq ft, 2025:\n" + "\n".join(f"{i + 1}. {k}: {p:,.0f}" for i, (k, p, _) in enumerate(CH[::-1][:5])))

# 14-15. quiz (SITE)
add("b2_quiz_prices", "quiz", "PRICE", "for prices by district", dict(kick="DUBAI OFFICE QUIZ", hook=("3 questions", "Do you know Dubai office prices?"),
    qs=[dict(q="Median price paid for a ready office in Business Bay, 2026?", opts=["1,249 AED per sq ft", "1,949 AED per sq ft", "2,949 AED per sq ft"], ans=1,
             why="1,949 AED per sq ft, 620 ready sales registered with DLD"),
        dict(q="Office rent tenants actually pay in Downtown, per sq ft a year?", opts=["147 AED", "307 AED", "507 AED"], ans=1,
             why="307 AED by Ejari. Listings ask 422"),
        dict(q="Share of Dubai office sales that are off-plan in 2026?", opts=["24%", "44%", "64%"], ans=2, why="64%: 2,763 of 4,332 office sales")],
    src="Source: DLD transactions and Ejari leases, 2026 YTD · osnova.property"),
    """3 questions on Dubai office prices. How many did you get?

1. Ready office in Business Bay: 1,949 AED per sq ft paid in 2026
2. Downtown office rent: 307 AED per sq ft a year by Ejari, listings ask 422
3. Off-plan share of office sales in 2026: 64%

Write your score in the comments.""")
add("b2_quiz_districts", "quiz", "YIELD", "for yields by district", dict(kick="DUBAI OFFICE QUIZ", hook=("3 questions", "Guess the Dubai office district"),
    qs=[dict(q="Where does AED 1 million buy the most office space?", opts=["Downtown", "JLT", "DIP"], ans=2, why="DIP: 1,377 sq ft. Downtown: 214 sq ft"),
        dict(q="Which district has the highest gross office yield?", opts=["DIP", "Business Bay", "Downtown"], ans=0, why="DIP 13.1%. Business Bay 8.0%, Downtown 6.6%"),
        dict(q="Most traded office project of 2026?", opts=["HQ by ROVE", "Shahrukhz by Danube", "Lumena Alta"], ans=1, why="Shahrukhz by Danube: 559 sales")],
    src="Source: DLD transactions and Ejari leases, 2026 YTD · osnova.property"),
    """Guess the Dubai office district: 3 questions.

1. AED 1M buys the most office in DIP: 1,377 sq ft, against 214 in Downtown
2. Highest gross office yield: DIP, 13.1%
3. Most traded office project of 2026: Shahrukhz by Danube, 559 sales

Write your score in the comments.""")

ORDER = ["b2_race_bb_towers", "b2_quiz_prices", "b2_rank_expensive",
         "b2_slope_price", "b2_wh_dumbbell", "b2_count_growth",
         "b2_race_deals", "b2_rank_shop_yield", "b2_quiz_districts",
         "b2_multiline", "b2_rank_traded", "b2_count_cheapest",
         "b2_race_jlt_towers", "b2_slope_rent", "b2_race_wh_rent"]
assert sorted(ORDER) == sorted(B)
