#!/usr/bin/env bash
# HouseCrafter Colab setup: keep Colab PyTorch, install wheels one-by-one.
# Never compile pytorch3d / flash-attn. Never abort the whole overlay
# because one optional package (open3d) has no cp313 wheel.

set -uo pipefail

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

echo "[*] Upgrading pip..."
python3 -m pip install -q --upgrade pip || true

try_install() {
  local pkg="$1"
  if python3 -m pip install -q "$pkg"; then
    echo "  OK  ${pkg}"
    return 0
  fi
  echo "  SKIP ${pkg} (no wheel for this Python — mock UI still works)"
  return 0
}

echo "[*] Installing overlay packages one-by-one..."
while IFS= read -r raw || [ -n "$raw" ]; do
  pkg="${raw%%#*}"
  pkg="${pkg#"${pkg%%[![:space:]]*}"}"
  pkg="${pkg%"${pkg##*[![:space:]]}"}"
  [ -z "$pkg" ] && continue
  try_install "$pkg"
done < "$REQ_FILE"

echo "[*] Optional Open3D (often missing on Python 3.13)..."
try_install "open3d"

echo "[*] Skipping pytorch3d / flash-attn / xformers / pinned torch."

mkdir -p ckpts dataRelease gen_rgbd generated_data_v0 \
  outputs/Gradio/houseCrafter/output

echo "[*] Verifying Gradio (required for the UI)..."
if python3 -c "import gradio; print('gradio', gradio.__version__)"; then
  echo "============================================================"
  echo " Ready. Launch: python app.py --mock --share"
  echo "============================================================"
  exit 0
fi

echo "[FAIL] gradio did not import. Retry: pip install gradio"
exit 1
