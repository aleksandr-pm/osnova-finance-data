import sys, os; sys.path.insert(0,'/home/claude/prop')
import pe2, pe3, b2
def mk(k):
    a=b2.B[k]; f=getattr(pe3,a["fmt"],None) or getattr(pe2,a["fmt"]); r=f(a["cfg"]); r.word,r.line=a["word"],a["line"]; return r
if __name__=="__main__":
    mode=sys.argv[1]
    for k in sys.argv[2:]:
        r=mk(k); bg=pe2.build_bg(k,r.TOTAL,sum(map(ord,k))+3)
        if mode=="stills":
            pe2.stills(r,bg,[30,int(r.N*0.35),int(r.N*0.7),r.N-15],f"/home/claude/prop/st6_{k}.png")
        else:
            TR=sorted(os.listdir(pe2.MUSIC)); pe2.render(r,bg,os.path.join(pe2.MUSIC,TR[b2.ORDER.index(k)%len(TR)]),f"/home/claude/prop/out6/{k}.mp4"); print("done",k,flush=True)
