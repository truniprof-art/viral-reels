import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""x2 Gates ZIGZAG (variation of gates): same bucket elevators, but the x2 gates are HALF-WIDTH and staggered
left / right / left, with a slanted ramp under each one. Shapes zigzag down the 'waterfall' gate -> ramp -> gate,
so a shape can be doubled up to three times on one trip. Gate 2 and 3 switch on mid-video."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GY", "880,1085,1300")
os.environ.setdefault("GACT", "0,12,19")
import numpy as np, pymunk, cairo
import base
from base import *
import gates as G

MID = 540
# gate k: (y, x0, x1); ramps under gates 1 and 2 push the flow to the other half
SPANS = [(G.GX0, MID + 70), (MID - 70, G.GX1), (G.GX0, MID + 70)]
RAMPS = [((G.GX0 - 30, G.GATES[0] + 55), (MID + 110, G.GATES[0] + 125)),
         ((G.GX1 + 30, G.GATES[1] + 55), (MID - 110, G.GATES[1] + 125))]

class GatesZig(G.Gates):
    name = "gates_zig"
    def build(self, space):
        super().build(space)
        for a, b in RAMPS:
            s = pymunk.Segment(space.static_body, a, b, 9); s.friction = 0.12; s.elasticity = 0.3; space.add(s); self.static.append(s)
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos): return m
        for k, gy in enumerate(G.GATES):
            if t < G.GACT[k] or self.charge[k] < G.recharge(t): continue
            x0, x1 = SPANS[k]
            zone = (np.abs(pos[:, 1] - gy) < 5) & (pos[:, 0] > x0) & (pos[:, 0] < x1)
            if zone.any():
                idx = np.where(zone)[0]; m[idx[:1 + int(len(idx) * min(1, t / T_ZERO))]] = True
                self.charge[k] = 0.0; self.flash[k] = t
        return m
    def spawn_xy(self, x0, y0, sgn):
        return min(G.GX1, max(G.GX0, x0 + sgn * BR * 1.1)), y0 + BR + 4
    def draw(self, ctx, t, st, a=1.0, under=True):
        if not under: return super().draw(ctx, t, st, a, under)
        pos = float(st[0])
        for side in (-1, 1):
            x0 = BX1 - G.COLW if side > 0 else BX0
            ctx.rectangle(x0, BY0, G.COLW, FLOOR - BY0); ctx.set_source_rgba(.13, .14, .16, a); ctx.fill()
        ctx.move_to(BX0 + G.COLW - 4, FLOOR); ctx.line_to(BX0 + G.COLW - 4, FLOOR - 40); ctx.line_to(540, FLOOR - 148); ctx.line_to(BX1 - G.COLW + 4, FLOOR - 40); ctx.line_to(BX1 - G.COLW + 4, FLOOR); ctx.close_path()
        ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
        # ramps
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for p, q in RAMPS:
            ctx.move_to(*p); ctx.line_to(*q); ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(18); ctx.stroke()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        for k, gy in enumerate(G.GATES):
            x0, x1 = SPANS[k]
            on = t >= G.GACT[k]; fl = max(0.0, 1 - (t - float(st[2 + k])) / .25) if on else 0.0
            c = (.25, .95, .55) if on else (.35, .36, .4)
            ctx.set_source_rgba(*c, (.10 + .25 * fl) * a); ctx.rectangle(x0, gy - 16, x1 - x0, 32); ctx.fill()
            ctx.set_source_rgba(*c, (.85 if on else .5) * a); ctx.set_line_width(5)
            ctx.move_to(x0, gy); ctx.line_to(x1, gy); ctx.stroke()
            for xx in (x0, x1):
                ctx.rectangle(xx - 9, gy - 22, 18, 44); ctx.set_source_rgba(.5, .52, .56, a); ctx.fill()
            tx = x1 - 62 if k % 2 == 0 else x0 + 16
            text(ctx, "×2", tx, gy - 26, 40, (*c, (.95 if on else .45) * a), cairo.FONT_WEIGHT_BOLD)

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((360, 700), (40, 0)))
    main(GatesZig, "gates_zig")
