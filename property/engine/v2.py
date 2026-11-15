"""OSNOVA Property Instagram v2 (brief 15.11.2026): conversion reels 18-22 s + 1080x1350 bar posts.
Reel: 0-2 s big number over Dubai clip + question; 2-12 s bars one by one on limestone; 12-17 s one-line conclusion;
last 3 s 'DM <WORD> / for the full table / osnova.property'. Max 7 words per frame, safe zone 250 px top and bottom."""
import sys, os, subprocess, random
sys.path.insert(0, '/home/claude/r10')
from fg import font, ease, tw, W, H, FPS
from PIL import Image, ImageDraw

NAVY = (27, 47, 74); MID = (14, 24, 38); INK = (22, 38, 61); PAPER = (241, 236, 227); PAPER2 = (232, 225, 213)
SAND = (201, 178, 138); STONE = (156, 138, 106); SLATE = (91, 104, 120); HAIR = (216, 208, 194); WHITE = (255, 255, 255)
M = 90; SAFE_T = 250; SAFE_B = H - 250
DISC = "Statistics only · Not an offer or advice"


def T(d, xy, s, f, col, a=1.0, anchor="la"):
    if a <= 0: return
    d.text(xy, s, font=f, fill=col + (int(255 * min(1, a)),), anchor=anchor)


def fit(d, s, w, size, minsize=28, weight=600):
    while size > minsize and tw(d, s, font(weight, size)) > w: size -= 2
    return font(weight, size)


def ring(d, cx, cy, R, col, a=1.0, wpx=None):
    wpx = wpx or max(3, int(R * 16 / 46))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=col + (int(255 * a),), width=wpx)


def nf(v, dec=0):
    return f"{v:,.{dec}f}"


# ------------------------------------------------------------------ reels
class Reel:
    """cfg: hook(big, question) · title · bars[(label, value, color_key, caption)] · fmt · conclusion(big, line) · word · src"""
    HOOK, CHART, CONC, CTA = 60, 330, 150, 90

    def __init__(self, c):
        self.c = c; self.TOTAL = self.HOOK + self.CHART + self.CONC + self.CTA
        self.N = self.TOTAL - self.CTA

    def render(self, fi):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        c = self.c
        if fi < self.HOOK:
            self.hook(d, fi / FPS)
        elif fi < self.HOOK + self.CHART:
            d.rectangle([0, 0, W, H], fill=PAPER + (255,)); self.chart(d, (fi - self.HOOK) / FPS)
        elif fi < self.N:
            d.rectangle([0, 0, W, H], fill=PAPER + (255,)); self.conc(d, (fi - self.HOOK - self.CHART) / FPS)
        else:
            d.rectangle([0, 0, W, H], fill=MID + (255,)); self.cta(d, (fi - self.N) / FPS)
        return img

    def hook(self, d, t):
        big, q = self.c["hook"]
        a = ease(t / 0.25)
        ring(d, W - M - 28, SAFE_T + 30, 26, WHITE, a)
        f = fit(d, big, W - 2 * M, 260, 120)
        T(d, (W / 2, 880 + 30 * (1 - a)), big, f, WHITE, a, "mm")
        e = ease((t - 0.35) / 0.3)
        T(d, (W / 2, 1080), q, fit(d, q, W - 2 * M, 64, 40, 500), SAND, e, "mm")

    def frame_chrome(self, d, a=1.0):
        ring(d, W - M - 28, SAFE_T + 30, 26, NAVY, a)
        T(d, (M, SAFE_T + 6), self.c.get("kick", "OSNOVA PROPERTY"), font(500, 26), SLATE, a)
        T(d, (M, SAFE_T + 60), self.c["title"], fit(d, self.c["title"], W - 2 * M - 80, 60, 40), MID, a)
        f = font(400, 24); y = SAFE_B - 70
        T(d, (M, y), self.c["src"], fit(d, self.c["src"], W - 2 * M, 24, 18, 400), SLATE, a)
        T(d, (M, y + 34), DISC, font(500, 22), STONE, a)

    def chart(self, d, t):
        c = self.c; bars = c["bars"]; n = len(bars); fmt = c["fmt"]
        self.frame_chrome(d, ease(t / 0.25))
        top, base = SAFE_T + 260, SAFE_B - 300
        gap = 40 if n <= 3 else 24
        bw = min(300, (W - 2 * M - gap * (n - 1)) / n)
        x0 = (W - (bw * n + gap * (n - 1))) / 2
        vmax = max(b[1] for b in bars)
        step = (self.CHART / FPS - 1.2) / n
        cap = None
        for i, (lab, v, ck, caption) in enumerate(bars):
            e = ease((t - 0.3 - i * step) / 0.7)
            if e <= 0: continue
            col = {"navy": NAVY, "sand": SAND, "stone": STONE}[ck]
            x = x0 + i * (bw + gap); h = (base - top - 90) * v / vmax * e
            d.rectangle([x, base - h, x + bw, base], fill=col + (255,))
            fv = font(600, 64 if n <= 3 else (48 if n <= 4 else 38))
            T(d, (x + bw / 2, base - h - 16), fmt(v * e if e < 1 else v), fv, MID, e, "md")
            fl = fit(d, lab, bw + gap - 6, 34 if n <= 3 else 28, 20, 500)
            T(d, (x + bw / 2, base + 20), lab, fl, INK, e, "ma")
            if t >= 0.3 + i * step: cap = caption
        d.line([(M, base), (W - M, base)], fill=HAIR + (255,), width=3)
        if cap:
            T(d, (W / 2, base + 120), cap, fit(d, cap, W - 2 * M, 50, 34, 500), NAVY, 1, "ma")

    def conc(self, d, t):
        big, line = self.c["conclusion"]
        self.frame_chrome(d, 1)
        a = ease(t / 0.35)
        T(d, (W / 2, 860 + 30 * (1 - a)), big, fit(d, big, W - 2 * M, 230, 100), NAVY, a, "mm")
        e = ease((t - 0.3) / 0.35)
        T(d, (W / 2, 1060), line, fit(d, line, W - 2 * M, 58, 36, 500), MID, e, "mm")

    def cta(self, d, t):
        a = ease(t / 0.25)
        ring(d, W / 2, 600, 70, SAND, a, 24)
        T(d, (W / 2, 840), "DM " + self.c["word"], fit(d, "DM " + self.c["word"], W - 2 * M, 190, 100), SAND, a, "mm")
        T(d, (W / 2, 990), self.c.get("cta_line", "for the full table"), font(500, 60), WHITE, ease((t - 0.2) / 0.3), "mm")
        T(d, (W / 2, 1130), "osnova.property", font(600, 64), SAND, ease((t - 0.4) / 0.3), "mm")
        T(d, (W / 2, SAFE_B - 20), DISC, font(400, 26), (184, 194, 207), ease((t - 0.4) / 0.3), "mm")


# ------------------------------------------------------------------ background + render
POOL = {f"n{i}": dd for i, dd in [(1, 7.2), (2, 12.46), (3, 18.8), (4, 14.26), (5, 15.36), (6, 8.43), (7, 46.9), (8, 14.0), (9, 19.9)]}
MUSIC = "/home/claude/osnova-finance-data/assets/music"


def build_bg(name, total, seed):
    """Dubai clip under 55% midnight for the hook; the overlay paints solid backgrounds afterwards."""
    rnd = random.Random(seed); k = rnd.choice(list(POOL)); st = rnd.uniform(0, max(0, POOL[k] - 3))
    dd = f"/home/claude/prop/bg2"; os.makedirs(dd, exist_ok=True); out = f"{dd}/{name}.mp4"
    if os.path.exists(out): return out
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{st:.2f}", "-i", f"/home/claude/t2/pool/{k}.mp4",
                    "-vf", f"drawbox=c=0x0E1826@0.55:t=fill,tpad=stop_mode=clone:stop_duration={total / FPS + 1:.1f}",
                    "-frames:v", str(total), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out], check=True)
    return out


def render(reel, bg, music, out):
    dur = reel.TOTAL / FPS
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-i", bg, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", music, "-filter_complex",
                          f"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];[2:a]atrim=0:{dur:.2f},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st={dur - 2:.2f}:d=2,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]",
                          "-map", "[v]", "-map", "[a]", "-frames:v", str(reel.TOTAL), "-t", f"{dur:.2f}",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-profile:v", "high",
                          "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for fi in range(reel.TOTAL): p.stdin.write(reel.render(fi).tobytes())
    p.stdin.close(); assert p.wait() == 0


def stills(reel, bg, frames, out):
    ims = []
    for f in frames:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", bg, "-vf", f"select=eq(n\\,{f})", "-frames:v", "1", "/home/claude/prop/bgf.png"])
        b = Image.open("/home/claude/prop/bgf.png").convert("RGBA"); b.alpha_composite(reel.render(f)); ims.append(b.convert("RGB").resize((360, 640)))
    s = Image.new("RGB", (370 * len(ims), 640), "white")
    for i, im in enumerate(ims): s.paste(im, (i * 370, 0))
    s.save(out)


# ------------------------------------------------------------------ posts 1080x1350
PW, PH = 1080, 1350


def post(c, out):
    """c: kick · headline (2 lines max) · sub · kind 'rank' rows[(label, value, highlight)] or 'pair' rows[(label, asked, paid)] · fmt · word · src"""
    img = Image.new("RGB", (PW, PH), PAPER); d = ImageDraw.Draw(img, "RGBA")
    m = 80
    ring(d, PW - m - 22, 92, 22, NAVY)
    T(d, (m, 76), c["kick"], font(500, 24), SLATE)
    y = 130
    for ln in c["headline"]:
        T(d, (m, y), ln, fit(d, ln, PW - 2 * m, 58, 40), MID); y += 70
    T(d, (m, y + 14), c["sub"], fit(d, c["sub"], PW - 2 * m, 30, 22, 400), SLATE); y += 90
    rows = c["rows"]; fmt = c["fmt"]
    lab_w = 300; x0 = m + lab_w; xmax = PW - m - 130
    if c["kind"] == "rank":
        vmax = max(r[1] for r in rows); rh = min(96, (1150 - y) / len(rows))
        for i, (lab, v, hl) in enumerate(rows):
            yy = y + i * rh; bh = rh * 0.56
            T(d, (m, yy + bh / 2), lab, fit(d, lab, lab_w - 16, 32, 22, 500), INK, 1, "lm")
            bw = (xmax - x0) * v / vmax
            d.rectangle([x0, yy, x0 + bw, yy + bh], fill=NAVY if hl else SAND)
            T(d, (x0 + bw + 14, yy + bh / 2), fmt(v), font(600, 34), NAVY if hl else INK, 1, "lm")
    else:
        vmax = max(max(r[1], r[2]) for r in rows); rh = min(104, (1150 - y - 50) / len(rows))
        d.rectangle([m, y, m + 26, y + 26], fill=STONE); T(d, (m + 38, y + 13), c.get("a_lab", "Asked (listings)"), font(500, 26), INK, 1, "lm")
        lx = m + 38 + tw(d, c.get("a_lab", "Asked (listings)"), font(500, 26)) + 40
        d.rectangle([lx, y, lx + 26, y + 26], fill=NAVY); T(d, (lx + 38, y + 13), c.get("p_lab", "Paid (Ejari)"), font(500, 26), INK, 1, "lm")
        y += 60
        for i, (lab, a_, p_) in enumerate(rows):
            yy = y + i * rh; bh = rh * 0.30
            T(d, (m, yy + bh), lab, fit(d, lab, lab_w - 16, 30, 20, 500), INK, 1, "lm")
            wa = (xmax - x0) * a_ / vmax; wp = (xmax - x0) * p_ / vmax
            d.rectangle([x0, yy, x0 + wa, yy + bh], fill=STONE)
            T(d, (x0 + wa + 12, yy + bh / 2), fmt(a_), font(500, 26), SLATE, 1, "lm")
            d.rectangle([x0, yy + bh + 6, x0 + wp, yy + 2 * bh + 6], fill=NAVY)
            T(d, (x0 + wp + 12, yy + bh * 1.5 + 6), fmt(p_), font(600, 28), NAVY, 1, "lm")
    T(d, (m, PH - 140), f"DM {c['word']} for the full table", font(600, 34), NAVY)
    T(d, (m, PH - 84), c["src"], fit(d, c["src"], PW - 2 * m, 24, 18, 400), SLATE)
    T(d, (m, PH - 50), DISC, font(500, 22), STONE)
    img.save(out, quality=95)
