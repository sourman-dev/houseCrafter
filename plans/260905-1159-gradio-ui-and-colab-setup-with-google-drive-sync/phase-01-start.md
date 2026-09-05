---
phase: 1
title: "Environment and Dependency Setup"
status: pending
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: Environment and Dependency Setup

## Overview
Prepare the Python environment, dependencies, and configuration to support the Gradio web interface, 3D point cloud/mesh processing, Google Drive management, and Google Colab execution without breaking existing HouseCrafter training or dataset modules.

## Requirements
- Functional:
  - Add `gradio>=4.20.0` (with 3D viewing support `gr.Model3D`), `trimesh>=4.3.0`, `gdown>=5.1.0`, and `pyngrok` (optional for Colab tunnels) to `requirements.txt` and `environment.yml`.
  - Ensure compatibility with Python 3.10, PyTorch 2.1.0 / 2.2.0+, CUDA 11.8 / 12.1, `open3d>=0.18.0`, and `diffusers`.
  - Provide a dedicated environment verification utility script (`scripts/verify_env.py`) to validate CUDA, GPU VRAM, Open3D, Gradio, and Google Drive access before running inference.
- Non-functional:
  - Keep core requirements clean and avoid dependency conflicts between Hugging Face `diffusers`, `transformers`, `torchvision`, and `gradio`.

## Architecture & File Changes
- Modify: `requirements.txt` (Append Gradio UI, 3D tools, and Colab utilities).
- Modify: `environment.yml` (Ensure pip section includes new packages).
- Create: `scripts/verify_env.py` (Pre-flight sanity checker for local and Colab environments).

## Implementation Steps
1. **Update `requirements.txt`**:
   - Add `gradio>=4.20.0`
   - Add `gdown>=5.1.0` (for direct Google Drive checkpoint download)
   - Add `trimesh>=4.3.0`
   - Add `plyfile>=1.0.0`
   - Add `pyngrok` (optional tunneling fallback)
2. **Update `environment.yml`**:
   - Synchronize conda pip dependencies with the updated `requirements.txt`.
3. **Develop `scripts/verify_env.py`**:
   - Check CUDA device availability and VRAM size (warning if <12GB).
   - Test Open3D PLY reading and point cloud creation.
   - Test Gradio import and Model3D component initialization.
   - Test Google Drive path accessibility and permission to create `Gradio/houseCrafter/output`.

## Success Criteria
- [x] `requirements.txt` and `environment.yml` updated with all required UI and 3D packages.
- [x] `python scripts/verify_env.py` executes successfully on both local workstation and Colab.
- [x] No version regression on `diffusers` or `torchvision`.

## Risk Assessment
- **Risk**: Conflicting version requirements between older `transformers==4.28.1` and modern `gradio`.
- **Mitigation**: Pin compatible `gradio` version (e.g. `gradio>=4.20.0,<=4.44.0`) that does not enforce restrictive upper bounds on `transformers` or `pydantic`.
