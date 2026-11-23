import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""x2 Gates: shapes are carried up two side elevators (belt pairs), fall back down through glowing x2 gates.
Passing a charged gate SPLITS the shape into two. Second gate switches on mid-video. Continuous, never reverses."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *

COLW = float(os.environ.get("COLW", "96"))             # elevator shaft width
SEP_TOP = BY0 + 300
SEP_BOT = float(os.environ.get("SEPB", "1380"))
PT, PB, PSP = BY0 + 110, FLOOR - 4, float(os.environ.get("PSP", "92"))               # paddle path top/bottom, spacing
GX0, GX1 = BX0 + COLW + 40, BX1 - COLW - 40
GATES = [float(x) for x in os.environ.get("GY", "900,1110,1320").split(",")]
GACT = [float(x) for x in os.environ.get("GACT", "0,12,20").split(",")]
V0, V1, VE = float(os.environ.get("V0", "380"), ), float(os.environ.get("V1", "1500")), float(os.environ.get("VE", "1.4"))
CH0, CH1 = float(os.environ.get("CH0", "1.6")), float(os.environ.get("CH1", "0.015"))   # gate recharge time (s)
base.MAXN = int(os.environ.get("MAXN", "760"))

def speed(t):
    u = min(1, t / T_ZERO); return V0 * (V1 / V0) ** (u ** VE)
def recharge(t):
    u = min(1, t / T_ZERO); return CH0 * (CH1 / CH0) ** (u ** 0.8)

class Gates(Mech):
    name = "gates"
    def build(self, space):
        self.static = []; self.paddles = []
        def seg(a, b, r=8, fr=0.5, e=0.4, body=None):
            s = pymunk.Segment(body or space.static_body, a, b, r); s.friction = fr; s.elasticity = e; space.add(s)
            if body is None: self.static.append(s)
            return s
        self.span = PB - PT; n = int(self.span // PSP); self.psp = self.span / n
        for side in (-1, 1):
            sep_x = BX1 - COLW - 8 if side > 0 else BX0 + COLW + 8
            seg((sep_x, SEP_TOP), (sep_x, SEP_BOT), 8, 0.3, 0.1)
            seg((BX1 - 230, BY0 + 6) if side > 0 else (BX0 + 230, BY0 + 6), (BX1, BY0 + 190) if side > 0 else (BX0, BY0 + 190), 9, 0.2, 0.5)
            # bucket elevator: tilted paddles riding up the shaft
            cx = BX1 - COLW / 2 if side > 0 else BX0 + COLW / 2
            for k in range(n):
                bd = pymunk.Body(body_type=pymunk.Body.KINEMATIC); bd.position = (cx, PB - k * self.psp)
                sh = pymunk.Segment(bd, (-side * (COLW / 2 - 4), -7), (side * (COLW / 2 - 4), 7), 4); sh.friction = 0.6; sh.elasticity = 0.1
                space.add(bd, sh); self.paddles.append((bd, sh, side))
        # roof-shaped floor with a lip into each shaft pit
        seg((540, FLOOR - 150), (BX1 - COLW - 4, FLOOR - 42), 10, 0.15, 0.3)
        seg((540, FLOOR - 150), (BX0 + COLW + 4, FLOOR - 42), 10, 0.15, 0.3)
        self.pos = 0.0; self.charge = [9.0] * len(GATES); self.flash = [-9.0] * len(GATES)
    def step(self, t, dt):
        v = speed(t); self.pos += v * dt
        for bd, sh, side in self.paddles:
            bd.velocity = (0, -v)
            if bd.position.y < PT: bd.position = (bd.position.x, bd.position.y + self.span)
        for k in range(len(GATES)):
            if t >= GACT[k]: self.charge[k] += dt
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos): return m
        for k, gy in enumerate(GATES):
            if t < GACT[k] or self.charge[k] < recharge(t): continue
            zone = (np.abs(pos[:, 1] - gy) < 5) & (pos[:, 0] > GX0) & (pos[:, 0] < GX1)
            if zone.any():
                idx = np.where(zone)[0]; m[idx[:1 + int(len(idx) * min(1, t / T_ZERO))]] = True
                self.charge[k] = 0.0; self.flash[k] = t
        return m
    def spawn_xy(self, x0, y0, sgn):
        return min(GX1, max(GX0, x0 + sgn * BR * 1.1)), y0 + BR + 4
    def spawn_dir(self, x, y): return (0.0, 0.6)
    def squash(self, x, y): return (1, 0)
    def state(self, t):
        return np.array([self.pos, speed(t)] + self.flash + [-9.0] * (4 - len(GATES)), np.float32)
    def explode(self, space):
        for s in self.static: s.sensor = True
        for bd, sh, side in self.paddles: sh.sensor = True
    def sounds(self): return [(g, "on") for g in GACT if g > 0]
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); v = np.array([speed(q) for q in x[::441]]); v = np.repeat(v, 441)[:len(x)]
        add(0, .04 * np.sin(2 * np.pi * np.cumsum(70 + v / 25) / sr) + .03 * np.convolve(rr.normal(0, 1, len(x)), np.ones(25) / 25, "same") * (v / V1) ** .5)
    def draw(self, ctx, t, st, a=1.0, under=True):
        pos = float(st[0])
        if under:
            # shafts
            for side in (-1, 1):
                x0 = BX1 - COLW if side > 0 else BX0
                ctx.rectangle(x0, BY0, COLW, FLOOR - BY0); ctx.set_source_rgba(.13, .14, .16, a); ctx.fill()
            # floor
            ctx.move_to(BX0 + COLW - 4, FLOOR); ctx.line_to(BX0 + COLW - 4, FLOOR - 40); ctx.line_to(540, FLOOR - 148); ctx.line_to(BX1 - COLW + 4, FLOOR - 40); ctx.line_to(BX1 - COLW + 4, FLOOR); ctx.close_path()
            ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
            # gates (glow bars with x2)
            for k, gy in enumerate(GATES):
                on = t >= GACT[k]; fl = max(0.0, 1 - (t - float(st[2 + k])) / .25) if on else 0.0
                c = (.25, .95, .55) if on else (.35, .36, .4)
                ctx.set_source_rgba(*c, (.10 + .25 * fl) * a); ctx.rectangle(GX0, gy - 16, GX1 - GX0, 32); ctx.fill()
                ctx.set_source_rgba(*c, (.85 if on else .5) * a); ctx.set_line_width(5)
                ctx.move_to(GX0, gy); ctx.line_to(GX1, gy); ctx.stroke()
                for xx in (GX0, GX1):
                    ctx.rectangle(xx - 9, gy - 22, 18, 44); ctx.set_source_rgba(.5, .52, .56, a); ctx.fill()
                text(ctx, "×2", GX1 - 60, gy - 26, 40, (*c, (.95 if on else .45) * a), cairo.FONT_WEIGHT_BOLD)
            return
        # separators, moving paddles (positions derived from belt travel), deflectors
        for side in (-1, 1):
            sep_x = BX1 - COLW - 8 if side > 0 else BX0 + COLW + 8
            ctx.set_source_rgba(.42, .44, .48, a); ctx.rectangle(sep_x - 7, SEP_TOP, 14, SEP_BOT - SEP_TOP); ctx.fill()
            cx = BX1 - COLW / 2 if side > 0 else BX0 + COLW / 2
            span = PB - PT; m = int(span // PSP); sp = span / m
            for k in range(m):
                y = PB - ((k * sp + pos) % span)
                ctx.move_to(cx - side * (COLW / 2 - 4), y - 7); ctx.line_to(cx + side * (COLW / 2 - 4), y + 7)
                ctx.set_source_rgba(.95, .75, .15, a); ctx.set_line_width(7); ctx.stroke()
            p, q = ((BX1 - 230, BY0 + 6), (BX1, BY0 + 190)) if side > 0 else ((BX0 + 230, BY0 + 6), (BX0, BY0 + 190))
            ctx.move_to(*p); ctx.line_to(*q); ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(16); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
            ctx.set_line_cap(cairo.LINE_CAP_BUTT)

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((540, 700), (60, 0)))
    main(Gates, "gates")
