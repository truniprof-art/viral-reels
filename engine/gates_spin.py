import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""x2 Gates SPIN (variation of gates, 2026-11-26): same bucket elevators, but instead of fixed horizontal gates
there is ONE spinning x2 LASER ROTOR in the middle of the tank. It turns slowly, always the same way.
Arm 1 (a single bar through the hub) is live from 0 s; at ACT2 the perpendicular bar lights up -> a spinning x2 CROSS.
Any shape the glowing bar sweeps through / falls through splits into two."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pymunk, cairo
import base
from base import *
import gates as G

CX, CY = 540.0, float(os.environ.get("CY", "1040"))
L = float(os.environ.get("RL", "300"))                  # half length of each bar
W0, W1 = float(os.environ.get("W0", "0.55")), float(os.environ.get("W1", "1.25"))   # rotor speed rad/s (never reverses)
ACT2 = float(os.environ.get("ACT2", "11"))

def omega(t):
    u = min(1, t / T_ZERO); return W0 + (W1 - W0) * u * u

class GatesSpin(G.Gates):
    name = "gates_spin"
    def build(self, space):
        super().build(space)
        self.th = 0.3; self.charge = [9.0, 9.0]; self.flash = [-9.0, -9.0]
        hub = pymunk.Circle(space.static_body, 26, (CX, CY)); hub.friction = 0.3; hub.elasticity = 0.4; space.add(hub); self.static.append(hub)
    def step(self, t, dt):
        v = G.speed(t); self.pos += v * dt
        for bd, sh, side in self.paddles:
            bd.velocity = (0, -v)
            if bd.position.y < G.PT: bd.position = (bd.position.x, bd.position.y + self.span)
        self.th += omega(t) * dt
        self.charge[0] += dt
        if t >= ACT2: self.charge[1] += dt
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos): return m
        dx, dy = pos[:, 0] - CX, pos[:, 1] - CY
        for k in range(2):
            if (k == 1 and t < ACT2) or self.charge[k] < G.recharge(t): continue
            th = self.th + k * math.pi / 2
            c, s = math.cos(th), math.sin(th)
            d = -dx * s + dy * c; al = dx * c + dy * s
            zone = (np.abs(d) < 6) & (np.abs(al) < L) & (np.abs(al) > 30)
            if zone.any():
                idx = np.where(zone)[0]; m[idx[:1 + int(len(idx) * min(1, t / T_ZERO))]] = True
                self.charge[k] = 0.0; self.flash[k] = t
        return m
    def spawn_xy(self, x0, y0, sgn):
        return min(BX1 - G.COLW - 30, max(BX0 + G.COLW + 30, x0 + sgn * BR * 1.1)), y0 + BR + 4
    def state(self, t):
        return np.array([self.pos, G.speed(t), self.th, -9.0] + self.flash, np.float32)
    def sounds(self): return [(ACT2, "on")]
    def draw(self, ctx, t, st, a=1.0, under=True):
        if not under: return super().draw(ctx, t, st, a, under)
        for side in (-1, 1):
            x0 = BX1 - G.COLW if side > 0 else BX0
            ctx.rectangle(x0, BY0, G.COLW, FLOOR - BY0); ctx.set_source_rgba(.13, .14, .16, a); ctx.fill()
        ctx.move_to(BX0 + G.COLW - 4, FLOOR); ctx.line_to(BX0 + G.COLW - 4, FLOOR - 40); ctx.line_to(540, FLOOR - 148); ctx.line_to(BX1 - G.COLW + 4, FLOOR - 40); ctx.line_to(BX1 - G.COLW + 4, FLOOR); ctx.close_path()
        ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
        th = float(st[2])
        # faint sweep circle
        ctx.arc(CX, CY, L, 0, 2 * math.pi); ctx.set_source_rgba(.25, .95, .55, .06 * a); ctx.fill()
        ctx.arc(CX, CY, L, 0, 2 * math.pi); ctx.set_source_rgba(.25, .95, .55, .18 * a); ctx.set_line_width(2); ctx.stroke()
        for k in range(2):
            on = (k == 0) or t >= ACT2
            fl = max(0.0, 1 - (t - float(st[4 + k])) / .25) if on else 0.0
            col = (.25, .95, .55) if on else (.35, .36, .4)
            ang = th + k * math.pi / 2; c, s = math.cos(ang), math.sin(ang)
            ctx.save(); ctx.translate(CX, CY); ctx.rotate(ang)
            ctx.set_source_rgba(*col, (.10 + .30 * fl) * a); ctx.rectangle(-L, -15, 2 * L, 30); ctx.fill()
            ctx.set_source_rgba(*col, (.9 if on else .5) * a); ctx.set_line_width(6); ctx.move_to(-L, 0); ctx.line_to(L, 0); ctx.stroke()
            for xx in (-L, L):
                ctx.rectangle(xx - 10, -20, 20, 40); ctx.set_source_rgba(.5, .52, .56, a); ctx.fill()
            ctx.restore()
            # upright "x2" label near one tip
            tx, ty = CX + c * (L - 70) - 24, CY + s * (L - 70) - 30
            text(ctx, "×2", tx, ty + 30, 38, (*col, (.95 if on else .45) * a), cairo.FONT_WEIGHT_BOLD)
        ctx.arc(CX, CY, 28, 0, 2 * math.pi); ctx.set_source_rgba(.5, .52, .56, a); ctx.fill()
        ctx.arc(CX, CY, 11, 0, 2 * math.pi); ctx.set_source_rgba(.22, .23, .26, a); ctx.fill()

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((540, 700), (60, 0)))
    main(GatesSpin, "gates_spin")
