import os as _os; WORK = _os.environ.get("WORK", "/tmp/vr"); _os.makedirs(WORK, exist_ok=True)
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pymunk, numpy as np
from base import *

NV = int(os.environ.get("NV", "1"))                       # number of V funnels across the floor
SLOT_Y = FLOOR - 60
TOP_Y = float(os.environ.get("TOPY", "1180"))
GAP = 14
S0, S1, SE = float(os.environ.get("S0", "30")), float(os.environ.get("S1", "1400")), float(os.environ.get("SE", "1.6"))
ZX, ZY = float(os.environ.get("ZX", "22")), float(os.environ.get("ZY", "16"))
SIGN = float(os.environ.get("SIGN", "1"))
CXS = [BX0 + (BX1 - BX0) * (k + 0.5) / NV for k in range(NV)]
PTH = float(os.environ.get('PTH', '60'))
ACT = [float(x) for x in os.environ.get("ACT", "14,0,18").split(",")][:NV]
HALF = (BX1 - BX0) / NV / 2
BELTS = []                                                 # (start top, end at slot)
for cx in CXS:
    BELTS.append(((cx - HALF + 2, TOP_Y), (cx - GAP / 2 - 12, SLOT_Y)))
    BELTS.append(((cx + HALF - 2, TOP_Y), (cx + GAP / 2 + 12, SLOT_Y)))
PINCH_Y = SLOT_Y - 4
_tan = (HALF - GAP / 2 - 12) / (SLOT_Y - TOP_Y)            # V opening per unit height
WMAX = float(os.environ.get("WMAX", "58"))                  # crush where the mouth is narrower than ~2 balls
H_CR = (WMAX - GAP) / 2 / _tan

def speed(t):
    u = min(1, t / T_ZERO); return S0 * (S1 / S0) ** (u ** SE)

class Belts(Mech):
    name = "belts"
    def build(self, space):
        self.segs = []
        for a, b in BELTS:
            s = pymunk.Segment(space.static_body, a, b, 12); s.friction = 1.4; s.elasticity = 0.3
            space.add(s); self.segs.append((s, a, b))
        self.pos = [0.0] * NV
        self.press = [0.0] * NV
        self.space = space; self.covers = {}
        for k, cx in enumerate(CXS):
            if ACT[k] > 0:
                c = pymunk.Segment(space.static_body, (cx - HALF + 6, TOP_Y - 14), (cx + HALF - 6, TOP_Y - 14), 9); c.friction = 0.2; c.elasticity = 0.5
                space.add(c); self.covers[k] = c
    def step(self, t, dt):
        v = speed(t)
        for k in list(self.covers):
            if t >= ACT[k]: self.space.remove(self.covers.pop(k))
        for i, (s, a, b) in enumerate(self.segs):
            k = i // 2; vv = v if t >= ACT[k] else 0.0
            if i % 2 == 0: self.pos[k] += min(vv, 700) * dt
            d = np.array(b) - np.array(a); d = d / np.linalg.norm(d)
            s.surface_velocity = (SIGN * -d[0] * vv, SIGN * -d[1] * vv)
    def crush(self, t, pos):
        m = np.zeros(len(pos), bool)
        dt = 1 / FPS / SUB
        for k, cx in enumerate(CXS):
            if t < ACT[k]: continue
            h = np.maximum(0, SLOT_Y - pos[:, 1])
            halfw = GAP / 2 + h * _tan
            zone = (h < H_CR) & (np.abs(pos[:, 0] - cx) < halfw + 2) & (pos[:, 1] < SLOT_Y + 30)
            if not zone.any(): continue
            # the belts have to chew through the ball: pressure builds with belt travel
            self.press[k] += speed(t) * dt
            if self.press[k] >= PTH:
                m |= zone; self.press[k] = 0.0
        return m
    def squash(self, x, y): return (0, 1)
    def state(self, t): return np.array(self.pos + [speed(t), t], np.float32)
    def explode(self, space):
        for s, a, b in self.segs: s.sensor = True
    def hum(self, add, tt, rr, sr):
        x = tt(T_ZERO); v = np.array([speed(q) for q in x[::441]]); v = np.repeat(v, 441)[:len(x)]
        nz = rr.normal(0, 1, len(x)); rum = np.convolve(nz, np.ones(20) / 20, "same")
        clack = (np.diff(np.floor(np.cumsum(v) / sr / 40), prepend=0) > 0).astype(float)
        k = np.exp(-np.arange(int(.02 * sr)) / sr * 150) * np.sin(2 * np.pi * 1400 * np.arange(int(.02 * sr)) / sr)
        add(0, .05 * rum * (v / S1) ** .5 + .06 * np.convolve(clack, k)[:len(x)] + .03 * np.sin(2 * np.pi * np.cumsum(45 + v / 30) / sr))
    def sounds(self): return [(x, "on") for x in ACT if x > 0]
    def draw(self, ctx, t, st, a=1.0):
        pos = 0.0
        # housing under the funnel
        for cx in CXS:
            ctx.move_to(cx - HALF, TOP_Y); ctx.line_to(cx - GAP / 2 - 12, SLOT_Y); ctx.line_to(cx + GAP / 2 + 12, SLOT_Y); ctx.line_to(cx + HALF, TOP_Y)
            ctx.line_to(cx + HALF, FLOOR + 200); ctx.line_to(cx - HALF, FLOOR + 200); ctx.close_path()
            ctx.set_source_rgba(.15, .16, .18, a); ctx.fill()
            ctx.rectangle(cx - GAP / 2, SLOT_Y, GAP, FLOOR - SLOT_Y + 200); ctx.set_source_rgba(.04, .04, .05, a); ctx.fill()
            hazard(ctx, cx - 40, FLOOR + 6, 80, 10, a)
        for bi, (p, q) in enumerate(BELTS):
            k = bi // 2; pos = float(st[k]); on = t >= ACT[k]
            p = np.array(p); q = np.array(q); d = q - p; L = np.linalg.norm(d); u = d / L; n = np.array([-u[1], u[0]])
            # belt body
            ctx.move_to(*(p)); ctx.line_to(*(q)); ctx.set_source_rgba(.2, .21, .23, a); ctx.set_line_width(26); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
            # moving tread marks (chevrons) that travel toward the slot
            ctx.save(); ctx.move_to(*p); ctx.line_to(*q); ctx.set_line_width(22); ctx.clip_preserve() if False else None; ctx.restore()
            spacing = 34
            off = pos % spacing
            k = 0
            while k * spacing + off < L:
                c = p + u * (k * spacing + off)
                ctx.move_to(*(c - n * 9)); ctx.line_to(*(c + u * 6)); ctx.line_to(*(c + n * 9))
                ctx.set_source_rgba(.55, .57, .62, a) if on else ctx.set_source_rgba(.35, .36, .4, a); ctx.set_line_width(3); ctx.stroke()
                k += 1
            # pulleys at both ends
            for e, sgn in ((p, 1), (q, -1)):
                ctx.save(); ctx.translate(*e); ctx.rotate(pos / 16)
                ctx.arc(0, 0, 16, 0, 2 * math.pi); ctx.set_source_rgba(.5, .52, .56, a); ctx.fill()
                ctx.move_to(-12, 0); ctx.line_to(12, 0); ctx.move_to(0, -12); ctx.line_to(0, 12); ctx.set_source_rgba(.25, .26, .28, a); ctx.set_line_width(4); ctx.stroke()
                ctx.restore()
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        for k, cx in enumerate(CXS):
            if ACT[k] <= 0: continue
            u = min(1, max(0, (t - ACT[k] + 0.35) / 0.35))
            if u < 1:
                w = 2 * HALF - 12; x0 = cx - w / 2 + (w + 30) * u * (1 if cx > 540 else -1)
                ctx.save(); ctx.rectangle(cx - HALF + 4, TOP_Y - 40, 2 * HALF - 8, 60); ctx.clip()
                ctx.rectangle(x0, TOP_Y - 22, w, 16); ctx.set_source_rgba(.4, .42, .46, a); ctx.fill(); hazard(ctx, x0, TOP_Y - 22, w, 6, a)
                ctx.restore()

if __name__ == "__main__":
    import base
    _r = base.run
    base.run = lambda m, seed, record=True: _r(m, seed, record, start=((CXS[len(CXS) // 2] - 60, 900), (30, 0)))
    main(Belts, "belts")
