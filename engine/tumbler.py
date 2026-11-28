import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Tumbler drum (NEW mechanism 2026-11-28): the tank IS a big round drum that keeps turning one way (cement-mixer /
tumble-dryer look). Short fins on the inner wall lift the pile up the rising side and drop it from the top.
A FIXED glowing x2 laser crosses the drum just above its centre: every shape that passes through the laser splits in two.
The drum never reverses; it speeds up slowly, the laser recharges faster -> slow start, then the drum fills."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *

C = (540.0, 1235.0)
R = float(os.environ.get("DR", "430"))           # drum inner radius
NF = int(os.environ.get("NF", "4"))              # fins
FL = float(os.environ.get("FL", "130"))          # fin length
LOFF = float(os.environ.get("LOFF", "40"))       # laser height above centre
base.BR = float(os.environ.get("TBR", "14"))
BRr = base.BR
base.BX0, base.BX1, base.BY0, base.FLOOR = 0, 1080, 560, 1880
base.MAXN = int(os.environ.get("MAXN", "760"))
W0, W1, WE = float(os.environ.get("W0", "0.55")), float(os.environ.get("W1", "1.5")), float(os.environ.get("WE", "1.2"))
CH0, CH1 = float(os.environ.get("CH0", "1.8")), float(os.environ.get("CH1", "0.025"))
LY = C[1] - LOFF
LHW = math.sqrt(max(1, R * R - LOFF * LOFF)) - 6   # laser half length (chord)

def omega(t):
    u = min(1, t / T_ZERO); return W0 * (W1 / W0) ** (u ** WE)
def recharge(t):
    u = min(1, t / T_ZERO); return CH0 * (CH1 / CH0) ** (u ** 0.7)

class Tumbler(Mech):
    name = "tumbler"
    tank_walls = False
    def build(self, space):
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC); self.body.position = C
        self.segs = []; N = 60; RR = R + 10
        for k in range(N):
            a0, a1 = 2 * math.pi * k / N, 2 * math.pi * (k + 1) / N
            s = pymunk.Segment(self.body, (RR * math.cos(a0), RR * math.sin(a0)), (RR * math.cos(a1), RR * math.sin(a1)), 10)
            s.friction = 0.6; s.elasticity = 0.2; self.segs.append(s)
        for k in range(NF):
            a = 2 * math.pi * k / NF
            s = pymunk.Segment(self.body, (R * math.cos(a), R * math.sin(a)), ((R - FL) * math.cos(a), (R - FL) * math.sin(a)), 9)
            s.friction = 0.9; s.elasticity = 0.1; self.segs.append(s)
        space.add(self.body, *self.segs)
        self.charge = 9.0; self.flash = -9.0
    def step(self, t, dt):
        self.body.angular_velocity = omega(t); self.charge += dt
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos) or self.charge < recharge(t): return m
        zone = (np.abs(pos[:, 1] - LY) < 5) & (np.abs(pos[:, 0] - C[0]) < LHW - 10)
        if zone.any():
            idx = np.where(zone)[0]; m[idx[:1 + int(len(idx) * min(1, t / T_ZERO))]] = True
            self.charge = 0.0; self.flash = t
        return m
    def spawn_xy(self, x0, y0, sgn):
        return x0 + sgn * BRr * 1.1, y0 - BRr - 6
    def fix_xy(self, x, y):
        dx, dy = x - C[0], y - C[1]; L = math.hypot(dx, dy); lim = R - BRr - 14
        if L > lim: x, y = C[0] + dx / L * lim, C[1] + dy / L * lim
        return x, y
    def spawn_dir(self, x, y): return (0.0, -0.4)
    def squash(self, x, y): return (0, 1)
    def state(self, t):
        return np.array([self.body.angle, self.flash, omega(t), 0], np.float32)
    def explode(self, space):
        for s in self.segs: s.sensor = True
    def sounds(self): return [(0.3, "on")]
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); v = np.array([omega(q) for q in x[::441]]); v = np.repeat(v, 441)[:len(x)]
        add(0, .05 * np.sin(2 * np.pi * np.cumsum(46 + v * 20) / sr) + .035 * np.convolve(rr.normal(0, 1, len(x)), np.ones(40) / 40, "same") * (v / W1) ** .5)
    def draw(self, ctx, t, st, a=1.0, under=True):
        ang, fl = float(st[0]), float(st[1])
        g = max(0.0, 1 - (t - fl) / .25)
        if under:
            # stand + drum interior
            ctx.set_source_rgba(.32, .34, .38, a)
            ctx.move_to(C[0] - 120, C[1] + R - 40); ctx.line_to(C[0] - 230, C[1] + R + 150); ctx.line_to(C[0] + 230, C[1] + R + 150)
            ctx.line_to(C[0] + 120, C[1] + R - 40); ctx.close_path(); ctx.fill()
            ctx.arc(*C, R + 6, 0, 2 * math.pi); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
            ctx.set_source_rgba(1, .25, .3, (.07 + .25 * g) * a); ctx.rectangle(C[0] - LHW, LY - 14, 2 * LHW, 28); ctx.fill()
            return
        # rim with rotating stripes (shows the drum turning)
        ctx.arc(*C, R + 24, 0, 2 * math.pi); ctx.set_source_rgba(.55, .57, .62, a); ctx.set_line_width(30); ctx.stroke()
        ctx.set_line_width(30)
        for k in range(16):
            q = ang + 2 * math.pi * k / 16
            ctx.arc(*C, R + 24, q, q + 0.12); ctx.set_source_rgba(.95, .72, .18, a); ctx.stroke()
        # fins
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(NF):
            q = ang + 2 * math.pi * k / NF
            ctx.move_to(C[0] + (R + 4) * math.cos(q), C[1] + (R + 4) * math.sin(q))
            ctx.line_to(C[0] + (R - FL) * math.cos(q), C[1] + (R - FL) * math.sin(q))
            ctx.set_source_rgba(.95, .72, .18, a); ctx.set_line_width(18); ctx.stroke()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        # fixed laser + emitters on both sides of the chord
        ctx.set_source_rgba(1, .25, .3, (.75 + .25 * g) * a); ctx.set_line_width(4 + 3 * g)
        ctx.move_to(C[0] - LHW, LY); ctx.line_to(C[0] + LHW, LY); ctx.stroke()
        for sx in (-1, 1):
            ctx.arc(C[0] + sx * (LHW + 34), LY, 22, 0, 2 * math.pi); ctx.set_source_rgba(.32, .34, .38, a); ctx.fill()
            ctx.arc(C[0] + sx * (LHW + 34), LY, 9, 0, 2 * math.pi); ctx.set_source_rgba(1, .3, .35, a); ctx.fill()
        text(ctx, "×2", C[0] - 30, LY - 22, 44, (1, .35, .38, .95 * a), cairo.FONT_WEIGHT_BOLD)

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((540 + (seed % 7 - 3) * 25, C[1] + 250), (80, 0)))
    main(Tumbler, "tumbler")
