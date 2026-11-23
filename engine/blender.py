import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Blender: a round jar with a spinning 3-arm blade. A blade arm SLICES a shape it pushes against -> two halves = two shapes.
Continuous rotation, one direction; the blade has to 'chew' (pressure builds with blade travel) so the start is slow."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *

JC = (540.0, 1185.0); JR = 425.0                         # jar (circle) centre / radius
HUB = (540.0, 1430.0)
ARM = float(os.environ.get("ARM", "172"))
NARM = int(os.environ.get("NARM", "4"))
W0, W1, WE = float(os.environ.get("W0", "0.25")), float(os.environ.get("W1", "9")), float(os.environ.get("WE", "1.5"))
PTH = float(os.environ.get("PTH", "2.6"))                # radians of blade travel per slice (per arm)
PTH1 = float(os.environ.get("PTH1", "0.15"))              # ... shrinking to this by 0:00
KE = float(os.environ.get("KE", "0.3"))                  # share of the balls on the edge sliced at once grows with t
base.MAXN = int(os.environ.get("MAXN", "560"))

def omega(t):
    u = min(1, t / T_ZERO); return W0 * (W1 / W0) ** (u ** WE)

def angle(t, n=400):
    ts = np.linspace(0, t, n); return float(np.trapezoid([omega(x) for x in ts], ts)) if t > 0 else 0.0

class Blender(Mech):
    name = "blender"
    tank_walls = False
    def build(self, space):
        self.walls = []
        N = 72
        for k in range(N):                                    # jar wall, open at the top (y < 820)
            a0 = 2 * math.pi * k / N; a1 = 2 * math.pi * (k + 1) / N
            p0 = (JC[0] + (JR + 12) * math.cos(a0), JC[1] + (JR + 12) * math.sin(a0))
            p1 = (JC[0] + (JR + 12) * math.cos(a1), JC[1] + (JR + 12) * math.sin(a1))
            s = pymunk.Segment(space.static_body, p0, p1, 12); s.elasticity = 0.6; s.friction = 0.5
            space.add(s); self.walls.append(s)
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC); self.body.position = HUB
        self.arms = []
        for k in range(NARM):
            a = 2 * math.pi * k / NARM
            s = pymunk.Segment(self.body, (0, 0), (ARM * math.cos(a), ARM * math.sin(a)), 7); s.friction = 0.6; s.elasticity = 0.4
            self.arms.append(s)
        hub = pymunk.Circle(self.body, 26); hub.friction = 0.5
        space.add(self.body, hub, *self.arms)
        self.ang = 0.0; self.press = [0.0] * NARM; self.cuts = []
    def step(self, t, dt):
        w = omega(t); self.body.angular_velocity = w; self.ang += w * dt
        for k in range(NARM): self.press[k] += w * dt
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos): return m
        d = pos - np.array(HUB); r = np.hypot(d[:, 0], d[:, 1]); th = np.arctan2(d[:, 1], d[:, 0])
        for k in range(NARM):
            if self.press[k] < PTH * (PTH1 / PTH) ** min(1, t / T_ZERO): continue
            a = self.body.angle + 2 * math.pi * k / NARM
            # leading side of the arm (rotation is +): ball just ahead of the edge, within the arm length
            da = (th - a) % (2 * math.pi)
            perp = r * np.sin(da)
            zone = (r > 40) & (r < ARM + 6) & (da < math.pi / 2) & (perp > 0) & (perp < BR + 12)
            if zone.any():
                idx = np.where(zone)[0]
                idx = idx[np.argsort(-r[idx])][:max(1, int(len(idx) * min(1, t / T_ZERO) ** KE))]
                m[idx] = True; self.press[k] = 0.0
        return m
    def spawn_xy(self, x0, y0, sgn):
        d = np.array([x0, y0]) - np.array(HUB); L = max(1.0, np.hypot(*d)); u = d / L
        n = np.array([-u[1], u[0]])
        p = np.array([x0, y0]) + n * sgn * BR * 1.05 - np.array([0, BR])
        q = p - np.array(JC); Lq = np.hypot(*q)
        if Lq > JR - BR - 4: p = np.array(JC) + q / Lq * (JR - BR - 4)
        return float(p[0]), float(p[1])
    def spawn_dir(self, x, y): return (0.0, -1.0)
    def fix_xy(self, x, y):
        q = np.array([x, y]) - np.array(JC); L = np.hypot(*q)
        if L > JR - BR - 4: q = q / L * (JR - BR - 4)
        return float(JC[0] + q[0]), float(JC[1] + q[1])
    def squash(self, x, y): return (1, 0)
    def state(self, t): return np.array([self.body.angle, omega(t), 0, 0], np.float32)
    def explode(self, space):
        for s in self.walls + self.arms: s.sensor = True
    def sounds(self): return [(0.05, "on")]
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); w = np.array([omega(q) for q in x[::441]]); w = np.repeat(w, 441)[:len(x)]
        ph = np.cumsum(60 + w * 22) / sr
        add(0, .07 * np.sin(2 * np.pi * ph) * (0.3 + w / W1) + .04 * np.sin(4 * np.pi * ph) * (w / W1)
            + .03 * np.convolve(rr.normal(0, 1, len(x)), np.ones(12) / 12, "same") * (w / W1))
    def draw(self, ctx, t, st, a=1.0, under=True):
        if under:
            # jar: glass ring + base housing
            ctx.rectangle(390, JC[1] + JR - 10, 300, 230); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
            hazard(ctx, 400, JC[1] + JR + 40, 280, 12, a)
            ctx.arc(JC[0], JC[1], JR + 4, 0, 2 * math.pi); ctx.set_source_rgba(.5, .52, .56, a); ctx.set_line_width(6); ctx.stroke()
            ctx.move_to(HUB[0] - 22, HUB[1]); ctx.line_to(HUB[0] + 22, HUB[1]); ctx.line_to(HUB[0] + 70, JC[1] + JR + 6); ctx.line_to(HUB[0] - 70, JC[1] + JR + 6)
            ctx.close_path(); ctx.set_source_rgba(.24, .25, .28, a); ctx.fill()
            return
        ang = float(st[0]); w = float(st[1])
        ctx.save(); ctx.translate(*HUB)
        # motion blur fan behind the arms when fast
        blur = min(1, w / W1)
        for k in range(NARM):
            aa = ang + 2 * math.pi * k / NARM
            if blur > .15:
                ctx.move_to(0, 0); ctx.arc_negative(0, 0, ARM, aa, aa - .9 * blur); ctx.close_path()
                ctx.set_source_rgba(.75, .77, .82, .12 * a * blur); ctx.fill()
            ctx.save(); ctx.rotate(aa)
            ctx.move_to(0, -14); ctx.curve_to(ARM * .4, -26, ARM * .8, -16, ARM + 2, 2); ctx.curve_to(ARM * .7, 8, ARM * .3, 10, 0, 14); ctx.close_path()
            ctx.set_source_rgba(.62, .64, .69, a); ctx.fill()
            ctx.move_to(ARM * .2, -12); ctx.curve_to(ARM * .5, -20, ARM * .8, -12, ARM - 4, 0); ctx.set_source_rgba(.88, .9, .93, a); ctx.set_line_width(2.5); ctx.stroke()
            ctx.restore()
        ctx.arc(0, 0, 26, 0, 2 * math.pi); ctx.set_source_rgba(.32, .33, .36, a); ctx.fill()
        ctx.arc(0, 0, 9, 0, 2 * math.pi); ctx.set_source_rgba(.6, .62, .66, a); ctx.fill()
        ctx.restore()

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((JC[0] - 40, 900), (40, 0)))
    main(Blender, "blender")
