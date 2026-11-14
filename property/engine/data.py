import pandas as pd, numpy as np
s=pd.read_csv('/home/claude/inv/sales_area.csv')
o=s[(s.segment=='Office')&(s.reg_type=='ready')&(s.year.between(2016,2025))]
A=[("Burj Khalifa","Downtown"),("Al Thanyah Third","The Greens"),("Marsa Dubai","Dubai Marina"),("Trade Center First","Sheikh Zayed Rd"),
   ("Business Bay","Business Bay"),("Al Thanyah First","Barsha Heights"),("Al Thanyah Fifth","JLT"),("Al Barsha South Fourth","JVC"),
   ("Al Barshaa South Third","Arjan"),("Al Hebiah First","Motor City"),("Nadd Hessa","Silicon Oasis"),("Dubai Investment Park First","DIP")]
YRS=list(range(2016,2026))
SER={}
for dn,en in A:
    q=o[o.area_name==dn].set_index('year')
    v=pd.Series({y:(q.median_psf[y] if y in q.index and q.deals[y]>=5 and q.median_psf[y]>=150 else np.nan) for y in YRS},dtype=float)
    v=v.interpolate(limit_direction='both')
    SER[en]=[round(x) for x in v]
if __name__=="__main__":
    for k,v in SER.items(): print(f"{k:16s}",v, f"2020→2025 {v[-1]/v[4]*100-100:+.0f}%", f"2016→2025 {v[-1]/v[0]*100-100:+.0f}%")
