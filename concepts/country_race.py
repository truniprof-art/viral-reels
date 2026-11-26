"""CONCEPT TRACK (D7): COUNTRY RACE — 8 flag-coloured marbles race down a zig-zag track (real pymunk physics, seed chosen
only for a readable race). Live standings, honest finish order, comment loop: 'comment your country — the most requested
race in the next race'. Usage: python3 country_race.py sim SEED | render SEED OUT.mp4   (env RACE=1, EP=24, TEAMS=...)"""
import pymunk, math, random, sys, os, json, subprocess
import numpy as np, cairo

W, H, FPS = 1080, 1920, 30
T_GO, T_RACE_END, T_END = 1.4, 30.0, 33.0
R = 36
NR = int(os.environ.get("NRAMPS", "13"))
DROP = int(os.environ.get('DROP', '150'))
GAP = int(os.environ.get('GAP', '380'))                       # vertical distance between ramps
TOP = 420
SNAPS = [float(q) for q in os.environ.get('SNAPS', '').split(',') if q]
RACE = os.environ.get("RACE", "1")
EP = os.environ.get("EP", "")
TEAMS = os.environ.get("TEAMS", "USA,BRA,IND,GER,JPN,UKR,FRA,NGA").split(",")
BG = (.06, .07, .13)
INK = (1, 1, 1)
GOLD = (1, .72, .25)

# ---- flags: simplified, emblem-free colour designs (honest stylisation) -------------------------
def bands(c, r, cols, vertical=False, weights=None):
    weights = weights or [1] * len(cols); tot = sum(weights); p = -r
    for col, w in zip(cols, weights):
        s = 2 * r * w / tot; c.set_source_rgb(*col)
        (c.rectangle(p, -r, s + .5, 2 * r) if vertical else c.rectangle(-r, p, 2 * r, s + .5)); c.fill(); p += s
RED, WHITE, BLUE, GREEN = (.82, .12, .17), (.96, .96, .96), (.0, .22, .55), (.0, .55, .27)
def flag(c, code, r):
    if code == "USA":
        bands(c, r, [RED, WHITE] * 3 + [RED]); c.set_source_rgb(.12, .2, .45); c.rectangle(-r, -r, r * 1.05, r * 1.0); c.fill()
        c.set_source_rgb(*WHITE)
        for i in range(3):
            for j in range(3): c.arc(-r + r * .2 + i * r * .32, -r + r * .2 + j * r * .3, r * .06, 0, 7); c.fill()
    elif code == "BRA":
        c.set_source_rgb(0, .6, .26); c.paint() if False else (c.rectangle(-r, -r, 2 * r, 2 * r), c.fill())
        c.set_source_rgb(1, .85, 0); c.move_to(-r * .9, 0); c.line_to(0, -r * .62); c.line_to(r * .9, 0); c.line_to(0, r * .62); c.close_path(); c.fill()
        c.set_source_rgb(0, .15, .45); c.arc(0, 0, r * .36, 0, 7); c.fill()
    elif code == "IND":
        bands(c, r, [(1, .6, .2), WHITE, (.07, .53, .03)]); c.set_source_rgb(0, 0, .5); c.set_line_width(r * .07); c.arc(0, 0, r * .22, 0, 7); c.stroke()
    elif code == "GER": bands(c, r, [(.1, .1, .1), (.87, 0, 0), (1, .8, 0)])
    elif code == "JPN":
        c.set_source_rgb(*WHITE); c.rectangle(-r, -r, 2 * r, 2 * r); c.fill(); c.set_source_rgb(.74, 0, .18); c.arc(0, 0, r * .45, 0, 7); c.fill()
    elif code == "UKR": bands(c, r, [(0, .36, .73), (1, .84, 0)])
    elif code == "FRA": bands(c, r, [(0, .14, .58), WHITE, (.93, .16, .22)], True)
    elif code == "NGA": bands(c, r, [(0, .53, .32), WHITE, (0, .53, .32)], True)
    elif code == "ITA": bands(c, r, [(0, .57, .27), WHITE, (.81, .17, .21)], True)
    elif code == "IRL": bands(c, r, [(.09, .61, .38), WHITE, (1, .53, .24)], True)
    elif code == "POL": bands(c, r, [WHITE, (.86, .08, .24)])
    elif code == "NLD": bands(c, r, [(.68, .11, .16), WHITE, (.13, .28, .55)])
    elif code == "IDN": bands(c, r, [(1, 0, 0), WHITE])
    elif code == "COL": bands(c, r, [(1, .8, 0), (0, .22, .58), (.81, .07, .15)], weights=[2, 1, 1])
    elif code == "ARG":
        bands(c, r, [(.45, .67, .87), WHITE, (.45, .67, .87)]); c.set_source_rgb(.96, .7, .05); c.arc(0, 0, r * .16, 0, 7); c.fill()
    elif code == "CAN":
        bands(c, r, [RED, WHITE, WHITE, RED], True); c.set_source_rgb(*RED); c.arc(0, 0, r * .25, 0, 7); c.fill()
    else:
        h = (sum(map(ord, code)) % 12) / 12; import colorsys; c.set_source_rgb(*colorsys.hsv_to_rgb(h, .7, .9)); c.rectangle(-r, -r, 2 * r, 2 * r); c.fill()

def ball_sprite(code, r=R):
    N = int(2 * r + 8); s = cairo.ImageSurface(cairo.FORMAT_ARGB32, N, N); c = cairo.Context(s); c.translate(N / 2, N / 2)
    c.arc(0, 0, r, 0, 7); c.set_source_rgb(.04, .04, .06); c.fill()
    c.save(); c.arc(0, 0, r - 3, 0, 7); c.clip(); flag(c, code, r - 3); c.restore()
    c.arc(0, 0, r - 3, 0, 7); c.set_source_rgba(1, 1, 1, .9); c.set_line_width(3); c.stroke()
    return s

# ---- world -------------------------------------------------------------------------------------
def ramp_y(i): return TOP + 260 + i * GAP
FINISH_Y = ramp_y(NR - 1) + 250
def build(seed):
    rnd = random.Random(seed)
    sp = pymunk.Space(); sp.gravity = (0, float(os.environ.get('G', '2200'))); sp.iterations = 20
    st = sp.static_body; segs = []; deco = []
    def seg(a, b, w=10, e=.35, f=.6):
        s = pymunk.Segment(st, a, b, w / 2); s.elasticity = e; s.friction = f; sp.add(s); segs.append((a, b, w))
    seg((20, 0), (20, FINISH_Y + 400), 24); seg((1060, 0), (1060, FINISH_Y + 400), 24)
    # start box with a gate
    seg((1060, TOP + 90), (190, TOP + 120), 12)
    gate = pymunk.Segment(st, (200, TOP + 30), (200, TOP + 115), 6); gate.elasticity = .3; sp.add(gate)
    for i in range(NR):
        y = ramp_y(i); drop = DROP
        if i % 2 == 0: a, b = (20, y), (860, y + drop)
        else: a, b = (1060, y), (220, y + drop)
        seg(a, b, 12)
        # bumps on the ramp (small pegs) and mid-air bumpers in the drop zones
        for k in range(rnd.choice([0, 1, 1])):
            u = rnd.uniform(.25, .8); px = a[0] + (b[0] - a[0]) * u; py = a[1] + (b[1] - a[1]) * u - 8
            p = pymunk.Circle(st, rnd.choice([6, 7]), (px, py)); p.elasticity = .5; p.friction = .4; sp.add(p); deco.append(("peg", px, py, p.radius))
        if i < NR - 1:
            bx = (960 if i % 2 == 0 else 120) + rnd.uniform(-25, 25)
            yn = ramp_y(i + 1); nx0 = 1060 if i % 2 == 0 else 20; nx1 = 220 if i % 2 == 0 else 860
            by = yn + DROP * (bx - nx0) / (nx1 - nx0) - 140
            pass
    seg((20, FINISH_Y + 120), (1060, FINISH_Y + 120), 12, e=.1, f=.9)
    # spinners (kinematic bars) on 3 ramps
    spins = []
    for i in rnd.sample(range(1, NR - 1), 4):
        y = ramp_y(i); cx = 540 + rnd.uniform(-120, 120); cy = y - 95 + (cx - (20 if i % 2 == 0 else 1060)) * 0 + 0
        # place above the ramp line at cx
        a, b = ((20, y), (860, y + DROP)) if i % 2 == 0 else ((1060, y), (220, y + DROP))
        u = (cx - a[0]) / (b[0] - a[0]); ry = a[1] + (b[1] - a[1]) * u; cy = ry - 120
        kb = pymunk.Body(body_type=pymunk.Body.KINEMATIC); kb.position = (cx, cy); kb.angular_velocity = (-1 if i % 2 == 0 else 1) * rnd.uniform(2.4, 3.4)
        L = 92; sh = pymunk.Segment(kb, (-L, 0), (L, 0), 9); sh.elasticity = .6; sh.friction = .5; sp.add(kb, sh); spins.append((kb, L))
    balls = []; slots = list(range(len(TEAMS))); rnd.shuffle(slots)   # random start order (fair: no fixed pole position)
    for k, code in enumerate(TEAMS):
        b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, R)); b.position = (250 + slots[k] * 100 + rnd.uniform(-6, 6), TOP + 40 - (slots[k] % 2) * 40)
        c = pymunk.Circle(b, R); c.elasticity = .45; c.friction = .5; sp.add(b, c); balls.append(b)
    return sp, gate, balls, segs, deco, spins

def progress(b):
    """track progress: ramp index + fraction along it (higher = further)."""
    x, y = b.position
    if y >= FINISH_Y: return 1000 + y
    i = int((y - ramp_y(0) + GAP * .5) // GAP); i = max(-1, min(NR - 1, i))
    if i < 0: return -1 + x / 1080
    f = x / 1080 if i % 2 == 0 else 1 - x / 1080
    return i + f + (y - ramp_y(i)) / 1e4

def simulate(seed):
    sp, gate, balls, segs, deco, spins = build(seed)
    dt = 1 / FPS / 8; frames = []; fin = {}; t = 0.0; sounds = []
    nF = int(T_END * FPS)
    hits = {}
    h = sp.add_collision_handler(0, 0) if hasattr(sp, "add_collision_handler") else None
    for f in range(nF):
        for _ in range(8):
            if t >= T_GO and gate in sp.shapes: sp.remove(gate); sounds.append((t, "gate"))
            if t < T_RACE_END: sp.step(dt)
            t += dt
            for k, b in enumerate(balls):
                if k not in fin and b.position.y > FINISH_Y: fin[k] = t; sounds.append((t, "fin%d" % len(fin)))
        # bounce clicks from speed changes
        st = [(b.position.x, b.position.y, b.angle) for b in balls]
        if frames:
            for k, b in enumerate(balls):
                vx, vy = b.velocity; pv = frames[-1]["v"][k]
                if abs(vx - pv[0]) + abs(vy - pv[1]) > 260: sounds.append((t, "tick%d" % k))
        frames.append({"b": st, "v": [tuple(b.velocity) for b in balls], "s": [(kb.angle) for kb, L in spins], "p": [progress(b) for b in balls]})
    order = sorted(fin, key=fin.get)
    return frames, fin, order, (segs, deco, [(kb.position.x, kb.position.y, L) for kb, L in spins]), sounds

def standings(fr, fin, t):
    done = sorted([k for k in fin if fin[k] <= t], key=fin.get)
    rest = sorted([k for k in range(len(TEAMS)) if k not in done], key=lambda k: -fr["p"][k])
    return done + rest, len(done)

def score(seed):
    frames, fin, order, _, _ = simulate(seed)
    if len(fin) < 3: return None
    t1 = fin[order[0]]; t3 = fin[order[2]]
    leads = []; last = None
    for i, fr in enumerate(frames):
        t = i / FPS
        if t < 4 or t > t1: continue
        L = max(range(len(TEAMS)), key=lambda k: fr["p"][k])
        if L != last: leads.append((round(t, 1), TEAMS[L])); last = L
    return dict(seed=seed, t1=round(t1, 2), t3=round(t3, 2), nfin=len(fin), winner=TEAMS[order[0]], lead_changes=len(leads) - 1, late=[l for l in leads if l[0] > 18], margin=round(fin[order[1]] - t1, 2))

# ---- render ------------------------------------------------------------------------------------
def text(c, s, x, y, size, rgba, bold=True, track=0, anchor="c"):
    c.select_font_face("Fira Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL); c.set_font_size(size)
    w = c.text_extents(s).x_advance + track * (len(s) - 1)
    x0 = x - w / 2 if anchor == "c" else (x if anchor == "l" else x - w)
    c.set_source_rgba(*rgba)
    for ch in s:
        c.move_to(x0, y); c.show_text(ch); x0 += c.text_extents(ch).x_advance + track

def render(seed, out):
    frames, fin, order, (segs, deco, spins), sounds = simulate(seed)
    spr = [ball_sprite(code) for code in TEAMS]; mini = [ball_sprite(code, 20) for code in TEAMS]
    camy = None
    if SNAPS: ff = None
    else: ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", out + ".v.mp4"], stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for i, fr in enumerate(frames):
        t = i / FPS; c = cairo.Context(surf)
        c.set_source_rgb(*BG); c.paint()
        # camera: follow the leader (smooth), keep within world
        rank, nd = standings(fr, fin, t)
        lead = rank[0] if nd == 0 else rank[min(nd, len(rank) - 1)] if t < T_RACE_END and nd < 3 else rank[0]
        ly = fr["b"][rank[0]][1] if nd == 0 else fr["b"][rank[min(nd, 2)]][1]
        target = min(max(ly - 900, 0), FINISH_Y + 260 - H)
        camy = target if camy is None else camy + (target - camy) * .08
        c.save(); c.translate(0, -camy)
        # finish line (checker)
        for q in range(27):
            for r_ in range(2):
                c.set_source_rgb(*( (1, 1, 1) if (q + r_) % 2 == 0 else (.1, .1, .12))); c.rectangle(32 + q * 38, FINISH_Y + r_ * 19, 38, 19); c.fill()
        text(c, "FINISH", 540, FINISH_Y + 100, 60, (*GOLD, 1), True, 10)
        for (a, b, w) in segs:
            c.set_source_rgb(.78, .8, .86); c.set_line_width(w); c.set_line_cap(cairo.LINE_CAP_ROUND); c.move_to(*a); c.line_to(*b); c.stroke()
        if t < T_GO:
            c.set_source_rgb(*GOLD); c.set_line_width(8); c.move_to(200, TOP + 30); c.line_to(200, TOP + 115); c.stroke()
        for kind, x, y, r in deco:
            c.arc(x, y, r, 0, 7); c.set_source_rgb(*((.95, .35, .5) if kind == "bump" else (.6, .62, .7))); c.fill()
        for (x, y, L), ang in zip(spins, fr["s"]):
            c.save(); c.translate(x, y); c.rotate(ang); c.set_source_rgb(*GOLD); c.set_line_width(18); c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.move_to(-L, 0); c.line_to(L, 0); c.stroke(); c.arc(0, 0, 10, 0, 7); c.set_source_rgb(.2, .2, .25); c.fill(); c.restore()
        for k in sorted(range(len(TEAMS)), key=lambda k: -rank.index(k)):
            x, y, a = fr["b"][k]; s = spr[k]; o = s.get_width() / 2
            c.save(); c.translate(x, y); c.rotate(a); c.set_source_surface(s, -o, -o); c.paint(); c.restore()
            text(c, TEAMS[k], x, y - R - 12, 28, (1, 1, 1, .95), True, 1)
        c.restore()
        # HUD: title + live standings
        c.set_source_rgba(*BG, .88); c.rectangle(0, 0, W, 250); c.fill()
        text(c, f"COUNTRY RACE #{RACE}", 540, 70, 54, (*GOLD, 1), True, 4)
        for j, k in enumerate(rank):
            x = 75 + j * 133; y = 160
            s = mini[k]; c.set_source_surface(s, x - s.get_width() / 2, y - s.get_height() / 2 - 8); c.paint()
            text(c, f"{j + 1}", x, y - 42, 24, (1, 1, 1, .6), True)
            text(c, TEAMS[k], x, y + 44, 26, ((*GOLD, 1) if j == 0 else (1, 1, 1, .9)), True)
        rem = max(0, T_RACE_END - t); text(c, f"0:{int(math.ceil(rem)):02d}", 1000, 70, 40, (1, 1, 1, .7), True, 0)
        # opener bet (0–2.6 s)
        if t < 2.6:
            a = 1 if t < 2.1 else (2.6 - t) / .5
            c.set_source_rgba(*BG, .82 * a); c.rectangle(90, 640, 900, 230); c.fill()
            text(c, "8 COUNTRIES. 1 WINNER.", 540, 730, 64, (1, 1, 1, a), True, 2)
            text(c, "PICK YOURS BEFORE THE GATE OPENS", 540, 815, 38, (*GOLD, a), True, 2)
        # mid follow cue 12–14.2 s
        if 12 <= t < 14.2:
            u = t - 12; a = min(1, u / .25, (2.2 - u) / .3)
            c.set_source_rgba(*GOLD, .93 * a); c.rectangle(110, 1712, 860, 110); c.fill()
            text(c, "FOLLOW @CRUSH.MULTIPLY", 540, 1762, 42, (.08, .08, .1, a), True, 4)
            text(c, "comment your country — it can race next", 540, 1804, 30, (.08, .08, .1, .85 * a), False, 1)
        # finish flash banners
        for p, k in enumerate(sorted(fin, key=fin.get)[:3]):
            if fin[k] <= t < fin[k] + 1.6 and t < T_RACE_END:
                a = min(1, (fin[k] + 1.6 - t) / .4)
                y0 = 1000 + p * 120; c.set_source_rgba(*BG, .8 * a); c.rectangle(240, y0 - 85, 600, 110); c.fill()
                text(c, ["1ST", "2ND", "3RD"][p] + "  " + TEAMS[k], 540, y0, 84, ((*GOLD, a) if p == 0 else (1, 1, 1, a)), True, 4)
        # end card
        if t >= T_RACE_END:
            a = min(1, (t - T_RACE_END) / .3)
            c.set_source_rgba(*BG, .9 * a); c.paint()
            if EP: text(c, f"EPISODE {EP} · COUNTRY RACE #{RACE}", 540, 330, 32, (1, 1, 1, .55 * a), True, 4)
            text(c, "WINNER", 540, 430, 44, (1, 1, 1, .75 * a), True, 10)
            big = ball_sprite(TEAMS[order[0]], 120); c.set_source_surface(big, 540 - big.get_width() / 2, 470); c.paint_with_alpha(a)
            text(c, TEAMS[order[0]], 540, 800, 110, (*GOLD, a), True, 6)
            for p in (1, 2):
                k = order[p]; s = ball_sprite(TEAMS[k], 40); x = 300 if p == 1 else 700
                c.set_source_surface(s, x - 150, 870); c.paint_with_alpha(a)
                text(c, f"{p + 1}{'ND' if p == 1 else 'RD'} {TEAMS[k]}", x - 50, 928, 44, (1, 1, 1, .9 * a), True, 2, "l")
            text(c, "Did your pick win?", 540, 1060, 54, (1, 1, 1, a), True)
            c.set_source_rgba(*GOLD, a); c.rectangle(80, 1130, 920, 330); c.fill()
            text(c, "COMMENT YOUR COUNTRY", 540, 1215, 58, (.08, .08, .1, a), True, 3)
            text(c, "the most requested ones race in", 540, 1280, 38, (.08, .08, .1, a), False, 1)
            text(c, f"COUNTRY RACE #{int(RACE) + 1} — TOMORROW", 540, 1340, 46, (.08, .08, .1, a), True, 2)
            text(c, "FOLLOW @CRUSH.MULTIPLY", 540, 1420, 46, (.08, .08, .1, a), True, 4)
        if SNAPS:
            if any(abs(t - q) < .5 / FPS for q in SNAPS): surf.write_to_png(f"{out}_{t:05.1f}.png")
            continue
        ff.stdin.write(bytes(surf.get_data()))
    if SNAPS: return
    ff.stdin.close(); assert ff.wait() == 0
    audio(sounds, fin, order, out + ".wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out + ".v.mp4", "-i", out + ".wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    os.remove(out + ".v.mp4"); os.remove(out + ".wav")
    print(json.dumps({"winner": TEAMS[order[0]], "order": [TEAMS[k] for k in order], "times": {TEAMS[k]: round(v, 2) for k, v in fin.items()}}))

def audio(sounds, fin, order, path):
    import wave
    sr = 44100; n = int(T_END * sr); y = np.zeros(n); rr = np.random.default_rng(3)
    def tt(d): return np.arange(int(d * sr)) / sr
    def add(at, s):
        i = int(at * sr); e = min(len(s), n - i)
        if e > 0 and i >= 0: y[i:i + e] += s[:e]
    # driving pulse (own synth): soft kick every 0.5 s + offbeat hat, rising slightly in the last 8 s
    for b in np.arange(T_GO, T_RACE_END, .5):
        k = tt(.25); add(b, .32 * np.sin(2 * np.pi * np.cumsum(50 * (1 + 2 * np.exp(-k * 25))) / sr) * np.exp(-k * 14))
        k = tt(.05); add(b + .25, (.05 + .04 * (b > 22)) * rr.normal(0, 1, len(k)) * np.exp(-k * 90))
    notes = [523.25, 587.33, 659.25, 698.46, 783.99, 880.0, 987.77, 1046.5]
    last = {}
    for te, kind in sounds:
        if te >= T_RACE_END: continue
        if kind.startswith("tick"):
            kk = int(kind[4:])
            if te - last.get(kk, -1) < .08: continue
            last[kk] = te; k = tt(.12); add(te, .12 * np.sin(2 * np.pi * notes[kk] * k) * np.exp(-k * 40))
        elif kind == "gate":
            k = tt(.5); add(te, .4 * np.sin(2 * np.pi * 220 * k) * np.exp(-k * 6))
        elif kind.startswith("fin"):
            p = int(kind[3:])
            if p <= 3:
                for j, f0 in enumerate([523.25, 659.25, 783.99] if p == 1 else [440, 554.37]):
                    k = tt(.5); add(te + j * .09, .22 * np.sin(2 * np.pi * f0 * k) * np.exp(-k * 5))
    for j, f0 in enumerate([523.25, 659.25, 783.99, 1046.5]):
        k = tt(1.2); add(T_RACE_END + j * .12, .2 * np.sin(2 * np.pi * f0 * k) * np.exp(-k * 3))
    y = y / max(1e-6, np.abs(y).max()) * .8
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "search":
        for s in range(int(sys.argv[2]), int(sys.argv[3])): print(score(s), flush=True)
    elif cmd == "render": render(int(sys.argv[2]), sys.argv[3])
