import sys, os; sys.path.insert(0,'/home/claude/prop')
import pe2, content_v4 as C
def mk(k):
    a=C.A[k]; r=getattr(pe2,a["fmt"])(a["cfg"]); r.word,r.line=a["word"],a["line"]; return r
if __name__=="__main__":
    mode=sys.argv[1]
    for k in sys.argv[2:]:
        r=mk(k); bg=pe2.build_bg(k,r.TOTAL,sum(map(ord,k)))
        if mode=="stills": pe2.stills(r,bg,[40,250,r.N-20],f"/home/claude/prop/st5_{k}.png")
        else:
            TR=sorted(os.listdir(pe2.MUSIC)); pe2.render(r,bg,os.path.join(pe2.MUSIC,TR[(list(C.A).index(k)+5)%len(TR)]),f"/home/claude/prop/out3/{k}.mp4"); print("done",k,flush=True)
