#!/usr/bin/env bash
# Installs the FREE video toolchain (verified 2026-11-28). No paid APIs, no API keys. Idempotent.
set -e
M=${MODELS:-/home/claude/models}; export HF_HUB_DISABLE_XET=1
pip install -q --break-system-packages pymunk pycairo numpy soundfile moviepy faster-whisper piper-tts kokoro-onnx
command -v espeak-ng >/dev/null || (apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq espeak-ng)
command -v blender >/dev/null || [ "$WITH_BLENDER" != 1 ] || DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends blender
# Kokoro-82M (Apache-2.0) ONNX int8 + voices packed into one npz
mkdir -p $M/kokoro/v; K=https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main
[ -s $M/kokoro/model_q8.onnx ] || curl -sL -o $M/kokoro/model_q8.onnx $K/onnx/model_quantized.onnx
for v in am_adam am_echo am_eric am_fenrir am_liam am_michael am_onyx am_puck af_bella af_heart af_nicole af_sky bm_george bm_lewis bm_fable bf_emma; do
  [ -s $M/kokoro/v/$v.bin ] || curl -sL -o $M/kokoro/v/$v.bin $K/voices/$v.bin; done
[ -s $M/kokoro/voices.bin ] || python3 -c "
import numpy as np,glob,os
np.savez('$M/kokoro/voices.npz',**{os.path.basename(f)[:-4]:np.fromfile(f,dtype=np.float32).reshape(-1,1,256) for f in glob.glob('$M/kokoro/v/*.bin')})" && mv -f $M/kokoro/voices.npz $M/kokoro/voices.bin 2>/dev/null || true
# Piper voices: ONLY commercial-safe licences (public domain / CC0 / Apache / CC BY)
mkdir -p $M/piper; P=https://huggingface.co/rhasspy/piper-voices/resolve/main/en
for v in en_US/bryce/medium en_US/norman/medium en_US/john/medium en_US/kristin/medium en_GB/cori/high en_US/joe/medium en_US/sam/medium en_US/ljspeech/high en_US/libritts_r/medium; do
  n=$(echo $v | awk -F/ '{print $1"-"$2"-"$3}'); [ -s $M/piper/$n.onnx ] || { curl -sL -o $M/piper/$n.onnx $P/$v/$n.onnx; curl -sL -o $M/piper/$n.onnx.json $P/$v/$n.onnx.json; }; done
# Whisper small.en (MIT) for captions + QC, downloaded on first use by faster-whisper
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small.en',device='cpu',compute_type='int8',download_root='$M/whisper')" 2>/dev/null
# Remotion + Three.js (optional, WITH_REMOTION=1): Remotion is free for individuals / companies <=3 employees
if [ "$WITH_REMOTION" = 1 ]; then (cd "$(dirname "$0")/remotion" && npm i -s); fi
echo "free toolchain ready"
