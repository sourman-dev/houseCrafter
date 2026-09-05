#!/usr/bin/env bash
# HouseCrafter Colab setup: keep Colab's PyTorch, install wheels only.
# Never compile pytorch3d / flash-attn from source.

set -euo pipefail

echo "============================================================"
echo " HouseCrafter Colab setup (wheels only, no compile)"
echo "============================================================"

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
else
  echo "[!] No GPU detected. Use --mock when launching the app."
fi

echo "[*] Preinstalled PyTorch (must keep):"
python3 - <<'PY'
import sys
print("python", sys.version.split()[0])
try:
    import torch
    print("torch", torch.__version__, "cuda", torch.cuda.is_available())
except Exception as exc:
    print("torch missing:", exc)
PY

REQ_FILE="requirements-colab.txt"
if [ ! -f "$REQ_FILE" ]; then
  echo "[FAIL] ${REQ_FILE} not found. Run this script from the repo root."
  exit 1
fi

echo "[*] Installing Colab overlay packages (no torch reinstall)..."
python3 -m pip install -q --upgrade pip
python3 -m pip install -q -r "$REQ_FILE"

echo "[*] Skipping pytorch3d / flash-attn / xformers / pinned torch."
echo "    Gradio --mock does not need them. Full diffusion needs checkpoints."

mkdir -p ckpts dataRelease gen_rgbd generated_data_v0 \
  outputs/Gradio/houseCrafter/output

echo "============================================================"
echo " Ready. Launch: python app.py --mock --share"
echo "============================================================"
