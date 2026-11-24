import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Bumper race: the tank is split in two by a wall. Each half is its own team colour with a spinning rotor at the bottom
that flings shapes up, and ONE round pinball bumper in the middle. Rule: a shape that TOUCHES the bumper splits in two.
Left side is quicker early, right side's bumper recharges faster later -> the lead flips. Viewer picks a side."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *

MID = 540.0
BPY = float(os.environ.get("BPY", "1280"))                    # bumper height
BRAD = float(os.environ.get("BRAD", "64"))                     # bumper radius
BUMP = [((BX0 + MID) / 2, BPY), ((MID + BX1) / 2, BPY)]
ROT = [((BX0 + MID) / 2, FLOOR - 165), ((MID + BX1) / 2, FLOOR - 165)]
RL = float(os.environ.get("RL", "150"))                        # rotor half length
TRR = RL + 22
def trough(cx, cy, xl, xr):
    pts = [(xl, cy - 130)] + [(cx + TRR * math.cos(math.radians(a)), cy + TRR * math.sin(math.radians(a))) for a in range(190, -11, -10)] + [(xr, cy - 130)]
    return pts
WR = float(os.environ.get("WROT", "3.2"))
# recharge (s between splits) per side: start -> end, with curve exponent
def _f(k, d): return [float(v) for v in os.environ.get(k, d).split(",")]
CHL = _f("CHL", "3.4,0.03,0.6")                              # left: fast early, slower finish
CHR = _f("CHR", "5.0,0.006,1.25")                              # right: slow start, fast finish
CAP = int(os.environ.get("CAP", "380"))                        # per-side max
base.MAXN = 2 * CAP + 10
COL = [(1.0, .52, .10), (.12, .78, 1.0)]

def recharge(t, c):
    u = min(1, t / T_ZERO); return c[0] * (c[1] / c[0]) ** (u ** c[2])

_k = [0]
def _alt(t):                                                    # initial balls: first left, then right
    c = COL[_k[0] % 2]; _k[0] += 1; return c

class Bumpers(Mech):
    name = "bumpers"
    def __init__(self):
        self.tr = [trough(p[0], p[1], xl, xr) for p, (xl, xr) in zip(ROT, ((BX0, MID), (MID, BX1)))]
    def build(self, space):
        d = pymunk.Segment(space.static_body, (MID, BY0 - 20), (MID, FLOOR + 20), 9); d.friction = .4; d.elasticity = .6
        space.add(d); self.div = d
        self.bumps = []
        for p in BUMP:
            c = pymunk.Circle(space.static_body, BRAD, p); c.elasticity = .8; c.friction = .2; space.add(c); self.bumps.append(c)
        for pts in self.tr:
            for a_, b_ in zip(pts, pts[1:]):
                g = pymunk.Segment(space.static_body, a_, b_, 8); g.friction = .3; g.elasticity = .3; space.add(g)
        self.rot = []
        for k, p in enumerate(ROT):
            b = pymunk.Body(body_type=pymunk.Body.KINEMATIC); b.position = p
            s = pymunk.Segment(b, (-RL, 0), (RL, 0), 10); s.friction = .9; s.elasticity = .3
            space.add(b, s); self.rot.append((b, s))
        self.charge = [0.0, 0.0]; self.flash = [-9.0, -9.0]; self.side = 0
        self.n = [1, 1]; self.pend = []
        base.colour = _alt
    def step(self, t, dt):
        u = min(1, t / 6)
        self.rot[0][0].angular_velocity = WR * (.35 + .65 * u)
        self.rot[1][0].angular_velocity = -WR * (.35 + .65 * u)
        self.charge[0] += dt; self.charge[1] += dt
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos): return m
        self.pend = [p for p in self.pend if p[0] > t]
        left = pos[:, 0] < MID
        self.n = [int(left.sum()) + sum(2 for p in self.pend if p[1] == 0), int((~left).sum()) + sum(2 for p in self.pend if p[1] == 1)]
        s = self.side; self.side ^= 1
        if self.charge[s] < recharge(t, CHL if s == 0 else CHR) or self.n[s] + 1 > CAP: return m
        bx, by = BUMP[s]
        touch = np.hypot(pos[:, 0] - bx, pos[:, 1] - by) < BRAD + BR + 3
        touch &= (left if s == 0 else ~left)
        if touch.any():
            i = np.where(touch)[0][0]; m[i] = True
            self.charge[s] = 0.0; self.flash[s] = t; self.pend.append((t + .12, s))
            base.colour = (lambda c: (lambda tt: c))(COL[s])
        return m
    def spawn_xy(self, x0, y0, sgn):
        s = 0 if x0 < MID else 1; bx, by = BUMP[s]
        d = math.atan2(y0 - by, x0 - bx) + sgn * .45; r = BRAD + BR + 4
        return bx + r * math.cos(d), by + r * math.sin(d)
    def fix_xy(self, x, y):
        if x < MID: x = min(MID - BR - 12, max(BX0 + BR + 2, x))
        else: x = min(BX1 - BR - 2, max(MID + BR + 12, x))
        return x, max(BY0 + BR + 2, y)
    def spawn_dir(self, x, y):
        s = 0 if x < MID else 1; bx, by = BUMP[s]; d = math.atan2(y - by, x - bx)
        return (math.cos(d), min(-.3, math.sin(d)))
    def squash(self, x, y): return (1, 1)
    def state(self, t):
        return np.array([self.rot[0][0].angle, self.flash[0], self.flash[1], self.n[0], self.n[1], 0], np.float32)
    def explode(self, space):
        self.div.sensor = True
        for c in self.bumps: c.sensor = True
        for b, s in self.rot: s.sensor = True
    def sounds(self): return [(0.3, "on")]
    def draw(self, ctx, t, st, a=1.0, under=True):
        ang = float(st[0]); fl = [float(st[1]), float(st[2])]; n = [int(st[3]), int(st[4])]
        if under:
            for k in range(2):
                ctx.set_source_rgba(*COL[k], .07 * a)
                ctx.rectangle(BX0 if k == 0 else MID, BY0, MID - BX0, FLOOR - BY0); ctx.fill()
            for pts in self.tr:
                ctx.move_to(*pts[0])
                for q in pts[1:]: ctx.line_to(*q)
                ctx.line_to(pts[-1][0], FLOOR); ctx.line_to(pts[0][0], FLOOR); ctx.close_path(); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
            return
        ctx.set_source_rgba(.5, .52, .56, a); ctx.rectangle(MID - 6, BY0 - 4, 12, FLOOR - BY0 + 4); ctx.fill()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k, (p, sg) in enumerate(zip(ROT, (1, -1))):
            q = ang * sg
            ctx.move_to(p[0] - RL * math.cos(q), p[1] - RL * math.sin(q)); ctx.line_to(p[0] + RL * math.cos(q), p[1] + RL * math.sin(q))
            ctx.set_source_rgba(.62, .64, .68, a); ctx.set_line_width(20); ctx.stroke()
            ctx.arc(*p, 16, 0, 2 * math.pi); ctx.set_source_rgba(.32, .34, .38, a); ctx.fill()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        for k, p in enumerate(BUMP):
            g = max(0.0, 1 - (t - fl[k]) / .2); c = COL[k]
            ctx.arc(*p, BRAD + 10 * g, 0, 2 * math.pi); ctx.set_source_rgba(*c, (.25 + .35 * g) * a); ctx.fill()
            ctx.arc(*p, BRAD, 0, 2 * math.pi); ctx.set_source_rgba(.95, .95, .97, a); ctx.fill()
            ctx.arc(*p, BRAD - 9, 0, 2 * math.pi); ctx.set_source_rgba(*c, a); ctx.fill()
            text(ctx, "×2", p[0], p[1] + 12, 34, (1, 1, 1, a), cairo.FONT_WEIGHT_BOLD)
        if t < T_ZERO:
            lead = 0 if n[0] > n[1] else (1 if n[1] > n[0] else -1)
            for k in range(2):
                cx = (BX0 + MID) / 2 if k == 0 else (MID + BX1) / 2
                ctx.new_path(); ctx.set_source_rgba(*ST_.BG, .85 * a); ctx.rectangle(cx - 105, BY0 + 18, 210, 112); ctx.fill()
                text(ctx, str(n[k]), cx, BY0 + 78, 64, (*COL[k], a), cairo.FONT_WEIGHT_BOLD, 2)
                if lead == k and t > 3: text(ctx, "LEADS" if t < T_ZERO - 1.5 else "WINS", cx, BY0 + 118, 26, (*COL[k], .85 * a), cairo.FONT_WEIGHT_BOLD, 6)
            if t < 4:
                text(ctx, "PICK A SIDE", 540, 520, 40, ST_.ink(min(1, (4 - t)) * .95), cairo.FONT_WEIGHT_BOLD, 6)
        ctx.new_path()

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=[((325, 800), (40, 0)), ((755, 800), (-40, 0))])
    main(Bumpers, "bumpers")
