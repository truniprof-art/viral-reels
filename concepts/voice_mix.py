"""D17 VOICE COMMENTATOR (D19: FREE local TTS only — ElevenLabs removed 2026-11-28 on Kolya's free-tools rule).
Synthesise timed commentator lines and mix them over a rendered reel (music ducked under speech).
Usage: python3 voice_mix.py LINES.json IN.mp4 OUT.mp4
LINES.json = [{"t": 0.2, "text": "The FINALE!"}, ...]  (t = video seconds; each line must be TRUE to the frame at t; [tags] are stripped)
Voice: studio/tts.py — Kokoro-82M (Apache-2.0) -> Piper (commercial-safe voices) -> espeak-ng. No API keys, no network."""
import json, os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "studio"))
import tts

VOICE = os.environ.get("VOICE", "kokoro:am_fenrir")   # energetic male caster
SPEED = float(os.environ.get("VOICE_SPEED", "1.12"))
MAXTEMPO = 1.15

def sh(*a): return subprocess.run(a, check=True, capture_output=True, text=True).stdout

def dur(p): return float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p))

def main(lines_p, vin, vout):
    lines = json.load(open(lines_p)); tmp = vout + "_vo"; os.makedirs(tmp, exist_ok=True); engine = "cached"
    total = dur(vin); parts = []
    for i, L in enumerate(lines):
        raw = f"{tmp}/l{i}.wav"
        if not os.path.exists(raw):
            engine = tts.say(L["text"], raw, VOICE, SPEED)
        trim = f"{tmp}/t{i}.wav"   # trim leading/trailing silence
        sh("ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
           "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
           "-ar", "44100", "-ac", "1", trim)
        d = dur(trim); nxt = lines[i + 1]["t"] if i + 1 < len(lines) else total
        room = max(.3, nxt - L["t"] - .05); tempo = min(MAXTEMPO, max(1.0, d / room))
        fit = f"{tmp}/f{i}.wav"; sh("ffmpeg", "-y", "-loglevel", "error", "-i", trim, "-af", f"atempo={tempo:.3f}", fit)
        d2 = dur(fit); parts.append((L["t"], fit))
        print(f"{L['t']:5.1f}s  {d:4.2f}->{d2:4.2f}s (room {room:4.2f}, tempo {tempo:.2f}){'  OVERLAP' if d2 > room + .05 else ''}  {L['text']}")
    # voice track
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for _, p in parts: args += ["-i", p]
    fl = "".join(f"[{k}]adelay={int(t * 1000)}|{int(t * 1000)},volume=1.6[v{k}];" for k, (t, _) in enumerate(parts))
    fl += "".join(f"[v{k}]" for k in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{total}[vo]"
    args += ["-filter_complex", fl, "-map", "[vo]", "-ar", "44100", "-ac", "1", f"{tmp}/voice.wav"]; sh(*args)
    # duck the race audio under the voice, then mix
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", vin, "-i", f"{tmp}/voice.wav", "-filter_complex",
       "[1:a]asplit=2[sc][vo];[0:a]aresample=44100,aformat=channel_layouts=mono[mu];"
       "[mu][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[duck];"
       "[duck][vo]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]",
       "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", vout)
    print("VOICE ENGINE:", engine)

if __name__ == "__main__": main(*sys.argv[1:4])
