import sys, os, importlib.util as iu; sys.path.insert(0,'/home/claude/prop')
import pe2
spec=iu.spec_from_file_location('reels','/home/claude/prop/reels.py'); reels=iu.module_from_spec(spec); sys.modules['pe']=pe2; spec.loader.exec_module(reels)
W4={"office_price_race":("PRICE","for prices by district"),"office_rent_race":("RENT","for rents by district"),
    "office_sales_value":("DATA","for the full research"),"office_price_line":("PRICE","for prices by district")}
def mk(k):
    r=reels.R[k]; reel=getattr(pe2,r["fmt"])(r["cfg"]); reel.word,reel.line=W4[k]; return reel
if __name__=="__main__":
    mode=sys.argv[1]
    for k in sys.argv[2:]:
        reel=mk(k); bg=f"/home/claude/prop/bg/{k}/bg.mp4"
        if mode=="stills": pe2.stills(reel,bg,[40,int(reel.N*0.5),reel.N-20,reel.TOTAL-30],f"/home/claude/prop/st4_{k}.png")
        else:
            TR=sorted(os.listdir(pe2.MUSIC)); pe2.render(reel,bg,os.path.join(pe2.MUSIC,TR[(list(W4).index(k)+3)%len(TR)]),f"/home/claude/prop/out3/db_{k}.mp4"); print("done",k,flush=True)
