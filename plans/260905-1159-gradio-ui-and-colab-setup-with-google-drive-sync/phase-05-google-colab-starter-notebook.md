---
phase: 5
title: "Google Colab Starter Notebook"
status: pending
priority: P1
effort: "4h"
dependencies: ["phase-04-gradio-ui-ux-application.md"]
---

# Phase 5: Google Colab Starter Notebook

## Overview
Author a self-contained, 1-click executable Google Colab Jupyter Notebook (`notebooks/HouseCrafter_Gradio_Colab.ipynb`) that sets up the environment, clones the repository from GitHub on branch `feat/gradio-colab-ui`, mounts Google Drive, downloads pre-trained models/sample data, and launches the Gradio UI with a public sharing link (`share=True`).

## Requirements
- Functional:
  - Provide an "Open In Colab" compatible `.ipynb` notebook file.
  - Cell Structure:
    1. **Markdown Introduction**: Description, requirements, and workflow overview.
    2. **Step 1: GPU & CUDA Environment Check**:
       - Verify GPU availability (`torch.cuda.is_available()`).
       - Display GPU name, VRAM size, and CUDA version (`!nvidia-smi`).
    3. **Step 2: Mount Google Drive & Setup Output Folder**:
       - Mount Drive via `google.colab.drive.mount('/content/drive')`.
       - Create target folder `/content/drive/MyDrive/Gradio/houseCrafter/output`.
    4. **Step 3: Clone / Fetch Repository**:
       - Clone `https://github.com/neu-vi/houseCrafter.git` into `/content/houseCrafter`.
       - Checkout `feat/gradio-colab-ui` branch (or pull latest changes).
    5. **Step 4: Install Dependencies & Packages**:
       - Install `requirements.txt` with accelerated wheels for Colab.
       - Install `gradio`, `open3d`, `trimesh`, `gdown`, and `pytorch3d`.
    6. **Step 5: Download Checkpoints and Sample Data**:
       - Download pre-trained weights to `ckpts/` (or check if already cached in user's Drive to save bandwidth).
       - Download sample data to `dataRelease/`.
    7. **Step 6: Launch Gradio Web Application**:
       - Execute `!python app.py --share --gdrive_dir "/content/drive/MyDrive/Gradio/houseCrafter/output"`.
       - Output public Gradio URL (`https://xxxx.gradio.live`).
    8. **Step 7: Inspect Google Drive Outputs**:
       - Provide helper cell to inspect synced 3D scenes in Drive.
- Non-functional:
  - Idempotent execution: cells can be re-run safely without error.
  - Robust download logic with integrity verification.

## Architecture & File Changes
- Create: `notebooks/HouseCrafter_Gradio_Colab.ipynb` (Jupyter notebook with complete markdown and code cells).
- Create: `scripts/colab_setup.sh` (Helper bash script for fast setup if user prefers single shell execution).

## Implementation Steps
1. **Develop `scripts/colab_setup.sh`**:
   - Write automated shell script that installs packages, verifies GPU, and checks model directories.
2. **Author `notebooks/HouseCrafter_Gradio_Colab.ipynb`**:
   - Construct notebook JSON containing all formatted markdown explanations and code cells.
   - Include clear troubleshooting tips for common Colab issues (e.g. CUDA out-of-memory, Google Drive disconnect, public share link expiration).
3. **Verify Notebook Syntax & Execution Flow**:
   - Test JSON validity of `.ipynb`.
   - Ensure all paths (`/content/...`) and relative links match standard Colab filesystem structure.

## Success Criteria
- [x] `notebooks/HouseCrafter_Gradio_Colab.ipynb` is formatted as a valid `.ipynb` file.
- [x] Colab cells cover end-to-end flow: Drive mount → Git clone → Package install → Checkpoint download → Gradio launch.
- [x] Public Gradio link is generated and outputs automatically land in `/content/drive/MyDrive/Gradio/houseCrafter/output`.

## Risk Assessment
- **Risk**: Google Drive download quotas on public links can occasionally throttle `gdown`.
- **Mitigation**: Support both official Google Drive links and Hugging Face mirror fallbacks, plus support using checkpoints already saved in the user's Google Drive.
