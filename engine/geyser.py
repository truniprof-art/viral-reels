import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Geyser + hoop (new mechanism 2026-11-26): the tank floor is a V funnel that rolls everything to a NOZZLE in the middle.
An air geyser column blasts shapes straight up; high above floats a glowing x2 HOOP. Every shape that flies UP through the
hoop becomes two (one rule). The geyser gets stronger over time (wider spray, more power), so early shots often miss
the hoop, later almost all go through. Continuous and self-feeding; nothing reverses."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *

NX = 540.0                                    # nozzle x
NY = FLOOR - 40                              # nozzle top (funnel bottom)
FUN_Y = float(os.environ.get("FUN_Y", "1440"))   # funnel walls start height at the tank sides
HY = float(os.environ.get("HY", "820"))       # hoop height
HW = float(os.environ.get("HW", "140"))       # hoop half width
JW0, JW1 = float(os.environ.get("JW0", "30")), float(os.environ.get("JW1", "80"))  # jet half width start -> end
J0, J1 = float(os.environ.get("J0", "1600")), float(os.environ.get("J1", "1700"))  # jet launch speed start -> end
SP0, SP1 = float(os.environ.get("SP0", "0.25"), ), float(os.environ.get("SP1", "0.12"))  # spray (vx spread, rad) start->end: early wide = misses
CH0, CH1 = float(os.environ.get("CH0", "1.0")), float(os.environ.get("CH1", "0.01"))
base.MAXN = int(os.environ.get("MAXN", "760"))

def u_(t): return min(1, t / T_ZERO)
def jet(t): return J0 + (J1 - J0) * u_(t) ** 0.6
def jw(t): return JW0 + (JW1 - JW0) * u_(t) ** 1.2
def spray(t): return SP0 + (SP1 - SP0) * u_(t) ** 0.8
def recharge(t): return CH0 * (CH1 / CH0) ** (u_(t) ** 0.7)

class Geyser(Mech):
    name = "geyser"
    def build(self, space):
        self.space = space; self.rng = np.random.default_rng(7)
        self.segs = []
        for p, q in (((BX0, FUN_Y), (NX - JW1 - 6, NY)), ((BX1, FUN_Y), (NX + JW1 + 6, NY)), ((NX - JW1 - 6, NY + 8), (NX + JW1 + 6, NY + 8))):
            s = pymunk.Segment(space.static_body, p, q, 8); s.friction = 0.05; s.elasticity = 0.2; space.add(s); self.segs.append(s)
        self.charge = 9.0; self.flash = -9.0; self.puff = -9.0
        self.prev = {}
    def step(self, t, dt):
        self.charge += dt
        v = jet(t); spr = spray(t)
        J = jw(t)
        for b in self.space.bodies:
            if b.body_type != pymunk.Body.DYNAMIC: continue
            x, y = b.position
            if abs(x - NX) < J and HY + 70 < y < NY + 4 and b.velocity.y > -0.7 * v:
                a = self.rng.normal(0, spr)
                b.velocity = (v * math.sin(a) + (NX - x) * 3, -v * math.cos(a)); self.puff = t
            elif abs(x - NX) < J + 14 and y > NY - 120 and abs(b.velocity.x) < 40 and abs(b.velocity.y) < 40:
                b.velocity = ((NX - x) * 6, b.velocity.y)          # gently nudge stuck shapes into the nozzle
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos) or self.charge < recharge(t): return m
        zone = (np.abs(pos[:, 1] - HY) < 9) & (np.abs(pos[:, 0] - NX) < HW - BR)
        if zone.any():
            # only shapes going UP: compare with their y one substep ago is not available -> use the jet side:
            idx = np.where(zone)[0]
            m[idx[:1 + int(len(idx) * u_(t))]] = True
            self.charge = 0.0; self.flash = t
        return m
    def spawn_xy(self, x0, y0, sgn):
        return min(NX + HW - BR, max(NX - HW + BR, x0 + sgn * BR * 1.1)), y0 - BR - 8
    def spawn_dir(self, x, y): return (0.0, -1.0)
    def squash(self, x, y): return (0, 1)
    def state(self, t): return np.array([self.flash, self.puff, jet(t), jw(t)], np.float32)
    def explode(self, space):
        for s in self.segs: s.sensor = True
    def sounds(self): return [(0.3, "on")]
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); env_ = np.repeat(np.array([jet(q) / J1 for q in x[::441]]), 441)[:len(x)]
        add(0, .06 * np.convolve(rr.normal(0, 1, len(x)), np.ones(14) / 14, "same") * env_ ** 2 + .03 * np.sin(2 * np.pi * np.cumsum(70 + env_ * 40) / sr))
    def draw(self, ctx, t, st, a=1.0, under=True):
        fl, pf, JW = float(st[0]), float(st[1]), float(st[3])
        g = max(0.0, 1 - (t - fl) / .25)
        if under:
            # funnel body
            ctx.move_to(BX0, FUN_Y); ctx.line_to(NX - JW1 - 6, NY); ctx.line_to(NX + JW1 + 6, NY); ctx.line_to(BX1, FUN_Y)
            ctx.line_to(BX1, FLOOR + 200); ctx.line_to(BX0, FLOOR + 200); ctx.close_path(); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
            # jet column
            ctx.rectangle(NX - JW, HY - 60, 2 * JW, NY - HY + 60); ctx.set_source_rgba(.35, .85, 1, .07 * a); ctx.fill()
            for k in range(7):
                yy = NY - ((t * 520 + k * 110) % 770)
                ctx.move_to(NX - 16, yy + 12); ctx.line_to(NX, yy); ctx.line_to(NX + 16, yy + 12)
                ctx.set_source_rgba(.35, .85, 1, .22 * a); ctx.set_line_width(4); ctx.stroke()
            # back half of the hoop
            ctx.save(); ctx.translate(NX, HY); ctx.scale(1, .22); ctx.arc(0, 0, HW, math.pi, 2 * math.pi); ctx.restore()
            ctx.set_source_rgba(1, .78, .2, (.55 + .3 * g) * a); ctx.set_line_width(7); ctx.stroke()
            ctx.rectangle(NX - HW, HY - 22, 2 * HW, 44); ctx.set_source_rgba(1, .78, .2, (.05 + .2 * g) * a); ctx.fill()
            return
        # nozzle
        ctx.rectangle(NX - JW1 - 12, NY - 6, 2 * JW1 + 24, 30); ctx.set_source_rgba(.5, .52, .56, a); ctx.fill()
        ctx.rectangle(NX - JW - 4, NY - 2, 2 * JW + 8, 8); ctx.set_source_rgba(.35, .85, 1, (.5 + .5 * max(0, 1 - (t - pf) / .15)) * a); ctx.fill()
        # front half of the hoop + mounts
        ctx.save(); ctx.translate(NX, HY); ctx.scale(1, .22); ctx.arc(0, 0, HW, 0, math.pi); ctx.restore()
        ctx.set_source_rgba(1, .78, .2, a); ctx.set_line_width(10 + 4 * g); ctx.stroke()
        for sx in (-1, 1):
            ctx.move_to(NX + sx * HW, HY); ctx.line_to(NX + sx * HW, BY0)
            ctx.set_source_rgba(.5, .52, .56, .8 * a); ctx.set_line_width(5); ctx.stroke()
        text(ctx, "×2", NX + HW + 70, HY + 14, 44, (1, .8, .25, .95 * a), cairo.FONT_WEIGHT_BOLD)

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((300, 1300), (80, 0)))
    main(Geyser, "geyser")
