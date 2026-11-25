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
# English on-screen text (council 2026-11-24: ~99% of views are global non-followers)
LABELS = {"circle": "BALLS", "tri": "TRIANGLES", "square": "CUBES", "ring": "RINGS",
          "hex": "HEX NUTS", "star": "STARS", "pill": "PILLS"}
LABEL = LABELS.get(SHAPE, "OBJECTS")
EP = os.environ.get("EP", "")
if not EP:   # episode number = next row of posts.csv (one data row per published reel)
    try:
        import csv as _csv
        EP = str(sum(1 for _ in _csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "posts.csv")))) + 1)
    except Exception:
        EP = ""
LAST = [0]          # renderers store the live count here; the end card shows the final one
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


FIRST = [int(os.environ.get("N0", "1"))]   # start count (bumpers race: N0=2); count on the first frame (for the opening bet and "from N" on the end card)
ONE = LABEL[:-1] if LABEL.endswith("S") else LABEL

def opener(ctx, t, text, dur=2.6):
    """Council 2026-11-25 (D3): the first frame states the bet, so the empty start reads as a challenge, not a diagram."""
    if t >= dur: return
    a = 1.0 if t < dur - .5 else max(0.0, (dur - t) / .5)
    n = FIRST[0]
    W, y = 540, 700
    ctx.set_source_rgba(*BG, .78 * a); ctx.rectangle(110, y - 95, 860, 190); ctx.fill()
    text(ctx, f"{n} {ONE if n == 1 else LABEL}. ONE RULE.", W, y - 18, 58, ink(a), cairo.FONT_WEIGHT_BOLD, 2)
    text(ctx, "HOW MANY AT 0:00?", W, y + 58, 50, (1, .72, .25, a), cairo.FONT_WEIGHT_BOLD, 4)

def endcard(ctx, t, T_END, text, dur=1.5):
    """Council 2026-11-24: replace the black fade with an end card (final count + follow CTA) over the full tank."""
    opener(ctx, t, text)
    t0 = T_END - dur
    if t <= t0: return
    a = min(1.0, (t - t0) / .25)
    ctx.set_source_rgba(*BG, .82 * a); ctx.paint()
    W = 540
    if EP: text(ctx, f"EPISODE {EP}", W, 640, 34, ink(.55 * a), cairo.FONT_WEIGHT_BOLD, 8)
    text(ctx, "FINAL COUNT", W, 760, 40, ink(.7 * a), cairo.FONT_WEIGHT_NORMAL, 8)
    text(ctx, f"{LAST[0]}", W, 920, 170, ink(a), cairo.FONT_WEIGHT_BOLD, 2)
    text(ctx, LABEL, W, 1000, 40, ink(.7 * a), cairo.FONT_WEIGHT_NORMAL, 8)
    text(ctx, f"from {FIRST[0]} in 30 seconds", W, 1070, 40, ink(.8 * a), cairo.FONT_WEIGHT_NORMAL, 2)
    text(ctx, "Did you guess it?", W, 1170, 52, ink(.95 * a), cairo.FONT_WEIGHT_BOLD, 0)
    text(ctx, "NEW SIMULATION EVERY FEW HOURS", W, 1300, 36, (1, .72, .25, a), cairo.FONT_WEIGHT_BOLD, 6)
    text(ctx, "FOLLOW @CRUSH.MULTIPLY", W, 1360, 36, (1, .72, .25, a), cairo.FONT_WEIGHT_BOLD, 6)
