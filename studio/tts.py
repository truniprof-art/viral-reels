"""FREE local text-to-speech (no paid APIs, no network at synthesis time).
Engines, in order: kokoro (Kokoro-82M ONNX, Apache-2.0) -> piper (piper1-gpl, GPL-3; only commercial-safe voices) -> espeak-ng (GPL-3).
Usage (CLI): python3 tts.py "text" out.wav [voice] [speed]
Voice ids: 'kokoro:am_puck', 'piper:en_US-bryce-medium', 'espeak:en-us'. Bare 'am_puck' = kokoro.
Models live in $MODELS (default /home/claude/models); fetch them with studio/setup_free_tools.sh."""
import os, sys, subprocess, re
import numpy as np

MODELS = os.environ.get("MODELS", "/home/claude/models")
# Piper voices whose MODEL_CARD licence allows commercial use (checked 2026-11-28). Others (ryan, lessac, hfc_*, semaine, amy,
# alan, kusal) are NON-commercial or unclear -> never use them on the monetised account.
PIPER_OK = {"en_US-bryce-medium": "public domain", "en_US-norman-medium": "public domain", "en_US-john-medium": "public domain",
            "en_US-kristin-medium": "public domain", "en_GB-cori-high": "public domain", "en_US-ljspeech-high": "public domain",
            "en_US-joe-medium": "CC0", "en_US-sam-medium": "Apache-2.0", "en_US-libritts_r-medium": "CC BY 4.0 (credit LibriTTS-R)"}
_kok = None

def _kokoro():
    global _kok
    if _kok is None:
        from kokoro_onnx import Kokoro
        _kok = Kokoro(f"{MODELS}/kokoro/model_q8.onnx", f"{MODELS}/kokoro/voices.bin")
    return _kok

def _write(path, a, sr):
    import soundfile as sf
    sf.write(path, np.asarray(a, dtype=np.float32), sr)

def say(text, out, voice="kokoro:am_puck", speed=1.0):
    """Synthesise `text` to WAV `out`. Returns the engine actually used. Strips [audio tags] (ElevenLabs-style) first."""
    text = re.sub(r"\[[^\]]*\]", "", text).strip()
    eng, _, v = voice.partition(":") if ":" in voice else ("kokoro", "", voice)
    chain = [eng] + [e for e in ("kokoro", "piper", "espeak") if e != eng]
    for e in chain:
        try:
            if e == "kokoro":
                vv = v if eng == "kokoro" else "am_puck"
                a, sr = _kokoro().create(text, voice=vv, speed=speed, lang="en-gb" if vv.startswith("b") else "en-us")
                _write(out, a, sr); return f"kokoro:{vv}"
            if e == "piper":
                vv = v if eng == "piper" else "en_US-bryce-medium"
                assert vv in PIPER_OK, f"piper voice {vv} is not on the commercial-safe list"
                subprocess.run([sys.executable, "-m", "piper", "-m", f"{MODELS}/piper/{vv}.onnx", "--length-scale", f"{1 / speed:.3f}",
                                "-f", out, "--", text], check=True, capture_output=True)
                return f"piper:{vv}"
            if e == "espeak":
                subprocess.run(["espeak-ng", "-v", v if eng == "espeak" else "en-us", "-s", str(int(170 * speed)), "-w", out, text],
                               check=True, capture_output=True)
                return "espeak-ng"
        except Exception as ex:
            print(f"[tts] {e} failed: {type(ex).__name__}: {ex}", file=sys.stderr)
    raise RuntimeError("all free TTS engines failed")

if __name__ == "__main__":
    print(say(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or ["kokoro:am_puck"]), *[float(x) for x in sys.argv[4:5]]))
