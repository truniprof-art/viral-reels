import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Twin paddle wheels (variation of wheel): TWO smaller wheels side by side in a W-shaped double trough, turning in
mirror directions (each one never reverses). Each wheel scoops shapes up its OUTER rising side through its own red x2
laser; the shapes are thrown back to the middle ridge and fall into one of the two wheels again."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *

HY = float(os.environ.get("HY", "1330"))
R = float(os.environ.get("WR", "190"))
NP = int(os.environ.get("NP", "5"))
HUBS = [(325.0, HY), (755.0, HY)]
SG = [1, -1]                                              # left wheel: left side rises; right wheel: right side rises
LY = float(os.environ.get("LY", str(HY - 105)))
LZ = [(BX0 + 4, HUBS[0][0] - 30), (HUBS[1][0] + 30, BX1 - 4)]
W0, W1, WE = float(os.environ.get("W0", "0.5")), float(os.environ.get("W1", "3.6")), float(os.environ.get("WE", "1.2"))
CH0, CH1 = float(os.environ.get("CH0", "3.0")), float(os.environ.get("CH1", "0.02"))
ACT2 = float(os.environ.get("ACT2", "9"))                 # right laser switches on later (slow start)
base.MAXN = int(os.environ.get("MAXN", "700"))
TR = R + 20

def omega(t):
    u = min(1, t / T_ZERO); return W0 * (W1 / W0) ** (u ** WE)
def recharge(t):
    u = min(1, t / T_ZERO); return CH0 * (CH1 / CH0) ** (u ** 0.7)

def arc_pts(h, n=30):
    return [(h[0] + TR * math.cos(math.radians(-8 + 196 * k / n)), h[1] + TR * math.sin(math.radians(-8 + 196 * k / n))) for k in range(n + 1)]

class WheelTwin(Mech):
    name = "wheel_twin"
    def __init__(self):
        A = arc_pts(HUBS[0]); B = arc_pts(HUBS[1])
        peak = (540, min(A[0][1], B[-1][1]) - 40)
        # outline left->right along the floor of the W
        self.OUT = [(BX0, B[-1][1] - 80)] + A[::-1] + [peak] + B[::-1] + [(BX1, A[0][1] - 80)]
    def build(self, space):
        self.bodies, self.pads = [], []
        for h in HUBS:
            b = pymunk.Body(body_type=pymunk.Body.KINEMATIC); b.position = h
            for k in range(NP):
                a = 2 * math.pi * k / NP
                s = pymunk.Segment(b, (44 * math.cos(a), 44 * math.sin(a)), (R * math.cos(a), R * math.sin(a)), 8)
                s.friction = 0.9; s.elasticity = 0.1; self.pads.append(s)
            hub = pymunk.Circle(b, 42); hub.friction = 0.6
            space.add(b, hub, *self.pads[-NP:]); self.bodies.append(b)
        self.tsegs = []
        for p, q in zip(self.OUT[:-1], self.OUT[1:]):
            s = pymunk.Segment(space.static_body, p, q, 10); s.friction = 0.3; s.elasticity = 0.3; space.add(s); self.tsegs.append(s)
        self.charge = [9.0, 9.0]; self.flash = [-9.0, -9.0]
    def step(self, t, dt):
        for b, s in zip(self.bodies, SG): b.angular_velocity = s * omega(t)
        self.charge = [c + dt for c in self.charge]
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos): return m
        for k in range(2):
            if k == 1 and t < ACT2: continue
            if self.charge[k] < recharge(t): continue
            x0, x1 = LZ[k]
            zone = (np.abs(pos[:, 1] - LY) < 5) & (pos[:, 0] > x0) & (pos[:, 0] < x1)
            if zone.any():
                idx = np.where(zone)[0]; m[idx[:1 + int(len(idx) * min(1, t / T_ZERO))]] = True
                self.charge[k] = 0.0; self.flash[k] = t
        return m
    def spawn_xy(self, x0, y0, sgn):
        return min(BX1 - BR - 2, max(BX0 + BR + 2, x0 + sgn * BR * 1.1)), y0 - BR - 6
    def spawn_dir(self, x, y): return (0.4 if x < 540 else -0.4, -0.5)
    def squash(self, x, y): return (0, 1)
    def state(self, t):
        return np.array([self.bodies[0].angle, self.bodies[1].angle, self.flash[0], self.flash[1]], np.float32)
    def explode(self, space):
        for s in self.pads + self.tsegs: s.sensor = True
    def sounds(self): return [(0.3, "on"), (ACT2, "on")]
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); v = np.array([omega(q) for q in x[::441]]); v = np.repeat(v, 441)[:len(x)]
        add(0, .05 * np.sin(2 * np.pi * np.cumsum(55 + v * 18) / sr) + .03 * np.convolve(rr.normal(0, 1, len(x)), np.ones(30) / 30, "same") * (v / W1) ** .5)
    def draw(self, ctx, t, st, a=1.0, under=True):
        angs, fls = (float(st[0]), float(st[1])), (float(st[2]), float(st[3]))
        on = [True, t >= ACT2]
        if under:
            ctx.move_to(*self.OUT[0])
            for p in self.OUT[1:]: ctx.line_to(*p)
            ctx.line_to(BX1, FLOOR); ctx.line_to(BX0, FLOOR); ctx.close_path(); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
            for k, h in enumerate(HUBS):
                ctx.arc(*h, R + 6, 0, 2 * math.pi); ctx.set_source_rgba(.5, .52, .56, .10 * a); ctx.fill()
                ctx.arc(*h, R + 6, 0, 2 * math.pi); ctx.set_source_rgba(.5, .52, .56, .5 * a); ctx.set_line_width(3); ctx.stroke()
                if on[k]:
                    g = max(0.0, 1 - (t - fls[k]) / .25); x0, x1 = LZ[k]
                    ctx.set_source_rgba(1, .25, .3, (.08 + .25 * g) * a); ctx.rectangle(x0, LY - 14, x1 - x0, 28); ctx.fill()
            return
        for k, h in enumerate(HUBS):
            x0, x1 = LZ[k]; em = x1 - 4 if k == 0 else x0 - 14
            if on[k]:
                g = max(0.0, 1 - (t - fls[k]) / .25)
                ctx.set_source_rgba(1, .25, .3, (.75 + .25 * g) * a); ctx.set_line_width(4 + 3 * g)
                ctx.move_to(x0, LY); ctx.line_to(x1, LY); ctx.stroke()
                text(ctx, "×2", (x0 + x1) / 2, LY - 24, 40, (1, .35, .38, .95 * a), cairo.FONT_WEIGHT_BOLD)
            ctx.rectangle(em, LY - 20, 18, 40); ctx.set_source_rgba(.5, .52, .56, a); ctx.fill()
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            for j in range(NP):
                q = angs[k] + 2 * math.pi * j / NP
                ctx.move_to(h[0] + 44 * math.cos(q), h[1] + 44 * math.sin(q)); ctx.line_to(h[0] + R * math.cos(q), h[1] + R * math.sin(q))
                ctx.set_source_rgba(.95, .75, .15, a); ctx.set_line_width(14); ctx.stroke()
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)
            ctx.arc(*h, 42, 0, 2 * math.pi); ctx.set_source_rgba(.32, .34, .38, a); ctx.fill()
            ctx.arc(*h, 15, 0, 2 * math.pi); ctx.set_source_rgba(.95, .75, .15, a); ctx.fill()

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((230, 900), (40, 0)))
    main(WheelTwin, "wheel_twin")
