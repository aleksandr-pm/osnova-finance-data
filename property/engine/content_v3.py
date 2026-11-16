"""Days 4-8: 20 reels (16 new + 4 rendered earlier). Numbers from osnova.property pages, read 16 Nov 2026."""
U = "?utm_source=instagram&utm_medium=dm&utm_campaign="
LINKS = {
    "RENT": "https://osnova.property/commercial-rent-dubai" + U + "rent",
    "YIELD": "https://osnova.property/guide-office-rental-yield-dubai" + U + "yield",
    "COST": "https://osnova.property/guide-cost-of-buying-office-dubai" + U + "cost",
    "CHECK": "https://osnova.property/guide-check-office-price-dld" + U + "check",
    "MARKET": "https://osnova.property/dubai-commercial-property-market-october-2026" + U + "market_oct2026",
    "VALUE": "https://osnova.property/" + U + "value#value-my-asset",
    "REVIEW": "https://osnova.property/offplan" + U + "review",
    "PRICE": "https://osnova.property/areas" + U + "price",
    "DATA": "https://osnova.property/blog" + U + "data",
    "WEALTH": "https://osnova.property/blog-uae-sovereign-wealth" + U + "wealth",
}
FOOT = "Market statistics, not an offer or investment advice."
TAGS = "#dubaioffice #dubaicommercialproperty #dubairealestate #dubaiinvestment #officespace"
i0 = lambda v: f"{v:,.0f}"
p1 = lambda v: f"{v:.1f}%"
def usd(v): return f"${v / 1000:.2f}T".replace("0T", "T") if v >= 1000 else f"${v:,.0f}B"
def k(v): return f"{v / 1000:.1f}K" if v >= 1000 else f"{v:,.0f}"
plus = lambda v: f"+{v:.0f}%"
mult = lambda v: f"{v:.1f}x"

N, S, ST = "navy", "sand", "stone"
R = {}
def reel(id_, word, kick, title, hook, bars, fmt, conc, src, cap, extra_tags="", cta=None):
    cfg = dict(kick=kick, title=title, hook=hook, bars=bars, fmt=fmt, conclusion=conc, src=src)
    if cta: cfg["cta_line"] = cta
    R[id_] = dict(word=word, cfg=cfg, cap=cap.strip() + f"\n\n{src}. {FOOT}\n\n{TAGS}{(' ' + extra_tags) if extra_tags else ''}")

reel("r_uae_wealth", "WEALTH", "UAE · SOVEREIGN WEALTH", "UAE sovereign funds, assets",
     ("$2.65T", "How much money does the UAE have?"),
     [("ADIA", 1200, N, "ADIA: $1.2 trillion"), ("ICD", 429, S, "ICD, Dubai: $429B"), ("Mubadala", 385, S, "Mubadala: $385B"),
      ("LIMAD", 300, S, "LIMAD: $300B"), ("Dubai Holding", 136, S, "Dubai Holding: $136B"), ("EIA", 116, S, "EIA: $116B")], usd,
     ("4.4x", "the UAE's annual GDP"), "Source: Global SWF ranking, April 2026 · osnova.property",
     """$2.65 trillion. That is how much the UAE holds in sovereign funds, 4.4 times its annual GDP.

ADIA alone manages $1.2 trillion, #4 in the world
Seven UAE funds sit in the global top 25
As one block, UAE funds would rank #1 globally, ahead of Norway

Why it matters for property: Mubadala, ICD and Dubai Holding hold large real estate portfolios and are not forced sellers.

DM WEALTH and get the full breakdown.""", "#uae #sovereignwealth #abudhabi", cta="for the full breakdown")

reel("r_shahrukhz_top", "REVIEW", "MOST TRADED · 2026", "Most traded office projects, 2026",
     ("559", "offices sold in one Dubai tower this year"),
     [("Shahrukhz", 559, N, "Shahrukhz by Danube: 559"), ("HQ by Rove", 251, S, "HQ by ROVE: 251"), ("RAW 2", 195, S, "RAW District 2: 195"),
      ("RAW District", 180, S, "RAW District: 180"), ("Samana Hub", 177, S, "Samana Business Hub: 177"), ("Lumena Alta", 155, S, "Lumena Alta: 155")], i0,
     ("2.2x", "more sales than number two"), "Source: DLD transactions, office sales 2026 YTD · osnova.property",
     """559 office sales in one tower. Shahrukhz by Danube is the most traded office project in Dubai in 2026.

Office sales registered with DLD, 2026:
Shahrukhz by Danube, Internet City: 559, median 4,135 AED per sq ft
HQ by ROVE, Business Bay: 251, 4,699 AED
RAW District 2, Downtown Jebel Ali: 195, 2,097 AED
Samana Business Hub: 177, 1,924 AED

DM REVIEW and get our reviews of Dubai office projects.""", "#danube #shahrukhz #offplan", cta="for project reviews")

reel("r_office_4x", "PRICE", "DUBAI OFFICES · 2015 TO 2026", "Median office price, AED/sq ft",
     ("4.3x", "Dubai office prices since 2020"),
     [("2015", 1092, S, "2015: 1,092 AED"), ("2020", 650, ST, "2020: 650, the low"), ("2022", 830, S, "2022: 830"),
      ("2024", 1287, S, "2024: 1,287"), ("2025", 1706, S, "2025: 1,706"), ("2026", 2798, N, "2026 so far: 2,798")], i0,
     ("AED 17.7bn", "office deals, Jan to Aug 2026"), "Source: DLD registered sales, office units; 2026 is Jan to Aug · osnova.property",
     """650 to 2,798 AED per sq ft. Dubai office prices are up 4.3x from the 2020 low.

2015: 1,092 AED, then five years down
2020: 650 AED, the bottom
2025: 1,706 AED, a record 4,560 deals
2026, Jan to Aug: 2,798 AED and AED 17.68bn traded, more than all of 2024

Part of the jump is off-plan towers pulling the median up. DM PRICE and get prices paid by district.""", cta="for prices by district")

reel("r_aed1m_buys", "PRICE", "WHAT AED 1M BUYS", "Sq ft of ready office for AED 1M",
     ("214 sq ft", "That is AED 1M in Downtown Dubai"),
     [("Downtown", 214, S, "Downtown: 214 sq ft"), ("Business Bay", 513, S, "Business Bay: 513"), ("JLT", 587, S, "JLT: 587"),
      ("JVC", 665, S, "JVC: 665"), ("Silicon Oasis", 953, S, "Silicon Oasis: 953"), ("DIP", 1377, N, "DIP: 1,377 sq ft")], i0,
     ("6.4x", "more office in DIP than Downtown"), "Source: DLD ready office sales, median AED/sq ft, 2026 YTD · osnova.property",
     """AED 1 million buys 214 sq ft of ready office in Downtown Dubai. In DIP it buys 1,377.

Median price paid for ready offices, 2026:
Downtown 4,674 AED per sq ft
Business Bay 1,949
JLT 1,703
Silicon Oasis 1,049
DIP 726

Cheaper districts also yield more: DIP 13.1% gross vs Downtown 6.6%. DM PRICE and get prices paid by district.""", cta="for prices by district")

reel("r_lumena_alta_top", "REVIEW", "THE TOP OF THE MARKET", "Office price paid per sq ft, 2026",
     ("6,122", "AED per sq ft for a Business Bay office"),
     [("Lumena Alta", 6122, N, "Lumena Alta: 6,122 AED"), ("HQ by Rove", 4699, S, "HQ by ROVE: 4,699"), ("Shahrukhz", 4135, S, "Shahrukhz: 4,135"),
      ("Burj Capital", 3598, S, "Burj Capital: 3,598"), ("Ready, Dubai", 1764, ST, "Ready office, Dubai: 1,764")], i0,
     ("3.5x", "the price of a ready Dubai office"), "Source: DLD transactions, office sales 2026 YTD · osnova.property",
     """6,122 AED per sq ft. Lumena Alta by Omniyat is the most expensive office project traded in Dubai in 2026.

Median price paid, 2026:
Lumena Alta, Business Bay: 6,122 AED per sq ft, 155 sales
HQ by ROVE: 4,699
Shahrukhz by Danube: 4,135
Ready office, all Dubai: 1,764

DM REVIEW and get our review of Lumena Alta and other office projects.""", "#omniyat #businessbay", cta="for project reviews")

reel("r_metro_price", "PRICE", "PRICE BY METRO STATION", "Office price by nearest metro, AED/sq ft",
     ("4,359", "AED per sq ft next to one metro stop"),
     [("Emirates Towers", 4359, N, "Emirates Towers: 4,359"), ("Creek", 2862, S, "Creek: 2,862"), ("Burj Khalifa", 2380, S, "Burj Khalifa: 2,380"),
      ("Internet City", 1845, S, "Internet City: 1,845"), ("Business Bay", 1746, S, "Business Bay: 1,746"), ("Rashidiya", 1463, S, "Rashidiya: 1,463")], i0,
     ("3x", "between top and bottom station"), "Source: DLD registered sales matched to nearest metro station · osnova.property",
     """Emirates Towers 4,359 AED per sq ft. Rashidiya 1,463. Same metro line, 3x the price.

Median office price by nearest metro station:
Emirates Towers 4,359 (111 deals)
Burj Khalifa / Dubai Mall 2,380 (1,236 deals)
Business Bay 1,746 (2,471 deals, the deepest market)
Rashidiya 1,463

Which station is your office near? DM PRICE and get prices paid by district.""", "#dubaimetro", cta="for prices by district")

reel("r_rent_downtown_alquoz", "RENT", "OFFICE RENT · 2026", "Office rent paid, AED/sq ft a year",
     ("5.5x", "Same city, very different rent"),
     [("Downtown", 307, N, "Downtown: 307 AED"), ("The Greens", 300, S, "The Greens: 300"), ("Internet City", 180, S, "Internet City: 180"),
      ("Business Bay", 155, S, "Business Bay: 155"), ("JLT", 128, S, "JLT: 128"), ("Al Quoz", 56, S, "Al Quoz: 56")], i0,
     ("5.5x", "Downtown rent vs Al Quoz"), "Source: Ejari new single-unit leases, 2026 YTD · osnova.property",
     """307 AED per sq ft a year in Downtown. 56 in Al Quoz. Office rents tenants actually signed in 2026.

Ejari new leases, AED per sq ft a year:
Downtown 307
The Greens 300
Internet City and Media City 180
Business Bay 155
JLT 128
Al Quoz 56

DM RENT and get asked vs paid rents for 17 office districts.""")

reel("r_10y_winners", "PRICE", "10-YEAR WINNERS", "Office price growth, 10 years",
     ("+209%", "The 10-year winner is not Business Bay"),
     [("DIFC / WTC", 209, N, "DIFC / WTC: +209%"), ("JVC", 195, S, "JVC: +195%"), ("Emirates Hills", 190, S, "Emirates Hills: +190%"),
      ("Al Warsan", 134, S, "Al Warsan: +134%"), ("Motor City", 121, S, "Motor City: +121%"), ("Business Bay", 104, ST, "Business Bay: +104%")], plus,
     ("#6", "Business Bay's place on the list"), "Source: DLD registered sales, median AED/sq ft, 2015-16 vs 2025-26 · osnova.property",
     """+209% in ten years. The office district that grew most in Dubai is DIFC / WTC, not Business Bay.

Median price growth, 2015-16 to 2025-26:
DIFC / WTC +209% (1,450 to 4,484 AED per sq ft)
JVC +195%
Emirates Hills +190%
Business Bay +104%, sixth

DM PRICE and get prices paid by district.""", "#difc", cta="for prices by district")

reel("r_hidden_costs", "COST", "BUYER MISTAKES · COSTS", "One-off costs on a AED 2M office",
     ("AED 130K", "on top of a AED 2M office"),
     [("DLD 4%", 80000, N, "DLD transfer fee 4%: 80,000"), ("Agent 2%", 42000, S, "Agent 2% + VAT: 42,000"), ("Trustee", 4410, S, "Trustee office: 4,410"),
      ("Mortgage", 2790, S, "Mortgage registration: 2,790"), ("Admin, deed", 850, S, "Admin and title deed: 850")], k,
     ("+AED 100K", "VAT 5%, if the seller is registered"), "Source: DLD fees and market practice, Nov 2026 · osnova.property",
     """The price on the listing is not the cheque you write. On a AED 2M ready office the one-off bill is AED 130K, 6.5%.

DLD transfer fee 4%: AED 80,000
Agent 2% + VAT: AED 42,000
Trustee office: AED 4,410
Mortgage registration on a 50% loan: AED 2,790
Plus VAT 5% on commercial property if the seller is VAT-registered: another AED 100,000

DM COST and get the full cost breakdown.""", cta="for the full cost breakdown")

reel("r_offplan_share", "DATA", "OFF-PLAN BOOM", "Off-plan share of office sales",
     ("0.1% to 65%", "Off-plan share of Dubai office sales"),
     [("2018", 6.7, S, "2018: 6.7%"), ("2021", 0.1, ST, "2021: 0.1%, almost zero"), ("2023", 4.1, S, "2023: 4.1%"),
      ("2024", 6.0, S, "2024: 6.0%"), ("2025", 31.0, S, "2025: 31%"), ("2026", 64.9, N, "2026 so far: 64.9%")], p1,
     ("2 years", "from 6% to 65% of the market"), "Source: DLD registered sales, office units; 2026 is Jan to Aug · osnova.property",
     """In 2021 almost no one bought Dubai offices off-plan: 0.1% of sales. In 2026 it is 65%.

Off-plan share of office sales:
2015: 21%
2021: 0.1%
2024: 6%
2025: 31%
2026, Jan to Aug: 64.9%

Off-plan used to be the discount. Now it is the premium. DM DATA and get the full research.""", "#offplan", cta="for the full research")

reel("r_jebel_ali_zero", "PRICE", "A NEW OFFICE DISTRICT", "Downtown Jebel Ali office sales, 2026",
     ("0 to 341", "office sales in one district since June"),
     [("May", 0, ST, "May: 0 sales"), ("June", 26, S, "June: 26"), ("July", 109, S, "July: 109"), ("August", 100, S, "August: 100"),
      ("September", 106, N, "September: 106")], i0,
     ("100%", "off-plan, median 2,000 AED/sq ft"), "Source: DLD registered sales, office units, Jan to Sep 2026 · osnova.property",
     """Zero office sales until June. 341 by September. Downtown Jebel Ali became a new office district in four months.

Registered office sales, 2026:
Jan to May: 0
June 26, July 109, August 100, September 106
Median price paid: 2,000 AED per sq ft
Off-plan share: 100%, mostly RAW District by Imtiaz and Samana Business Hub

DM PRICE and get prices paid by district.""", "#jebelali", cta="for prices by district")

reel("r_cash_buyers", "DATA", "WHO BUYS OFFICES", "Office deals with a mortgage, %",
     ("12%", "of Dubai offices bought with a mortgage"),
     [("2016", 36.9, S, "2016: 36.9%"), ("2018", 39.4, S, "2018: 39.4%, the peak"), ("2020", 28.1, S, "2020: 28.1%"),
      ("2022", 20.4, S, "2022: 20.4%"), ("2024", 15.2, S, "2024: 15.2%"), ("2026", 12.0, N, "2026: 12%")], p1,
     ("4.1x", "bigger average deal than in 2020"), "Source: DLD registered sales, mortgage vs cash; 2026 is Jan to Aug · osnova.property",
     """Only 12% of Dubai office purchases in 2026 use a mortgage. In 2018 it was 39.4%.

Mortgage share of office deals: 39.4% (2018), 28.1% (2020), 12.1% (2023), 12.0% (2026)
Average office deal: AED 631,680 in 2020, AED 2,561,280 in 2026

Bigger cheques, more deals, less debt: a cash buyers' market. DM DATA and get the full research.""", cta="for the full research")

reel("r_top_ready_buildings", "PRICE", "MOST TRADED · READY", "Most traded ready office buildings, 2026",
     ("62", "ready offices sold in one building this year"),
     [("Bay Square", 62, N, "Bay Square: 62 sales"), ("Tamani Arts", 57, S, "Tamani Arts: 57"), ("JBC 5", 39, S, "Jumeirah Business Centre 5: 39"),
      ("The One Tower", 38, S, "The One Tower: 38"), ("JBC 1", 37, S, "Jumeirah Business Centre 1: 37"), ("Burlington", 36, S, "Burlington Tower: 36")], i0,
     ("2,800", "AED per sq ft paid at Bay Square"), "Source: DLD transactions, ready office sales 2026 YTD · osnova.property",
     """62 ready offices sold in Bay Square this year, the most of any ready building in Dubai.

Most traded ready office buildings, 2026, median price paid:
Bay Square, Business Bay: 62 sales, 2,800 AED per sq ft
Tamani Arts Offices, Business Bay: 57, 2,050
Jumeirah Business Centre 5, JLT: 39, 2,707
The One Tower, Barsha Heights: 38, 2,040
Burlington Tower, Business Bay: 36, 1,944

DM PRICE and get prices paid by district and building.""", "#businessbay #jlt", cta="for prices by building")

reel("r_sports_city", "DATA", "A WARNING SIGN", "Office price growth since the 2020 low",
     ("5.2x", "Sports City office prices since 2020"),
     [("Sports City", 5.24, N, "Sports City: 5.2x"), ("Emirates Hills", 3.48, S, "Emirates Hills: 3.5x"), ("Barsha Heights", 3.37, S, "Barsha Heights: 3.4x"),
      ("Business Bay", 3.11, S, "Business Bay: 3.1x"), ("Downtown", 2.86, S, "Downtown: 2.9x"), ("JLT", 2.86, S, "JLT: 2.9x")], mult,
     ("−62%", "Sports City office rent in 10 years"), "Source: DLD prices, Ejari rents · osnova.property",
     """Sports City office prices are up 5.2x since 2020, the most in Dubai. Its office rent is down 62% over ten years, also the most.

Price, 2020 low to now: 453 to 2,374 AED per sq ft
Rent, 10-year change: −62%
Whole market rent over the same span: −18%

When price and rent move in opposite directions this long, one of them is wrong. DM DATA and get the full research.""", "#sportscity", cta="for the full research")

reel("r_dubai_vs_abudhabi", "DATA", "DUBAI VS ABU DHABI", "Residential price, AED per sq m",
     ("~2x", "Dubai vs Abu Dhabi, price per sq m"),
     [("Dubai 2008", 18000, S, "2008: both near 18,000"), ("Abu Dhabi 2008", 18000, ST, "Abu Dhabi 2008: 18,000"),
      ("Dubai 2026", 25000, N, "Dubai 2026: 25,000"), ("Abu Dhabi 2026", 13500, ST, "Abu Dhabi 2026: 13,500")], i0,
     ("~100%", "the widest gap on record"), "Source: BIS, local agents, UBS via OSNOVA Analytics",
     """25,000 AED per sq m in Dubai. 13,500 in Abu Dhabi. The gap is close to 100%, the widest on record.

2003 to 2008: the two moved together, both near 18,000 at the 2008 peak
2009 to 2020: a gap of a few thousand dirhams either way
2021 to 2026: Dubai breaks away

Abu Dhabi is building fast: Aldar and Mubadala just committed AED 60bn to Al Maryah Island. DM DATA and get the full research.""", "#abudhabi #uae", cta="for the full research")

reel("r_retail_vs_office", "DATA", "SHOPS VS OFFICES · 2010 TO 2026", "Median price, AED/sq ft",
     ("3.6x vs 2.1x", "Shops vs offices since 2010"),
     [("Shops 2010", 829, S, "Shops, 2010: 829 AED"), ("Shops 2026", 3000, N, "Shops, 2026: 3,000"), ("Offices 2010", 1123, ST, "Offices, 2010: 1,123"),
      ("Offices 2020", 650, ST, "Offices, 2020: 650"), ("Offices 2026", 2386, S, "Offices, 2026: 2,386")], i0,
     ("14 years", "for a 2010 office buyer to break even"), "Source: DLD registered sales, office and shop units; 2026 to 23 Oct · osnova.property",
     """A Dubai shop bought in 2010 is up 3.6x. An office bought the same year took 14 years just to break even.

Median price, AED per sq ft:
Shops: 829 (2010) to 3,000 (2026)
Offices: 1,123 (2010), 650 (2020), 2,386 (2026)
A 2020 office buyer is up 3.7x on the same median

Entry point decides the return. DM DATA and get the full research.""", "#dubairetail", cta="for the full research")

# 4 reels rendered earlier, reused as they are
REUSED = {"r_rent_barsha_heights": "RENT", "r_offplan_premium": "CHECK", "r_rent_al_quoz_warehouse": "RENT", "r_rent_business_bay_v2": "RENT"}

ORDER = ["r_uae_wealth", "r_rent_barsha_heights", "r_shahrukhz_top", "r_office_4x",
         "r_aed1m_buys", "r_offplan_premium", "r_lumena_alta_top", "r_metro_price",
         "r_rent_downtown_alquoz", "r_10y_winners", "r_rent_al_quoz_warehouse", "r_hidden_costs",
         "r_offplan_share", "r_rent_business_bay_v2", "r_jebel_ali_zero", "r_cash_buyers",
         "r_top_ready_buildings", "r_sports_city", "r_dubai_vs_abudhabi", "r_retail_vs_office"]
