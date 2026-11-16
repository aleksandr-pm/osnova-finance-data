import sys, os; sys.path.insert(0,'/home/claude/prop')
import v2, content_v3 as C, content_v2 as C2
TR=sorted(os.listdir(v2.MUSIC))
def cfg(k):
    if k=="r_rent_business_bay_v2": c=C2.REELS["r_rent_business_bay"]; return dict(c["cfg"],word=c["word"])
    c=C.R[k]; return dict(c["cfg"],word=c["word"])
def reel(k): return v2.Reel(cfg(k))
if __name__=="__main__":
    mode=sys.argv[1]
    if mode=="stills":
        for k in sys.argv[2:]:
            r=reel(k); bg=v2.build_bg(k,r.TOTAL,sum(map(ord,k)))
            v2.stills(r,bg,[25,60+300,60+330+60,r.TOTAL-30],f"/home/claude/prop/st3_{k}.png")
    else:
        for k in sys.argv[2:]:
            r=reel(k); bg=v2.build_bg(k,r.TOTAL,sum(map(ord,k))+7)
            i=C.ORDER.index(k); v2.render(r,bg,os.path.join(v2.MUSIC,TR[i%len(TR)]),f"/home/claude/prop/out3/{k}.mp4"); print("done",k,flush=True)
