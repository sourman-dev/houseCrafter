#!/usr/bin/env bash
# ==============================================================================
# HouseCrafter Google Colab Environment Setup Script
# Installs dependencies, sets up PyTorch3D, and prepares folders.
# ==============================================================================

set -e

echo "============================================================"
echo " 🚀 Setting up HouseCrafter Environment for Google Colab"
echo "============================================================"

# 1. Verify GPU
echo "[*] Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "[!] Warning: No GPU detected. Running in CPU/Mock mode."
fi

# 2. Install pip dependencies
echo "[*] Installing Python packages from requirements.txt..."
pip install -r requirements.txt --quiet || pip install -r requirements.txt

# 3. Ensure UI and 3D packages
echo "[*] Installing Gradio, Open3D, Trimesh, and gdown..."
pip install gradio>=4.20.0 open3d trimesh gdown plyfile pyngrok --quiet

# 4. Attempt PyTorch3D wheel installation
echo "[*] Configuring PyTorch3D..."
python3 -c "import pytorch3d" 2>/dev/null && echo "  [OK] PyTorch3D already available." || {
    echo "  [*] Installing PyTorch3D precompiled wheel..."
    pip install --no-index --no-cache-dir pytorch3d -f https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/py310_cu121_pyt210/download.html || {
        echo "  [!] Precompiled wheel not matching, trying pip install pytorch3d..."
        pip install pytorch3d || echo "  [!] PyTorch3D install skipped (fallback active)."
    }
}

# 5. Create directories
echo "[*] Preparing workspace directories..."
mkdir -p ckpts
mkdir -p dataRelease
mkdir -p gen_rgbd
mkdir -p generated_data_v0
mkdir -p outputs/Gradio/houseCrafter/output

echo "============================================================"
echo " ✅ HouseCrafter environment is ready!"
echo "============================================================"
