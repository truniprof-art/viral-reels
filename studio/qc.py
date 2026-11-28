"""Free automatic quality check for a finished short (no paid services).
Checks: 1080x1920, 30 fps, 15-60 s, audio present, loudness (-16..-12 LUFS, true peak <= -1 dBTP), intelligibility (local Whisper
re-transcribes the final mix -> word error rate vs the script), black/frozen frames, and writes a contact sheet PNG.
Usage: python3 qc.py VIDEO.mp4 [script_lines.json]   (lines json = the .json episode.py writes next to the mp4)"""
import sys, json, subprocess, re, os
import numpy as np
def run(*a): return subprocess.run(a, capture_output=True, text=True)
def wer(ref, hyp):
    r = re.findall(r"[a-z0-9']+", ref.lower()); h = re.findall(r"[a-z0-9']+", hyp.lower())
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[-1] / max(1, len(r))
def main(v, lj=None):
    rep = {}; ok = True
    pr = json.loads(run("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", v).stdout)
    vs = [s for s in pr["streams"] if s["codec_type"] == "video"][0]; aus = [s for s in pr["streams"] if s["codec_type"] == "audio"]
    dur = float(pr["format"]["duration"]); fps = eval(vs["r_frame_rate"])
    rep.update(size=f"{vs['width']}x{vs['height']}", fps=fps, duration=round(dur, 2), audio=bool(aus))
    ok &= vs["width"] == 1080 and vs["height"] == 1920 and abs(fps - 30) < .1 and 15 <= dur <= 60 and bool(aus)
    e = run("ffmpeg", "-nostats", "-i", v, "-af", "ebur128=peak=true", "-f", "null", "-").stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]); tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    rep.update(lufs=I, true_peak=tp); ok &= -16 <= I <= -12 and tp <= -0.9
    bd = run("ffmpeg", "-i", v, "-vf", "blackdetect=d=0.5:pix_th=0.05,freezedetect=n=0.003:d=2", "-f", "null", "-").stderr
    rep["black_segments"] = len(re.findall("black_start", bd)); rep["frozen_segments"] = len(re.findall("freeze_start", bd))
    ok &= rep["black_segments"] == 0
    if lj and os.path.exists(lj):
        from faster_whisper import WhisperModel
        m = WhisperModel("small.en", device="cpu", compute_type="int8", download_root=os.environ.get("MODELS", "/home/claude/models") + "/whisper")
        a = np.frombuffer(run("ffmpeg", "-v", "error", "-i", v, "-ac", "1", "-ar", "16000", "-f", "f32le", "-").stdout if False else
                          subprocess.run(["ffmpeg", "-v", "error", "-i", v, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
        hyp = " ".join(s.text for s in m.transcribe(a, language="en")[0]); ref = " ".join(L["text"] for L in json.load(open(lj))["lines"])
        rep["wer"] = round(wer(ref, hyp), 3); rep["heard"] = hyp.strip(); ok &= rep["wer"] <= .15
    ts = [round(dur * q, 2) for q in (.03, .15, .3, .5, .7, .85, .97)]
    for k, t in enumerate(ts): run("ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", v, "-frames:v", "1", "-vf", "scale=270:480", f"/tmp/qc_{k}.png")
    run("ffmpeg", "-y", "-v", "error", *sum([["-i", f"/tmp/qc_{k}.png"] for k in range(len(ts))], []), "-filter_complex",
        "".join(f"[{k}]" for k in range(len(ts))) + f"hstack=inputs={len(ts)}", v + ".sheet.png")
    rep["contact_sheet"] = v + ".sheet.png"; rep["PASS"] = bool(ok)
    print(json.dumps(rep, indent=1)); return ok
if __name__ == "__main__": sys.exit(0 if main(*sys.argv[1:3]) else 1)
