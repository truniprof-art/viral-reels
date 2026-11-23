import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Paddle wheel: a big wheel with paddles turns one way through the pile, scooping shapes up its rising side.
A red laser line crosses the rising side: every shape carried through the laser SPLITS in two. Continuous, never reverses."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *

HUB = (540.0, 1290.0)
R = float(os.environ.get("WR", "330"))
NP = int(os.environ.get("NP", "6"))
LY = float(os.environ.get("LY", "1080"))                 # laser height (above the hub, rising = left side)
LX0, LX1 = BX0 + 4, HUB[0] - 30
W0, W1, WE = float(os.environ.get("W0", "0.45")), float(os.environ.get("W1", "3.2")), float(os.environ.get("WE", "1.2"))
CH0, CH1 = float(os.environ.get("CH0", "1.8")), float(os.environ.get("CH1", "0.01"))
base.MAXN = int(os.environ.get("MAXN", "720"))

def omega(t):
    u = min(1, t / T_ZERO); return W0 * (W1 / W0) ** (u ** WE)
def recharge(t):
    u = min(1, t / T_ZERO); return CH0 * (CH1 / CH0) ** (u ** 0.7)

class Wheel(Mech):
    name = "wheel"
    def __init__(self):
        TR = R + 22; pts = [(BX1, HUB[1] + TR * math.sin(math.radians(-8)) - 90)]
        for k in range(41):
            a = math.radians(-8 + 196 * k / 40); pts.append((HUB[0] + TR * math.cos(a), HUB[1] + TR * math.sin(a)))
        pts.append((BX0, pts[-1][1] - 90)); self.TR_PTS = pts
    def build(self, space):
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC); self.body.position = HUB
        self.pads = []
        for k in range(NP):
            a = 2 * math.pi * k / NP
            s = pymunk.Segment(self.body, (60 * math.cos(a), 60 * math.sin(a)), (R * math.cos(a), R * math.sin(a)), 8)
            s.friction = 0.9; s.elasticity = 0.1; self.pads.append(s)
        hub = pymunk.Circle(self.body, 58); hub.friction = 0.6
        space.add(self.body, hub, *self.pads)
        self.trough = []
        TR = R + 22; N = 40
        for k in range(N):
            a0 = math.radians(-8 + 196 * k / N); a1 = math.radians(-8 + 196 * (k + 1) / N)
            self.trough.append(((HUB[0] + TR * math.cos(a0), HUB[1] + TR * math.sin(a0)), (HUB[0] + TR * math.cos(a1), HUB[1] + TR * math.sin(a1))))
        e0 = self.trough[0][0]; e1 = self.trough[-1][1]
        self.trough += [((BX1, e0[1] - 90), e0), (e1, (BX0, e1[1] - 90))]
        self.tsegs = []
        for p, q in self.trough:
            s = pymunk.Segment(space.static_body, p, q, 10); s.friction = 0.3; s.elasticity = 0.3; space.add(s); self.tsegs.append(s)
        self.charge = 9.0; self.flash = -9.0
    def step(self, t, dt):
        self.body.angular_velocity = omega(t); self.charge += dt
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos): return m
        if self.charge < recharge(t): return m
        zone = (np.abs(pos[:, 1] - LY) < 5) & (pos[:, 0] > LX0) & (pos[:, 0] < LX1)
        if zone.any():
            idx = np.where(zone)[0]; m[idx[:1 + int(len(idx) * min(1, t / T_ZERO))]] = True
            self.charge = 0.0; self.flash = t
        return m
    def spawn_xy(self, x0, y0, sgn):
        return min(BX1 - BR - 2, max(BX0 + BR + 2, x0 + sgn * BR * 1.1)), y0 - BR - 6
    def spawn_dir(self, x, y): return (0.4, -0.5)
    def squash(self, x, y): return (0, 1)
    def state(self, t):
        return np.array([self.body.angle, self.flash, omega(t), 0], np.float32)
    def explode(self, space):
        for s in self.pads + self.tsegs: s.sensor = True
    def sounds(self): return [(0.3, "on")]
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); v = np.array([omega(q) for q in x[::441]]); v = np.repeat(v, 441)[:len(x)]
        add(0, .05 * np.sin(2 * np.pi * np.cumsum(55 + v * 18) / sr) + .03 * np.convolve(rr.normal(0, 1, len(x)), np.ones(30) / 30, "same") * (v / W1) ** .5)
    def draw(self, ctx, t, st, a=1.0, under=True):
        ang, fl = float(st[0]), float(st[1])
        if under:
            ctx.move_to(*self.TR_PTS[0])
            for p in self.TR_PTS[1:]: ctx.line_to(*p)
            ctx.line_to(BX0, FLOOR); ctx.line_to(BX1, FLOOR); ctx.close_path(); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
            ctx.arc(*HUB, R + 6, 0, 2 * math.pi); ctx.set_source_rgba(.5, .52, .56, .10 * a); ctx.fill()
            ctx.arc(*HUB, R + 6, 0, 2 * math.pi); ctx.set_source_rgba(.5, .52, .56, .5 * a); ctx.set_line_width(3); ctx.stroke()
            g = max(0.0, 1 - (t - fl) / .25)
            ctx.set_source_rgba(1, .25, .3, (.08 + .25 * g) * a); ctx.rectangle(LX0, LY - 14, LX1 - LX0, 28); ctx.fill()
            return
        # laser line + emitters
        g = max(0.0, 1 - (t - fl) / .25)
        ctx.set_source_rgba(1, .25, .3, (.75 + .25 * g) * a); ctx.set_line_width(4 + 3 * g)
        ctx.move_to(LX0, LY); ctx.line_to(LX1, LY); ctx.stroke()
        ctx.rectangle(LX1 - 4, LY - 20, 18, 40); ctx.set_source_rgba(.5, .52, .56, a); ctx.fill()
        text(ctx, "×2", LX0 + 60, LY - 24, 40, (1, .35, .38, .95 * a), cairo.FONT_WEIGHT_BOLD)
        # paddles + hub
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(NP):
            q = ang + 2 * math.pi * k / NP
            ctx.move_to(HUB[0] + 60 * math.cos(q), HUB[1] + 60 * math.sin(q)); ctx.line_to(HUB[0] + R * math.cos(q), HUB[1] + R * math.sin(q))
            ctx.set_source_rgba(.95, .75, .15, a); ctx.set_line_width(16); ctx.stroke()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        ctx.arc(*HUB, 58, 0, 2 * math.pi); ctx.set_source_rgba(.32, .34, .38, a); ctx.fill()
        ctx.arc(*HUB, 20, 0, 2 * math.pi); ctx.set_source_rgba(.95, .75, .15, a); ctx.fill()

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((300, 900), (60, 0)))
    main(Wheel, "wheel")
