---
name: free-shorts-studio
description: Build vertical Reels/Shorts for @crush.multiply with a 100% FREE local toolchain — voiced cartoon-ball episodes, commentary over sims, captions, sound and automatic QC. Use whenever making, voicing, captioning, mixing or checking a short in the viral-reels repo. Never uses paid APIs (no ElevenLabs/OpenAI/Runway/HeyGen), not even as a fallback.
---

# Free Shorts Studio

Owner rule (Kolya, 2026-11-28): every tool, model, library and service must be free. No paid subscription, paid API, trial-then-paid
service or any spend without his approval — not even as a fallback. If something is only partly free, say so.

## Toolchain (all verified in this container: 2 CPU, 7 GB RAM, no GPU)

| Job | Tool | Licence / free status |
|---|---|---|
| Edit, mux, captions burn-in, loudness | FFmpeg 6.1 (apt) + libass | LGPL/GPL, free |
| Voice (default) | Kokoro-82M ONNX via `kokoro-onnx` | Apache-2.0 weights, MIT lib, free commercial |
| Voice (fallback) | Piper (`piper-tts`, piper1-gpl) | GPL-3 code; voices — ONLY the commercial-safe list in `studio/tts.py` |
| Voice (last resort) | espeak-ng | GPL-3 |
| Word timings, subtitles, intelligibility QC | faster-whisper `small.en` int8 | MIT |
| 2D animation | pycairo + pymunk + numpy | LGPL/MPL/MIT, free |
| Python edit automation | MoviePy 2.2 | MIT |
| Programmatic motion / 3D | Remotion 4 + @remotion/three + Three.js (`studio/remotion`) | Three.js MIT; **Remotion free only for individuals / companies ≤3 employees** |
| 3D characters / stills | Blender 4.0 (apt), Cycles CPU | GPL, free; slow here (~9 s/frame at 540x960, no denoiser) |
| Image/video generation | ComfyUI | GPL, free, but **not usable here**: no GPU |

Setup: `bash studio/setup_free_tools.sh` (models go to /home/claude/models, never into the repo).
Set `HF_HUB_DISABLE_XET=1` before the first Whisper download (the xet CDN is blocked here).

## Pipeline: voiced character episode (D18)

1. Write `studio/scripts/<ep>.json` (see `ep_test_gus.json`): `cast` (voice id, colour, speed, pitch in semitones, label),
   `stage` (start x), `beats` = `{"say":NAME,"text":...,"look":NAME}` or `{"act":"slam"|"move"|"wait"|"enter",...}`,
   `hook` (≤28 chars, shown 0–2.8 s), `tag`, `endcard` lines. Write the jokes with the cartoon-humor-writer skill and
   score them with cartoon-humor-judge (ship ≥7/10). Lines ≤12 words.
2. `python3 studio/episode.py studio/scripts/<ep>.json out/reel.mp4` → TTS per line, Whisper word timings, lip-sync from
   the audio envelope, squash-and-stretch press gag, word-highlight captions in speaker colour, synthesised music + SFX,
   voice ducking, two-pass loudnorm to -14 LUFS.
3. `python3 studio/qc.py out/reel.mp4 out/reel.mp4.json` must print `"PASS": true` (1080x1920, 30 fps, 15–60 s, -16..-12 LUFS,
   true peak ≤ -0.9 dBTP, no black frames, Whisper WER ≤ 15%). Then LOOK at the contact sheet (`*.sheet.png`): captions must not cover
   characters, nothing off-screen, the end card says FOLLOW @CRUSH.MULTIPLY.

## Commentary over an existing reel (league, sims)

`python3 concepts/voice_mix.py LINES.json IN.mp4 OUT.mp4` — free TTS (default `kokoro:am_fenrir`, env VOICE / VOICE_SPEED).
Every line must be true to the frame at its timestamp.

## Voices (cast sheet)

Kokoro: am_puck (bright, comic lead), am_fenrir (energetic caster), am_michael, am_onyx (deep), am_echo, am_liam, af_bella,
af_heart, af_nicole, af_sky, bm_george / bm_lewis / bm_fable (British), bf_emma. Variants of the same character: same voice + `pitch`.
Piper (commercial-safe): bryce, norman, john, kristin, cori(GB), ljspeech (public domain); joe (CC0); sam (Apache-2.0);
libritts_r (CC BY 4.0 — credit "LibriTTS-R" in the description). Never: ryan, lessac, hfc_*, semaine (non-commercial), amy/alan/kusal
(unclear). Never clone or imitate a real person's voice.

## Craft rules for retention (from the vetted skills in /skills: yt-retention, yt-shorts, viral-hooks, storytelling)

- Frame 1 already moves and states the stake in ≤6 words; first spoken line lands by 0.5 s.
- A visible change every 2–3 s (slam, new character, camera/position change); no line longer than ~3 s.
- Captions: ≤4 words per chunk, current word highlighted, above the characters, out of the bottom 300 px (UI).
- End on an open loop the next episode really answers (honesty rule: every promise is kept).
- Sound: original synthesised music/SFX only; no third-party audio or footage except public domain / free-licence stock.
