import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
import pymunk, math, random, sys, os
import numpy as np

W, H, FPS = 1080, 1920, 30
BX0, BX1, BY0, BY1 = 150, 930, 900, 1640       # glass box (inner)
ANVIL_Y = 1600                                  # anvil top surface
PX0, PX1 = 390, 690                             # press / anvil span
SLOPE_Y = 1330                                  # where the V floor meets the side walls
BR = 15.0
T_ZERO, T_END = 30.0, 33.0
SUB = 10
MAXN = int(os.environ.get("MAXN", "820"))
HEAD_H = 70
UP_GAP = 120                                    # gap between head and anvil when raised

def slam_times(first, i0, i1, end):
    ts = []; t = first
    while t < end:
        ts.append(t); u = min(1, t / end); t += i0 + (i1 - i0) * u ** 0.8
    return ts

PAL = [(0.0, (1.0, 0.5, 0.08)), (8.0, (0.1, 0.8, 1.0)), (14.0, (0.62, 0.3, 1.0)),
       (19.0, (1.0, 0.82, 0.1)), (23.5, (0.2, 0.88, 0.42)), (27.0, (1.0, 0.28, 0.55))]
PAL = [(t, __import__("hue").rot(c)) for t, c in PAL]
def colour(t):
    c = PAL[0][1]
    for s, cc in PAL:
        if t >= s: c = cc
    return c

def head_bottom(t, slams):
    """press head bottom y: fast drop (0.09 s), short dwell, slower lift (0.35 s)"""
    y_up = ANVIL_Y - UP_GAP; y_dn = ANVIL_Y - 4
    for s in slams:
        d = t - s
        if -0.09 <= d < 0: u = (d + 0.09) / 0.09; return y_up + (y_dn - y_up) * u * u
        if 0 <= d < 0.06: return y_dn
        if 0.06 <= d < 0.41: u = (d - 0.06) / 0.35; return y_dn + (y_up - y_dn) * (u * u * (3 - 2 * u))
    return y_up

def run(first, i0, i1, seed, record=True):
    rnd = random.Random(seed)
    slams = slam_times(first, i0, i1, T_ZERO - 0.05)
    space = pymunk.Space(); space.gravity = (0, 1800); space.iterations = 30
    statics = []
    def seg(a, b, r=22, e=0.7):
        s = pymunk.Segment(space.static_body, a, b, r); s.elasticity = e; s.friction = 0.05; space.add(s); statics.append(s); return s
    seg((BX0 - 14, BY0 - 300), (BX0 - 14, SLOPE_Y)); seg((BX1 + 14, BY0 - 300), (BX1 + 14, SLOPE_Y))
    seg((BX0 - 14, BY0 - 14), (BX1 + 14, BY0 - 14))
    seg((BX0 - 14, SLOPE_Y - 14), (PX0, ANVIL_Y + 14)); seg((BX1 + 14, SLOPE_Y - 14), (PX1, ANVIL_Y + 14))
    anvil = seg((PX0, ANVIL_Y + 22), (PX1, ANVIL_Y + 22), 22, 0.4)
    head = pymunk.Body(body_type=pymunk.Body.KINEMATIC); head.position = ((PX0 + PX1) / 2, ANVIL_Y - UP_GAP - HEAD_H / 2)
    hw = (PX1 - PX0) / 2
    hs = pymunk.Poly(head, [(-hw, HEAD_H / 2), (hw, HEAD_H / 2), (hw, -HEAD_H / 2), (0, -HEAD_H / 2 - 110), (-hw, -HEAD_H / 2)], radius=3)
    hs.elasticity = 0.5; hs.friction = 0.02; space.add(head, hs)
    rod = pymunk.Segment(head, (0, -HEAD_H / 2 - 110), (0, -1400), 22); rod.elasticity = 0.8; space.add(rod)
    balls = {}; nid = [0]; spawnq = []
    def add_ball(pos, vel, col, f):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BR)); b.position = pos; b.velocity = vel
        c = pymunk.Circle(b, BR); c.elasticity = 0.78; c.friction = 0.1
        space.add(b, c); balls[c] = [b, col, f, nid[0]]; nid[0] += 1
    add_ball((PX0 - 60, BY0 + 80), (120, 0), colour(0), 0)
    nfr = int(T_END * FPS); MAXID = 5000
    P = np.full((nfr, MAXID, 2), np.nan, np.float32) if record else None
    COLS = np.zeros((MAXID, 3), np.float32); BORN = np.full(MAXID, -1, np.int32)
    HEADY = np.zeros(nfr, np.float32); CR = []          # crush events (t, x, y)
    SLAMHIT = []                                        # (t, n_crushed)
    exploded = False
    done_slam = set()
    for f in range(nfr):
        for s_ in range(SUB):
            t = (f + s_ / SUB) / FPS; dt = 1 / FPS / SUB
            if t >= T_ZERO and not exploded:
                exploded = True
                for s in statics: space.remove(s)
                space.gravity = (0, 0); space.damping = 0.3
                hs.sensor = True; rod.sensor = True
                for c, bl in balls.items():
                    b = bl[0]; d = b.position - (540, 1100); L = max(1, d.length)
                    b.velocity = d / L * rnd.uniform(600, 1500) + pymunk.Vec2d(rnd.uniform(-150, 150), rnd.uniform(-300, 100))
            yb = head_bottom(t, slams) if not exploded else ANVIL_Y - UP_GAP
            target = yb - HEAD_H / 2
            head.velocity = (0, (target - head.position.y) / dt)
            space.step(dt)
            head.position = ((PX0 + PX1) / 2, target)
            # crush: balls trapped between the head and the anvil when the gap is smaller than a ball
            gap = ANVIL_Y - yb
            if not exploded and gap < 2 * BR - 2:
                crushed = [c for c, bl in balls.items() if PX0 - 4 < bl[0].position.x < PX1 + 4 and bl[0].position.y > yb - BR]
                n0 = 0
                for c in crushed:
                    if len(balls) + 2 * len(spawnq) >= MAXN: break
                    b, col, bf, i_ = balls.pop(c); pos = b.position; space.remove(b, c)
                    CR.append((t, pos.x, pos.y, col[0], col[1], col[2]))
                    spawnq.append((t + 0.14, pos.x, colour(t)))
                    n0 += 1
                if n0: SLAMHIT.append((t, n0))
            for item in [q for q in spawnq if q[0] <= t]:
                spawnq.remove(item); _, x0, col = item
                for sgn in (-1, 1):
                    x = (PX0 - BR - 8) if sgn < 0 else (PX1 + BR + 8)
                    add_ball((x + rnd.uniform(-3, 3), ANVIL_Y - BR - 6 - rnd.uniform(0, 20)),
                             (sgn * rnd.uniform(380, 820), -rnd.uniform(900, 1350)), col, f)
            if not exploded:
                for c, bl in balls.items():
                    v = bl[0].velocity
                    if v.length > 1500: bl[0].velocity = v * (1500 / v.length)
                    p = bl[0].position
                    if not (BX0 - 5 < p.x < BX1 + 5 and BY0 - 5 < p.y < ANVIL_Y + 30):
                        bl[0].position = (540 + rnd.uniform(-200, 200), BY0 + 200); bl[0].velocity = (0, 0)
        if record:
            for c, (b, col, bf, i_) in balls.items():
                P[f, i_] = b.position; COLS[i_] = col; BORN[i_] = bf
            HEADY[f] = head_bottom(f / FPS, slams) if f / FPS < T_ZERO else ANVIL_Y - UP_GAP
    return dict(P=P, COLS=COLS, BORN=BORN, HEADY=HEADY, CR=np.array(CR), SLAMS=np.array(slams), HIT=np.array(SLAMHIT), n=len(balls))

if __name__ == "__main__":
    if sys.argv[1] == "search":
        for cfg in sys.argv[2:]:
            first, i0, i1 = map(float, cfg.split(","))
            for seed in (1, 2):
                r = run(first, i0, i1, seed, record=False)
                cr = r["HIT"]
                def n_at(s): return 1 + int(cr[cr[:, 0] <= s][:, 1].sum()) if len(cr) else 1
                print(cfg, seed, "final", r["n"], [n_at(s) for s in (3, 6, 10, 15, 20, 25, 28)], flush=True)
    else:
        first, i0, i1 = map(float, sys.argv[2].split(",")); seed = int(sys.argv[3])
        r = run(first, i0, i1, seed)
        np.savez(f"{WORK}/press2.npz", **{k: v for k, v in r.items() if k != "n"})
        print("final", r["n"])
