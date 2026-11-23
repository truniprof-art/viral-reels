import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
import pymunk, math, random, sys, os
import numpy as np

W, H, FPS = 1080, 1920, 30
BX0, BX1, BY0 = 110, 970, 560           # tank inner walls / lid
RR = 38                                 # roller radius
GAP = 12                                # gap between the two rollers of a pair (< ball diameter)
ROLL_Y = 1600                           # roller centre height
NPAIR = 5
BR = 15.0
T_ZERO, T_END = 30.0, 33.0
SUB = 8
MAXN = int(os.environ.get("MAXN", "1050"))
PAIR_W = (BX1 - BX0) / NPAIR
ZX, ZY = float(os.environ.get('ZX', '13')), float(os.environ.get('ZY', '0'))
PINCH_Y = ROLL_Y - math.sqrt((RR + BR) ** 2 - (RR + GAP / 2) ** 2) - 9
PAIRS = [BX0 + PAIR_W * (k + 0.5) for k in range(NPAIR)]      # pair centre x
OPEN = [float(x) for x in os.environ.get("OPEN", "11,11,0,6,6").split(",")]  # time each pair opens
def roller_speed(t):
    # rad/s, spins up over time (one direction per roller, never reverses)
    s0, s1 = float(os.environ.get("S0", "0.6")), float(os.environ.get("S1", "9"))
    return s0 + (s1 - s0) * min(1, t / T_ZERO) ** 2.2

SPL, SPH = float(os.environ.get("SPL", "600")), float(os.environ.get("SPH", "1000"))
PAL = [(0.0, (1.0, 0.5, 0.08)), (9.0, (0.1, 0.8, 1.0)), (15.0, (0.62, 0.3, 1.0)),
       (20.0, (1.0, 0.82, 0.1)), (24.0, (0.2, 0.88, 0.42)), (27.0, (1.0, 0.28, 0.55))]
PAL = [(t, __import__("hue").rot(c)) for t, c in PAL]
def colour(t):
    c = PAL[0][1]
    for s, cc in PAL:
        if t >= s: c = cc
    return c

def run(seed, record=True):
    rnd = random.Random(seed)
    space = pymunk.Space(); space.gravity = (0, 1500); space.iterations = 25
    statics = []
    def seg(a, b, r=20, e=0.75, fr=0.3):
        s = pymunk.Segment(space.static_body, a, b, r); s.elasticity = e; s.friction = fr; space.add(s); statics.append(s); return s
    seg((BX0 - 20, BY0 - 20), (BX0 - 20, ROLL_Y + 200)); seg((BX1 + 20, BY0 - 20), (BX1 + 20, ROLL_Y + 200))
    seg((BX0 - 20, BY0 - 20), (BX1 + 20, BY0 - 20))
    rollers = []
    for k, cx in enumerate(PAIRS):
        for side in (-1, 1):
            b = pymunk.Body(body_type=pymunk.Body.KINEMATIC); b.position = (cx + side * (RR + GAP / 2), ROLL_Y)
            c = pymunk.Circle(b, RR); c.friction = 1.2; c.elasticity = 0.3; space.add(b, c)
            rollers.append((k, side, b))
        # catch plate under each pair so a ball can never fall out
        seg((cx - RR, ROLL_Y + RR + 30), (cx + RR, ROLL_Y + RR + 30), 10)
    # dividers between pairs (small peaks so balls roll toward a gap)
    for k in range(NPAIR + 1):
        x = BX0 + k * PAIR_W
        seg((x, ROLL_Y - RR - 8), (x, ROLL_Y + RR), 9, 0.6, 0.1)
    covers = {}
    for k, cx in enumerate(PAIRS):
        if OPEN[k] > 0:
            covers[k] = seg((cx - PAIR_W / 2 + 6, ROLL_Y - RR - 14), (cx + PAIR_W / 2 - 6, ROLL_Y - RR - 14), 8, 0.7, 0.2)
    balls = {}; nid = [0]; spawnq = []
    def add_ball(pos, vel, col, f):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BR)); b.position = pos; b.velocity = vel
        c = pymunk.Circle(b, BR); c.elasticity = 0.8; c.friction = 0.4
        space.add(b, c); balls[c] = [b, col, f, nid[0]]; nid[0] += 1
    add_ball((PAIRS[2] - 140, BY0 + 120), (160, 0), colour(0), 0)
    nfr = int(T_END * FPS); MAXID = 6000
    P = np.full((nfr, MAXID, 2), np.nan, np.float32) if record else None
    COLS = np.zeros((MAXID, 3), np.float32); BORN = np.full(MAXID, -1, np.int32)
    RANG = np.zeros(nfr, np.float32); CR = []; COUNT = np.zeros(nfr, np.int32); OPENED = []
    exploded = False; ang = 0.0
    for f in range(nfr):
        for s_ in range(SUB):
            t = (f + s_ / SUB) / FPS; dt = 1 / FPS / SUB
            for k in list(covers):
                if t >= OPEN[k]: space.remove(covers.pop(k)); OPENED.append((t, k))
            if t >= T_ZERO and not exploded:
                exploded = True
                for s in statics:
                    if s in space.shapes: space.remove(s)
                for (_, _, b) in rollers:
                    for sh in b.shapes: sh.sensor = True
                space.gravity = (0, 0); space.damping = 0.3
                for c, bl in balls.items():
                    b = bl[0]; d = b.position - (540, 1150); L = max(1, d.length)
                    b.velocity = d / L * rnd.uniform(700, 1600) + pymunk.Vec2d(rnd.uniform(-150, 150), rnd.uniform(-150, 150))
            w = roller_speed(t) if not exploded else 0.0
            ang += w * dt
            for (k, side, b) in rollers:
                b.angular_velocity = (w if side < 0 else -w) if t >= OPEN[k] else 0.0
            space.step(dt)
            if not exploded:
                # crush: a ball that is in contact with BOTH rollers of an open pair is squeezed in the gap
                for k, cx in enumerate(PAIRS):
                    if t < OPEN[k]: continue
                    lc = (cx - RR - GAP / 2, ROLL_Y); rc = (cx + RR + GAP / 2, ROLL_Y)
                    for c in [c for c, bl in balls.items() if abs(bl[0].position.x - cx) < 40 and bl[0].position.y > ROLL_Y - RR - BR - 40]:
                        p = balls[c][0].position
                        if abs(p.x - cx) < ZX and p.y > PINCH_Y - ZY:
                            if len(balls) + 2 * len(spawnq) >= MAXN: continue
                            b, col, bf, i_ = balls.pop(c); space.remove(b, c)
                            CR.append((t, p.x, p.y, *col))
                            spawnq.append((t + 0.12, cx, colour(t)))
                for item in [q for q in spawnq if q[0] <= t]:
                    spawnq.remove(item); _, cx, col = item
                    col_y = [bl[0].position.y for bl in balls.values() if abs(bl[0].position.x - cx) < 70]
                    ytop = min([ROLL_Y - RR - BR - 6] + [y - 2.2 * BR for y in col_y])
                    ytop = max(ytop, BY0 + BR + 4)
                    for sgn in (-1, 1):
                        add_ball((cx + sgn * 20, ytop - (0 if sgn < 0 else 2 * BR + 2)), (sgn * rnd.uniform(200, 500), -rnd.uniform(SPL, SPH)), col, f)
                for c, bl in balls.items():
                    v = bl[0].velocity
                    if v.length > 1700: bl[0].velocity = v * (1700 / v.length)
                    p = bl[0].position
                    if not (BX0 - 5 < p.x < BX1 + 5 and BY0 - 5 < p.y < ROLL_Y + RR + 40):
                        bl[0].position = (540 + rnd.uniform(-250, 250), BY0 + 60); bl[0].velocity = (0, 0)
        COUNT[f] = len(balls) + 2 * len(spawnq)
        if record:
            for c, (b, col, bf, i_) in balls.items():
                P[f, i_] = b.position; COLS[i_] = col; BORN[i_] = bf
            RANG[f] = ang
    return dict(P=P, COLS=COLS, BORN=BORN, RANG=RANG, CR=np.array(CR), COUNT=COUNT, OPENED=np.array(OPENED))

if __name__ == "__main__":
    if sys.argv[1] == "search":
        for seed in map(int, sys.argv[2:]):
            r = run(seed, record=False); C = r["COUNT"]
            print(seed, [int(C[int(s * FPS)]) for s in (5, 10, 15, 20, 24, 27, 29.9)], flush=True)
    else:
        r = run(int(sys.argv[2])); np.savez(f"{WORK}/roll.npz", **r)
        print("final", int(r["COUNT"][int(29.9 * FPS)]))
