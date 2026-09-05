#!/usr/bin/env bash
# Sidecar Python 3.10 on Colab — do NOT replace /usr/bin/python3.
# The Medium apt-get + update-alternatives trick leaves the Jupyter kernel
# on 3.13 and often breaks apt. This env is only used as:
#   $MAMBA_ROOT/envs/housecrafter/bin/python
set -euo pipefail

ROOT="${MAMBA_ROOT:-/content/micromamba}"
ENV_NAME="housecrafter"
BIN="${ROOT}/envs/${ENV_NAME}/bin/python"

echo "============================================================"
echo " Colab sidecar: Python 3.10 (kernel stays ${PY:-unchanged})"
echo "============================================================"
echo "[*] Notebook kernel (this process if any):"
python3 - <<'PY' || true
import sys
print("  kernel", sys.version.split()[0], sys.executable)
PY

if [ ! -x "${ROOT}/bin/micromamba" ]; then
  echo "[*] Installing micromamba into ${ROOT}..."
  mkdir -p "${ROOT}"
  curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xj -C "${ROOT}" --strip-components=1 bin/micromamba
fi

export MAMBA_ROOT_PREFIX="${ROOT}"
MM="${ROOT}/bin/micromamba"

if [ ! -x "${BIN}" ]; then
  echo "[*] Creating env ${ENV_NAME} with Python 3.10..."
  "${MM}" create -y -p "${ROOT}/envs/${ENV_NAME}" python=3.10 pip -c conda-forge
fi

echo "[*] Sidecar python:"
"${BIN}" - <<'PY'
import sys
print("  sidecar", sys.version.split()[0], sys.executable)
assert sys.version_info[:2] == (3, 10), sys.version
PY

echo "[*] Installing Open3D into the 3.10 env (has cp310 wheels)..."
"${BIN}" -m pip install -q --upgrade pip
"${BIN}" -m pip install -q "open3d==0.18.0" || "${BIN}" -m pip install -q open3d

"${BIN}" - <<'PY'
import open3d as o3d
print("  open3d", o3d.__version__, "OK")
PY

echo "============================================================"
echo " Use this interpreter for HouseCrafter, not the notebook kernel:"
echo "   ${BIN}"
echo "============================================================"
