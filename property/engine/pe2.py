"""OSNOVA Property reels engine (EN). Formats: race, bars, dumbbell, columns, line. Design B on darkened Dubai clips."""
import sys, os, subprocess, math, random
sys.path.insert(0,'/home/claude/r10')
from fg import font, ease, wrap, T, fitf, tw, ring, kicker, VIG, W, H, FPS, M, SAND, LIME, GREY, MID
from PIL import Image, ImageDraw
BLUE=(125,165,210); WHITE=(255,255,255); NEG=(226,120,100)
DISC="Statistics only · Not an offer or advice"
CT=440; X0=M+270; XMAX=W-M-140
def nf(v,d=0): return f"{v:,.{d}f}"

# ---------- shared pieces ----------
def head(d,a,kick,title,sub):
    kicker(d,kick,a); ring(d,a)
    T(d,(M,250),title,fitf(d,title,600,62,W-2*M,40),WHITE,a)
    T(d,(M,330),sub,fitf(d,sub,400,32,W-2*M,22),GREY,a)
def footer(d,a,src):
    fs=font(400,22); y=H-330
    for ln in wrap(d,src,fs,W-2*M): T(d,(M,y),ln,fs,GREY,a); y+=32
    T(d,(M,y+6),DISC,font(500,22),SAND,a)
def plaque(d,x,y,w,h,a):
    if a<=0: return
    d.rectangle([x,y,x+w,y+h],fill=MID+(int(235*a),)); d.rectangle([x,y,x+8,y+h],fill=SAND+(int(255*a),))
def hook_plaque(d,y,big,txt,ee):
    plaque(d,M,y,W-2*M,230,ee)
    T(d,(M+40,y+30),big,fitf(d,big,600,104,W-2*M-80,60),SAND,ee)
    f=fitf(d,txt,500,40,W-2*M-80,30)
    T(d,(M+40,y+150),txt,f,LIME,ee)
def note_plaque(d,y,kick,txt,ee,w=W-2*M):
    lines=wrap(d,txt,font(500,40),w-80); h=70+48*len(lines)
    plaque(d,M,y,w,h,ee); T(d,(M+36,y+26),kick,font(500,26),SAND,ee)
    for j,ln in enumerate(lines): T(d,(M+36,y+64+j*48),ln,font(500,40),LIME,ee)
def win(fi,a,b,f=10):  # fade in/out envelope for frame window [a,b)
    if fi<a or fi>=b: return 0.0
    return min(ease((fi-a)/f),ease((b-fi)/f))

def cta(d,t,word="DATA",line="for the full table"):
    d.rectangle([0,0,W,H],fill=MID+(int(255*min(1,t/0.2)),))
    a=ease(t/0.25); cx=W/2; r=70
    d.ellipse([cx-r,600-r,cx+r,600+r],outline=SAND+(int(255*a),),width=24)
    T(d,(cx,790),"Full data on",font(500,56),WHITE,a,anchor="mm")
    T(d,(cx,900),"osnova.property",fitf(d,"osnova.property",600,120,W-2*M,80),SAND,a,anchor="mm")
    T(d,(cx,1010),"link in bio",font(500,56),WHITE,ease((t-0.2)/0.3),anchor="mm")
    T(d,(cx,1160),"or comment "+word,font(600,60),SAND,ease((t-0.45)/0.3),anchor="mm")
    T(d,(cx,H-270),DISC,font(400,26),GREY,ease((t-0.4)/0.3),anchor="mm")
CTA=120

class Reel:
    def __init__(self,main_frames,draw_main,word="DATA",line="for the full table"):
        self.N=main_frames; self.draw=draw_main; self.TOTAL=main_frames+CTA; self.word=word; self.line=line
    def render(self,fi):
        img=Image.new("RGBA",(W,H),(0,0,0,0)); img.alpha_composite(VIG); d=ImageDraw.Draw(img)
        if fi<self.N: self.draw(d,fi)
        else: cta(d,(fi-self.N)/FPS,self.word,self.line)
        return img

# ---------- A. bar race ----------
def race(c):
    S=c["series"]; YRS=c["years"]; NAMES=list(S); N=len(NAMES); NY=len(YRS)
    HOOK=90; PER=c.get("per",60); HOLD=75; SUM=165; RACE=PER*(NY-1); RH=c.get("rh",68); BH=44
    fmt=c.get("fmt",lambda v:nf(v))
    def yr_at(fi):
        f=fi-HOOK
        if f<=0: return 0.0
        if f>=RACE: return NY-1.0
        k=f//PER; x=(f%PER)/PER; return k+x*x*(3-2*x)
    def vals(y):
        k=int(min(y,NY-2)); x=y-k; return [S[n][k]+(S[n][k+1]-S[n][k])*x for n in NAMES]
    POS=[];SC=[];pos=None;sc=None
    for fi in range(HOOK+RACE+HOLD):
        v=vals(yr_at(fi)); order=sorted(range(N),key=lambda i:-v[i]); tgt=[0]*N
        for r,i in enumerate(order): tgt[i]=r
        pos=list(map(float,tgt)) if pos is None else [p+(t-p)*0.16 for p,t in zip(pos,tgt)]
        m=max(v); sc=m if sc is None else sc+(m-sc)*0.12; POS.append(pos[:]); SC.append(sc)
    if not c.get("summary"): SUM=0
    b=c.get("base_idx",0); G=sorted([(n,S[n][b],S[n][-1]) for n in NAMES],key=lambda r:-(r[2]/max(r[1],1e-9)))
    def draw(d,fi):
        if fi>=HOOK+RACE+HOLD: return summ(d,(fi-HOOK-RACE-HOLD)/FPS)
        t=fi/FPS; a=ease(t/0.3); head(d,a,c["kick"],c["title"],c["sub"])
        y=yr_at(fi); v=vals(y); P=POS[fi]; Sc=SC[fi]
        for i,n in enumerate(NAMES):
            e=ease((t-0.1-P[i]*0.03)/0.35); yy=CT+P[i]*RH
            T(d,(M,yy+BH/2),n,fitf(d,n,500,32,X0-M-16,24),LIME,e,anchor="lm")
            bw=(XMAX-X0)*v[i]/Sc*e; d.rectangle([X0,yy,X0+bw,yy+BH],fill=SAND+(int(230*e),))
            T(d,(X0+bw+14,yy+BH/2),fmt(v[i]),font(600,34),LIME,e,anchor="lm")
        yb=CT+N*RH+40
        if fi>=HOOK-10:
            ea=ease((fi-HOOK+10)/12)
            T(d,(W-M,yb+175),str(int(YRS[0]+y+0.5)),font(600,170),SAND,ea,anchor="rs")
            tx0,tx1,ty=M,W-M,yb+215
            d.rectangle([tx0,ty,tx1,ty+4],fill=(255,255,255,int(60*ea))); d.rectangle([tx0,ty,tx0+(tx1-tx0)*y/(NY-1),ty+4],fill=SAND+(int(255*ea),))
            T(d,(tx0,ty+18),str(YRS[0]),font(400,24),GREY,ea); T(d,(tx1,ty+18),str(YRS[-1]),font(400,24),GREY,ea,anchor="ra")
            cy=YRS[0]+y
            for y0,y1,k_,txt in c.get("events",[]):
                if y0<=cy<=y1 and fi<HOOK+RACE:
                    ee=min(ease((cy-y0)/0.15),ease((y1-cy)/0.15))
                    plaque(d,M,yb+30,430,150,ee); T(d,(M+36,yb+60),k_,font(500,28),SAND,ee)
                    for j,ln in enumerate(wrap(d,txt,font(500,38),360)): T(d,(M+36,yb+100+j*46),ln,font(500,38),LIME,ee)
            if fi>=HOOK+RACE:
                ee=ease((fi-HOOK-RACE)/12); k_,txt=c["end"]
                plaque(d,M,yb+30,430,150,ee); T(d,(M+36,yb+60),k_,font(500,28),SAND,ee)
                for j,ln in enumerate(wrap(d,txt,font(500,38),360)): T(d,(M+36,yb+100+j*46),ln,font(500,38),LIME,ee)
        if fi<HOOK: hook_plaque(d,yb+20,c["hook"][0],c["hook"][1],min(ease(fi/10),ease((HOOK-fi)/10)))
        footer(d,a,c["src"])
    def summ(d,t):
        s=c["summary"]; a=ease(t/0.35); head(d,1,s["kick"],s["title"],s["sub"])
        gmax=max(z/x-1 for _,x,z in G)
        for j,(n,x,z) in enumerate(G):
            e=ease((t-0.2-j*0.06)/0.35); yy=CT+j*RH; g=z/x-1
            T(d,(M,yy+BH/2),n,fitf(d,n,500,32,X0-M-16,24),LIME,e,anchor="lm")
            bw=max(4,(XMAX-X0-120)*g/gmax)*e; col=SAND if j==0 else BLUE
            d.rectangle([X0,yy,X0+bw,yy+BH],fill=col+(int(230*e),))
            T(d,(X0+bw+14,yy+BH/2-12),f"{'+' if g>=0 else '−'}{abs(g)*100:.0f}%",font(600,34),SAND if j==0 else LIME,e,anchor="lm")
            T(d,(X0+bw+14,yy+BH/2+20),f"{fmt(x)} to {fmt(z)}",font(400,24),GREY,e,anchor="lm")
        e=ease((t-1.3)/0.4); T(d,(M,CT+N*RH+50),s["take"],fitf(d,s["take"],600,50,W-2*M,30),SAND,e)
        footer(d,a,c["src"])
    return Reel(HOOK+RACE+HOLD+SUM,draw)

# ---------- B. ranked bars ----------
def bars(c):
    R=c["rows"]; N=len(R); RH=c.get("rh",80); BH=50; fmt=c["fmt"]; vmax=max(r[1] for r in R)
    HOOK=96; TOT=c.get("frames",450); TAKE=c.get("take_at",240)
    def draw(d,fi):
        t=fi/FPS; a=ease(t/0.3); head(d,a,c["kick"],c["title"],c["sub"])
        for j,(lab,v,small) in enumerate(R):
            jj=N-1-j if c.get("reveal_from_bottom",True) else j
            e=ease((t-0.4-jj*0.28)/0.45); yy=CT+j*RH; hl=j in c.get("hl",[0])
            T(d,(M,yy+BH/2),lab,fitf(d,lab,500,32,X0-M-16,24),LIME,e,anchor="lm")
            bw=max(4,(XMAX-X0-60)*v/vmax)*e
            d.rectangle([X0,yy,X0+bw,yy+BH],fill=(SAND if hl else BLUE)+(int(230*e),))
            T(d,(X0+bw+14,yy+BH/2-(12 if small else 0)),fmt(v),font(600,34),SAND if hl else LIME,e,anchor="lm")
            if small: T(d,(X0+bw+14,yy+BH/2+20),small,font(400,24),GREY,e,anchor="lm")
        yb=CT+N*RH+30
        if fi<HOOK: hook_plaque(d,yb,c["hook"][0],c["hook"][1],min(ease(fi/10),ease((HOOK-fi)/10)))
        ee=win(fi,TAKE,TOT+20,14)
        if ee: note_plaque(d,yb,c["take"][0],c["take"][1],ee)
        footer(d,a,c["src"])
    return Reel(TOT,draw)

# ---------- C. dumbbell: asked vs paid ----------
def dumbbell(c):
    R=c["rows"]; N=len(R); RH=c.get("rh",86); fmt=c["fmt"]
    lo=min(min(a,p) for _,a,p in R); hi=max(max(a,p) for _,a,p in R); lo=c.get("lo",0)
    GX0=X0+10; GX1=W-M-170
    def X(v): return GX0+(GX1-GX0)*(v-lo)/(hi-lo)
    HOOK=96; TOT=c.get("frames",480); TAKE=c.get("take_at",270)
    def draw(d,fi):
        t=fi/FPS; a=ease(t/0.3); head(d,a,c["kick"],c["title"],c["sub"])
        # legend
        ly=CT-20; d.ellipse([M,ly-11,M+22,ly+11],fill=SAND+(int(255*a),)); T(d,(M+34,ly),c["paid_lab"],font(500,28),LIME,a,anchor="lm")
        x2=M+60+tw(d,c["paid_lab"],font(500,28))+30
        d.ellipse([x2,ly-11,x2+22,ly+11],fill=GREY+(int(255*a),)); T(d,(x2+34,ly),c["ask_lab"],font(500,28),LIME,a,anchor="lm")
        for j,(lab,ask,paid) in enumerate(R):
            yy=CT+40+j*RH; cy=yy+RH/2-6
            e=ease((t-0.4-j*0.22)/0.4); e2=ease((t-0.7-j*0.22)/0.6); e3=ease((t-1.3-j*0.22)/0.3)
            T(d,(M,cy),lab,fitf(d,lab,500,32,X0-M-16,24),LIME,e,anchor="lm")
            xp=X(paid); xa=X(paid)+(X(ask)-X(paid))*e2
            d.line([(xp,cy),(xa,cy)],fill=(255,255,255,int(110*e)),width=6)
            r=13; d.ellipse([xa-r,cy-r,xa+r,cy+r],fill=GREY+(int(255*e2),))
            d.ellipse([xp-r,cy-r,xp+r,cy+r],fill=SAND+(int(255*e),))
            g=ask/paid-1; col=SAND if g>0 else NEG
            T(d,(W-M,cy-14),f"{'+' if g>=0 else '−'}{abs(g)*100:.0f}%",font(600,36),col,e3,anchor="rm")
            T(d,(W-M,cy+20),f"{fmt(paid)} / {fmt(ask)}",font(400,22),GREY,e3,anchor="rm")
        yb=CT+40+N*RH+30
        if fi<HOOK: hook_plaque(d,yb,c["hook"][0],c["hook"][1],min(ease(fi/10),ease((HOOK-fi)/10)))
        ee=win(fi,TAKE,TOT+20,14)
        if ee: note_plaque(d,yb,c["take"][0],c["take"][1],ee)
        footer(d,a,c["src"])
    return Reel(TOT,draw)

# ---------- D. columns (stacked, by year) ----------
def columns(c):
    L=c["labels"]; A=c["a"]; B=c["b"]; N=len(L); fmt=c["fmt"]
    tot=[x+y for x,y in zip(A,B)]; vmax=max(tot)
    gx0,gx1=M,W-M; gw=(gx1-gx0)/N; cw=gw*0.72; gy0,gy1=CT+90,1300
    HOOK=96; TOT=c.get("frames",480); TAKE=c.get("take_at",270)
    def draw(d,fi):
        t=fi/FPS; a=ease(t/0.3); head(d,a,c["kick"],c["title"],c["sub"])
        ly=CT+10; d.rectangle([M,ly-12,M+24,ly+12],fill=SAND+(int(255*a),)); T(d,(M+36,ly),c["a_lab"],font(500,28),LIME,a,anchor="lm")
        x2=M+36+tw(d,c["a_lab"],font(500,28))+40
        d.rectangle([x2,ly-12,x2+24,ly+12],fill=BLUE+(int(255*a),)); T(d,(x2+36,ly),c["b_lab"],font(500,28),LIME,a,anchor="lm")
        d.line([(gx0,gy1),(gx1,gy1)],fill=(255,255,255,int(90*a)),width=2)
        for i in range(N):
            e=ease((t-0.4-i*0.32)/0.5); x=gx0+i*gw+(gw-cw)/2
            ha=(gy1-gy0)*A[i]/vmax*e; hb=(gy1-gy0)*B[i]/vmax*e
            hl=i in c.get("hl",[N-1])
            d.rectangle([x,gy1-ha,x+cw,gy1],fill=SAND+(int(240*e),))
            if B[i]>0: d.rectangle([x,gy1-ha-hb,x+cw,gy1-ha],fill=BLUE+(int(240*e),))
            T(d,(x+cw/2,gy1+14),L[i],font(500 if hl else 400,24),SAND if hl else GREY,a,anchor="ma")
            e2=ease((t-0.8-i*0.32)/0.3)
            T(d,(x+cw/2,gy1-ha-hb-10),fmt(tot[i]),font(600,26 if not hl else 32),SAND if hl else LIME,e2,anchor="md")
        yb=gy1+70
        if fi<HOOK: hook_plaque(d,yb,c["hook"][0],c["hook"][1],min(ease(fi/10),ease((HOOK-fi)/10)))
        ee=win(fi,TAKE,TOT+20,14)
        if ee: note_plaque(d,yb,c["take"][0],c["take"][1],ee)
        footer(d,a,c["src"])
    return Reel(TOT,draw)

# ---------- E. line (progressive) ----------
def line(c):
    X=c["x"]; Y=c["y"]; N=len(X); fmt=c["fmt"]; lo,hi=c["yrange"]
    gx0,gx1,gy0,gy1=M+10,W-M-130,CT+60,1270
    HOOK=96; DRAW=c.get("draw",420); HOLD=c.get("hold",150); TOT=HOOK+DRAW+HOLD
    def px(i): return gx0+(gx1-gx0)*i/(N-1)
    def py(v): return gy1-(gy1-gy0)*(v-lo)/(hi-lo)
    def draw(d,fi):
        t=fi/FPS; a=ease(t/0.3); head(d,a,c["kick"],c["title"],c["sub"])
        for gv in c["grid"]:
            yy=py(gv); d.line([(gx0,yy),(gx1,yy)],fill=(255,255,255,int(40*a)),width=1)
            T(d,(gx1+12,yy),fmt(gv),font(400,24),GREY,a,anchor="lm")
        for k,lab in c["xticks"]:
            T(d,(px(k),gy1+16),lab,font(400,24),GREY,a,anchor="ma")
        u=min(1,max(0,(fi-30)/(HOOK-30+DRAW)))  # starts drawing early, under the hook
        u=u*u*(3-2*u)*0.5+u*0.5
        hiI=u*(N-1); k=int(hiI); fr=hiI-k
        pts=[(px(i),py(Y[i])) for i in range(k+1)]
        if k<N-1: pts.append((px(k)+(px(k+1)-px(k))*fr, py(Y[k]+(Y[k+1]-Y[k])*fr)))
        if len(pts)>1: d.line(pts,fill=SAND+(255,),width=7,joint="curve")
        hx,hy=pts[-1]; d.ellipse([hx-12,hy-12,hx+12,hy+12],fill=SAND+(255,))
        cur=Y[k]+(Y[min(k+1,N-1)]-Y[k])*fr
        T(d,(hx-16,hy-30),fmt(cur),font(600,40),WHITE,a,anchor="rd" if hx>gx0+200 else "ld")
        yb=gy1+80
        T(d,(W-M,yb+170),c["xlab"](k),font(600,140),SAND,ease((fi-HOOK+10)/12) if fi>=HOOK-10 else 0,anchor="rs")
        for i0,i1,kk,txt in c.get("events",[]):
            if i0<=hiI<=i1 and fi<HOOK+DRAW:
                ee=min(ease((hiI-i0)/3),ease((i1-hiI)/3))
                # marker at event point
                ex,ey=px(i0),py(Y[i0]); d.ellipse([ex-9,ey-9,ex+9,ey+9],outline=WHITE+(int(255*ee),),width=3)
                plaque(d,M,yb+20,480,150,ee); T(d,(M+36,yb+48),kk,font(500,28),SAND,ee)
                for j,ln in enumerate(wrap(d,txt,font(500,38),410)): T(d,(M+36,yb+88+j*46),ln,font(500,38),LIME,ee)
        if fi<HOOK: hook_plaque(d,yb,c["hook"][0],c["hook"][1],min(ease(fi/10),ease((HOOK-fi)/10)))
        ee=win(fi,HOOK+DRAW,TOT+20,14)
        if ee: note_plaque(d,yb,c["take"][0],c["take"][1],ee,w=500)
        footer(d,a,c["src"])
    return Reel(TOT,draw)

# ---------- render with background + music ----------
POOL={f"n{i}":dd for i,dd in [(1,7.2),(2,12.46),(3,18.8),(4,14.26),(5,15.36),(6,8.43),(7,46.9),(8,14.0),(9,19.9)]}
MUSIC="/home/claude/osnova-finance-data/assets/music"
def build_bg(name,total,seed,dark=0.72,seg=150):
    segs=[seg]*((total+seg-1)//seg); segs[-1]=total-seg*(len(segs)-1)+5
    rnd=random.Random(seed); keys=list(POOL); rnd.shuffle(keys)
    dd=f"/home/claude/prop/bg/{name}"; os.makedirs(dd,exist_ok=True); used={k:rnd.uniform(0,3) for k in keys}; files=[]; last=None
    for i,n_ in enumerate(segs):
        dur=n_/30
        for j in range(len(keys)):
            k=keys[(i+j)%len(keys)]
            if k!=last and POOL[k]-used[k]>=dur+0.1: break
        else: k=keys[i%len(keys)]; used[k]=0.0
        st=used[k]; used[k]=st+dur+0.3; last=k; fn=f"{dd}/{i:02d}.mp4"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",f"{st:.2f}","-i",f"/home/claude/t2/pool/{k}.mp4","-frames:v",str(n_),
            "-vf",f"drawbox=c=0x0E1826@{dark}:t=fill","-an","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",fn],check=True)
        files.append(fn)
    open(f"{dd}/list.txt","w").write("".join(f"file '{f}'\n" for f in files))
    out=f"{dd}/bg.mp4"; subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{dd}/list.txt","-c","copy",out],check=True)
    return out
def stills(reel,bg,frames,out):
    ims=[]
    for f in frames:
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",bg,"-vf",f"select=eq(n\\,{f})","-frames:v","1","/home/claude/prop/bgf.png"])
        b=Image.open("/home/claude/prop/bgf.png").convert("RGBA"); b.alpha_composite(reel.render(f)); ims.append(b.convert("RGB").resize((360,640)))
    s=Image.new("RGB",(370*len(ims),640),"white")
    for i,im in enumerate(ims): s.paste(im,(i*370,0))
    s.save(out)
def render(reel,bg,music,out,music_start=0.0):
    dur=reel.TOTAL/FPS
    p=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-i",bg,"-f","rawvideo","-pix_fmt","rgba","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-ss",f"{music_start:.2f}","-i",music,
        "-filter_complex",f"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];[2:a]atrim=0:{dur:.2f},asetpts=PTS-STARTPTS,afade=t=in:d=0.4,afade=t=out:st={dur-2.5:.2f}:d=2.5,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]",
        "-map","[v]","-map","[a]","-frames:v",str(reel.TOTAL),"-t",f"{dur:.2f}",
        "-c:v","libx264","-preset","medium","-crf","20","-maxrate","8M","-bufsize","16M","-pix_fmt","yuv420p","-profile:v","high",
        "-c:a","aac","-b:a","128k","-ar","48000","-movflags","+faststart",out],stdin=subprocess.PIPE)
    for fi in range(reel.TOTAL): p.stdin.write(reel.render(fi).tobytes())
    p.stdin.close(); assert p.wait()==0
