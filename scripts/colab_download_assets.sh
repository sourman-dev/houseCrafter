#!/usr/bin/env bash
# Cache ckpts + dataRelease on Google Drive after the first download.
# Later Colab runtimes only symlink; they do not gdown again.
set -uo pipefail

PY="${PY:-/content/micromamba/envs/housecrafter/bin/python}"
REPO="${1:-.}"
cd "${REPO}"
REPO="$(pwd)"

DRIVE_ROOT="/content/drive/MyDrive"
CACHE="${GDRIVE_CACHE:-${DRIVE_ROOT}/Gradio/houseCrafter/cache}"
DATA_ID="18p5m_RN5O9zDNe80ertQJPjEDTqAqTM-"
CKPT_ID="1OY_V9nV5kOfGLa6oSlZMzVp0vRst2g3Y"

cache_ready() {
  local dir="$1"
  [ -d "${dir}" ] && [ "$(find "${dir}" -type f 2>/dev/null | head -1)" ]
}

link_into_repo() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "${dest}")"
  rm -rf "${dest}"
  ln -sfn "${src}" "${dest}"
  echo "[*] ${dest} -> ${src}"
}

echo "[*] repo ${REPO}"

if [ -d "${DRIVE_ROOT}" ]; then
  echo "[*] Drive mounted. Cache: ${CACHE}"
  mkdir -p "${CACHE}/ckpts" "${CACHE}/dataRelease"
else
  echo "[!] Drive not mounted. Downloading into the runtime only (lost on reset)."
  CACHE="${REPO}/.local_cache"
  mkdir -p "${CACHE}/ckpts" "${CACHE}/dataRelease"
fi

# If a previous Step 5 filled the repo dirs, copy once into Drive cache.
for name in ckpts dataRelease; do
  local_dir="${REPO}/${name}"
  cache_dir="${CACHE}/${name}"
  if cache_ready "${local_dir}" && ! cache_ready "${cache_dir}"; then
    echo "[*] copying existing ${name} -> Drive cache..."
    mkdir -p "${cache_dir}"
    cp -a "${local_dir}/." "${cache_dir}/"
  fi
done

need_gdown=0
cache_ready "${CACHE}/dataRelease" || need_gdown=1
cache_ready "${CACHE}/ckpts" || need_gdown=1

if [ "${need_gdown}" -eq 1 ]; then
  echo "[*] cache incomplete — downloading with gdown..."
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
  cache_ready "${CACHE}/dataRelease" || download_folder "${DATA_ID}" "${CACHE}/dataRelease"
  cache_ready "${CACHE}/ckpts" || download_folder "${CKPT_ID}" "${CACHE}/ckpts"
else
  echo "[*] Drive cache already has files — skip gdown."
fi

link_into_repo "${CACHE}/ckpts" "${REPO}/ckpts"
link_into_repo "${CACHE}/dataRelease" "${REPO}/dataRelease"

echo "[*] ckpts:"
ls -lh "${REPO}/ckpts" | head -15
echo "[*] dataRelease:"
ls -lh "${REPO}/dataRelease" | head -15
