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

try_install() {
  if "${PY}" -m pip install -q "$@"; then
    echo "  OK  $*"
    return 0
  fi
  echo "  SKIP $*"
  return 0
}

echo "[*] Pin NumPy 1.26 (torch 2.1 is not NumPy 2 compatible)..."
"${PY}" -m pip install -q --upgrade pip
"${PY}" -m pip install -q "numpy==1.26.4"

echo "[*] Remove PyPI diffusers if present (repo vendors src/diffusers)..."
"${PY}" -m pip uninstall -y diffusers >/dev/null 2>&1 || true

echo "[*] PyTorch 2.1.2 + CUDA 12.1..."
"${PY}" -m pip install -q torch==2.1.2 torchvision==0.16.2 \
  --index-url https://download.pytorch.org/whl/cu121

"${PY}" - <<'PY'
import numpy as np
import torch
print("numpy", np.__version__)
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
    x = torch.zeros(1, device="cuda")
    print("cuda tensor", x.device)
assert np.__version__.startswith("1.26"), np.__version__
assert torch.cuda.is_available(), "CUDA not visible in sidecar"
PY

echo "[*] HuggingFace stack matching transformers 4.28..."
try_install "huggingface-hub==0.25.2"
try_install "transformers==4.28.1"
try_install "accelerate==0.27.2"
try_install "safetensors==0.4.5"

echo "[*] Remaining packages..."
for pkg in \
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
  "gdown>=5.1.0"
do
  try_install "${pkg}"
done

echo "[*] xformers (optional)..."
try_install "xformers==0.0.23.post1"

echo "[*] pytorch3d deps then official wheel..."
try_install fvcore iopath
if "${PY}" -m pip install -q --no-index --no-cache-dir pytorch3d \
  -f https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/py310_cu121_pyt210/download.html
then
  echo "  OK  pytorch3d (cu121 / torch2.1 wheel)"
else
  echo "  SKIP pytorch3d wheel"
fi

echo "[*] torch-scatter (pyg wheel for torch 2.1 cu121)..."
if "${PY}" -m pip install -q torch-scatter \
  -f https://data.pyg.org/whl/torch-2.1.0+cu121.html
then
  echo "  OK  torch-scatter"
else
  try_install torch-scatter
fi
try_install pandas
try_install wandb

"${PY}" - <<'PY'
import importlib
for name in ("numpy", "torch", "open3d", "transformers", "pytorch3d", "torch_scatter"):
    try:
        m = importlib.import_module(name)
        extra = ""
        if name == "torch":
            extra = " cuda=" + str(m.cuda.is_available())
        print(" ", name, getattr(m, "__version__", "ok"), extra)
    except Exception as exc:
        print(" ", name, "MISSING", type(exc).__name__, exc)
PY

echo "============================================================"
echo " Need: numpy 1.26, torch 2.1.2 cuda True, pytorch3d, torch_scatter"
echo " Then Step 5 cache + Step 6 generate_scene.py"
echo "============================================================"
