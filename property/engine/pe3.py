"""New reel formats on the pe2 base: slope (2020 vs 2025), countdown cards 10->1, quiz x3, multi-line race."""
import math
from pe2 import (font, ease, wrap, T, fitf, tw, ring, kicker, VIG, W, H, FPS, M, SAND, LIME, GREY, MID, BLUE, WHITE, NEG,
                 DISC, CT, Reel, head, footer, plaque, note_plaque, hook_plaque, win, nf, build_bg, stills, render, MUSIC, POOL)
from PIL import Image, ImageDraw


def _spread(ys, gap):
    """push label y-positions apart so they do not overlap (keeps order)."""
    idx = sorted(range(len(ys)), key=lambda i: ys[i]); out = list(ys)
    for _ in range(60):
        moved = False
        for a, b in zip(idx, idx[1:]):
            if out[b] - out[a] < gap:
                d = (gap - (out[b] - out[a])) / 2; out[a] -= d; out[b] += d; moved = True
        if not moved: break
    return out


# ---------- slope: before / after ----------
def slope(c):
    R = c["rows"]; fmt = c["fmt"]; N = len(R)
    lo = min(min(a, b) for _, a, b in R); hi = max(max(a, b) for _, a, b in R)
    XL, XR = M + 330, W - M - 210; Y0, Y1 = CT + 140, 1220
    def Y(v): return Y1 - (Y1 - Y0) * (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo))
    HOOK = 96; TOT = c.get("frames", 480); TAKE = c.get("take_at", 300)
    gl = _spread([Y(a) for _, a, _ in R], 42); gr = _spread([Y(b) for _, _, b in R], 42)
    best = max(range(N), key=lambda i: R[i][2] / R[i][1])
    def draw(d, fi):
        t = fi / FPS; a = ease(t / 0.3); head(d, a, c["kick"], c["title"], c["sub"])
        T(d, (XL, CT + 50), c["left"], font(600, 40), GREY, a, anchor="mm"); T(d, (XR, CT + 50), c["right"], font(600, 40), SAND, a, anchor="mm")
        d.line([(XL, Y0 - 20), (XL, Y1 + 20)], fill=(255, 255, 255, int(70 * a)), width=2)
        d.line([(XR, Y0 - 20), (XR, Y1 + 20)], fill=(255, 255, 255, int(70 * a)), width=2)
        for i, (lab, v0, v1) in enumerate(R):
            e = ease((t - 0.4 - i * 0.12) / 0.4); e2 = ease((t - 1.0 - i * 0.18) / 0.8)
            col = SAND if i == best else BLUE; y0, y1 = Y(v0), Y(v1)
            if e > 0:
                d.ellipse([XL - 8, y0 - 8, XL + 8, y0 + 8], fill=col + (int(255 * e),))
                T(d, (XL - 22, gl[i]), f"{lab}  {fmt(v0)}", fitf(d, f"{lab}  {fmt(v0)}", 500, 28, XL - M - 30, 18), LIME, e, anchor="rm")
            if e2 > 0:
                xe = XL + (XR - XL) * e2; ye = y0 + (y1 - y0) * e2
                d.line([(XL, y0), (xe, ye)], fill=col + (230,), width=6 if i == best else 4)
                if e2 >= 0.99:
                    d.ellipse([XR - 9, y1 - 9, XR + 9, y1 + 9], fill=col + (255,))
                    g = v1 / v0 - 1
                    T(d, (XR + 22, gr[i]), f"{fmt(v1)}  +{g * 100:.0f}%", font(600 if i == best else 500, 28), SAND if i == best else LIME, 1, anchor="lm")
        yb = 1310
        if fi < HOOK: hook_plaque(d, yb, c["hook"][0], c["hook"][1], min(ease(fi / 10), ease((HOOK - fi) / 10)))
        ee = win(fi, TAKE, TOT + 20, 14)
        if ee: note_plaque(d, yb, c["take"][0], c["take"][1], ee)
        footer(d, a, c["src"])
    return Reel(TOT, draw)


# ---------- countdown cards 10 -> 1 ----------
def countdown(c):
    R = c["rows"]; n = len(R); fmt = c["fmt"]
    HOOK, CARD, SUMF = 75, 51, 150
    TOT = HOOK + CARD * n + SUMF
    def draw(d, fi):
        if fi < HOOK:
            t = fi / FPS; a = ease(t / 0.25); kicker(d, c["kick"], a); ring(d, a)
            f = fitf(d, c["hook"][0], 600, 230, W - 2 * M, 100)
            T(d, (W / 2, 820 + 30 * (1 - a)), c["hook"][0], f, SAND, a, anchor="mm")
            for j, ln in enumerate(wrap(d, c["hook"][1], font(500, 58), W - 2 * M)):
                T(d, (W / 2, 1000 + j * 72), ln, font(500, 58), WHITE, ease((t - 0.3) / 0.3), anchor="mm")
            return
        if fi < HOOK + CARD * n:
            k = (fi - HOOK) // CARD; t = ((fi - HOOK) % CARD) / FPS; lab, v, sub = R[k]; rank = n - k
            kicker(d, c["kick"], 1); ring(d, 1)
            pw = (W - 2 * M - 8 * (n - 1)) / n
            for j in range(n):
                x = M + j * (pw + 8); d.rectangle([x, 300, x + pw, 306], fill=(SAND if j <= k else WHITE) + (255 if j <= k else 60,))
            a = ease(t / 0.18); top = rank <= 3
            T(d, (M, 420 + 30 * (1 - a)), f"#{rank}", font(600, 150), SAND if top else LIME, a)
            fN = fitf(d, lab, 600, 104, W - 2 * M, 50)
            for j, ln in enumerate(wrap(d, lab, fN, W - 2 * M)):
                T(d, (M, 640 + j * fN.size * 1.1), ln, fN, WHITE, ease((t - 0.08) / 0.2))
            e = ease((t - 0.2) / 0.35)
            T(d, (M, 930), fmt(v * min(1, e * 1.0)), font(600, 170), SAND if top else LIME, ease((t - 0.15) / 0.2))
            T(d, (M, 1140), sub, fitf(d, sub, 500, 44, W - 2 * M, 28), GREY, ease((t - 0.35) / 0.2))
            footer(d, 1, c["src"]); return
        t = (fi - HOOK - CARD * n) / FPS; a = ease(t / 0.3)
        kicker(d, c["kick"], 1); ring(d, 1)
        T(d, (M, 300), c["sum_title"], fitf(d, c["sum_title"], 600, 60, W - 2 * M, 36), WHITE, a)
        for j, (lab, v, _) in enumerate(reversed(R)):
            e = ease((t - 0.15 - j * 0.05) / 0.3); y = 420 + j * 84
            T(d, (M, y), f"{j + 1}. {lab}", fitf(d, f"{j + 1}. {lab}", 500, 40, W - 2 * M - 260, 26), SAND if j == 0 else LIME, e)
            T(d, (W - M, y), fmt(v), font(600, 40), SAND if j == 0 else LIME, e, anchor="ra")
        footer(d, a, c["src"])
    return Reel(TOT, draw)


# ---------- quiz: 3 questions ----------
def quiz(c):
    Q = c["qs"]; HOOK, QF = 66, 210; TOT = HOOK + QF * len(Q) + 90
    def draw(d, fi):
        if fi < HOOK:
            t = fi / FPS; a = ease(t / 0.25); kicker(d, c["kick"], a); ring(d, a)
            T(d, (W / 2, 820), c["hook"][0], fitf(d, c["hook"][0], 600, 200, W - 2 * M, 90), SAND, a, anchor="mm")
            for j, ln in enumerate(wrap(d, c["hook"][1], font(500, 56), W - 2 * M)):
                T(d, (W / 2, 990 + j * 70), ln, font(500, 56), WHITE, ease((t - 0.3) / 0.3), anchor="mm")
            return
        if fi < HOOK + QF * len(Q):
            k = (fi - HOOK) // QF; t = ((fi - HOOK) % QF) / FPS; q = Q[k]
            kicker(d, f"{c['kick']} · {k + 1} OF {len(Q)}", 1); ring(d, 1)
            a = ease(t / 0.25)
            for j, ln in enumerate(wrap(d, q["q"], font(600, 64), W - 2 * M)):
                T(d, (M, 330 + j * 78 + 20 * (1 - a)), ln, font(600, 64), WHITE, a)
            reveal = t >= 4.0
            for j, opt in enumerate(q["opts"]):
                e = ease((t - 0.4 - j * 0.15) / 0.3); y = 640 + j * 170
                ok = j == q["ans"]
                fill = (SAND if ok else (70, 80, 95)) if reveal else (40, 55, 78)
                alpha = 255 if (not reveal or ok) else 120
                d.rectangle([M, y, W - M, y + 130], fill=fill + (int(alpha * e),))
                T(d, (M + 40, y + 65), "ABC"[j], font(600, 56), (MID if (reveal and ok) else SAND), e, anchor="lm")
                T(d, (M + 120, y + 65), opt, fitf(d, opt, 600, 56, W - 2 * M - 160, 30), (MID if (reveal and ok) else WHITE), e, anchor="lm")
            if 1.3 <= t < 4.0:
                n = 3 - int((t - 1.3) / 0.9)
                if n > 0: T(d, (W / 2, 1230), str(n), font(600, 140), SAND, 1, anchor="mm")
            if reveal:
                e = ease((t - 4.0) / 0.3)
                for j, ln in enumerate(wrap(d, q["why"], font(500, 40), W - 2 * M)):
                    T(d, (M, 1180 + j * 52), ln, font(500, 40), LIME, e)
            footer(d, 1, c["src"]); return
        t = (fi - HOOK - QF * len(Q)) / FPS; a = ease(t / 0.3); kicker(d, c["kick"], 1); ring(d, 1)
        T(d, (W / 2, 820), "How many did you get?", fitf(d, "How many did you get?", 600, 80, W - 2 * M), WHITE, a, anchor="mm")
        T(d, (W / 2, 960), "Write your score in the comments", font(500, 48), SAND, ease((t - 0.3) / 0.3), anchor="mm")
        footer(d, a, c["src"])
    return Reel(TOT, draw)


# ---------- multi-line race ----------
def multiline(c):
    S = c["series"]; X = c["years"]; names = list(S); n = len(X); fmt = c["fmt"]
    cols = [SAND, BLUE, LIME, NEG][:len(names)]
    HOOK, DRAW, HOLD = 75, 420, 150; TOT = HOOK + DRAW + HOLD
    hi = max(max(v) for v in S.values()) * 1.1
    gx0, gx1, gy0, gy1 = M + 10, W - M - 200, CT + 80, 1250
    def px(u): return gx0 + (gx1 - gx0) * u / (n - 1)
    def py(v): return gy1 - (gy1 - gy0) * v / hi
    def val(s, u):
        k = min(int(u), n - 2); x = u - k; x = x * x * (3 - 2 * x); return S[s][k] + (S[s][k + 1] - S[s][k]) * x
    def draw(d, fi):
        t = fi / FPS; a = ease(t / 0.3); head(d, a, c["kick"], c["title"], c["sub"])
        for gv in c["grid"]:
            y = py(gv); d.line([(gx0, y), (gx1, y)], fill=(255, 255, 255, int(40 * a)), width=1)
            T(d, (gx0, y - 6), fmt(gv), font(400, 22), GREY, a, anchor="ld")
        for i, yr in enumerate(X):
            if i % 2 == 0 or i == n - 1: T(d, (px(i), gy1 + 14), str(yr), font(400, 24), GREY, a, anchor="ma")
        u = max(0, min(1, (fi - 20) / (HOOK - 20 + DRAW))); u = (n - 1) * (u * u * (3 - 2 * u))
        ends = []
        for s, col in zip(names, cols):
            pts = []; steps = int(u * 12) + 1
            for j in range(steps + 1):
                uu = u * j / steps; pts.append((px(uu), py(val(s, uu))))
            if len(pts) > 1: d.line(pts, fill=col + (255,), width=7, joint="curve")
            hx, hy = pts[-1]; d.ellipse([hx - 11, hy - 11, hx + 11, hy + 11], fill=col + (255,)); ends.append([hy, s, col, val(s, u), hx])
        ys = _spread([e[0] for e in ends], 70)
        for (hy, s, col, v, hx), yy in zip(ends, ys):
            T(d, (hx + 20, yy - 16), s, font(600, 30), col, 1, anchor="lm"); T(d, (hx + 20, yy + 18), fmt(v), font(500, 28), WHITE, 1, anchor="lm")
        T(d, (W - M, 1420), str(X[min(n - 1, int(u + 0.5))]), font(600, 140), SAND, ease((fi - HOOK + 10) / 12) if fi >= HOOK - 10 else 0, anchor="rs")
        if fi < HOOK: hook_plaque(d, 1300, c["hook"][0], c["hook"][1], min(ease(fi / 10), ease((HOOK - fi) / 10)))
        ee = win(fi, HOOK + DRAW, TOT + 20, 14)
        if ee: note_plaque(d, 1300, c["take"][0], c["take"][1], ee, w=560)
        footer(d, a, c["src"])
    return Reel(TOT, draw)
