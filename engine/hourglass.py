import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Hourglass: the tank IS a giant hourglass that keeps turning slowly one way (never reverses).
Rule: every shape that squeezes through the glowing NECK becomes THREE (x3 on the far side).
Starts with one shape; each half-turn pours the whole pile through the neck again -> slow start, then it explodes."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *

base.BR = float(os.environ.get("HBR", "9"))
BRr = base.BR
C = (540.0, 1230.0)
NW = float(os.environ.get("NW", "50"))         # neck half width
HW = float(os.environ.get("HW", "270"))        # bulb half width
HL = float(os.environ.get("HL", "410"))        # half length
SH = float(os.environ.get("SH", "165"))        # where the cone meets the straight side
base.BX0, base.BX1, base.BY0, base.FLOOR = 0, 1080, 560, 1880
base.MAXN = int(os.environ.get("MAXN", "700"))
NSPLIT = int(os.environ.get("NSPLIT", "3"))
W0, W1, WE = float(os.environ.get("W0", "0.48")), float(os.environ.get("W1", "0.85")), float(os.environ.get("WE", "1.0"))
CH0, CH1 = float(os.environ.get("CH0", "1.6")), float(os.environ.get("CH1", "0.004"))
A0 = float(os.environ.get("A0", "0.0"))

def omega(t):
    u = min(1, t / T_ZERO); return W0 * (W1 / W0) ** (u ** WE)
def recharge(t):
    u = min(1, t / T_ZERO); return CH0 * (CH1 / CH0) ** (u ** 0.65)

# outline (local coords, y down), closed loop
OUT = [(-NW, -14), (-HW, -SH), (-HW, -HL), (HW, -HL), (HW, -SH), (NW, -14),
       (NW, 14), (HW, SH), (HW, HL), (-HW, HL), (-HW, SH), (-NW, 14)]

class Hourglass(Mech):
    name = "hourglass"
    NSPLIT = NSPLIT
    tank_walls = False
    def build(self, space):
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC); self.body.position = C; self.body.angle = A0
        self.segs = []
        for p, q in zip(OUT, OUT[1:] + OUT[:1]):
            s = pymunk.Segment(self.body, p, q, 9); s.friction = 0.35; s.elasticity = 0.25; self.segs.append(s)
        space.add(self.body, *self.segs)
        self.charge = 9.0; self.flash = -9.0
    def step(self, t, dt):
        self.body.angular_velocity = omega(t); self.charge += dt
    def local(self, x, y):
        a = self.body.angle; ca, sa = math.cos(a), math.sin(a)
        dx, dy = x - C[0], y - C[1]
        return dx * ca + dy * sa, -dx * sa + dy * ca
    def world(self, lx, ly):
        a = self.body.angle; ca, sa = math.cos(a), math.sin(a)
        return C[0] + lx * ca - ly * sa, C[1] + lx * sa + ly * ca
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos) or self.charge < recharge(t): return m
        a = self.body.angle; ca, sa = math.cos(a), math.sin(a)
        dx, dy = pos[:, 0] - C[0], pos[:, 1] - C[1]
        lx = dx * ca + dy * sa; ly = -dx * sa + dy * ca
        zone = (np.abs(ly) < 6) & (np.abs(lx) < NW)
        if zone.any():
            idx = np.where(zone)[0]; m[idx[:1 + int(len(idx) * min(1, t / T_ZERO))]] = True
            self.charge = 0.0; self.flash = t
        return m
    def _down(self):
        # which bulb is lower in world space: local +y or -y
        a = self.body.angle
        return 1.0 if math.cos(a) >= 0 else -1.0
    def spawn_xy(self, x0, y0, sgn):
        d = self._down(); lx, ly = self.local(x0, y0)
        return self.world(max(-NW + 4, min(NW - 4, lx * .3 + sgn * BRr * 1.9)), d * (BRr * 2.6))
    def fix_xy(self, x, y):
        lx, ly = self.local(x, y); d = self._down()
        if abs(ly) < 2 * BRr + 4: ly = d * (2 * BRr + 4)
        lim = NW + (HW - NW) * min(1, max(0, (abs(ly) - 14) / (SH - 14))) - BRr - 8
        lx = max(-lim, min(lim, lx)); ly = max(-HL + BRr + 10, min(HL - BRr - 10, ly))
        return self.world(lx, ly)
    def spawn_dir(self, x, y):
        a = self.body.angle; d = self._down(); return (-math.sin(a) * d * .3, math.cos(a) * d * .3)
    def squash(self, x, y): return (0, 1)
    def state(self, t):
        return np.array([self.body.angle, self.flash, omega(t), 0], np.float32)
    def explode(self, space):
        for s in self.segs: s.sensor = True
    def sounds(self): return [(0.3, "on")]
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); v = np.array([omega(q) for q in x[::441]]); v = np.repeat(v, 441)[:len(x)]
        add(0, .03 * np.sin(2 * np.pi * np.cumsum(48 + v * 22) / sr) + .04 * np.convolve(rr.normal(0, 1, len(x)), np.ones(12) / 12, "same") * (v / W1))
    def draw(self, ctx, t, st, a=1.0, under=True):
        ang, fl = float(st[0]), float(st[1])
        g = max(0.0, 1 - (t - fl) / .25)
        ctx.save(); ctx.translate(*C); ctx.rotate(ang)
        ink = ST_.ink
        if under:
            ctx.move_to(*OUT[0])
            for p in OUT[1:]: ctx.line_to(*p)
            ctx.close_path(); ctx.set_source_rgba(*ink(.06 * a)[:3], .06 * a); ctx.fill()
            ctx.restore(); return
        # glass outline
        ctx.move_to(*OUT[0])
        for p in OUT[1:]: ctx.line_to(*p)
        ctx.close_path(); ctx.set_source_rgba(.62, .64, .68, .9 * a); ctx.set_line_width(7); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
        # end caps + side posts (flat, matte)
        for sy in (-1, 1):
            ctx.rectangle(-HW - 40, sy * HL - 22 + (0 if sy < 0 else 0) - (0 if sy > 0 else 0), 2 * HW + 80, 44)
            ctx.set_source_rgba(.95, .72, .18, a); ctx.fill()
        for sx in (-1, 1):
            ctx.rectangle(sx * (HW + 28) - 7, -HL + 20, 14, 2 * HL - 40); ctx.set_source_rgba(.95, .72, .18, .85 * a); ctx.fill()
        # x2 neck: glowing bar across the neck
        ctx.set_source_rgba(1, .25, .3, (.25 + .4 * g) * a); ctx.rectangle(-NW - 30, -9, 2 * NW + 60, 18); ctx.fill()
        ctx.set_source_rgba(1, .25, .3, (.85 + .15 * g) * a); ctx.set_line_width(4 + 3 * g)
        ctx.move_to(-NW - 26, 0); ctx.line_to(NW + 26, 0); ctx.stroke()
        ctx.restore()
        # upright x2 label next to the neck
        lx, ly = C[0] + 150, C[1] + 14
        text(ctx, f"×{NSPLIT}", lx, ly, 46, (1, .35, .38, .95 * a), cairo.FONT_WEIGHT_BOLD)

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((540 + (seed % 7 - 3) * 20, C[1] - 330), (40, 0)))
    main(Hourglass, "hourglass")
