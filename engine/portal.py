import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
"""Portal pegboard (NEW mechanism 2026-11-27 09:47): a V funnel floor rolls everything into a glowing green IN-portal at the
bottom. Every shape that sinks into it comes out of the violet OUT-portal at the top as TWO (one rule), and falls back down
through a plinko pegboard into the funnel. The IN-portal needs a moment to recharge at first (slow start), later it swallows
shapes almost continuously -> waterfall. Continuous, self-feeding, nothing reverses."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
import base
from base import *

PX, PY_ = 540.0, FLOOR - 22                     # IN portal centre (bottom)
OX, OY = 540.0, float(os.environ.get("OY", "650"))  # OUT portal centre (top)
PW = float(os.environ.get("PW", "70"))          # IN portal half width
FUN_Y = float(os.environ.get("FUN_Y", "1400"))  # funnel walls start height at the tank sides
PEG0, PEG1 = float(os.environ.get("PEG0", "800")), float(os.environ.get("PEG1", "1280"))
PEGDX, PEGDY = float(os.environ.get("PEGDX", "124")), float(os.environ.get("PEGDY", "96"))
PEGR = float(os.environ.get("PEGR", "10"))
CH0, CH1 = float(os.environ.get("CH0", "1.1")), float(os.environ.get("CH1", "0.012"))
base.MAXN = int(os.environ.get("MAXN", "760"))

def u_(t): return min(1, t / T_ZERO)
def recharge(t): return CH0 * (CH1 / CH0) ** (u_(t) ** float(os.environ.get("CE", "0.7")))

class Portal(Mech):
    name = "portal"
    def __init__(self):
        self.pegs = []; r = 0; y = PEG0
        while y <= PEG1:
            x = BX0 + 60 + (0 if r % 2 == 0 else PEGDX / 2)
            while x < BX1 - 50:
                if not (r == 0 and abs(x - OX) < 40): self.pegs.append((x, y))   # drop line under OUT open on row 0
                x += PEGDX
            y += PEGDY; r += 1
    def build(self, space):
        self.space = space; self.segs = []
        for p, q in (((BX0, FUN_Y), (PX - PW - 4, FLOOR - 4)), ((BX1, FUN_Y), (PX + PW + 4, FLOOR - 4))):
            s = pymunk.Segment(space.static_body, p, q, 8); s.friction = 0.05; s.elasticity = 0.2; space.add(s); self.segs.append(s)
        for (x, y) in self.pegs:
            c = pymunk.Circle(space.static_body, PEGR, (x, y)); c.elasticity = 0.55; c.friction = 0.2
            space.add(c); self.segs.append(c)
        self.charge = 9.0; self.flash = -9.0; self.out = -9.0
    def step(self, t, dt):
        self.charge += dt
        for b in self.space.bodies:                # nudge shapes resting at the funnel bottom into the portal mouth
            if b.body_type != pymunk.Body.DYNAMIC: continue
            x, y = b.position
            if y > FLOOR - 90 and abs(x - PX) < PW + 60 and abs(b.velocity.x) < 60:
                b.velocity = ((PX - x) * 4, b.velocity.y)
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        if not len(pos) or self.charge < recharge(t): return m
        zone = (pos[:, 1] > PY_ - 26) & (np.abs(pos[:, 0] - PX) < PW)
        if zone.any():
            idx = np.where(zone)[0]
            m[idx[:1 + int(len(idx) * u_(t) * 0.5)]] = True
            self.charge = 0.0; self.flash = t
        return m
    def spawn_xy(self, x0, y0, sgn):
        self.out = self._t if hasattr(self, "_t") else 0
        return OX + sgn * BR * 1.2, OY + 10
    def fix_xy(self, x, y): return x, max(y, BY0 + BR + 2)
    def spawn_dir(self, x, y): return (0.0, 0.15)
    def squash(self, x, y): return (0, 1)
    def state(self, t):
        self._t = t
        return np.array([self.flash, self.out, recharge(t), 0], np.float32)
    def explode(self, space):
        for s in self.segs: s.sensor = True
    def sounds(self): return [(0.3, "on")]
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); e = np.repeat(np.array([u_(q) for q in x[::441]]), 441)[:len(x)]
        add(0, .05 * np.sin(2 * np.pi * np.cumsum(55 + e * 50) / sr) * (0.4 + e) + .02 * np.sin(2 * np.pi * np.cumsum(110 + e * 100) / sr))
    def _ring(self, ctx, x, y, w, col, a, g, front):
        ctx.save(); ctx.translate(x, y); ctx.scale(1, .26)
        if front: ctx.arc(0, 0, w, 0, math.pi)
        else: ctx.arc(0, 0, w, math.pi, 2 * math.pi)
        ctx.restore(); ctx.set_source_rgba(*col, a); ctx.set_line_width(10 + 5 * g); ctx.stroke()
    def draw(self, ctx, t, st, a=1.0, under=True):
        fl, ot = float(st[0]), float(st[1])
        g = max(0.0, 1 - (t - fl) / .25); go = max(0.0, 1 - (t - ot) / .25)
        GR, VI = (.3, .95, .45), (.75, .45, 1.0)
        if under:
            ctx.move_to(BX0, FUN_Y); ctx.line_to(PX - PW - 4, FLOOR - 4); ctx.line_to(PX + PW + 4, FLOOR - 4); ctx.line_to(BX1, FUN_Y)
            ctx.line_to(BX1, FLOOR + 200); ctx.line_to(BX0, FLOOR + 200); ctx.close_path(); ctx.set_source_rgba(.17, .18, .2, a); ctx.fill()
            # IN portal disc (glowing hole)
            ctx.save(); ctx.translate(PX, PY_); ctx.scale(1, .26); ctx.arc(0, 0, PW + 10, 0, 2 * math.pi); ctx.restore()
            ctx.set_source_rgba(*GR, (.25 + .45 * g) * a); ctx.fill()
            self._ring(ctx, PX, PY_, PW + 10, GR, (.6 + .3 * g) * a, g, False)
            # OUT portal disc + back rim
            ctx.save(); ctx.translate(OX, OY); ctx.scale(1, .26); ctx.arc(0, 0, 80, 0, 2 * math.pi); ctx.restore()
            ctx.set_source_rgba(*VI, (.22 + .4 * go) * a); ctx.fill()
            self._ring(ctx, OX, OY, 80, VI, (.6 + .3 * go) * a, go, False)
            # pegs
            for (x, y) in self.pegs:
                ctx.arc(x, y, PEGR, 0, 2 * math.pi); ctx.set_source_rgba(.62, .64, .68, a); ctx.fill()
            return
        self._ring(ctx, PX, PY_, PW + 10, GR, a, g, True)
        self._ring(ctx, OX, OY, 80, VI, a, go, True)
        text(ctx, "IN", PX + PW + 70, PY_ - 4, 34, (*GR, .95 * a), cairo.FONT_WEIGHT_BOLD)
        text(ctx, "OUT ×2", OX + 175, OY + 12, 40, (*VI, .95 * a), cairo.FONT_WEIGHT_BOLD)

if __name__ == "__main__":
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((540, 700), (40, 0)))
    main(Portal, "portal")
