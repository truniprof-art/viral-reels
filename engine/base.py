import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Shared engine for the 'crush to multiply' series: tank, balls, spawning, explosion, recording, rendering, audio."""
import pymunk, math, random, sys, os, subprocess, wave
import numpy as np
import cairo

W, H, FPS = 1080, 1920, 30
BX0, BX1, BY0, FLOOR = 110, 970, 560, 1640
BR = 15.0
T_ZERO, T_END = 30.0, 33.0
SUB = 8
MAXN = 1050

PAL = [(0.0, (1.0, 0.5, 0.08)), (9.0, (0.1, 0.8, 1.0)), (15.0, (0.62, 0.3, 1.0)),
       (20.0, (1.0, 0.82, 0.1)), (24.0, (0.2, 0.88, 0.42)), (27.0, (1.0, 0.28, 0.55))]
PAL = [(t, __import__("hue").rot(c)) for t, c in PAL]
def colour(t):
    c = PAL[0][1]
    for s, cc in PAL:
        if t >= s: c = cc
    return c

class Mech:
    """override in each mechanism"""
    name = "mech"
    tank_walls = True
    def build(self, space): pass
    def step(self, t, dt): pass
    def crush(self, t, pos):           # pos: (n,2) array of ball positions -> boolean mask of crushed balls
        return np.zeros(len(pos), bool)
    def spawn_dir(self, x, y):         # preferred launch direction for the two new balls
        return (0.0, -1.0)
    def state(self, t): return np.zeros(4, np.float32)
    def draw(self, ctx, t, st, a=1.0): pass
    def sounds(self): return []        # list of (time, kind)
    def explode(self, space): pass

def run(mech, seed, record=True, start=((540, 900), (150, 0))):
    rnd = random.Random(seed)
    space = pymunk.Space(); space.gravity = (0, 1500); space.iterations = 25
    statics = []
    if mech.tank_walls:
        for a, b in (((BX0 - 20, BY0 - 20), (BX0 - 20, FLOOR + 20)), ((BX1 + 20, BY0 - 20), (BX1 + 20, FLOOR + 20)),
                     ((BX0 - 20, BY0 - 20), (BX1 + 20, BY0 - 20)), ((BX0 - 20, FLOOR + 20), (BX1 + 20, FLOOR + 20))):
            s = pymunk.Segment(space.static_body, a, b, 20); s.elasticity = 0.7; s.friction = 0.4; space.add(s); statics.append(s)
    mech.build(space)
    balls = {}; nid = [0]; spawnq = []
    def add_ball(pos, vel, col, f):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BR)); b.position = pos; b.velocity = vel
        c = pymunk.Circle(b, BR); c.elasticity = 0.78; c.friction = 0.4
        space.add(b, c); balls[c] = [b, col, f, nid[0]]; nid[0] += 1
    for st_ in (start if isinstance(start, list) else [start]): add_ball(st_[0], st_[1], colour(0), 0)
    nfr = int(T_END * FPS); MAXID = 7000
    P = np.full((nfr, MAXID, 2), np.nan, np.float32) if record else None
    COLS = np.zeros((MAXID, 3), np.float32); BORN = np.full(MAXID, -1, np.int32)
    CR = []; COUNT = np.zeros(nfr, np.int32); ST = []
    exploded = False
    for f in range(nfr):
        for s_ in range(SUB):
            t = (f + s_ / SUB) / FPS; dt = 1 / FPS / SUB
            if t >= T_ZERO and not exploded:
                exploded = True
                for s in statics: space.remove(s)
                mech.explode(space)
                space.gravity = (0, 0); space.damping = 0.3
                for c, bl in balls.items():
                    b = bl[0]; d = b.position - (540, 1150); L = max(1, d.length)
                    b.velocity = d / L * rnd.uniform(700, 1600) + pymunk.Vec2d(rnd.uniform(-150, 150), rnd.uniform(-150, 150))
            if not exploded: mech.step(t, dt)
            space.step(dt)
            if not exploded:
                shapes = list(balls.keys())
                if shapes:
                    pos = np.array([balls[c][0].position for c in shapes])
                    mask = mech.crush(t, pos)
                    for c, m in zip(shapes, mask):
                        if not m: continue
                        if len(balls) + 2 * len(spawnq) >= MAXN: break
                        b, col, bf, i_ = balls.pop(c); p = b.position; space.remove(b, c)
                        CR.append((t, p.x, p.y, *col))
                        spawnq.append((t + 0.12, p.x, p.y, colour(t)))
                due = [q for q in spawnq if q[0] <= t]
                if due:
                    pos = np.array([bl[0].position for bl in balls.values()]) if balls else np.zeros((0, 2))
                    for item in due:
                        spawnq.remove(item); _, x0, y0, col = item
                        dx, dy = mech.spawn_dir(x0, y0)
                        for sgn in (-1, 1):
                            # first free spot from the crush point moving against gravity
                            if hasattr(mech, "spawn_xy"): x, y = mech.spawn_xy(x0, y0, sgn)
                            else:
                                x = min(BX1 - BR - 2, max(BX0 + BR + 2, mech.spawn_x(x0, sgn) if hasattr(mech, "spawn_x") else x0 + sgn * BR * 1.1)); y = y0 - 2 * BR
                            for _ in range(80):
                                if y < BY0 + BR + 2: y = BY0 + BR + 2; break
                                if len(pos) == 0 or np.min(np.hypot(pos[:, 0] - x, pos[:, 1] - y)) > 2 * BR - 1: break
                                y -= BR * 0.7
                            vx = sgn * rnd.uniform(150, 420) + dx * 300; vy = dy * rnd.uniform(700, 1100)
                            add_ball((x, y), (vx, vy), col, f)
                            pos = np.vstack([pos, [x, y]]) if len(pos) else np.array([[x, y]])
                for c, bl in balls.items():
                    v = bl[0].velocity
                    if v.length > 1700: bl[0].velocity = v * (1700 / v.length)
                    p = bl[0].position
                    if not (BX0 - 8 < p.x < BX1 + 8 and BY0 - 8 < p.y < FLOOR + 8):
                        bl[0].position = (min(BX1 - 20, max(BX0 + 20, p.x)), min(FLOOR - 20, max(BY0 + 20, p.y))); bl[0].velocity = (0, 0)
        COUNT[f] = len(balls) + 2 * len(spawnq)
        ST.append(mech.state(f / FPS))
        if record:
            for c, (b, col, bf, i_) in balls.items():
                P[f, i_] = b.position; COLS[i_] = col; BORN[i_] = bf
    return dict(P=P, COLS=COLS, BORN=BORN, CR=np.array(CR), COUNT=COUNT, ST=np.array(ST))

def search(make, seeds):
    import base as _b
    for seed in seeds:
        r = _b.run(make(), seed, record=False); C = r["COUNT"]
        print(seed, [int(C[int(s * FPS)]) for s in (5, 10, 15, 20, 24, 27, 29.9)], flush=True)

# ---------------- rendering ----------------
SPR = {}
def sprite(c, glow=0.0):
    key = (tuple(np.round(c, 3)), round(glow, 1))
    if key in SPR: return SPR[key]
    S = int(BR * 2 + 8); s = cairo.ImageSurface(cairo.FORMAT_ARGB32, S, S); x = cairo.Context(s)
    r, g, b = key[0]; cx = S / 2
    x.arc(cx, cx, BR, 0, 2 * math.pi); x.set_source_rgb(r * .78, g * .78, b * .78); x.fill()
    x.arc(cx, cx, BR - 2.2, 0, 2 * math.pi); x.set_source_rgb(r, g, b); x.fill()
    if glow > 0: x.arc(cx, cx, BR - 2.2, 0, 2 * math.pi); x.set_source_rgba(1, 1, 1, .45 * glow); x.fill()
    SPR[key] = s; return s

def hazard(ctx, x, y, w, h, a=1.0):
    ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip()
    ctx.set_source_rgba(.95, .75, .15, a); ctx.paint(); ctx.set_source_rgba(.13, .13, .15, a)
    for k in range(-8, int(w / 30) + 8):
        x0 = x + k * 36
        ctx.move_to(x0, y + h); ctx.line_to(x0 + 18, y + h); ctx.line_to(x0 + 18 + h, y); ctx.line_to(x0 + h, y); ctx.close_path(); ctx.fill()
    ctx.restore()

def text(ctx, s, x, y, size, rgba, weight=cairo.FONT_WEIGHT_NORMAL, track=0):
    ctx.select_font_face("Fira Sans", cairo.FONT_SLANT_NORMAL, weight); ctx.set_font_size(size)
    ws = [ctx.text_extents(ch).x_advance for ch in s]; tot = sum(ws) + track * (len(s) - 1); xx = x - tot / 2
    for ch, w in zip(s, ws): ctx.move_to(xx, y); ctx.set_source_rgba(*rgba); ctx.show_text(ch); xx += w + track

def draw_tank(ctx, a=1.0):
    ctx.rectangle(BX0, FLOOR, BX1 - BX0, 200); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
    ctx.move_to(BX0 - 4, FLOOR + 200); ctx.line_to(BX0 - 4, BY0 - 4); ctx.line_to(BX1 + 4, BY0 - 4); ctx.line_to(BX1 + 4, FLOOR + 200)
    ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(6); ctx.stroke()
    ctx.move_to(BX0, FLOOR); ctx.line_to(BX1, FLOOR); ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(4); ctx.stroke()

def render(mech, npz, out, part, npart, snap=None):
    D = np.load(npz)
    P, COLS, BORN, CR, COUNT, ST = D["P"], D["COLS"], D["BORN"], D["CR"], D["COUNT"], D["ST"]
    NF = len(P)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(surf)
    def draw(f):
        t = f / FPS; zt = t - T_ZERO
        ctx.set_source_rgb(.075, .08, .09); ctx.paint()
        sh = 18 * math.exp(-zt * 5) * math.sin(zt * 80) if 0 <= zt < 1 else 0
        zoom = 1 + .4 * (1 - math.exp(-zt * 2)) if zt > 0 else 1
        ctx.save(); ctx.translate(540 + sh, 1150); ctx.scale(zoom, zoom); ctx.translate(-540, -1150)
        al = 1.0 if zt <= 0 else max(0, 1 - zt / .6)
        if mech.tank_walls: draw_tank(ctx, al)
        mech.draw(ctx, t, ST[f], al, under=True) if "under" in mech.draw.__code__.co_varnames else None
        pf = P[f]; alive = np.where(~np.isnan(pf[:, 0]))[0]
        for i in alive:
            x, y = pf[i]; age = f - BORN[i]
            glow = max(0.0, 1 - age / 8) if BORN[i] > 0 and age >= 0 else 0.0
            s = sprite(COLS[i], glow); o = s.get_width() / 2
            ctx.set_source_surface(s, x - o, y - o); ctx.paint()
        if "under" in mech.draw.__code__.co_varnames: mech.draw(ctx, t, ST[f], al, under=False)
        else: mech.draw(ctx, t, ST[f], al)
        if len(CR):
            for row in CR[(CR[:, 0] > t - .35) & (CR[:, 0] <= t)]:
                te, ex, ey = row[0], row[1], row[2]; c_ = row[3:6]; d = t - te
                if d < .12:
                    u = d / .12; sx, sy = mech.squash(ex, ey) if hasattr(mech, "squash") else (1, 0)
                    ctx.save(); ctx.translate(ex, ey)
                    ctx.scale(1 + (1.6 * u) * abs(sx), 1 + (1.6 * u) * abs(sy)); ctx.scale(1 - .7 * u * abs(sy), 1 - .7 * u * abs(sx))
                    ctx.arc(0, 0, BR, 0, 2 * math.pi); ctx.set_source_rgb(*c_); ctx.fill(); ctx.restore()
                else:
                    d2 = d - .12
                    ctx.arc(ex, ey, 14 + d2 * 220, 0, 2 * math.pi); ctx.set_source_rgba(*c_, .7 * (1 - d2 / .23)); ctx.set_line_width(3); ctx.stroke()
                    rr_ = np.random.default_rng(int(te * 1e4 + ex))
                    for _ in range(5):
                        a_ = rr_.uniform(0, 2 * math.pi); sp = rr_.uniform(200, 450)
                        ctx.arc(ex + math.cos(a_) * sp * d2, ey + math.sin(a_) * sp * d2, 3, 0, 2 * math.pi)
                        ctx.set_source_rgba(*c_, max(0, 1 - d2 / .23)); ctx.fill()
        ctx.restore()
        if 0 <= zt < .3: ctx.set_source_rgba(1, 1, 1, .5 * (1 - zt / .3)); ctx.paint()
        if zt <= 0:
            rem = T_ZERO - t; sec = max(0, math.ceil(rem - 1e-6)); last = sec <= 5
            frac = rem % 1; pulse = 1 + (.08 if last else .02) * math.exp(-(1 - frac) * 10)
            col = (1, .32, .32, 1) if last else (1, 1, 1, .92)
            ctx.save(); ctx.translate(540, 250); ctx.scale(pulse, pulse); text(ctx, f"0:{sec:02d}", 0, 0, 120, col, cairo.FONT_WEIGHT_NORMAL, 4); ctx.restore()
            bw = 360; ctx.set_source_rgba(1, 1, 1, .12); ctx.rectangle(540 - bw / 2, 292, bw, 3); ctx.fill()
            ctx.set_source_rgba(*col[:3], .9); ctx.rectangle(540 - bw / 2, 292, bw * rem / T_ZERO, 3); ctx.fill()
            text(ctx, f"{int(COUNT[f])}", 540, 410, 64, (1, 1, 1, .9), cairo.FONT_WEIGHT_BOLD, 2)
            text(ctx, "КУЛЬОК", 540, 452, 24, (1, 1, 1, .4), cairo.FONT_WEIGHT_NORMAL, 8)
        else:
            text(ctx, "0:00", 540, 250, 120, (1, .32, .32, max(0, 1 - zt / .8)), cairo.FONT_WEIGHT_NORMAL, 4)
        if t > T_END - .4: ctx.set_source_rgba(0, 0, 0, (t - (T_END - .4)) / .4); ctx.paint()
    if snap is not None:
        for s_ in snap: draw(int(s_ * FPS)); surf.write_to_png(f"{out}_{s_}.png")
        return
    a = NF * part // npart; b = NF * (part + 1) // npart
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", "yuv420p", f"{out}_p{part}_tmp.mp4"], stdin=subprocess.PIPE)
    for f in range(a, b): draw(f); surf.flush(); p.stdin.write(bytes(surf.get_data()))
    p.stdin.close(); assert p.wait() == 0
    os.replace(f"{out}_p{part}_tmp.mp4", f"{out}_p{part}.mp4")

def audio(mech, npz, path):
    D = np.load(npz); CR = D["CR"]
    sr = 44100; n = int(T_END * sr); y = np.zeros(n)
    def add(at, s):
        i = int(at * sr); e = min(len(s), n - i)
        if e > 0 and i >= 0: y[i:i + e] += s[:e]
    def tt(d): return np.arange(int(d * sr)) / sr
    rr = np.random.default_rng(6)
    for (te, kind) in mech.sounds():
        if te >= T_ZERO: continue
        if kind == "hit":
            k = tt(.35); add(te, .35 * np.sin(2 * np.pi * np.cumsum(60 * (1 + 2.5 * np.exp(-k * 30))) / sr) * np.exp(-k * 12))
            nz = rr.normal(0, 1, len(k)); add(te, .1 * (nz - np.convolve(nz, np.ones(3) / 3, "same")) * np.exp(-k * 40))
        elif kind == "snip":
            k = tt(.12); add(te, .25 * np.sin(2 * np.pi * 2600 * k) * np.exp(-k * 50) + .15 * rr.normal(0, 1, len(k)) * np.exp(-k * 70))
        elif kind == "whoosh":
            k = tt(.3); add(te, .12 * np.convolve(rr.normal(0, 1, len(k)), np.ones(8) / 8, "same") * np.sin(np.pi * k / .3))
        elif kind == "on":
            k = tt(.6); add(te, .5 * np.sin(2 * np.pi * np.cumsum(60 * (1 + 2 * np.exp(-k * 20))) / sr) * np.exp(-k * 7))
    if hasattr(mech, "hum"):
        mech.hum(add, tt, rr, sr)
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

def main(make, name):
    cmd = sys.argv[1]
    npz = f"{WORK}/{name}.npz"; out = f"{WORK}/{name}"
    if cmd == "search": search(make, [int(s) for s in sys.argv[2:]])
    elif cmd == "rec":
        import base as _b
        r = _b.run(make(), int(sys.argv[2])); np.savez(npz, **r); print("final", int(r["COUNT"][int(29.9 * FPS)]))
    elif cmd == "snap": render(make(), npz, out, 0, 1, snap=[float(s) for s in sys.argv[2:]])
    elif cmd == "render": render(make(), npz, out, int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "audio": audio(make(), npz, out + ".wav")
    elif cmd == "all":
        procs = [subprocess.Popen([sys.executable, "-B", sys.argv[0], "render", str(p), "2"]) for p in range(2)]
        for p in procs: assert p.wait() == 0
        audio(make(), npz, out + ".wav")
        with open(out + "_l.txt", "w") as fh: fh.write(f"file '{out}_p0.mp4'\nfile '{out}_p1.mp4'\n")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", out + "_l.txt", "-i", out + ".wav",
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{WORK}/{name}.mp4"], check=True)
        print("ok")
