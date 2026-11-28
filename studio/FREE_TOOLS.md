# Free toolchain audit — 2026-11-28

Rule from Kolya, 2026-11-28: only free tools. No paid subscriptions, no paid APIs (not even as a fallback), no tools that charge after a
trial, and no spending without his approval.

Environment: Ubuntu 24.04 cloud container, 2 CPUs, 7 GB RAM, **no GPU**, about 30 GB of disk. Python 3.13, Node 22, FFmpeg 6.1, and
Chromium from Playwright. Network: pip, npm, apt and Hugging Face work. github.com release downloads are blocked; `git clone` works.

| # | Tool | Licence | Free? | Status here | Measured |
|---|---|---|---|---|---|
| 1 | FFmpeg 6.1 (+libass, ebur128, loudnorm) | LGPL/GPL | yes | installed | used for mux, ASS captions, two-pass loudness, black-frame QC |
| 2 | Remotion 4.0.547 + @remotion/three | Remotion License | **partly**: free for individuals, for-profit companies with up to 3 employees, and non-profits; above that a paid company licence is required | installed in /home/claude/remotion-lab, template in studio/remotion | 3 s 1080x1920 Three.js clip in about 31 s, using `--gl=swangle` and the Playwright Chromium |
| 3 | Blender 4.0.2 (apt) | GPL | yes | installed | Cycles CPU: about 9 s per frame at 540x960 with 24 samples. The Ubuntu build has **no OpenImageDenoise** (grainy) and Eevee has no EGL/GPU here. Fit for stills and short shots, not for 30 s at 1080p |
| 4 | MoviePy 2.2.1 | MIT | yes | installed (downgraded Pillow to 11.3; pdfplumber warns, harmless here) | — |
| 5 | Whisper via faster-whisper 1.2.1, small.en int8 | MIT (code and weights) | yes | installed | about 2 s per 4 s clip; word timestamps work. Needs `HF_HUB_DISABLE_XET=1` and numpy audio input (bundled av 19 API mismatch) |
| 6a | Kokoro-82M ONNX (kokoro-onnx 0.6.1) | Apache-2.0 weights | yes | installed, **default voice** | about 1.8x real time on 2 CPUs; Whisper reads its speech back 100% correctly |
| 6b | Piper TTS (piper1-gpl 1.8.0) | GPL-3 code; **voice licences vary** | yes for the voices listed in studio/tts.py | installed, fallback | about 0.5x real time. NON-commercial voices excluded: ryan, lessac, hfc_male, hfc_female, semaine; amy, alan and kusal unclear |
| 6c | espeak-ng | GPL-3 | yes | installed, last resort | robotic |
| 7 | Three.js 0.169 | MIT | yes | installed (inside Remotion) | see #2 |
| 8 | ComfyUI | GPL-3 | free, **but not usable here** | NOT installed | no GPU, 7 GB RAM: SD-class models would take minutes per image on CPU and video models will not run. Revisit only with a free GPU machine |

**Paid services still in the automation, which Kolya needs to decide on:**
- **ElevenLabs** — removed. `concepts/voice_mix.py` now uses studio/tts.py, and the scheduled-task prompt no longer contains the key.
  Kolya should revoke that key in his ElevenLabs account, because it was written into the task prompt in plain text.
- **Windsor.ai** — all Instagram posting and analytics go through it, and it is a paid SaaS whose free trial ends. This was NOT
  changed, because removing it stops posting. A free alternative is the official Instagram Graph API (free, but it needs a Meta developer app and
  a long-lived token from Kolya).

## Skills
- Vetted free skills from GitHub (all MIT, offline, no API keys) are in `/skills`, each with ATTRIBUTION.md: viral-hooks and storytelling
  (artemnovitckii/content-skills); yt-script, yt-retention, yt-edit, yt-viral, yt-shorts and yt-package (Jakeschincariol/youtube-agent-skill);
  genre-craft (danjdewhurst/story-skills); marketing-psychology (coreyhaines31/marketingskills).
- Rejected: remotion-dev/skills and comedy-writers-room (no licence, so all rights reserved); sergebulaev/youtube-skills (paid SaaS publishing);
  claude-motion-design ("remake" mode copies other people's videos and needs paid API keys); AskEditor (about 600 MB installer, built for talking heads,
  links to a paid app); jtydhr88 screenwriting (Chinese-language TV material, and the quoted book passages are not MIT).
- Own skill: `skills/free-shorts-studio/SKILL.md` covers the pipeline, voices and QC rules.
