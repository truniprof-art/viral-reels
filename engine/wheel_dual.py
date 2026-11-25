import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Wheel variation (2026-11-26): ONE paddle wheel, TWO x2 lasers — a red one across the RISING side (left) and a
cyan one across the DESCENDING side (right), so a shape can double twice per lap (up through red, down through cyan).
The cyan laser switches on at ACT2 s for the slow start. Same single rule: crossing a laser = x2."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import base
from base import *
import wheel as W
from wheel import Wheel, HUB, LY, LX0, LX1, recharge

LY2 = float(os.environ.get("LY2", "1150"))
RX0, RX1 = HUB[0] + 30, BX1 - 4
ACT2 = float(os.environ.get("ACT2", "10"))
BAND = float(os.environ.get("BAND", "7"))
K2 = float(os.environ.get("K2", "1.3"))

class WheelDual(Wheel):
    name = "wheel_dual"
    def build(self, space):
        super().build(space); self.charge2 = 0.0; self.flash2 = -9.0
    def step(self, t, dt):
        super().step(t, dt); self.charge2 += dt
    def crush(self, t, pos):
        m = super().crush(t, pos)
        if not len(pos) or t < ACT2 or self.charge2 < recharge(t) * K2: return m
        zone = (np.abs(pos[:, 1] - LY2) < BAND) & (pos[:, 0] > RX0) & (pos[:, 0] < RX1) & ~m
        if zone.any():
            idx = np.where(zone)[0]; m[idx[:1 + int(len(idx) * min(1, t / T_ZERO))]] = True
            self.charge2 = 0.0; self.flash2 = t
        return m
    def spawn_xy(self, x0, y0, sgn):
        if x0 > HUB[0]:   # below the cyan laser: spawn under it so it doesn't re-trigger instantly
            return min(BX1 - BR - 2, max(BX0 + BR + 2, x0 + sgn * BR * 1.1)), y0 + BR + 6
        return super().spawn_xy(x0, y0, sgn)
    def state(self, t):
        s = super().state(t); s[3] = self.flash2; return s
    def draw(self, ctx, t, st, a=1.0, under=True):
        super().draw(ctx, t, st, a, under)
        on = t >= ACT2; fl = float(st[3]); g = max(0.0, 1 - (t - fl) / .25)
        if under:
            ctx.set_source_rgba(.2, .85, 1, ((.08 + .25 * g) if on else .03) * a); ctx.rectangle(RX0, LY2 - 14, RX1 - RX0, 28); ctx.fill(); return
        if on:
            ctx.set_source_rgba(.2, .85, 1, (.75 + .25 * g) * a); ctx.set_line_width(4 + 3 * g)
        else:
            ctx.set_source_rgba(.2, .85, 1, .18 * a); ctx.set_line_width(2); ctx.set_dash([10, 10])
        ctx.move_to(RX0, LY2); ctx.line_to(RX1, LY2); ctx.stroke(); ctx.set_dash([])
        ctx.rectangle(RX0 - 14, LY2 - 20, 18, 40); ctx.set_source_rgba(.5, .52, .56, a); ctx.fill()
        text(ctx, "×2", RX1 - 60, LY2 - 24, 40, (.3, .88, 1, (.95 if on else .3) * a), cairo.FONT_WEIGHT_BOLD)

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((300, 900), (60, 0)))
    main(WheelDual, "wheel_dual")
