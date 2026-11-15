import sys, os; sys.path.insert(0,'/home/claude/prop')
import v2, content_v2 as C
TR=sorted(os.listdir(v2.MUSIC))
def reel(k): return v2.Reel(dict(C.REELS[k]["cfg"],word=C.REELS[k]["word"]))
if __name__=="__main__":
    mode=sys.argv[1]
    if mode=="posts":
        for k,p in C.POSTS.items(): v2.post(dict(p["cfg"],word=p["word"]),f"/home/claude/prop/out2/{k}.jpg")
    elif mode=="stills":
        for k in sys.argv[2:]:
            r=reel(k); bg=v2.build_bg(k,r.TOTAL,sum(map(ord,k)))
            v2.stills(r,bg,[30,60+40,60+200,60+320,60+330+80,r.TOTAL-30],f"/home/claude/prop/st2_{k}.png")
    else:
        k=sys.argv[2]; r=reel(k); bg=v2.build_bg(k,r.TOTAL,sum(map(ord,k)))
        i=list(C.REELS).index(k); v2.render(r,bg,os.path.join(v2.MUSIC,TR[(i+2)%len(TR)]),f"/home/claude/prop/out2/{k}.mp4"); print("done",k,r.TOTAL/30)
