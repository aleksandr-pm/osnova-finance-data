import sys, json; sys.path.insert(0,'/home/claude/prop'); sys.path.insert(0,'/home/claude/en1')
import pandas as pd, numpy as np, pe
nf0=lambda v:f"{v:,.0f}"
from data import SER as PRICE, YRS
AGG='/mnt/user-data/outputs/dld_aggregates_2026'
TAGS="#dubai #dubaiproperty #dubaioffice #commercialrealestate #dubairealestate #propertydata #uae #investment"
FOOT="Market statistics for information only. Not an offer to buy, sell or lease property, and not investment advice."
AREA={"Downtown":"Burj Khalifa","The Greens":"Al Thanyah Third","Dubai Marina":"Marsa Dubai","Sheikh Zayed Rd":"Trade Center First","Business Bay":"Business Bay",
      "Barsha Heights":"Al Thanyah First","JLT":"Al Thanyah Fifth","JVC":"Al Barsha South Fourth","Arjan":"Al Barshaa South Third","Motor City":"Al Hebiah First",
      "Silicon Oasis":"Nadd Hessa","DIP":"Dubai Investment Park First"}
R={}

# 1. office price race (DLD)
R["office_price_race"]=dict(fmt="race",music=0,cfg=dict(series=PRICE,years=YRS,base_idx=4,kick="DUBAI OFFICES · DLD DATA",title="Office price per sq ft",
    sub="Median sale price by area, ready offices, AED",hook=("+220%","One Dubai office area since 2020. Which one?"),
    events=[(2020.0,2021.2,"2020","Prices hit the bottom"),(2023.0,2024.0,"2023","Downtown passes 3,600")],end=("2025 · TOP","Downtown 5,110"),
    summary=dict(kick="DUBAI OFFICES · 2020 TO 2025",title="Growth since 2020",sub="Median AED per sq ft, 2020 vs 2025",take="JVC: office prices x3.2 in five years"),
    src="Source: Dubai Land Department sales, ready offices, median AED per sq ft, 2016–2025. Years with under 5 deals interpolated."),
  cap="""+220%. One Dubai office area tripled in price since 2020. Which one?

Median sale price per sq ft, ready offices, 12 areas, 2016 to 2025:
JVC: 418 to 1,339 AED (+220%)
The Greens: 1,000 to 3,146 AED (+215%)
Barsha Heights: 543 to 1,650 AED (+204%)
Downtown is still the most expensive at 5,110 AED per sq ft.

Which area surprised you most?

Area-by-area data on every deal: link in bio.

Source: Dubai Land Department (DLD) sales transactions, ready office units, median AED per sq ft, 2016–2025. Years with under 5 deals interpolated. """+FOOT)

# 2. rent race (Ejari)
r=pd.read_csv('/home/claude/inv/rent_area.csv'); o=r[(r.segment=='Office')&(r.version=='New')]
RENT={}
for en,dn in AREA.items():
    q=o[o.area_name==dn].set_index('year')
    v=pd.Series({y:(q.median_psf[y] if y in q.index and q.contracts_physical[y]>=20 else np.nan) for y in YRS},dtype=float)
    for y in YRS[1:-1]:  # isolated dips below 60% of both neighbours are mix outliers
        if v[y]<0.6*min(v[y-1],v[y+1]): v[y]=np.nan
    v=v.interpolate(limit_direction='both')
    RENT[en]=[round(x) for x in v]
g=sorted(((k,v[4],v[-1]) for k,v in RENT.items()),key=lambda z:-(z[2]/z[1]))
R["office_rent_race"]=dict(fmt="race",music=1,cfg=dict(series=RENT,years=YRS,base_idx=4,kick="DUBAI OFFICES · EJARI DATA",title="Office rent per sq ft a year",
    sub="Median new lease by area, AED",hook=(f"+{(g[0][2]/g[0][1]-1)*100:.0f}%","Office rents in one Dubai area since 2020. Which one?"),
    events=[(2020.0,2021.2,"2020","Rents hit the bottom"),(2023.0,2024.0,"2023","The rent cycle turns")],end=("2025 · TOP",f"{max(RENT,key=lambda k:RENT[k][-1])} {RENT[max(RENT,key=lambda k:RENT[k][-1])][-1]}"),
    summary=dict(kick="OFFICE RENTS · 2020 TO 2025",title="Rent growth since 2020",sub="Median new-lease AED per sq ft, 2020 vs 2025",take=f"{g[0][0]}: rents x{g[0][2]/g[0][1]:.1f} in five years"),
    src="Source: Ejari new lease contracts registered with DLD, office units, median annual rent AED per sq ft, 2016–2025."),
  cap=None)
R["office_rent_race"]["cap"]=f"""+{(g[0][2]/g[0][1]-1)*100:.0f}%. That's how much office rents grew in one Dubai area since 2020.

Median new-lease rent per sq ft a year, 12 areas, 2020 to 2025:
"""+"\n".join(f"{k}: {a} to {b} AED (+{(b/a-1)*100:.0f}%)" for k,a,b in g[:3])+f"""

Is your office lease up for renewal next year?

Area-by-area data: link in bio.

Source: Ejari new lease contracts (DLD), office units, median annual rent AED per sq ft, 2016–2025. {FOOT}"""

# 3. office sales by year (columns)
m=pd.read_csv(f'{AGG}/sales_dubai_segment_month.csv'); m['y']=m.month.str[:4]
f=m[m.segment=='Office'].pivot_table(index='y',columns='reg_type',values='total_aed',aggfunc='sum').fillna(0)/1e9
f=f.loc['2016':'2026']
RE=list(f.ready.round(2)); OP=list(f.off_plan.round(2)); L=[("'"+y[2:]) for y in f.index]; L[-1]="2026*"
tot26=RE[-1]+OP[-1]; tot25=RE[-2]+OP[-2]; tot20=RE[4]+OP[4]
R["office_sales_value"]=dict(fmt="columns",music=2,cfg=dict(labels=L,a=RE,b=OP,a_lab="Ready",b_lab="Off-plan",fmt=lambda v:f"{v:.1f}",
    kick="DUBAI OFFICES · DLD DATA",title="Office sales, AED billion",sub="All registered office sales in Dubai by year",
    hook=(f"AED {tot26:.1f}bn","of Dubai offices sold in 9 months of 2026. Most in DLD data"),
    take=("2026 · JAN TO 5 OCT",f"AED {tot26:.1f}bn so far, {tot26/tot20:.0f}x the 2020 total. {OP[-1]/tot26*100:.0f}% of it off-plan"),
    src="Source: Dubai Land Department sales transactions, office units, total AED by year, 2016 to 5 Oct 2026. *2026 year to date."),
  cap=f"""AED {tot26:.1f} billion of Dubai offices sold in 9 months of 2026. More than any full year in DLD data since 2009.

Registered office sales in Dubai:
2020: AED {tot20:.1f}bn
2025: AED {tot25:.1f}bn
2026, Jan to 5 Oct: AED {tot26:.1f}bn, of which {OP[-1]/tot26*100:.0f}% off-plan

What's driving it: new supply or demand?

More office market data: link in bio.

Source: Dubai Land Department (DLD) sales transactions, office units, total value by year, 2016 to 5 October 2026. {FOOT}""")

# 4. rent asked vs paid (dumbbell)
LR=pd.read_csv('/home/claude/prop/list_rent.csv'); d=LR[(LR.emirate=='Dubai')&(LR.type=='Office')&(LR.sqft>=200)].copy(); d['psf']=d.price_curr/d.sqft
GRP=[("JLT","JLT"),("Jumeirah Lake","JLT"),("Business Bay","Business Bay"),("Bay Square","Business Bay"),("Barsha Heights","Barsha Heights"),("Tecom","Barsha Heights"),("JVC","JVC"),("Jumeirah Village Circle","JVC"),
     ("Silicon Oasis","Silicon Oasis"),("DSO","Silicon Oasis"),("Downtown Dubai","Downtown"),("Sheikh Zayed Road","Sheikh Zayed Rd"),("Trade Cent","Sheikh Zayed Rd"),("Investment Park","DIP"),
     ("Deira","Deira"),("Bur Dubai","Bur Dubai"),("Greens","The Greens")]
def grp(a):
    for k,v in GRP:
        if k in str(a): return v
d['g']=d.area.map(grp); ask=d.groupby('g').psf.agg(['count','median'])
e=r[(r.segment=='Office')&(r.version=='New')&(r.year==2026)].set_index('area_name')
EJ={**AREA,"Deira":"Hor Al Anz East","Bur Dubai":"Mankhool"}
rows=[]
for k,(cnt,med) in ask.iterrows():
    if cnt>=15 and EJ.get(k) in e.index and e.contracts_physical[EJ[k]]>=100: rows.append((k,round(med),round(e.median_psf[EJ[k]])))
rows.sort(key=lambda z:-(z[1]/z[2]))
R["office_rent_asked_paid"]=dict(fmt="dumbbell",music=3,cfg=dict(rows=rows,fmt=lambda v:nf0(v),kick="ASKED VS PAID · OFFICE RENT",title="Asked is an opinion. Paid is a fact.",
    sub="Office rent, AED per sq ft a year, by area",paid_lab="Paid (Ejari 2026)",ask_lab="Asked (listings)",lo=60,
    hook=(f"+{(rows[0][1]/rows[0][2]-1)*100:.0f}%",f"How far {rows[0][0]} office listings ask above signed leases"),
    take=("WHAT IT MEANS",f"In {sum(1 for x in rows if x[1]>x[2])} of {len(rows)} areas landlords ask more than tenants actually sign for"),
    src="Source: asking rents from Bayut and Property Finder office listings, Nov 2026, median per area (15+ listings); paid rents from Ejari new leases, Jan to Oct 2026, median per area."),
  cap=None)
R["office_rent_asked_paid"]["cap"]=f"""Asked is an opinion. Paid is a fact.

Dubai office rents, AED per sq ft a year: listings vs signed Ejari leases in 2026.
"""+"\n".join(f"{k}: asked {a}, paid {p} ({'+' if a>=p else '−'}{abs(a/p-1)*100:.0f}%)" for k,a,p in rows[:4])+f"""

Negotiating a lease? Start from what was signed, not what is listed.

Area-by-area data: link in bio.

Source: asking rents from Bayut and Property Finder office listings (Nov 2026, median per area, 15+ listings); Ejari new lease contracts Jan–Oct 2026 (DLD), median per area. {FOOT}"""

# 5. gross yield by area 2025 (bars)
Y=sorted(((k,RENT[k][-1]/PRICE[k][-1]*100,RENT[k][-1],PRICE[k][-1]) for k in AREA),key=lambda z:-z[1])
R["office_yield_bars"]=dict(fmt="bars",music=4,cfg=dict(rows=[(k,y,f"rent {nf0(a)} / price {nf0(b)}") for k,y,a,b in Y],fmt=lambda v:f"{v:.1f}%",
    kick="DUBAI OFFICES · 2025",title="Gross rental yield by area",sub="Median rent ÷ median price per sq ft, ready offices",
    hook=(f"{Y[0][1]:.1f}%",f"The highest office yield in Dubai is not in Downtown"),hl=[0],
    take=("CHEAPER AREAS, HIGHER YIELD",f"{Y[0][0]} {Y[0][1]:.1f}% vs Downtown {dict((k,y) for k,y,_,_ in Y)['Downtown']:.1f}%. Gross, before service charges and vacancy"),
    src="Source: DLD sales (median AED per sq ft, ready offices) and Ejari new leases (median annual AED per sq ft), 2025. Gross yield, before service charges, fees and vacancy."),
  cap=f"""{Y[0][1]:.1f}%. The highest gross office yield in Dubai is in {Y[0][0]}, not Downtown.

Median rent ÷ median price per sq ft, ready offices, 2025:
"""+"\n".join(f"{k}: {y:.1f}%" for k,y,_,_ in Y[:3])+f"""
...
Downtown: {dict((k,y) for k,y,_,_ in Y)['Downtown']:.1f}%

Gross yield, before service charges and vacancy. Yield or growth: which do you choose?

Area-by-area data: link in bio.

Source: DLD sales transactions and Ejari new leases, ready office units, medians for 2025. {FOOT}""")

# 6. Dubai office psf line (monthly)
o=m[(m.segment=='Office')&(m.reg_type=='ready')&(m.month>='2015-01')&(m.month<='2026-09')].set_index('month').median_psf.rolling(3).median().dropna()
X=list(o.index); V=[float(v) for v in o]
iL=V.index(min(V)); iH=V.index(max(V))
def mlab(k):
    y,mo=X[k].split('-'); return y
MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
def ml(k): y,mo=X[k].split('-'); return f"{MON[int(mo)-1]} {y}"
i1k=next(i for i in range(iL,len(V)) if V[i]>=1000)
R["office_price_line"]=dict(fmt="line",music=5,cfg=dict(x=X,y=V,fmt=lambda v:nf0(v),yrange=(400,1900),grid=[500,1000,1500],
    xticks=[(X.index(f"{y}-01") if f"{y}-01" in X else 0,str(y)) for y in (2016,2018,2020,2022,2024,2026)],xlab=mlab,
    kick="DUBAI OFFICES · DLD DATA",title="Dubai office price per sq ft",sub="Median sale price, ready offices, AED, 3-month rolling",
    hook=(f"x{max(V)/min(V):.1f}","Dubai office prices from the 2020 low to the record"),
    events=[(iL,iL+14,ml(iL),f"The low: {nf0(V[iL])} AED"),(i1k,i1k+14,ml(i1k),"Back above 1,000"),(iH,iH+5,ml(iH),f"Record {nf0(V[iH])} AED")],
    take=("SEP 2026",f"{nf0(V[-1])} AED per sq ft. x{V[-1]/V[iL]:.1f} from the {ml(iL)} low"),
    src="Source: Dubai Land Department sales, ready office units, monthly median AED per sq ft, 3-month rolling median, Jan 2015 to Sep 2026."),
  cap=f"""From {nf0(V[iL])} to {nf0(V[iH])} AED per sq ft. Dubai office prices since the {ml(iL)} low.

Median sale price of ready offices, all Dubai, 3-month rolling:
2015: around {nf0(V[0])} AED
{ml(iL)}: {nf0(V[iL])} AED, the low
{ml(i1k)}: back above 1,000
{ml(iH)}: {nf0(V[iH])} AED, the record

Where do you think the line goes next?

Area-by-area data: link in bio.

Source: Dubai Land Department (DLD) sales transactions, ready office units, monthly median AED per sq ft, Jan 2015 to Sep 2026. {FOOT}""")

# 7. shops 2025 by area (bars)
s=pd.read_csv('/home/claude/inv/sales_area.csv'); q=s[(s.segment=='Shop')&(s.reg_type=='ready')&(s.year==2025)&(s.deals>=15)&(s.area_name!='Al Safouh Second')]
SN={"Al Merkadh":"Meydan / Sobha","Business Bay":"Business Bay","Jabal Ali First":"Al Furjan","Al Barsha South Fourth":"JVC","Marsa Dubai":"Dubai Marina","Al Barshaa South Third":"Arjan",
    "Nadd Hessa":"Silicon Oasis","Al Thanyah Fifth":"JLT","Al Warsan First":"International City","Dubai Investment Park First":"DIP","Al Jadaf":"Al Jadaf","Warsan Fourth":"Intl City Ph 2-3","Al Safouh Second":"Al Sufouh 2"}
SH=sorted(((SN.get(a,a),p,n) for a,p,n in zip(q.area_name,q.median_psf,q.deals)),key=lambda z:-z[1])
R["shop_price_bars"]=dict(fmt="bars",music=6,cfg=dict(rows=[(k,p,f"{int(n)} deals") for k,p,n in SH],fmt=lambda v:nf0(v),
    kick="DUBAI RETAIL · DLD DATA",title="Shop price per sq ft by area",sub="Median sale price, ready shops, AED, 2025",
    hook=(f"{nf0(SH[0][1])} AED",f"per sq ft for a shop in one Dubai area. Which one?"),hl=[0],
    take=("THE SPREAD",f"{SH[0][0]} {nf0(SH[0][1])} vs {SH[-1][0]} {nf0(SH[-1][1])} AED per sq ft: x{SH[0][1]/SH[-1][1]:.0f} between the top and bottom"),
    src="Source: Dubai Land Department sales, ready shop units, median AED per sq ft, 2025, areas with 15+ deals."),
  cap=f"""{nf0(SH[0][1])} AED per sq ft. The most expensive area to buy a shop in Dubai in 2025 was {SH[0][0]}.

Median sale price of ready shops, 2025 (areas with 15+ deals):
"""+"\n".join(f"{k}: {nf0(p)} AED" for k,p,_ in SH[:4])+f"""
...
{SH[-1][0]}: {nf0(SH[-1][1])} AED

Retail or offices: which would you hold?

Area-by-area data: link in bio.

Source: Dubai Land Department (DLD) sales transactions, ready shop units, median AED per sq ft, 2025. {FOOT}""")
