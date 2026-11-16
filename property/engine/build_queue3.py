import sys, os, json, shutil, importlib.util as iu; sys.path.insert(0,'/home/claude/prop')
import pe2, content_v3 as C3, content_v4 as C4
spec=iu.spec_from_file_location('reels','/home/claude/prop/reels.py'); reels=iu.module_from_spec(spec); sys.modules['pe']=pe2; spec.loader.exec_module(reels)
spec=iu.spec_from_file_location('run4','/home/claude/prop/run4.py'); run4=iu.module_from_spec(spec); spec.loader.exec_module(run4)
REPO="/home/claude/osnova-finance-data/property"
DBREP={"db_office_price_race":("Area-by-area data on every deal: link in bio.","DM PRICE and get prices paid by district.","PRICE"),
       "db_office_rent_race":("Area-by-area data: link in bio.","DM RENT and get rents by district.","RENT"),
       "db_office_sales_value":("More office market data: link in bio.","DM DATA and get the full research.","DATA"),
       "db_office_price_line":("Area-by-area data: link in bio.","DM PRICE and get prices paid by district.","PRICE")}
ORDER=["r_uae_wealth","r_rent_barsha_heights","r_shahrukhz_top","db_office_price_line",
       "r_aed1m_buys","alt_metro_ranked","r_offplan_premium","r_lumena_alta_top",
       "db_office_rent_race","r_hidden_costs","r_rent_al_quoz_warehouse","db_office_price_race",
       "db_office_sales_value","alt_rent_dumbbell","r_jebel_ali_zero","r_cash_buyers",
       "alt_top_buildings_ranked","r_sports_city","r_dubai_vs_abudhabi","r_retail_vs_office"]
q=json.load(open(f"{REPO}/queue.json",encoding="utf-8")); st=json.load(open(f"{REPO}/state.json",encoding="utf-8"))
posted={p["id"] for p in st["posted"]}; old={x["id"]:x for x in q}
newq=[x for x in q if x["id"] in posted]+[x for x in q if x["id"] not in posted and x["type"]=="post"]
for i,k in enumerate(ORDER):
    day=i//4+1
    if k in old: e=dict(old[k]); e["day"]=day; newq.append(e); continue
    if k.startswith("db_"):
        src_k=k[3:]; a,b,w=DBREP[k]; cap=reels.R[src_k]["cap"]; assert a in cap,k; cap=cap.replace(a,b)+"\n\n"+C3.TAGS
        reel=run4.mk(src_k); thumb=int((reel.N-45)/30*1000)
    elif k.startswith("alt_"):
        a=C4.A[k]; w=a["word"]; cap=a["caption"]; reel=getattr(pe2,a["fmt"])(a["cfg"]); thumb=int((reel.N-45)/30*1000)
    else:
        r=C3.R[k]; w=r["word"]; cap=r["cap"]; thumb=14000
    src=f"/home/claude/prop/out3/{k}.mp4"; assert os.path.exists(src),src
    shutil.copy(src,f"{REPO}/media/{k}.mp4")
    assert len(cap)<2200 and "—" not in cap
    newq.append(dict(id=k,type="reel",day=day,file=f"media/{k}.mp4",word=w,link=C3.LINKS[w],caption=cap,thumb_ms=thumb))
json.dump(newq,open(f"{REPO}/queue.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
json.dump(C3.LINKS,open(f"{REPO}/dm_keywords.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(len(newq),[x["id"] for x in newq if x["id"] not in posted])
