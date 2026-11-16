"""Alternative-format reels (pe2 engine): ranked bars x2, dumbbell asked vs paid. Site numbers, 16 Nov 2026."""
from content_v3 import FOOT, TAGS
i0 = lambda v: f"{v:,.0f}"
A = {}
A["alt_metro_ranked"] = dict(fmt="bars", word="PRICE", line="for prices by district", cfg=dict(
    kick="PRICE BY METRO STATION", title="Office price by nearest metro station", sub="Median sale price, AED per sq ft, DLD",
    rows=[("Emirates Towers", 4359, "111 deals"), ("Creek", 2862, ""), ("Burj Khalifa", 2380, "1,236 deals"), ("Nakheel", 2364, ""),
          ("UAE Exchange", 2000, ""), ("Internet City", 1845, "1,911 deals"), ("Business Bay", 1746, "2,471 deals"),
          ("Deira City Ctr", 1651, "34 deals"), ("JLT", 1500, ""), ("Rashidiya", 1463, "")],
    fmt=i0, hl=[0], rh=78, hook=("4,359", "AED per sq ft next to one metro station. Which?"),
    take=("SAME METRO, 3X THE PRICE", "Emirates Towers vs Rashidiya. Business Bay has the deepest market: 2,471 deals"),
    src="Source: DLD registered sales matched to nearest metro station · osnova.property"),
  cap="""Emirates Towers 4,359 AED per sq ft. Rashidiya 1,463. Same metro, 3x the office price.

Median office price by nearest metro station:
Emirates Towers 4,359 (111 deals)
Creek 2,862
Burj Khalifa / Dubai Mall 2,380 (1,236 deals)
Business Bay 1,746 (2,471 deals, the deepest market)
Rashidiya 1,463

Which station is your office near? DM PRICE and get prices paid by district.""")

A["alt_top_buildings_ranked"] = dict(fmt="bars", word="PRICE", line="for prices by building", cfg=dict(
    kick="MOST TRADED · READY OFFICES", title="Most traded ready office buildings", sub="Ready office sales registered with DLD, 2026",
    rows=[("Bay Square", 62, "2,800 AED/sq ft"), ("Tamani Arts", 57, "2,050 AED/sq ft"), ("JBC 5", 39, "2,707 AED/sq ft"),
          ("The One Tower", 38, "2,040 AED/sq ft"), ("JBC 1", 37, "2,730 AED/sq ft"), ("Burlington", 36, "1,944 AED/sq ft"),
          ("Churchill", 34, "1,852 AED/sq ft"), ("Dubai Star", 34, "1,700 AED/sq ft")],
    fmt=lambda v: f"{v:,.0f} sales", hl=[0], rh=92, hook=("62", "ready offices sold in one building this year"),
    take=("BUSINESS BAY LEADS", "4 of the 8 most traded ready office buildings are in Business Bay"),
    src="Source: DLD transactions, ready office sales 2026 YTD · osnova.property"),
  cap="""62 ready offices sold in Bay Square this year, the most of any ready building in Dubai.

Most traded ready office buildings, 2026, median price paid:
Bay Square, Business Bay: 62 sales, 2,800 AED per sq ft
Tamani Arts Offices, Business Bay: 57, 2,050
Jumeirah Business Centre 5, JLT: 39, 2,707
The One Tower, Barsha Heights: 38, 2,040
Burlington Tower, Business Bay: 36, 1,944

DM PRICE and get prices paid by district and building.""")

A["alt_rent_dumbbell"] = dict(fmt="dumbbell", word="RENT", line="for all 17 districts", cfg=dict(
    kick="ASKED VS PAID · OFFICE RENT", title="Asked is an opinion. Paid is a fact.", sub="Office rent, AED per sq ft a year",
    rows=[("Downtown", 422, 307), ("Barsha Heights", 274, 134), ("Sheikh Zayed Rd", 250, 157), ("Internet City", 230, 180),
          ("Business Bay", 202, 155), ("JLT", 169, 128), ("Al Quoz", 136, 56), ("Bur Dubai", 135, 88), ("Deira", 131, 62), ("DIP", 108, 92)],
    fmt=i0, lo=40, rh=82, paid_lab="Paid (Ejari 2026)", ask_lab="Asked (listings)",
    hook=("+111%", "How far Deira listings ask above real leases"),
    take=("WHAT IT MEANS", "In all 10 districts tenants sign below the asking rent"),
    src="Source: portal listings Nov 2026 · Ejari new leases, 2026 YTD · osnova.property"),
  cap="""Listings ask. Tenants pay less. In all 10 big office districts of Dubai.

Office rent, AED per sq ft a year, asked vs paid (Ejari 2026):
Downtown 422 vs 307
Barsha Heights 274 vs 134
Business Bay 202 vs 155
Al Quoz 136 vs 56
Deira 131 vs 62

Negotiating a lease? Start from what was signed. DM RENT and get all 17 districts.""")

for k, v in A.items():
    v["caption"] = v["cap"].strip() + f"\n\n{v['cfg']['src']}. {FOOT}\n\n{TAGS}"
