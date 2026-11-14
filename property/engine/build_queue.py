import sys, os, json, shutil, subprocess; sys.path.insert(0,'/home/claude/prop')
import importlib.util as iu
spec=iu.spec_from_file_location('prun','/home/claude/prop/run.py'); run=iu.module_from_spec(spec); spec.loader.exec_module(run)
import reels
REPO="/home/claude/osnova-finance-data/property"
TAGS={"default":"#dubai #dubaiproperty #dubaioffice #commercialrealestate #dubairealestate #propertydata #uae #officespace",
      "shop_price_bars":"#dubai #dubaiproperty #dubairetail #commercialrealestate #dubairealestate #propertydata #uae #retailspace"}
Q=[]
for i,k in enumerate(run.ORDER):
    src=f"/home/claude/prop/out/{i+1:02d}_{k}.mp4"; dst=f"reels/{i+1:02d}_{k}.mp4"
    shutil.copy(src,os.path.join(REPO,dst))
    reel=run.mk(k); thumb=int((reel.N-45)/30*1000)
    cap=reels.R[k]["cap"]+"\n\n"+TAGS.get(k,TAGS["default"])
    assert len(cap)<2200 and "WhatsApp" not in cap
    Q.append({"id":k,"file":dst,"thumb_ms":thumb,"caption":cap})
json.dump(Q,open(os.path.join(REPO,"queue.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(len(Q),"queued")
