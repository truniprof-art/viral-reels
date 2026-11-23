import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
import cairo, math, sys, os, subprocess, wave
import numpy as np
import style as ST_
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from presssim2 import BX0, BX1, BY0, BY1, ANVIL_Y, PX0, PX1, SLOPE_Y, BR, T_ZERO, T_END, FPS, W, H, HEAD_H

D = np.load(f"{WORK}/press2.npz")
P, COLS, BORN, HEADY, CR, SLAMS, HIT = D["P"], D["COLS"], D["BORN"], D["HEADY"], D["CR"], D["SLAMS"], D["HIT"]
NF = len(P)
SLOW = []
SLOWF = 0.25
def build_map():
    ts = []; t = 0.0
    while t < T_END - 1e-6:
        ts.append(t)
        slow = any(a <= t < b for a, b in SLOW)
        t += (SLOWF if slow else 1.0) / FPS
    return np.array(ts)
TMAP = build_map()
def interp_pos(ts):
    fi = ts * FPS; f0 = int(min(NF - 1, math.floor(fi))); f1 = min(NF - 1, f0 + 1); u = fi - f0
    a, b = P[f0], P[f1]
    out = a * (1 - u) + b * u
    out = np.where(np.isnan(out), np.where(np.isnan(a), b, a), out)
    return out, f0
def slow_amount(ts):
    best = 0.0
    for a, b in SLOW:
        if a - 0.25 <= ts < b + 0.25:
            u = min(1, (ts - (a - 0.25)) / 0.25, (b + 0.25 - ts) / 0.25); best = max(best, u)
    return best
CXm = (PX0 + PX1) / 2

SPR = {}
def sprite(c, glow=0.0):
    key = (tuple(np.round(c, 3)), round(glow, 1))
    if key in SPR: return SPR[key]
    S = int(BR * 2 + 8); s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); x = cairo.Context(s)
    r, g, b = key[0]; cx = S / 2
    x.arc(cx, cx, BR, 0, 2 * math.pi); x.set_source_rgb(r * .78, g * .78, b * .78); x.fill()
    x.arc(cx, cx, BR - 2.2, 0, 2 * math.pi); x.set_source_rgb(r, g, b); x.fill()
    if glow > 0:
        x.arc(cx, cx, BR - 2.2, 0, 2 * math.pi); x.set_source_rgba(1, 1, 1, .45 * glow); x.fill()
    SPR[key] = s; return s

def hazard(ctx, x, y, w, h, a=1.0):
    ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip()
    ctx.set_source_rgba(.95, .75, .15, a); ctx.paint(); ctx.set_source_rgba(.13, .13, .15, a)
    for k in range(-10, int(w / 30) + 10):
        x0 = x + k * 44
        ctx.move_to(x0, y + h); ctx.line_to(x0 + 22, y + h); ctx.line_to(x0 + 22 + h, y); ctx.line_to(x0 + h, y); ctx.close_path(); ctx.fill()
    ctx.restore()

def draw_press(ctx, yb, a=1.0, shake=0.0):
    top = yb - HEAD_H
    ctx.rectangle(CXm - 18, 600, 36, top - 100 - 600); ctx.set_source_rgba(.55, .57, .61, a); ctx.fill()
    ctx.rectangle(CXm - 60, 600, 120, BY0 - 60 - 600); ctx.set_source_rgba(.24, .25, .28, a); ctx.fill()
    ctx.rectangle(CXm - 66, BY0 - 110, 132, 10); ctx.set_source_rgba(.4, .42, .46, a); ctx.fill()
    ctx.move_to(PX0, top); ctx.line_to(CXm, top - 110); ctx.line_to(PX1, top); ctx.close_path(); ctx.set_source_rgba(.42, .44, .48, a); ctx.fill()
    ctx.rectangle(PX0, top, PX1 - PX0, HEAD_H - 22); ctx.set_source_rgba(.34, .36, .4, a); ctx.fill()
    hazard(ctx, PX0, yb - 22, PX1 - PX0, 22, a)

def _surf(A, B, side):
    dx, dy = B[0] - A[0], B[1] - A[1]; L = math.hypot(dx, dy)
    nx, ny = (dy / L, -dx / L) if side > 0 else (-dy / L, dx / L)
    return (A[0] + nx * 22, A[1] + ny * 22), (B[0] + nx * 22, B[1] + ny * 22)
LA, LB = _surf((BX0 - 14, SLOPE_Y - 14), (PX0, ANVIL_Y + 14), 1)
RA, RB = _surf((BX1 + 14, SLOPE_Y - 14), (PX1, ANVIL_Y + 14), -1)
def _x_at(A, B, y): return A[0] + (B[0] - A[0]) * (y - A[1]) / (B[1] - A[1])
WL, WR, LID = BX0 + 8, BX1 - 8, BY0 + 8
YL = A_y = LA[1] + (LB[1] - LA[1]) * (WL - LA[0]) / (LB[0] - LA[0])
YR = RA[1] + (RB[1] - RA[1]) * (WR - RA[0]) / (RB[0] - RA[0])
XL_AN, XR_AN = _x_at(LA, LB, ANVIL_Y), _x_at(RA, RB, ANVIL_Y)

def draw_box(ctx, a=1.0):
    pts = [(WL, YL), (XL_AN, ANVIL_Y), (XR_AN, ANVIL_Y), (WR, YR)]
    ctx.move_to(*pts[0]); [ctx.line_to(*p) for p in pts[1:]]
    ctx.line_to(WR, BY1 + 140); ctx.line_to(WL, BY1 + 140); ctx.close_path()
    ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
    ctx.move_to(*pts[0]); [ctx.line_to(*p) for p in pts[1:]]
    ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(4); ctx.stroke()
    hazard(ctx, XL_AN, ANVIL_Y + 2, XR_AN - XL_AN, 20, a)
    ctx.rectangle(XL_AN - 20, ANVIL_Y + 22, XR_AN - XL_AN + 40, 90); ctx.set_source_rgba(.24, .25, .28, a); ctx.fill()
    ctx.move_to(WL, YL); ctx.line_to(WL, LID); ctx.line_to(WR, LID); ctx.line_to(WR, YR)
    ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(6); ctx.stroke()

def text(ctx, s, x, y, size, rgba, weight=cairo.FONT_WEIGHT_NORMAL, track=0):
    ctx.select_font_face("Fira Sans", cairo.FONT_SLANT_NORMAL, weight); ctx.set_font_size(size)
    ws = [ctx.text_extents(ch).x_advance for ch in s]; tot = sum(ws) + track * (len(s) - 1); xx = x - tot / 2
    for ch, w in zip(s, ws): ctx.move_to(xx, y); ctx.set_source_rgba(*rgba); ctx.show_text(ch); xx += w + track

def draw(ctx, fo):
    t = float(TMAP[fo]); f = int(min(NF - 1, round(t * FPS))); zt = t - T_ZERO
    pfi, f0i = interp_pos(t)
    ctx.set_source_rgb(*ST_.BG); ctx.paint()
    # camera shake on each slam impact
    sh = 0.0
    for s in SLAMS:
        d = t - s
        if 0 <= d < 0.25: sh = 9 * math.exp(-d * 18) * math.sin(d * 120)
    if 0 <= zt < 1: sh = 18 * math.exp(-zt * 5) * math.sin(zt * 80)
    zoom = 1 + 0.45 * (1 - math.exp(-zt * 2)) if zt > 0 else 1.0
    sm = slow_amount(t); fx, fy = 540, 1150
    if sm > 0:
        zoom = 1 + 1.1 * sm * sm * (3 - 2 * sm); fx = 540; fy = 1150 + (ANVIL_Y - 60 - 1150) * sm
    ctx.save(); ctx.translate(540 + sh, 1150); ctx.scale(zoom, zoom); ctx.translate(-fx, -fy)
    if zt <= 0: draw_box(ctx)
    pf = pfi; alive = np.where(~np.isnan(pf[:, 0]))[0]
    pprev, _ = interp_pos(max(0.0, t - 0.05))
    for i in alive:
        x, y = pf[i]
        px_, py_ = pprev[i]
        if False:
            c_ = COLS[i]
            for k in range(1, 6):
                u_ = k / 6; tx = x + (px_ - x) * u_; ty = y + (py_ - y) * u_
                ctx.arc(tx, ty, BR * (1 - u_ * .6), 0, 2 * math.pi); ctx.set_source_rgba(c_[0], c_[1], c_[2], .22 * (1 - u_)); ctx.fill()
        age = f - BORN[i]; glow = max(0.0, 1 - age / 8) if BORN[i] > 0 and age >= 0 else 0.0
        ST_.put(ctx, COLS[i], round(glow, 1), x, y, i, BR)
    if zt <= 0:
        draw_press(ctx, float(HEADY[f]))
    else:
        draw_press(ctx, float(HEADY[f]) - zt * 900, max(0, 1 - zt / .6))
    if len(CR):
        for row in CR[(CR[:, 0] > t - 0.45) & (CR[:, 0] <= t)]:
            te, ex, ey = row[0], row[1], row[2]; c_ = row[3:6]; d = t - te
            if d < 0.14:
                u = d / 0.14
                ctx.save(); ctx.translate(ex, ANVIL_Y - 7); ctx.scale(1.3 + 2.4 * u, 0.55 - 0.3 * u)
                ctx.arc(0, 0, BR, 0, 2 * math.pi)
                ctx.set_source_rgb(c_[0], c_[1], c_[2]); ctx.fill(); ctx.restore()
                if u > 0.5:
                    for k in range(5):
                        a_ = math.pi + k * math.pi / 4
                        ctx.move_to(ex, ANVIL_Y - 5); ctx.line_to(ex + math.cos(a_) * BR * 2.2 * u, ANVIL_Y - 5 + math.sin(a_) * 6)
                    ctx.set_source_rgba(1, 1, 1, .9); ctx.set_line_width(2); ctx.stroke()
            else:
                d2 = d - 0.14
                ctx.arc(ex, ANVIL_Y - 10, 20 + d2 * 260, math.pi, 2 * math.pi); ctx.set_source_rgba(c_[0], c_[1], c_[2], .8 * (1 - d2 / .31)); ctx.set_line_width(3); ctx.stroke()
                rr_ = np.random.default_rng(int(te * 1e4 + ex))
                for _ in range(8):
                    a_ = rr_.uniform(math.pi * 1.05, math.pi * 1.95); sp = rr_.uniform(300, 700)
                    ctx.arc(ex + math.cos(a_) * sp * d2, ANVIL_Y - 10 + math.sin(a_) * sp * d2 + 1200 * d2 * d2, 3, 0, 2 * math.pi)
                    ctx.set_source_rgba(c_[0], c_[1], c_[2], max(0, 1 - d2 / .31)); ctx.fill()
    ctx.restore()
    # impact flash on slams that crushed something
    if len(HIT):
        for (te, n) in HIT[(HIT[:, 0] > t - 0.12) & (HIT[:, 0] <= t)]:
            if slow_amount(t) > 0: continue
            pass
    if 0 <= zt < 0.3: ctx.set_source_rgba(1, 1, 1, .5 * (1 - zt / .3)); ctx.paint()
    # HUD
    if zt <= 0:
        rem = T_ZERO - t; sec = max(0, math.ceil(rem - 1e-6)); last = sec <= 5
        frac = rem % 1; pulse = 1 + (0.08 if last else 0.025) * math.exp(-(1 - frac) * 10)
        col = (1, .32, .32, 1) if last else ST_.ink(.92)
        ctx.save(); ctx.translate(540, 300); ctx.scale(pulse, pulse); text(ctx, f"0:{sec:02d}", 0, 0, 120, col, cairo.FONT_WEIGHT_NORMAL, 4); ctx.restore()
        bw = 360; ctx.set_source_rgba(*ST_.ink(.12)); ctx.rectangle(540 - bw / 2, 342, bw, 3); ctx.fill()
        ctx.set_source_rgba(*col[:3], .9); ctx.rectangle(540 - bw / 2, 342, bw * rem / T_ZERO, 3); ctx.fill()
        n = int(np.sum(~np.isnan(P[f, :, 0]))) + (int(np.sum((CR[:, 0] <= t) & (CR[:, 0] > t - 0.14))) if len(CR) else 0)
        text(ctx, f"{n}", 540, 470, 64, ST_.ink(.9), cairo.FONT_WEIGHT_BOLD, 2)
        text(ctx, ST_.LABEL, 540, 512, 24, ST_.ink(.4), cairo.FONT_WEIGHT_NORMAL, 8)
    else:
        text(ctx, "0:00", 540, 300, 120, (1, .32, .32, max(0, 1 - zt / .8)), cairo.FONT_WEIGHT_NORMAL, 4)
    sm_ = slow_amount(t)
    if sm_ > 0.3 and zt <= 0:
        text(ctx, "SLOW-MO", 540, 1830, 40, (1, .85, .2, sm_), cairo.FONT_WEIGHT_BOLD, 10)
    if t > T_END - 0.4: ctx.set_source_rgba(0, 0, 0, (t - (T_END - .4)) / .4); ctx.paint()

def audio(path):
    sr = 44100; n = int(len(TMAP) / FPS * sr); y = np.zeros(n)
    def s2v(ts): return float(np.searchsorted(TMAP, ts)) / FPS
    def add(at, s, raw=False):
        i = int((at if raw else s2v(at)) * sr); e = min(len(s), n - i)
        if e > 0 and i >= 0: y[i:i + e] += s[:e]
    def tt(d): return np.arange(int(d * sr)) / sr
    rr = np.random.default_rng(4)
    for s in SLAMS:
        x = tt(0.09); add(s - 0.09, 0.12 * rr.normal(0, 1, len(x)) * (x / 0.09) ** 2)               # hydraulic hiss down
        x = tt(0.5); add(s, 0.7 * np.sin(2 * np.pi * np.cumsum(55 * (1 + 2.5 * np.exp(-x * 30))) / sr) * np.exp(-x * 9))  # BAM
        nz = rr.normal(0, 1, len(x)); add(s, 0.25 * (nz - np.convolve(nz, np.ones(3) / 3, "same")) * np.exp(-x * 40))
        x = tt(0.35); add(s + 0.06, 0.05 * rr.normal(0, 1, len(x)) * np.exp(-x * 6))                # lift hiss
    if len(HIT):
        for (te, k) in HIT:
            x = tt(0.3); nz = rr.normal(0, 1, len(x))
            crunch = (nz - np.convolve(nz, np.ones(2) / 2, "same")) * np.exp(-x * 30) * min(0.6, 0.15 + 0.03 * k)
            pop = np.sin(2 * np.pi * np.cumsum(700 * (1 + 2 * np.exp(-x * 40))) / sr) * np.exp(-x * 25) * 0.2
            add(te, crunch + pop)
    for s in range(int(T_ZERO)):
        x = tt(0.05); l5 = s >= T_ZERO - 5
        add(s, (0.2 if l5 else 0.08) * np.sin(2 * np.pi * (1700 if l5 else 1100) * x) * np.exp(-x * 90))
    x = tt(s2v(T_ZERO)); add(0, (np.sin(2 * np.pi * 55 * x) + .5 * np.sin(2 * np.pi * 82.4 * x)) * .04 * (x / T_ZERO) ** 2)
    x = tt(2.4); add(T_ZERO, np.sin(2 * np.pi * np.cumsum(36 * (1 + 3 * np.exp(-x * 18))) / sr) * np.exp(-x * 2.5))
    nz = rr.normal(0, 1, len(x)); add(T_ZERO, .45 * (nz - np.convolve(nz, np.ones(4) / 4, "same")) * np.exp(-x * 3))
    for k in range(50):
        xx = tt(.08); add(T_ZERO + rr.uniform(0, 1.6), .05 * np.sin(2 * np.pi * rr.uniform(2500, 6000) * xx) * np.exp(-xx * 60))
    y = np.tanh(y * 1.3) * .85; fl = int(.4 * sr); y[-fl:] *= np.linspace(1, 0, fl)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(surf)
    if sys.argv[1] == "snap":
        for x in map(float, sys.argv[2:]):
            draw(ctx, int(np.searchsorted(TMAP, x))); surf.write_to_png(f"{WORK}/p3_{x}.png")
    elif sys.argv[1] == "audio":
        audio(f"{WORK}/p3_audio.wav")
    else:
        part, npart = int(sys.argv[2]), int(sys.argv[3]); a = len(TMAP) * part // npart; b = len(TMAP) * (part + 1) // npart
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", "yuv420p", f"{WORK}/p3p{part}_tmp.mp4"], stdin=subprocess.PIPE)
        for f in range(a, b): draw(ctx, f); surf.flush(); p.stdin.write(bytes(surf.get_data()))
        p.stdin.close(); assert p.wait() == 0
        os.replace(f"{WORK}/p3p{part}_tmp.mp4", f"{WORK}/p3p{part}.mp4")
