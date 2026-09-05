#!/usr/bin/env bash
# Drive stores the official .tar.gz files (download once).
# Each runtime extracts them onto local /content for generate_scene.py.
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

CACHE_CKPT="${CACHE}/ckpts"
CACHE_DATA="${CACHE}/dataRelease"
WORK_CKPT="${REPO}/ckpts"
WORK_DATA="${REPO}/dataRelease"

tars_ckpt_ok() {
  [ -f "${CACHE_CKPT}/3dfront_layout_iodepth_1871_scene_3m.tar.gz" ] \
    && [ -f "${CACHE_CKPT}/vae-ft-mse-840000-ema-pruned.ckpt" ]
}

tars_data_ok() {
  [ -f "${CACHE_DATA}/layout_samples.tar.gz" ] \
    && [ -f "${CACHE_DATA}/graph_poses_all.tar.gz" ]
}

extracted_ckpt_ok() {
  [ -f "${WORK_CKPT}/3dfront_layout_iodepth_1871_scene_3m/model_index.json" ] \
    || [ -f "${WORK_CKPT}/3dfront_layout_iodepth_1871_scene_3m/image_encoder/config.json" ]
}

extracted_data_ok() {
  [ -d "${WORK_DATA}/layout_samples" ] || [ -d "${WORK_DATA}/rendered_floor_sample" ]
}

echo "[*] repo ${REPO}"

if [ -d "${DRIVE_ROOT}" ]; then
  echo "[*] Drive cache: ${CACHE}"
  mkdir -p "${CACHE_CKPT}" "${CACHE_DATA}"
else
  echo "[!] Drive not mounted — tars will not persist."
  CACHE="${REPO}/.local_cache"
  CACHE_CKPT="${CACHE}/ckpts"
  CACHE_DATA="${CACHE}/dataRelease"
  mkdir -p "${CACHE_CKPT}" "${CACHE_DATA}"
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

if [ "${FORCE}" = "1" ] || ! tars_data_ok; then
  download_folder "${DATA_ID}" "${CACHE_DATA}"
else
  echo "[*] data tars already on Drive — skip gdown"
fi

if [ "${FORCE}" = "1" ] || ! tars_ckpt_ok; then
  download_folder "${CKPT_ID}" "${CACHE_CKPT}"
else
  echo "[*] ckpt tars already on Drive — skip gdown"
fi

# Working copies must be real directories (not Drive symlinks) for speed.
if [ -L "${WORK_CKPT}" ]; then rm -f "${WORK_CKPT}"; fi
if [ -L "${WORK_DATA}" ]; then rm -f "${WORK_DATA}"; fi
mkdir -p "${WORK_CKPT}" "${WORK_DATA}"

if extracted_ckpt_ok; then
  echo "[*] ckpts already extracted locally"
else
  echo "[*] extracting ckpts tars -> ${WORK_CKPT} (local disk)..."
  cp -n "${CACHE_CKPT}/vae-ft-mse-840000-ema-pruned.ckpt" "${WORK_CKPT}/" 2>/dev/null || \
    cp "${CACHE_CKPT}/vae-ft-mse-840000-ema-pruned.ckpt" "${WORK_CKPT}/"
  tar -xzf "${CACHE_CKPT}/3dfront_layout_iodepth_1871_scene_3m.tar.gz" -C "${WORK_CKPT}"
fi

if extracted_data_ok; then
  echo "[*] dataRelease already extracted locally"
else
  echo "[*] extracting data tars -> ${WORK_DATA} (local disk)..."
  for f in "${CACHE_DATA}"/*.tar.gz; do
    [ -f "${f}" ] || continue
    echo "    tar -xzf $(basename "${f}")"
    tar -xzf "${f}" -C "${WORK_DATA}"
  done
  if [ -f "${CACHE_DATA}/3D_front_mapping.csv" ]; then
    cp -n "${CACHE_DATA}/3D_front_mapping.csv" "${WORK_DATA}/" || true
  fi
fi

echo "[*] extracted ckpt? $(extracted_ckpt_ok && echo YES || echo NO)"
echo "[*] extracted data? $(extracted_data_ok && echo YES || echo NO)"
echo "[*] ${WORK_CKPT}:"
ls -lh "${WORK_CKPT}" | head -15
echo "[*] ${WORK_DATA}:"
ls -lh "${WORK_DATA}" | head -15
find "${WORK_CKPT}" -name 'config.json' | head -8
