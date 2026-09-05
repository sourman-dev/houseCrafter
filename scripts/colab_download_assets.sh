#!/usr/bin/env bash
# Download HouseCrafter sample data + checkpoints with sidecar gdown.
set -uo pipefail

PY="${PY:-/content/micromamba/envs/housecrafter/bin/python}"
ROOT="${1:-.}"
cd "${ROOT}"

DATA_ID="18p5m_RN5O9zDNe80ertQJPjEDTqAqTM-"
CKPT_ID="1OY_V9nV5kOfGLa6oSlZMzVp0vRst2g3Y"

echo "[*] upgrading gdown..."
"${PY}" -m pip install -q --upgrade "gdown>=5.2.0"

download_folder() {
  local id="$1"
  local dest="$2"
  mkdir -p "${dest}"
  echo "[*] gdown folder ${id} -> ${dest}"
  if "${PY}" -m gdown --folder "${id}" -O "${dest}"; then
    return 0
  fi
  echo "[*] retry with full Drive URL..."
  "${PY}" -m gdown --folder \
    "https://drive.google.com/drive/folders/${id}" -O "${dest}"
}

download_folder "${DATA_ID}" "dataRelease"
download_folder "${CKPT_ID}" "ckpts"

echo "[*] dataRelease:"
ls -lh dataRelease | head -20
echo "[*] ckpts:"
ls -lh ckpts | head -20
