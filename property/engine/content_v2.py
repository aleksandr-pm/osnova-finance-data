"""First 3 days for @osnova.property, numbers from osnova.property pages updated 14 Nov 2026."""
U = "?utm_source=instagram&utm_medium=dm&utm_campaign="
LINKS = {
    "RENT": "https://osnova.property/commercial-rent-dubai" + U + "rent",
    "YIELD": "https://osnova.property/guide-office-rental-yield-dubai" + U + "yield",
    "COST": "https://osnova.property/guide-cost-of-buying-office-dubai" + U + "cost",
    "CHECK": "https://osnova.property/guide-check-office-price-dld" + U + "check",
    "MARKET": "https://osnova.property/dubai-commercial-property-market-october-2026" + U + "market_oct2026",
    "VALUE": "https://osnova.property/" + U + "value#value-my-asset",
    "REVIEW": "https://osnova.property/offplan" + U + "review",
}
TAGS = "#dubaioffice #dubaicommercialproperty #dubairealestate #businessbay #dubaiinvestment #officespace"
FOOT = "Market statistics, not an offer or investment advice."
SRC_RENT = "Source: portal listings Nov 2026 · Ejari new leases, 2026 YTD · osnova.property"
SRC_DLD = "Source: DLD transactions / Ejari, 2026 YTD · osnova.property"
a0 = lambda v: f"{v:,.0f}"
pct = lambda v: f"{v:.1f}%"

REELS = {
 "r_rent_business_bay": dict(word="RENT", hyp="Asked vs paid по одному району с крупным разрывом даёт больше DM, чем рейтинг.",
   cfg=dict(kick="ASKED VS PAID · OFFICE RENT", title="Business Bay office rent, AED/sq ft", hook=("202 or 155?", "What Business Bay tenants really pay"),
     bars=[("Asked", 202, "stone", "Listings ask 202 AED"), ("Paid", 155, "navy", "Ejari leases: 155 AED")], fmt=a0,
     conclusion=("−23%", "Tenants pay less than listings ask"), src=SRC_RENT),
   cap="""Business Bay office listings ask 202 AED per sq ft a year. Tenants sign at 155.

Asked: 202 AED per sq ft a year, 441 listings
Paid: 155 AED per sq ft a year, Ejari new leases 2026
Gap: 23%

DM RENT and get asked vs paid rents for 17 office districts and 9 warehouse areas."""),
 "r_yield_districts": dict(word="YIELD", hyp="Крючок-загадка с процентом доходности (без названия района) удерживает и ведёт на гайд по доходности.",
   cfg=dict(kick="OFFICE YIELDS · 2026", title="Office gross yield by district", hook=("13.1%", "Which Dubai office district yields this?"),
     bars=[("DIP", 13.1, "navy", "DIP: 13.1% gross"), ("Arjan", 10.6, "sand", "Arjan: 10.6%"), ("Business Bay", 8.0, "sand", "Business Bay: 8.0%"),
           ("Sheikh Zayed Rd", 2.9, "sand", "Sheikh Zayed Road: 2.9%")], fmt=pct,
     conclusion=("4.5x", "DIP out-yields Sheikh Zayed Road"), src=SRC_DLD),
   cap="""13.1% gross. The highest office yield in Dubai is in DIP, not Downtown.

Gross yield = Ejari rent ÷ price paid for ready offices, 2026:
DIP 13.1%
Arjan 10.6%
Business Bay 8.0%
Sheikh Zayed Road 2.9%

DM YIELD and get yields for 12 office districts and 12 retail districts."""),
 "r_market_october": dict(word="MARKET", hyp="Ежемесячный отчёт как повод: проверяем, дают ли итоги месяца переходы на страницу отчёта.",
   cfg=dict(kick="MARKET THIS MONTH", title="Dubai office sales per month", hook=("422", "Office sales in October. Up or down?"),
     bars=[("May", 244, "sand", "May: 244 sales"), ("Jun", 334, "sand", "June: 334"), ("Jul", 382, "sand", "July: 382"), ("Aug", 326, "sand", "August: 326"),
           ("Sep", 423, "sand", "September: 423"), ("Oct", 422, "navy", "October: 422")], fmt=a0,
     conclusion=("0%", "October matched September"), src="Source: DLD transactions, office units, May to Oct 2026 · osnova.property"),
   cap="""422 office sales in Dubai in October. Flat on September.

Median price paid: 2,134 AED per sq ft, ready offices 1,949
Value: AED 1.83bn
New office leases in Ejari: 4,690

DM MARKET and get the full October report: districts, buildings, rents."""),
 "r_rent_barsha_heights": dict(word="RENT", hyp="Самый большой разрыв asked/paid (−51%) как крючок: сильнее ли он, чем Business Bay.",
   cfg=dict(kick="ASKED VS PAID · OFFICE RENT", title="Barsha Heights office rent, AED/sq ft", hook=("274 or 134?", "What Barsha Heights tenants really pay"),
     bars=[("Asked", 274, "stone", "Listings ask 274 AED"), ("Paid", 134, "navy", "Ejari leases: 134 AED")], fmt=a0,
     conclusion=("−51%", "Paid rent is half the asking"), src=SRC_RENT),
   cap="""Barsha Heights office listings ask 274 AED per sq ft a year. Tenants sign at 134.

Asked: 274 AED per sq ft a year, 62 listings
Paid: 134 AED per sq ft a year, Ejari new leases 2026
Gap: 51%, the widest of the big office districts

DM RENT and get asked vs paid rents for 17 office districts."""),
 "r_rent_al_quoz_warehouse": dict(word="RENT", hyp="Склады: проверяем, есть ли спрос у аудитории на индустриальный сегмент.",
   cfg=dict(kick="ASKED VS PAID · WAREHOUSES", title="Al Quoz warehouse rent, AED/sq ft", hook=("100 or 55?", "What Al Quoz warehouses really rent for"),
     bars=[("Asked", 100, "stone", "Listings ask 100 AED"), ("Paid", 55, "navy", "Ejari leases: 55 AED")], fmt=a0,
     conclusion=("−45%", "Warehouse tenants pay far less"), src=SRC_RENT),
   cap="""Al Quoz warehouse listings ask 100 AED per sq ft a year. Tenants sign at 55.

Asked: 100 AED per sq ft a year, 351 listings
Paid: 55 AED per sq ft a year, Ejari new leases 2026
DIP warehouses: asked 68, paid 51

DM RENT and get warehouse rents for 9 industrial areas, asked vs paid."""),
 "r_offplan_premium": dict(word="CHECK", hyp="Ошибка покупателя (премия off-plan +90%) ведёт на гайд проверки цены по DLD.",
   cfg=dict(kick="BUYER MISTAKES · OFF-PLAN", title="Office price paid per sq ft, 2026", hook=("+90%", "What off-plan offices cost over ready"),
     bars=[("Off-plan", 3354, "stone", "Off-plan: 3,354 AED paid"), ("Ready", 1764, "navy", "Ready: 1,764 AED paid")], fmt=a0,
     conclusion=("64%", "of 2026 office sales are off-plan"), src=SRC_DLD, cta_line="for the price check guide"),
   cap="""+90%. Off-plan offices in Dubai sell for almost twice the price of ready ones per sq ft.

Off-plan: 3,354 AED per sq ft paid
Ready: 1,764 AED per sq ft paid
Off-plan share of office sales in 2026: 64%

Part of the gap is location, part is the payment plan. DM CHECK and get the guide to checking any office price against DLD."""),
}

POSTS = {
 "p_yield_ranking": dict(word="YIELD", hyp="Таблица-рейтинг сохраняется и ведёт на гайд доходности: сравниваем сохранения и DM с рилсом.",
   cfg=dict(kick="OSNOVA · OFFICE YIELDS 2026", headline=["DIP offices yield 13.1%.", "Sheikh Zayed Road: 2.9%"],
     sub="Gross yield = Ejari rent ÷ price paid for ready offices, 2026 to date", kind="rank", fmt=pct, src=SRC_DLD,
     rows=[("DIP", 13.1, True), ("International City", 12.6, False), ("Arjan", 10.6, False), ("Silicon Oasis", 9.1, False),
           ("Business Bay", 8.0, False), ("JLT", 7.5, False), ("Downtown", 6.6, False), ("Sheikh Zayed Rd", 2.9, False)]),
   cap="""DIP offices yield 13.1% gross. Sheikh Zayed Road yields 2.9%.

Ejari rent divided by the price buyers paid for ready offices, 2026:
Business Bay 8.0% (1,949 paid, 155 rent)
JLT 7.5%
Downtown 6.6%
Higher yield usually means older stock or weaker resale, so check the number of ready sales first.

DM YIELD and get the full table for 12 office districts."""),
 "p_rent_asked_paid": dict(word="RENT", hyp="Asked vs paid по 8 районам в одном посте: проверяем, сохраняют ли таблицу и пишут ли RENT.",
   cfg=dict(kick="OSNOVA · ASKED VS PAID", headline=["Dubai office tenants pay", "22% to 53% less than listings ask"],
     sub="Office rent, AED per sq ft a year: listings vs Ejari new leases 2026", kind="pair", fmt=a0, src=SRC_RENT,
     rows=[("Downtown", 422, 307), ("Barsha Heights", 274, 134), ("Sheikh Zayed Rd", 250, 157), ("Internet City", 230, 180),
           ("Business Bay", 202, 155), ("JLT", 169, 128), ("Bur Dubai", 135, 88), ("Deira", 131, 62)]),
   cap="""Dubai office tenants pay 22% to 53% less than listings ask.

Asked vs paid, AED per sq ft a year:
Deira 131 vs 62
Barsha Heights 274 vs 134
Business Bay 202 vs 155
Internet City 230 vs 180

Negotiating a lease? Start from what was signed, not what is listed. DM RENT and get all 17 districts."""),
 "p_market_october": dict(word="MARKET", hyp="Пост с итогами месяца: проверяем интерес к ежемесячной рубрике.",
   cfg=dict(kick="OSNOVA · MARKET THIS MONTH", headline=["422 office sales in October,", "flat on September"],
     sub="Office sales registered with DLD per month, 2026", kind="rank", fmt=a0, src="Source: DLD transactions, office units, 2026 · osnova.property",
     rows=[("May", 244, False), ("June", 334, False), ("July", 382, False), ("August", 326, False), ("September", 423, False), ("October", 422, True)]),
   cap="""422 office sales in Dubai in October, flat on September.

Median paid: 2,134 AED per sq ft, ready 1,949
Value: AED 1.83bn
Year to date: 4,332 office sales worth AED 22.61bn, 64% off-plan

DM MARKET and get the October report with districts and the most traded buildings."""),
}

# day = (reel 11:41, post 15:11, reel 19:41 Dubai)
SCHEDULE = [("r_rent_business_bay", "p_yield_ranking", "r_market_october"),
            ("r_yield_districts", "p_rent_asked_paid", "r_rent_barsha_heights"),
            ("r_rent_al_quoz_warehouse", "p_market_october", "r_offplan_premium")]


def caption(item):
    return f"{item['cap']}\n\n{SRC_RENT.replace('Source: ', 'Source: ') if item['word'] == 'RENT' else SRC_DLD}. {FOOT}\n\n{TAGS}"
