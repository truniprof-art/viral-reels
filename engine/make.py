"""Generate one finished reel.  usage: python3 make.py KIND OUT.mp4 [SEED]
KIND: press | crusher | belts.  Random seed + hue picked from SEED; growth curve checked before rendering."""
import os, sys, random, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__))
kind, out = sys.argv[1], os.path.abspath(sys.argv[2])
master = int(sys.argv[3]) if len(sys.argv) > 3 else random.randrange(10**9)
rnd = random.Random(master)
MECHS = json.load(open(os.path.join(HERE, "mechs.json")))          # base.py-engine mechanisms
if kind == "auto":                                                   # weighted pick, never the same kind twice in a row
    W = json.load(open(os.path.join(HERE, "..", "rotation.json")))
    last = ""
    pc = os.path.join(HERE, "..", "posts.csv")
    if os.path.exists(pc):
        import csv
        rows = list(csv.DictReader(open(pc)))
        if rows: last = rows[-1]["kind"]
    opts = {k: w for k, w in W.items() if w > 0 and k != last} or W
    kind = rnd.choices(list(opts), weights=list(opts.values()))[0]
# ---- per-video style: shape + background never repeat the recent posts ----
import style as _st
recent = []
_pc = os.path.join(HERE, "..", "posts.csv")
if os.path.exists(_pc):
    import csv
    recent = [r.get("style", "") for r in csv.DictReader(open(_pc))][-6:]
_shapes = [x for x in _st.SHAPES if all(not r.startswith(x + ":") for r in recent[-4:])] or _st.SHAPES
_bgs = [x for x in _st.BG_NAMES if all(not r.endswith(":" + x) for r in recent[-2:])] or _st.BG_NAMES
STYLE = {"shape": os.environ.get("SHAPE") or rnd.choice(_shapes), "bg": os.environ.get("BG") or rnd.choice(_bgs)}
WORK = f"/tmp/vr_{kind}_{master}"
os.makedirs(WORK, exist_ok=True)
env = dict(os.environ, WORK=WORK, HUE=str(rnd.choice([0, 0, 40, 80, 140, 200, 260, 310])), PYTHONDONTWRITEBYTECODE="1", STYLE=json.dumps(STYLE))
PY = [sys.executable, "-B"]

def sh(args, **kw):
    subprocess.run(args, check=True, cwd=HERE, env={**env, **kw.get("extra", {})})

def capture(code, extra=None):
    r = subprocess.run(PY + ["-c", code], cwd=HERE, env={**env, **(extra or {})}, check=True, capture_output=True, text=True)
    return r.stdout

def mux(parts, wav):
    lst = os.path.join(WORK, "l.txt")
    with open(lst, "w") as f:
        for p in parts: f.write(f"file '{p}'\n")
    tmp = out[:-4] + "_tmp.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)

def pick(test, seeds):
    for s in seeds:
        if test(s): return s
    return seeds[0]

seeds = [rnd.randrange(1, 100000) for _ in range(12)]
info = dict(kind=kind, master=master, hue=env["HUE"], style=f"{STYLE['shape']}:{STYLE['bg']}")

if kind == "press":
    cfg = rnd.choice(["2.2,1.5,0.7", "2.0,1.4,0.65", "2.4,1.6,0.75"])
    def ok(s):
        o = capture(f"import presssim2 as p\nr=p.run({cfg},{s},record=False)\ncr=r['HIT']\n"
                    "n=lambda t:1+int(cr[cr[:,0]<=t][:,1].sum()) if len(cr) else 1\nprint(r['n'],n(6),n(15))")
        fin, a6, a15 = map(int, o.split())
        print("press", s, fin, a6, a15, flush=True)
        return fin >= 250 and a6 <= 6 and a15 <= 80
    s = pick(ok, seeds); info.update(seed=s, cfg=cfg)
    sh(PY + ["presssim2.py", "rec", cfg, str(s)])
    ps = [subprocess.Popen(PY + ["pressrender3.py", "render", str(i), "2"], cwd=HERE, env=env) for i in range(2)]
    sh(PY + ["pressrender3.py", "audio"])
    assert all(p.wait() == 0 for p in ps)
    mux([f"{WORK}/p3p0.mp4", f"{WORK}/p3p1.mp4"], f"{WORK}/p3_audio.wav")

elif kind == "crusher":
    R = dict(ZX="24", ZY="18", S1="50", OPEN="17,17,0,12,12")
    def ok(s):
        o = capture(f"import rollsim as r\nx=r.run({s},record=False)\nC=x['COUNT']\nprint(*[int(C[int(t*r.FPS)]) for t in (5,10,29.9)])", R)
        a5, a10, fin = map(int, o.split())
        print("crusher", s, a5, a10, fin, flush=True)
        return fin >= 800 and a5 <= 3 and a10 <= 40
    s = pick(ok, seeds); info.update(seed=s)
    sh(PY + ["rollsim.py", "rec", str(s)], extra=R)
    ps = [subprocess.Popen(PY + ["rollrender.py", "render", str(i), "2"], cwd=HERE, env=env) for i in range(2)]
    sh(PY + ["rollrender.py", "audio"])
    assert all(p.wait() == 0 for p in ps)
    mux([f"{WORK}/rlp0.mp4", f"{WORK}/rlp1.mp4"], f"{WORK}/rl_audio.wav")

elif kind in MECHS:
    m = MECHS[kind]; env.update(m.get("env", {}))
    o = subprocess.run(PY + [m["file"], "search"] + [str(x) for x in seeds[:8]], cwd=HERE, env=env, check=True, capture_output=True, text=True).stdout
    best = seeds[0]
    for line in o.strip().splitlines():
        sd, rest = line.split(" ", 1); c = json.loads(rest)
        print(kind, sd, c, flush=True)
        if c[-1] >= m.get("min_final", 500) and c[0] <= 3 and c[1] <= 12: best = int(sd); break
    info.update(seed=best)
    sh(PY + [m["file"], "rec", str(best)])
    sh(PY + [m["file"], "all"])
    os.replace(f"{WORK}/{m['name']}.mp4", out)
else:
    sys.exit("unknown kind")

print(json.dumps(info))
