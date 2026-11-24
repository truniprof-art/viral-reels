import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
import cairo, math, sys, os, subprocess, wave
import numpy as np
import style as ST_
os.environ.update(ZX="24", ZY="18", S1="50", OPEN="17,17,0,12,12")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rollsim import BX0, BX1, BY0, RR, GAP, ROLL_Y, NPAIR, PAIRS, PAIR_W, OPEN, BR, T_ZERO, T_END, FPS, W, H, PINCH_Y, roller_speed

D = np.load(f"{WORK}/roll.npz")
P, COLS, BORN, RANG, CR, COUNT = D["P"], D["COLS"], D["BORN"], D["RANG"], D["CR"], D["COUNT"]
NF = len(P)

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

def angle_since(t, t0):
    """roller rotation accumulated since it opened"""
    if t <= t0: return 0.0
    f = min(NF - 1, int(t * FPS)); f0 = min(NF - 1, int(t0 * FPS))
    return float(RANG[f] - RANG[f0])

def draw_roller(ctx, cx, cy, ang, active):
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(ang)
    n = 14
    ctx.new_path()
    for i in range(n * 2):
        a = i * math.pi / n; r = RR + 2 if i % 2 == 0 else RR - 5
        a0, a1 = a - math.pi / n / 2, a + math.pi / n / 2
        ctx.arc(0, 0, r, a0, a1)
    ctx.close_path()
    ctx.set_source_rgb(.36, .38, .42) if active else ctx.set_source_rgb(.26, .27, .3); ctx.fill()
    ctx.arc(0, 0, RR - 12, 0, 2 * math.pi); ctx.set_source_rgb(.22, .23, .26); ctx.fill()
    for k in range(3):
        a = k * 2 * math.pi / 3
        ctx.move_to(0, 0); ctx.line_to((RR - 12) * math.cos(a), (RR - 12) * math.sin(a))
    ctx.set_source_rgb(.45, .47, .52); ctx.set_line_width(5); ctx.stroke()
    ctx.arc(0, 0, 7, 0, 2 * math.pi); ctx.set_source_rgb(.6, .62, .66); ctx.fill()
    ctx.restore()

def hazard(ctx, x, y, w, h, a=1.0):
    ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip()
    ctx.set_source_rgba(.95, .75, .15, a); ctx.paint(); ctx.set_source_rgba(.13, .13, .15, a)
    for k in range(-6, int(w / 30) + 6):
        x0 = x + k * 36
        ctx.move_to(x0, y + h); ctx.line_to(x0 + 18, y + h); ctx.line_to(x0 + 18 + h, y); ctx.line_to(x0 + h, y); ctx.close_path(); ctx.fill()
    ctx.restore()

def draw_machine(ctx, t, a=1.0):
    # floor housing under the rollers
    ctx.rectangle(BX0, ROLL_Y, BX1 - BX0, 260); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
    for k, cx in enumerate(PAIRS):
        active = t >= OPEN[k]
        ang = angle_since(t, OPEN[k]) if t < T_ZERO else angle_since(T_ZERO, OPEN[k])
        draw_roller(ctx, cx - RR - GAP / 2, ROLL_Y, ang, active)
        draw_roller(ctx, cx + RR + GAP / 2, ROLL_Y, -ang, active)
        # sliding cover plate over a pair that is not open yet
        if OPEN[k] > 0:
            u = min(1, max(0, (t - OPEN[k] + 0.35) / 0.35))
            if u < 1:
                w = PAIR_W - 12
                x0 = cx - w / 2 + (w + 20) * u * (1 if k > 2 else -1)
                ctx.save(); ctx.rectangle(cx - PAIR_W / 2 + 4, ROLL_Y - RR - 40, PAIR_W - 8, 60); ctx.clip()
                ctx.rectangle(x0, ROLL_Y - RR - 22, w, 16); ctx.set_source_rgb(.4, .42, .46); ctx.fill()
                hazard(ctx, x0, ROLL_Y - RR - 22, w, 6)
                ctx.restore()
    # dividers
    for k in range(NPAIR + 1):
        x = BX0 + k * PAIR_W
        ctx.move_to(x, ROLL_Y - RR - 8); ctx.line_to(x, ROLL_Y + RR)
        ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(14); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    ctx.set_line_cap(cairo.LINE_CAP_BUTT)
    # tank outline
    ctx.move_to(BX0 - 4, ROLL_Y + 260); ctx.line_to(BX0 - 4, BY0 - 4); ctx.line_to(BX1 + 4, BY0 - 4); ctx.line_to(BX1 + 4, ROLL_Y + 260)
    ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(6); ctx.stroke()
    hazard(ctx, BX0, ROLL_Y + RR + 30, BX1 - BX0, 14, a)

def text(ctx, s, x, y, size, rgba, weight=cairo.FONT_WEIGHT_NORMAL, track=0):
    ctx.select_font_face("Fira Sans", cairo.FONT_SLANT_NORMAL, weight); ctx.set_font_size(size)
    ws = [ctx.text_extents(ch).x_advance for ch in s]; tot = sum(ws) + track * (len(s) - 1); xx = x - tot / 2
    for ch, w in zip(s, ws): ctx.move_to(xx, y); ctx.set_source_rgba(*rgba); ctx.show_text(ch); xx += w + track

def draw(ctx, f):
    t = f / FPS; zt = t - T_ZERO
    ctx.set_source_rgb(*ST_.BG); ctx.paint()
    sh = 18 * math.exp(-zt * 5) * math.sin(zt * 80) if 0 <= zt < 1 else 0
    zoom = 1 + .4 * (1 - math.exp(-zt * 2)) if zt > 0 else 1
    ctx.save(); ctx.translate(540 + sh, 1150); ctx.scale(zoom, zoom); ctx.translate(-540, -1150)
    if zt <= 0: draw_machine(ctx, t)
    else: draw_machine(ctx, t, max(0, 1 - zt / .6))
    pf = P[f]; alive = np.where(~np.isnan(pf[:, 0]))[0]
    for i in alive:
        x, y = pf[i]; age = f - BORN[i]
        glow = max(0.0, 1 - age / 8) if BORN[i] > 0 and age >= 0 else 0.0
        ST_.put(ctx, COLS[i], glow, x, y, i, BR)
    # squeeze FX: the ball is pinched between the rollers (tall & thin), then pops
    if len(CR):
        for row in CR[(CR[:, 0] > t - .35) & (CR[:, 0] <= t)]:
            te, ex = row[0], row[1]; c_ = row[3:6]; d = t - te
            cx = min(PAIRS, key=lambda p: abs(p - ex))
            if d < .12:
                u = d / .12
                ctx.save(); ctx.translate(cx, PINCH_Y + 8 + 14 * u); ctx.scale(.75 - .5 * u, 1.0 + .7 * u)
                ctx.arc(0, 0, BR, 0, 2 * math.pi); ctx.set_source_rgb(*c_); ctx.fill(); ctx.restore()
            else:
                d2 = d - .12
                ctx.arc(cx, PINCH_Y, 14 + d2 * 220, math.pi, 2 * math.pi); ctx.set_source_rgba(*c_, .8 * (1 - d2 / .23)); ctx.set_line_width(3); ctx.stroke()
                rr_ = np.random.default_rng(int(te * 1e4 + ex))
                for _ in range(5):
                    a_ = rr_.uniform(math.pi * 1.1, math.pi * 1.9); sp = rr_.uniform(200, 450)
                    ctx.arc(cx + math.cos(a_) * sp * d2, PINCH_Y + math.sin(a_) * sp * d2, 3, 0, 2 * math.pi)
                    ctx.set_source_rgba(*c_, max(0, 1 - d2 / .23)); ctx.fill()
    ctx.restore()
    if 0 <= zt < .3: ctx.set_source_rgba(1, 1, 1, .5 * (1 - zt / .3)); ctx.paint()
    if zt <= 0:
        rem = T_ZERO - t; sec = max(0, math.ceil(rem - 1e-6)); last = sec <= 5
        frac = rem % 1; pulse = 1 + (.08 if last else .02) * math.exp(-(1 - frac) * 10)
        col = (1, .32, .32, 1) if last else ST_.ink(.92)
        ctx.save(); ctx.translate(540, 250); ctx.scale(pulse, pulse); text(ctx, f"0:{sec:02d}", 0, 0, 120, col, cairo.FONT_WEIGHT_NORMAL, 4); ctx.restore()
        bw = 360; ctx.set_source_rgba(*ST_.ink(.12)); ctx.rectangle(540 - bw / 2, 292, bw, 3); ctx.fill()
        ctx.set_source_rgba(*col[:3], .9); ctx.rectangle(540 - bw / 2, 292, bw * rem / T_ZERO, 3); ctx.fill()
        ST_.LAST[0] = int(COUNT[f]); text(ctx, f"{int(COUNT[f])}", 540, 410, 64, ST_.ink(.9), cairo.FONT_WEIGHT_BOLD, 2)
        text(ctx, ST_.LABEL, 540, 452, 24, ST_.ink(.4), cairo.FONT_WEIGHT_NORMAL, 8)
    else:
        text(ctx, "0:00", 540, 250, 120, (1, .32, .32, max(0, 1 - zt / .8)), cairo.FONT_WEIGHT_NORMAL, 4)
    ST_.endcard(ctx, t, T_END, text)

def audio(path):
    sr = 44100; n = int(T_END * sr); y = np.zeros(n)
    def add(at, s):
        i = int(at * sr); e = min(len(s), n - i)
        if e > 0 and i >= 0: y[i:i + e] += s[:e]
    def tt(d): return np.arange(int(d * sr)) / sr
    rr = np.random.default_rng(6)
    # motor hum rising with roller speed; grinding noise grows with number of open pairs
    x = tt(T_ZERO); sp = np.array([roller_speed(v) for v in x[::441]]); sp = np.repeat(sp, 441)[:len(x)]
    nopen = np.array([sum(v >= o for o in OPEN) for v in x[::441]]); nopen = np.repeat(nopen, 441)[:len(x)]
    ph = np.cumsum(40 + 6 * sp) / sr
    nz = rr.normal(0, 1, len(x)); grind = (nz - np.convolve(nz, np.ones(6) / 6, "same"))
    add(0, (.05 * np.sin(2 * np.pi * ph) + .025 * np.sin(4 * np.pi * ph)) * np.minimum(1, nopen) + .02 * grind * nopen / 5 * (sp / 50) ** .5)
    for o in OPEN:
        if o > 0:
            k = tt(.5); add(o - .3, .25 * np.sin(2 * np.pi * np.cumsum(300 - 200 * k / .5) / sr) * np.exp(-k * 6))
            add(o, .5 * np.sin(2 * np.pi * np.cumsum(60 * (1 + 2 * np.exp(-k * 20))) / sr) * np.exp(-k * 7))
    last = -1
    for row in CR:
        te = row[0]
        if te - last < .015: continue
        last = te; k = tt(.18); nz = rr.normal(0, 1, len(k))
        add(te, .2 * (nz - np.convolve(nz, np.ones(2) / 2, "same")) * np.exp(-k * 45) + .1 * np.sin(2 * np.pi * rr.uniform(500, 900) * k) * np.exp(-k * 20))
    for s in range(int(T_ZERO)):
        k = tt(.05); l5 = s >= T_ZERO - 5
        add(s, (.2 if l5 else .08) * np.sin(2 * np.pi * (1700 if l5 else 1100) * k) * np.exp(-k * 90))
    k = tt(2.4); add(T_ZERO, np.sin(2 * np.pi * np.cumsum(36 * (1 + 3 * np.exp(-k * 18))) / sr) * np.exp(-k * 2.5))
    nz = rr.normal(0, 1, len(k)); add(T_ZERO, .45 * (nz - np.convolve(nz, np.ones(4) / 4, "same")) * np.exp(-k * 3))
    for j in range(50):
        kk = tt(.08); add(T_ZERO + rr.uniform(0, 1.6), .05 * np.sin(2 * np.pi * rr.uniform(2500, 6000) * kk) * np.exp(-kk * 60))
    y = np.tanh(y * 1.3) * .85; fl = int(.4 * sr); y[-fl:] *= np.linspace(1, 0, fl)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(surf)
    if sys.argv[1] == "snap":
        for x in map(float, sys.argv[2:]):
            draw(ctx, int(x * FPS)); surf.write_to_png(f"{WORK}/rl_{x}.png")
    elif sys.argv[1] == "audio": audio(f"{WORK}/rl_audio.wav")
    else:
        part, npart = int(sys.argv[2]), int(sys.argv[3]); a = NF * part // npart; b = NF * (part + 1) // npart
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", "yuv420p", f"{WORK}/rlp{part}_tmp.mp4"], stdin=subprocess.PIPE)
        for f in range(a, b): draw(ctx, f); surf.flush(); p.stdin.write(bytes(surf.get_data()))
        p.stdin.close(); assert p.wait() == 0
        os.replace(f"{WORK}/rlp{part}_tmp.mp4", f"{WORK}/rlp{part}.mp4")
