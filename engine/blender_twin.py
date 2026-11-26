import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Blender variation (2026-11-26): TWIN BLADES. One round jar, two 3-arm blades low in the jar (left + right),
counter-rotating so both sweep UP through the middle (a mill). Same single rule: a blade arm slicing a shape = x2.
The right blade starts at ACT2 s (slow start), both speed up to 0:00."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *
import blender as B
from blender import Blender, JC, JR, omega

HUBS = [(540.0 - 140, 1445.0), (540.0 + 140, 1445.0)]
APEX = (540.0, 1475.0); WL = (390.0, 1583.0); WR_ = (690.0, 1583.0)   # centre divider: shapes slide into the two blade pockets
SGN = [-1, 1]                                            # left CCW, right CW on screen -> both sweep up in the middle
ARM = float(os.environ.get("ARM2", "132"))
NARM = int(os.environ.get("NARM2", "3"))
ACT2 = float(os.environ.get("ACT2", "8"))
PTH = float(os.environ.get("PTH", "3.2")); PTH1 = float(os.environ.get("PTH1", "0.2")); KE = B.KE

class BlenderTwin(Blender):
    name = "blender_twin"
    def build(self, space):
        self.walls = []
        N = 72
        for k in range(N):
            a0 = 2 * math.pi * k / N; a1 = 2 * math.pi * (k + 1) / N
            p0 = (JC[0] + (JR + 12) * math.cos(a0), JC[1] + (JR + 12) * math.sin(a0))
            p1 = (JC[0] + (JR + 12) * math.cos(a1), JC[1] + (JR + 12) * math.sin(a1))
            s = pymunk.Segment(space.static_body, p0, p1, 12); s.elasticity = 0.6; s.friction = 0.5
            space.add(s); self.walls.append(s)
        for a_, b_ in ((APEX, WL), (APEX, WR_)):
            s = pymunk.Segment(space.static_body, a_, b_, 10); s.elasticity = 0.5; s.friction = 0.3; space.add(s); self.walls.append(s)
        self.bodies = []; self.arms = []
        for j, h in enumerate(HUBS):
            b = pymunk.Body(body_type=pymunk.Body.KINEMATIC); b.position = h
            arms = []
            for k in range(NARM):
                a = 2 * math.pi * k / NARM + j * math.pi / NARM
                s = pymunk.Segment(b, (0, 0), (ARM * math.cos(a), ARM * math.sin(a)), 7); s.friction = 0.6; s.elasticity = 0.4
                arms.append(s)
            hub = pymunk.Circle(b, 24); hub.friction = 0.5
            space.add(b, hub, *arms); self.bodies.append(b); self.arms += arms
        self.press = [[0.0] * NARM for _ in HUBS]
    def wj(self, j, t):
        if j == 1 and t < ACT2: return 0.0
        return omega(t)
    def step(self, t, dt):
        for j, b in enumerate(self.bodies):
            w = self.wj(j, t); b.angular_velocity = SGN[j] * w
            for k in range(NARM): self.press[j][k] += w * dt
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos): return m
        u = min(1, t / T_ZERO); need = PTH * (PTH1 / PTH) ** u
        for j, b in enumerate(self.bodies):
            d = pos - np.array(HUBS[j]); r = np.hypot(d[:, 0], d[:, 1]); th = np.arctan2(d[:, 1], d[:, 0])
            for k in range(NARM):
                if self.press[j][k] < need: continue
                a = b.angle + 2 * math.pi * k / NARM + j * math.pi / NARM
                da = ((th - a) if SGN[j] > 0 else (a - th)) % (2 * math.pi)
                perp = r * np.sin(da)
                zone = (r > 36) & (r < ARM + 6) & (da < math.pi / 2) & (perp > 0) & (perp < BR + 12) & ~m
                if zone.any():
                    idx = np.where(zone)[0]
                    idx = idx[np.argsort(-r[idx])][:max(1, int(len(idx) * u ** KE))]
                    m[idx] = True; self.press[j][k] = 0.0
        return m
    def spawn_xy(self, x0, y0, sgn):
        p = np.array([x0 + sgn * BR * 1.05, y0 - BR])
        q = p - np.array(JC); Lq = np.hypot(*q)
        if Lq > JR - BR - 4: p = np.array(JC) + q / Lq * (JR - BR - 4)
        return float(p[0]), float(p[1])
    def state(self, t):
        return np.array([self.bodies[0].angle, self.bodies[1].angle, self.wj(0, t), self.wj(1, t)], np.float32)
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); w = np.array([omega(q) for q in x[::441]]); w = np.repeat(w, 441)[:len(x)]
        ph = np.cumsum(60 + w * 22) / sr; ph2 = np.cumsum(75 + w * 26) / sr; on2 = (x >= ACT2)
        add(0, .06 * np.sin(2 * np.pi * ph) * (0.3 + w / B.W1) + .05 * on2 * np.sin(2 * np.pi * ph2) * (w / B.W1)
            + .03 * np.convolve(rr.normal(0, 1, len(x)), np.ones(12) / 12, "same") * (w / B.W1))
    def sounds(self): return [(0.05, "on"), (ACT2, "on")]
    def draw(self, ctx, t, st, a=1.0, under=True):
        if under:
            ctx.rectangle(330, JC[1] + JR - 10, 420, 230); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
            hazard(ctx, 340, JC[1] + JR + 40, 400, 12, a)
            ctx.arc(JC[0], JC[1], JR + 4, 0, 2 * math.pi); ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(6); ctx.stroke()
            ctx.move_to(*APEX); ctx.line_to(WR_[0] + 6, WR_[1] + 4); ctx.arc(JC[0], JC[1], JR + 4, math.atan2(WR_[1] + 4 - JC[1], WR_[0] + 6 - JC[0]), math.atan2(WL[1] + 4 - JC[1], WL[0] - 6 - JC[0]))
            ctx.close_path(); ctx.set_source_rgba(.24, .25, .28, a); ctx.fill_preserve(); ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(4); ctx.stroke()
            for h in HUBS:
                ctx.move_to(h[0] - 20, h[1]); ctx.line_to(h[0] + 20, h[1]); ctx.line_to(h[0] + 50, JC[1] + JR + 6); ctx.line_to(h[0] - 50, JC[1] + JR + 6)
                ctx.close_path(); ctx.set_source_rgba(.24, .25, .28, a); ctx.fill()
            return
        for j, h in enumerate(HUBS):
            ang = float(st[j]); w = float(st[2 + j]); sg = SGN[j]
            ctx.save(); ctx.translate(*h)
            blur = min(1, w / B.W1)
            for k in range(NARM):
                aa = ang + 2 * math.pi * k / NARM + j * math.pi / NARM
                if blur > .15:
                    ctx.move_to(0, 0)
                    if sg > 0: ctx.arc_negative(0, 0, ARM, aa, aa - .9 * blur)
                    else: ctx.arc(0, 0, ARM, aa, aa + .9 * blur)
                    ctx.close_path(); ctx.set_source_rgba(.75, .77, .82, .12 * a * blur); ctx.fill()
                ctx.save(); ctx.rotate(aa); ctx.scale(1, sg)
                ctx.move_to(0, -13); ctx.curve_to(ARM * .4, -24, ARM * .8, -15, ARM + 2, 2); ctx.curve_to(ARM * .7, 8, ARM * .3, 10, 0, 13); ctx.close_path()
                ctx.set_source_rgba(.62, .64, .69, a); ctx.fill()
                ctx.move_to(ARM * .2, -11); ctx.curve_to(ARM * .5, -19, ARM * .8, -11, ARM - 4, 0); ctx.set_source_rgba(.88, .9, .93, a); ctx.set_line_width(2.5); ctx.stroke()
                ctx.restore()
            ctx.arc(0, 0, 24, 0, 2 * math.pi); ctx.set_source_rgba(.32, .33, .36, a); ctx.fill()
            ctx.arc(0, 0, 8, 0, 2 * math.pi); ctx.set_source_rgba(.6, .62, .66, a); ctx.fill()
            ctx.restore()

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((JC[0] - 60, 900), (40, 0)))
    main(BlenderTwin, "blender_twin")
