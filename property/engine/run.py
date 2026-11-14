import sys, os; sys.path.insert(0,'/home/claude/prop')
import pe, reels
ORDER=["office_price_race","office_sales_value","office_rent_race","office_rent_asked_paid","office_yield_bars","office_price_line","shop_price_bars"]
TR=sorted(os.listdir(pe.MUSIC))
def mk(k):
    r=reels.R[k]; return getattr(pe,r["fmt"])(r["cfg"])
if __name__=="__main__":
    k=sys.argv[1]; reel=mk(k); seed=ORDER.index(k)*13+5
    bg=f"/home/claude/prop/bg/{k}/bg.mp4"
    if not os.path.exists(bg): bg=pe.build_bg(k,reel.TOTAL,seed)
    if sys.argv[2]=="stills":
        fr=list(map(int,sys.argv[3:])) or [40,int(reel.N*0.35),int(reel.N*0.7),reel.N-20,reel.TOTAL-30]
        pe.stills(reel,bg,fr,f"/home/claude/prop/prev_{k}.png"); print(k,reel.TOTAL/30,"s")
    else:
        os.makedirs("/home/claude/prop/out",exist_ok=True)
        mus=os.path.join(pe.MUSIC,TR[reels.R[k]["music"]%len(TR)])
        out=f"/home/claude/prop/out/{ORDER.index(k)+1:02d}_{k}.mp4"; pe.render(reel,bg,mus,out); print("done",out,reel.TOTAL/30)
