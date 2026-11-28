"""FREE voiced-character shorts pipeline (D18 format). 100% local, no paid APIs.
script.json  ->  TTS (kokoro/piper/espeak)  ->  Whisper word timings  ->  2D cairo animation with lip-sync from audio RMS
             ->  ASS word-highlight captions  ->  synth music + SFX, voice ducking  ->  FFmpeg mux + loudnorm (-14 LUFS)
Usage: python3 episode.py script.json OUT.mp4 [--snaps 0.5,3,10]
Script format: see studio/scripts/ep_test_gus.json"""
import json, os, sys, math, subprocess, random
import numpy as np, cairo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts

W, H, FPS, SR = 1080, 1920, 30, 44100
FLOOR = 1330; R = 150; PRESS_X = 540; PRESS_REST = 560
FONT = "Fira Sans"

def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def sh(*a): return subprocess.run(a, check=True, capture_output=True, text=True).stdout
def load_wav(p, sr=SR):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                                        capture_output=True, check=True).stdout, np.float32).copy()
def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)

# ---------------------------------------------------------------- 1. voices + timeline
def build(script, work):
    os.makedirs(work, exist_ok=True)
    cast = script["cast"]; beats = script["beats"]
    from faster_whisper import WhisperModel
    wm = WhisperModel(os.environ.get("WHISPER", "small.en"), device="cpu", compute_type="int8", download_root=f"{tts.MODELS}/whisper")
    t = script.get("start", 0.5); lines = []; acts = []; engines = set()
    for i, b in enumerate(beats):
        if "say" in b:
            c = cast[b["say"]]; raw = f"{work}/l{i}_raw.wav"; wav = f"{work}/l{i}.wav"
            if not os.path.exists(raw): engines.add(tts.say(b["text"], raw, c["voice"], c.get("speed", 1.0)))
            p = c.get("pitch", 0)   # semitones; asetrate trick keeps it free & local
            af = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
            if p:
                r = 2 ** (p / 12); sr0 = int(sh("ffprobe", "-v", "error", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", raw).strip())
                af += f",asetrate={int(sr0 * r)},aresample={SR},atempo={1 / r:.4f}"
            sh("ffmpeg", "-y", "-v", "error", "-i", raw, "-af", af, "-ar", str(SR), "-ac", "1", wav)
            a = load_wav(wav); d = len(a) / SR
            segs, _ = wm.transcribe(load_wav(wav, 16000), word_timestamps=True, language="en")
            words = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
            toks = b["text"].replace("—", " ").split()
            if len(toks) == len(words): words = [(tok, s_, e_) for tok, (_, s_, e_) in zip(toks, words)]   # script spelling, whisper timing
            hop = SR // FPS; env = np.array([np.sqrt(np.mean(a[k:k + hop] ** 2)) for k in range(0, len(a), hop)])
            env = np.clip(env / (np.percentile(env, 95) + 1e-6), 0, 1)
            lines.append(dict(who=b["say"], text=b["text"], t0=t, dur=d, wav=wav, words=words, env=env, look=b.get("look")))
            t += d + b.get("gap", 0.18)
        else:
            a = dict(b); a["t0"] = t; acts.append(a)
            t += {"slam": 1.25, "move": b.get("dur", .7), "wait": b.get("dur", .4), "enter": .6}[b["act"]]
    total = t + script.get("endcard_dur", 2.6)
    return lines, acts, total, engines

# ---------------------------------------------------------------- 2. character positions over time
def tracks(script, acts):
    pos = {k: [(0.0, x)] for k, x in script["stage"].items()}   # name -> [(t, x)] keyframes
    born = {k: 0.0 for k in script["stage"]}; slams = []
    for a in acts:
        if a["act"] == "slam":
            ti = a["t0"] + .25; slams.append(dict(t0=a["t0"], ti=ti, target=a["target"], spawn=a.get("spawn")))
            if a.get("spawn"): born[a["spawn"]] = ti + .2; pos[a["spawn"]] = [(ti + .2, PRESS_X)]
            for k, x in a.get("after", {}).items(): pos[k].append((ti + .25, pos[k][-1][1])); pos[k].append((ti + .75, x))
        elif a["act"] in ("move", "enter"):
            for k, x in a["to"].items():
                if k not in pos: pos[k] = [(a["t0"], 1300 if x > 540 else -200)]; born[k] = a["t0"]
                pos[k].append((a["t0"], pos[k][-1][1])); pos[k].append((a["t0"] + a.get("dur", .6), x))
    return pos, born, slams

def xat(kf, t):
    if t <= kf[0][0]: return kf[0][1]
    for (t0, x0), (t1, x1) in zip(kf, kf[1:]):
        if t0 <= t <= t1: return x0 + (x1 - x0) * ease((t - t0) / max(1e-6, t1 - t0))
    return kf[-1][1]

# ---------------------------------------------------------------- 3. drawing
def text(c, s, x, y, size, rgba, weight=cairo.FONT_WEIGHT_BOLD, anchor="c"):
    c.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, weight); c.set_font_size(size)
    w = c.text_extents(s).x_advance; c.move_to(x - w / 2 if anchor == "c" else x, y); c.set_source_rgba(*rgba); c.show_text(s)

def draw_char(c, x, sx, sy, col, mouth, look_dx, blink, hop, name, alpha=1):
    cy = FLOOR - R * sy - hop
    c.new_path()
    c.save(); c.translate(x, FLOOR + 6); c.scale(sx * 1.05, .16); c.arc(0, 0, R, 0, 7); c.set_source_rgba(0, 0, 0, .28 * alpha); c.fill(); c.restore()
    c.save(); c.translate(x, cy); c.scale(sx, sy)
    c.new_sub_path(); c.arc(0, 0, R, 0, 7); c.set_source_rgba(*col, alpha); c.fill()
    c.arc(-R * .3, -R * .35, R * .22, 0, 7); c.set_source_rgba(1, 1, 1, .18 * alpha); c.fill()          # flat highlight
    for ex in (-.36, .36):
        c.save(); c.translate(ex * R, -R * .18); c.scale(1, max(.08, 1 - blink))
        c.new_sub_path(); c.arc(0, 0, R * .24, 0, 7); c.set_source_rgba(1, 1, 1, alpha); c.fill()
        c.arc(look_dx * R * .1, R * .02, R * .11, 0, 7); c.set_source_rgba(.07, .07, .1, alpha); c.fill(); c.restore()
    if mouth > .04:
        c.save(); c.translate(0, R * .42); c.scale(1, .2 + mouth * .9); c.arc(0, 0, R * .26, 0, 7); c.restore()
        c.set_source_rgba(.18, .05, .08, alpha); c.fill()
    else:
        c.new_sub_path(); c.arc(0, R * .3, R * .22, .15 * math.pi, .85 * math.pi); c.set_line_width(R * .07); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.set_source_rgba(.18, .05, .08, alpha); c.stroke()
    c.restore()
    c.new_path(); text(c, name, x, cy - R * sy - 30, 38, (1, 1, 1, .85 * alpha))

def render(script, out, lines, acts, total, snaps=None):
    cast = script["cast"]; pos, born, slams = tracks(script, acts)
    bg = hexrgb(script.get("bg", "#141827")); acc = hexrgb(script.get("accent", "#ffb830"))
    nF = int(total * FPS); rnd = random.Random(7)
    blinks = {k: sorted(rnd.uniform(0, total) for _ in range(int(total / 2.5))) for k in pos}
    ff = None if snaps else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r",
                                              str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
                                              out + ".v.mp4"], stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for i in range(nF):
        t = i / FPS
        if snaps and not any(abs(t - q) < .5 / FPS for q in snaps): continue
        c = cairo.Context(surf); c.set_source_rgb(*bg); c.paint()
        # floor + machine frame (flat 2D)
        c.set_source_rgb(*[v * .6 for v in bg]); c.rectangle(0, FLOOR, W, H - FLOOR); c.fill()
        c.set_source_rgba(*acc, .9); c.rectangle(0, FLOOR, W, 10); c.fill()
        for k in range(0, W, 120): c.set_source_rgba(0, 0, 0, .25); c.rectangle(k + 30, FLOOR + 10, 60, 18); c.fill()
        c.save(); c.rectangle(PRESS_X - 210, FLOOR + 10, 420, 46); c.clip()
        for k in range(-2, 12):
            c.move_to(PRESS_X - 210 + k * 46, FLOOR + 10); c.rel_line_to(23, 0); c.rel_line_to(-46, 46); c.rel_line_to(-23, 0); c.close_path()
            c.set_source_rgba(.07, .07, .1, .9); c.fill()
        c.restore()
        for gx, gy, gr, sp_ in ((140, 760, 110, .4), (950, 980, 80, -.6), (900, 430, 60, .8)):
            c.save(); c.translate(gx, gy); c.rotate(t * sp_); c.set_source_rgba(1, 1, 1, .05)
            for q in range(10): c.save(); c.rotate(q * math.pi / 5); c.rectangle(-gr * .18, -gr * 1.25, gr * .36, gr * .5); c.fill(); c.restore()
            c.new_sub_path(); c.arc(0, 0, gr, 0, 7); c.fill(); c.set_source_rgb(*bg); c.new_sub_path(); c.arc(0, 0, gr * .35, 0, 7); c.fill(); c.restore()
        # press: rest -> slam -> rise
        py = PRESS_REST; squash = {}
        for s in slams:
            u = t - s["t0"]
            if 0 <= u < 1.15:
                low = FLOOR - 2 * R * .32
                if u < .25: py = PRESS_REST + (low - PRESS_REST) * (u / .25) ** 2
                elif u < .45: py = low
                else: py = low + (PRESS_REST - low) * ease((u - .45) / .6)
                if .25 <= u < .7: squash[s["target"]] = max(.32, min(1, (FLOOR - py) / (2 * R)))
        sx_ = 1 + .02 * math.sin(t * 9)
        c.set_source_rgb(.35, .37, .45); c.rectangle(PRESS_X - 26, 0, 52, py - 80); c.fill()
        c.set_source_rgb(*acc); c.rectangle(PRESS_X - 210, py - 100, 420, 100); c.fill()
        c.set_source_rgba(0, 0, 0, .25); c.rectangle(PRESS_X - 200, py - 22, 400, 22); c.fill()
        for k in range(5): c.set_source_rgba(.08, .08, .1, .85); c.rectangle(PRESS_X - 190 + k * 80, py - 70, 40, 14); c.fill()
        # impact flash
        for s in slams:
            u = t - s["ti"]
            if 0 <= u < .25: c.set_source_rgba(1, 1, 1, .5 * (1 - u / .25)); c.paint()
        # who speaks now
        cur = next((L for L in lines if L["t0"] <= t < L["t0"] + L["dur"]), None)
        for k, kf in pos.items():
            if t < born[k]: continue
            x = xat(kf, t); col = hexrgb(cast[k]["color"])
            pop = min(1, (t - born[k]) / .25) if born[k] > 0 else 1
            sq = squash.get(k, 1); sx = (1 / sq) ** .5 * (.6 + .4 * pop); sy = sq * (.6 + .4 * pop)
            mouth = 0; hop = 0
            if cur and cur["who"] == k:
                fi = int((t - cur["t0"]) * FPS); mouth = float(cur["env"][min(fi, len(cur["env"]) - 1)]); hop = 10 * mouth
            target = (cur["look"] if cur and cur["who"] == k and cur.get("look") else cur["who"] if cur and cur["who"] != k else None)
            ldx = 0 if target not in pos or t < born.get(target, 0) else max(-1, min(1, (xat(pos[target], t) - x) / 200))
            if k in squash: ldx = 0
            bl = max([max(0, 1 - abs(t - b) / .07) for b in blinks[k]] + [0])
            draw_char(c, x, sx * sx_ if cur and cur["who"] == k else sx, sy, col, mouth, ldx, bl, hop, cast[k].get("label", k))
        # header: episode tag + hook banner (first 2.8 s)
        text(c, script.get("tag", ""), 540, 120, 40, (1, 1, 1, .7))
        if t < 2.8 and script.get("hook"):
            a = min(1, (2.8 - t) / .4); c.set_source_rgba(*acc, .95 * a); c.rectangle(0, 170, W, 120); c.fill()
            text(c, script["hook"], 540, 248, 56, (.07, .07, .1, a), cairo.FONT_WEIGHT_BOLD)
        # end card
        te = total - script.get("endcard_dur", 2.6)
        if t >= te:
            a = min(1, (t - te) / .3); c.set_source_rgba(*bg, .9 * a); c.paint()
            for j, s_ in enumerate(script.get("endcard", [])): text(c, s_, 540, 760 + j * 90, 64 if j == 0 else 46, (1, 1, 1, a))
            c.set_source_rgba(*acc, a); c.rectangle(110, 1080, 860, 140); c.fill()
            text(c, "FOLLOW @CRUSH.MULTIPLY", 540, 1170, 58, (.07, .07, .1, a))
        if snaps: surf.write_to_png(f"{out}_{t:05.1f}.png"); continue
        ff.stdin.write(bytes(surf.get_data()))
    if ff: ff.stdin.close(); assert ff.wait() == 0

# ---------------------------------------------------------------- 4. captions (ASS, word highlight, speaker colour)
def ass(script, lines, path):
    def ts(x): x = max(0, x); return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"
    def bgr(h): r, g, b = hexrgb(h); return f"&H00{int(b * 255):02X}{int(g * 255):02X}{int(r * 255):02X}"
    out = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "",
           "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Cap,Fira Sans Black,74,&H00FFFFFF,&H00FFFFFF,&H00101010,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,70,1010,1", "",
           "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for L in lines:
        col = bgr(script["cast"][L["who"]]["color"]); ws = L["words"]
        # chunks of <=4 words so the caption never covers the characters
        for k in range(0, len(ws), 4):
            ch = ws[k:k + 4]; st = L["t0"] + ch[0][1]; en = L["t0"] + (ws[k + 4][1] if k + 4 < len(ws) else L["dur"] + .1)
            for j, (w, s_, e_) in enumerate(ch):
                a = L["t0"] + s_; b = L["t0"] + (ch[j + 1][1] if j + 1 < len(ch) else en - L["t0"])
                if j == 0: a = st
                txt = " ".join((f"{{\\c{col}\\fscx112\\fscy112}}{x}{{\\r}}" if q == j else x) for q, (x, _, _) in enumerate(ch))
                out.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{txt.upper()}")
    open(path, "w").write("\n".join(out) + "\n")

# ---------------------------------------------------------------- 5. audio: voice + SFX + synth music bed, ducking, loudnorm
def audio(script, lines, acts, total, work):
    n = int(total * SR) + SR; voice = np.zeros(n, np.float32); fx = np.zeros(n, np.float32); tt = lambda d: np.arange(int(d * SR)) / SR
    def add(buf, at, s): i = int(at * SR); buf[i:i + len(s)] += s[:max(0, n - i)]
    for L in lines: add(voice, L["t0"], load_wav(L["wav"]))
    _, _, slams = tracks(script, acts)
    for s in slams:
        x = tt(.5); add(fx, s["ti"], (np.sin(2 * np.pi * 55 * x) * np.exp(-x * 9) * .9 + np.random.default_rng(1).normal(0, .5, len(x)) * np.exp(-x * 30)).astype(np.float32))
        x = tt(.18); add(fx, s["ti"] + .2, (np.sin(2 * np.pi * (500 + 1800 * x / .18) * x) * np.exp(-x * 12) * .35).astype(np.float32))
    # music bed: 100 bpm pentatonic plucks + soft bass, original & synthesised (no third-party audio)
    mus = np.zeros(n, np.float32); beat = 60 / 100 / 2; notes = [0, 3, 5, 7, 10, 12, 7, 5]; rnd = random.Random(3)
    k = 0; tt0 = 0.0
    while tt0 < total:
        f = 220 * 2 ** (notes[(k + rnd.choice([0, 0, 1])) % len(notes)] / 12); x = tt(.3)
        add(mus, tt0, (np.sin(2 * np.pi * f * x) * np.exp(-x * 14) * .22).astype(np.float32))
        if k % 4 == 0: x = tt(.5); add(mus, tt0, (np.sin(2 * np.pi * 55 * x) * np.exp(-x * 5) * .3).astype(np.float32))
        k += 1; tt0 += beat
    for nm, b in (("voice", voice), ("fx", fx), ("mus", mus)):
        import soundfile as sf; sf.write(f"{work}/{nm}.wav", b[:int(total * SR)], SR)
    sh("ffmpeg", "-y", "-v", "error", "-i", f"{work}/voice.wav", "-i", f"{work}/fx.wav", "-i", f"{work}/mus.wav", "-filter_complex",
       "[0:a]asplit=2[sc][vo];[2:a]volume=0.5[m];[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=250[md];"
       "[vo][1:a][md]amix=inputs=3:normalize=0,acompressor=threshold=0.1:ratio=4:attack=5:release=120,alimiter=limit=0.5:level=disabled[a]", "-map", "[a]", "-ar", str(SR), f"{work}/premix.wav")
    # two-pass EBU R128 loudness normalisation to -14 LUFS / -1.5 dBTP (Reels/Shorts level)
    e = subprocess.run(["ffmpeg", "-i", f"{work}/premix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = json.loads(e[e.rindex("{"):e.rindex("}") + 1])
    sh("ffmpeg", "-y", "-v", "error", "-i", f"{work}/premix.wav", "-af",
       f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
       f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true", "-ar", str(SR), f"{work}/mix.wav")

def main():
    sp, out = sys.argv[1], sys.argv[2]; script = json.load(open(sp))
    snaps = [float(x) for x in sys.argv[sys.argv.index("--snaps") + 1].split(",")] if "--snaps" in sys.argv else None
    work = out + "_work"; lines, acts, total, eng = build(script, work)
    print("TTS engines:", eng, "| total", round(total, 2), "s")
    for L in lines: print(f"{L['t0']:5.2f}+{L['dur']:.2f} {L['who']}: {' '.join(w for w, _, _ in L['words'])}")
    render(script, out, lines, acts, total, snaps)
    if snaps: return
    ass(script, lines, f"{work}/cap.ass"); audio(script, lines, acts, total, work)
    sh("ffmpeg", "-y", "-v", "error", "-i", out + ".v.mp4", "-i", f"{work}/mix.wav", "-vf", f"ass={work}/cap.ass", "-c:v", "libx264", "-crf", "19",
       "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out)
    os.remove(out + ".v.mp4"); json.dump(dict(total=total, engines=sorted(eng), lines=[dict(who=L["who"], text=L["text"], t0=L["t0"], dur=L["dur"]) for L in lines]),
                                         open(out + ".json", "w"), indent=1)
    print("OK", out)

if __name__ == "__main__": main()
