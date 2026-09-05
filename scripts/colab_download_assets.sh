#!/usr/bin/env bash
# Cache ckpts + dataRelease on Google Drive after a *complete* download.
set -uo pipefail

PY="${PY:-/content/micromamba/envs/housecrafter/bin/python}"
REPO="${1:-.}"
cd "${REPO}"
REPO="$(pwd)"

DRIVE_ROOT="/content/drive/MyDrive"
CACHE="${GDRIVE_CACHE:-${DRIVE_ROOT}/Gradio/houseCrafter/cache}"
DATA_ID="18p5m_RN5O9zDNe80ertQJPjEDTqAqTM-"
CKPT_ID="1OY_V9nV5kOfGLa6oSlZMzVp0vRst2g3Y"
FORCE="${FORCE:-0}"

ckpts_ready() {
  local dir="$1"
  [ -f "${dir}/3dfront_layout_iodepth_1871_scene_3m/model_index.json" ] \
    || [ -f "${dir}/3dfront_layout_iodepth_1871_scene_3m/image_encoder/config.json" ] \
    || [ -f "${dir}/image_encoder/config.json" ] \
    || [ -f "${dir}/model_index.json" ]
}

data_ready() {
  local dir="$1"
  [ -d "${dir}/layout_samples" ] || [ -d "${dir}/rendered_floor_sample" ] \
    || [ -f "${dir}/val_scenes_300_3000.json" ]
}

link_into_repo() {
  local src="$1"
  local dest="$2"
  rm -rf "${dest}"
  ln -sfn "${src}" "${dest}"
  echo "[*] ${dest} -> ${src}"
}

echo "[*] repo ${REPO} FORCE=${FORCE}"

if [ -d "${DRIVE_ROOT}" ]; then
  echo "[*] Drive mounted. Cache: ${CACHE}"
  mkdir -p "${CACHE}/ckpts" "${CACHE}/dataRelease"
else
  echo "[!] Drive not mounted. Using local cache."
  CACHE="${REPO}/.local_cache"
  mkdir -p "${CACHE}/ckpts" "${CACHE}/dataRelease"
fi

if [ "${FORCE}" = "1" ]; then
  echo "[*] FORCE=1 — will gdown even if cache looks full"
fi

# Promote a *complete* local download into Drive (not a half-copied dir).
if ckpts_ready "${REPO}/ckpts" && ! ckpts_ready "${CACHE}/ckpts"; then
  echo "[*] copying complete local ckpts -> Drive..."
  mkdir -p "${CACHE}/ckpts"
  cp -a "${REPO}/ckpts/." "${CACHE}/ckpts/"
fi
if data_ready "${REPO}/dataRelease" && ! data_ready "${CACHE}/dataRelease"; then
  echo "[*] copying complete local dataRelease -> Drive..."
  mkdir -p "${CACHE}/dataRelease"
  cp -a "${REPO}/dataRelease/." "${CACHE}/dataRelease/"
fi

"${PY}" -m pip install -q --upgrade "gdown>=5.2.0"

download_folder() {
  local id="$1"
  local dest="$2"
  mkdir -p "${dest}"
  echo "[*] gdown ${id} -> ${dest}"
  "${PY}" -m gdown --folder "${id}" -O "${dest}" \
    || "${PY}" -m gdown --folder \
         "https://drive.google.com/drive/folders/${id}" -O "${dest}"
}

if [ "${FORCE}" = "1" ] || ! data_ready "${CACHE}/dataRelease"; then
  download_folder "${DATA_ID}" "${CACHE}/dataRelease"
else
  echo "[*] dataRelease cache OK — skip gdown"
fi

if [ "${FORCE}" = "1" ] || ! ckpts_ready "${CACHE}/ckpts"; then
  download_folder "${CKPT_ID}" "${CACHE}/ckpts"
else
  echo "[*] ckpts cache OK — skip gdown"
fi

link_into_repo "${CACHE}/ckpts" "${REPO}/ckpts"
link_into_repo "${CACHE}/dataRelease" "${REPO}/dataRelease"

echo "[*] ckpts ready? $(ckpts_ready "${CACHE}/ckpts" && echo YES || echo NO)"
echo "[*] data ready? $(data_ready "${CACHE}/dataRelease" && echo YES || echo NO)"
echo "[*] ckpts listing:"
ls -lh "${REPO}/ckpts/" | head -20
echo "[*] dataRelease listing:"
ls -lh "${REPO}/dataRelease/" | head -20
find "${REPO}/ckpts" -name 'config.json' | head -10
find "${REPO}/ckpts" -name 'model_index.json' | head -5
