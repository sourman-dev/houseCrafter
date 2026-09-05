#!/usr/bin/env bash
# Install HouseCrafter wheels into the sidecar Python 3.10 env.
# Does not touch the Colab Jupyter kernel.
set -uo pipefail

PY="${PY:-/content/micromamba/envs/housecrafter/bin/python}"
if [ ! -x "${PY}" ]; then
  echo "[FAIL] sidecar missing: ${PY}"
  echo "Run scripts/colab_py310.sh first."
  exit 1
fi

echo "============================================================"
echo " HouseCrafter deps → ${PY}"
"${PY}" -c "import sys; print('python', sys.version.split()[0])"
echo "============================================================"

echo "[*] PyTorch 2.1.2 + CUDA 12.1 (own copy, not Colab's 2.11)..."
"${PY}" -m pip install -q --upgrade pip
"${PY}" -m pip install -q torch==2.1.2 torchvision==0.16.2 \
  --index-url https://download.pytorch.org/whl/cu121

"${PY}" - <<'PY'
import torch
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
assert torch.cuda.is_available(), "CUDA not visible in sidecar"
PY

try_install() {
  if "${PY}" -m pip install -q "$@"; then
    echo "  OK  $*"
  else
    echo "  SKIP $*"
  fi
}

echo "[*] Python packages (no flash-attn compile)..."
for pkg in \
  "diffusers" \
  "transformers==4.28.1" \
  "accelerate==0.27.2" \
  "safetensors==0.4.1" \
  "einops==0.7.0" \
  "omegaconf==2.3.0" \
  "opencv-python==4.8.1.78" \
  "scipy==1.11.4" \
  "scikit-image==0.22.0" \
  "trimesh==4.3.2" \
  "matplotlib==3.8.2" \
  "tqdm==4.67.0" \
  "pyyaml==6.0.1" \
  "imageio==2.33.1" \
  "lmdb" \
  "networkx" \
  "lpips==0.1.4" \
  "timm==0.9.12" \
  "kornia==0.6.9" \
  "gdown>=5.1.0" \
  "gradio>=4.20.0"
do
  try_install "${pkg}"
done

echo "[*] xformers (optional)..."
try_install "xformers==0.0.23.post1"

echo "[*] pytorch3d wheel for py310+cu121+torch2.1..."
if "${PY}" -m pip install -q --no-index --no-cache-dir pytorch3d \
  -f https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/py310_cu121_pyt210/download.html
then
  echo "  OK  pytorch3d (cu121 wheel)"
else
  echo "  retry pytorch3d from PyPI..."
  try_install pytorch3d
fi

"${PY}" - <<'PY'
import importlib
for name in ("torch", "open3d", "diffusers", "pytorch3d"):
    try:
        m = importlib.import_module(name)
        print(" ", name, getattr(m, "__version__", "ok"))
    except Exception as exc:
        print(" ", name, "MISSING", exc)
PY

echo "============================================================"
echo " Next: download ckpts + dataRelease, then:"
echo "   ${PY} src/generate_scene.py --start 0 --end 1 ..."
echo "============================================================"
