"""Per-video visual style (shape of the objects, background, counter label).
Chosen by make.py and passed in the STYLE env var as JSON, e.g. {"shape":"tri","bg":"navy"}.
Physics stays circular; only the look changes. Non-round shapes roll: angle follows x."""
import os, json, math
import cairo
import numpy as np

S = json.loads(os.environ.get("STYLE", "{}") or "{}")
SHAPE = S.get("shape", "circle")
BGS = {"char": (.075, .08, .09), "navy": (.06, .07, .13), "plum": (.10, .06, .11),
       "forest": (.05, .09, .08), "sand": (.93, .90, .84), "slate": (.15, .17, .20)}
BG = BGS.get(S.get("bg", "char"), BGS["char"])
LIGHT = sum(BG) > 1.5                                   # light background -> dark text
LABELS = {"circle": "КУЛЬОК", "tri": "ТРИКУТНИКІВ", "square": "КУБИКІВ", "ring": "КІЛЕЦЬ",
          "hex": "ГАЙОК", "star": "ЗІРОК", "pill": "ПІГУЛОК"}
LABEL = LABELS.get(SHAPE, "ШТУК")
SHAPES = list(LABELS)
BG_NAMES = list(BGS)

def ink(a=1.0):
    return (0.1, 0.1, 0.12, a) if LIGHT else (1, 1, 1, a)

def path(x, r, shape=None):
    shape = shape or SHAPE
    if shape == "circle" or shape == "ring":
        x.arc(0, 0, r, 0, 2 * math.pi)
    elif shape in ("tri", "square", "hex"):
        n = {"tri": 3, "square": 4, "hex": 6}[shape]; rr = r * {"tri": 1.28, "square": 1.12, "hex": 1.05}[shape]
        off = -math.pi / 2 if n == 3 else (math.pi / 4 if n == 4 else 0)
        for k in range(n):
            a = off + 2 * math.pi * k / n; (x.move_to if k == 0 else x.line_to)(rr * math.cos(a), rr * math.sin(a))
        x.close_path()
    elif shape == "star":
        for k in range(10):
            a = -math.pi / 2 + math.pi * k / 5; q = r * (1.3 if k % 2 == 0 else .62)
            (x.move_to if k == 0 else x.line_to)(q * math.cos(a), q * math.sin(a))
        x.close_path()
    elif shape == "pill":
        w = r * .62
        x.arc(-r * .45, 0, w, math.pi / 2, 3 * math.pi / 2); x.arc(r * .45, 0, w, -math.pi / 2, math.pi / 2); x.close_path()

_SPR = {}
def sprite(c, glow, BR):
    key = (tuple(np.round(c, 3)), round(float(glow), 1))
    if key in _SPR: return _SPR[key]
    N = int(BR * 2 * 1.4 + 8); s = cairo.ImageSurface(cairo.FORMAT_ARGB32, N, N); x = cairo.Context(s)
    r, g, b = key[0]; x.translate(N / 2, N / 2)
    path(x, BR); x.set_source_rgb(r * .78, g * .78, b * .78); x.fill()
    x.save(); x.scale((BR - 2.4) / BR, (BR - 2.4) / BR); path(x, BR); x.restore()
    x.set_source_rgb(r, g, b); x.fill()
    if SHAPE == "ring":
        x.arc(0, 0, BR * .45, 0, 2 * math.pi); x.set_source_rgb(r * .78, g * .78, b * .78); x.fill()
        x.set_operator(cairo.OPERATOR_CLEAR); x.arc(0, 0, BR * .45 - 2.2, 0, 2 * math.pi); x.fill(); x.set_operator(cairo.OPERATOR_OVER)
    if key[1] > 0:
        x.save(); x.scale((BR - 2.4) / BR, (BR - 2.4) / BR); path(x, BR); x.restore()
        x.set_source_rgba(1, 1, 1, .45 * key[1]); x.fill()
    _SPR[key] = s; return s

def put(ctx, c, glow, x, y, i, BR):
    """draw object i at (x,y); polygons roll with their x position"""
    s = sprite(c, glow, BR); o = s.get_width() / 2
    if SHAPE in ("circle", "ring"):
        ctx.set_source_surface(s, x - o, y - o); ctx.paint(); return
    ctx.save(); ctx.translate(x, y); ctx.rotate(x / BR * .8 + i * 1.7)
    ctx.set_source_surface(s, -o, -o); ctx.paint(); ctx.restore()
