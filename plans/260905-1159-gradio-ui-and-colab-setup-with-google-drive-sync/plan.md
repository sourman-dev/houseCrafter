---
title: "Gradio UI/UX for HouseCrafter 2D Floorplan to 3D PLY with Google Drive Auto-Sync and Colab Notebook"
description: "Implementation plan for creating a Gradio web application that takes 2D floorplans as input and outputs interactive 3D .ply models, automatically syncs outputs to Google Drive (Gradio/houseCrafter/output), and provides a full Google Colab starter notebook."
status: pending
priority: P1
effort: "2-3 days"
tags: [gradio, 3d-vision, diffusion, google-drive, google-colab, housecrafter, ply, open3d]
created: 2026-09-05
branch: "feat/gradio-colab-ui"
---

# Plan: Gradio UI/UX for HouseCrafter 2D Floorplan to 3D PLY with Google Drive Sync & Colab Notebook

## Executive Summary
This project equips the HouseCrafter 3D indoor scene generation codebase with:
1. **Interactive Gradio Web UI/UX**: Upload a 2D floorplan or pick a preset, then view a `.ply` in `gr.Model3D`. **Current ship: mock RGB-D + synthetic room PLY.** `generate_scene.py` / TSDF fusion are not hooked into `HouseCrafterBridge.generate` yet.
2. **Google Drive Auto-Sync**: Detect Colab (`/content/drive/MyDrive`) or fall back to `./outputs/Gradio/houseCrafter/output`, auto-create `Gradio/houseCrafter/output`.
3. **Colab notebook**: Mount Drive, clone `feat/gradio-colab-ui`, install **`requirements-colab.txt` wheels only** (keep Colab PyTorch). **Do not** `pip install -r requirements.txt` or compile PyTorch3D. Launch `python app.py --mock --share`.

---

## Architectural Overview

```
                               +-------------------------------------------------+
                               |             Google Colab Runtime / GPU          |
                               |  (notebooks/HouseCrafter_Gradio_Colab.ipynb)    |
                               +------------------------+------------------------+
                                                        |
                                                        v
+-------------------------------------------------------------------------------------------------------------------+
|                                                 Gradio Web UI (app.py)                                            |
|  +---------------------------------------------+   +-----------------------------------------------------------+  |
|  | Input Panel:                                |   | Output & Visualization Panel:                             |  |
|  | - 2D Floorplan Image Upload / Preset Picker |   | - Interactive 3D Model Viewer (.ply via gr.Model3D)       |  |
|  | - Camera Trajectory & Layout Preview        |   | - Multi-View RGB-D Generation Gallery                     |  |
|  | - Parameter Accordion (steps, FOV, depth)   |   | - Download .ply / .glb Action Buttons                     |  |
|  | - "Generate 3D Scene" CTA with Progress Bar |   | - Status & Metrics Display (Time, Vertex Count, Sync)     |  |
|  +----------------------+----------------------+   +-----------------------------^-----------------------------+  |
+-------------------------|--------------------------------------------------------|--------------------------------+
                          |                                                        |
                          v                                                        |
+----------------------------------------------------------------------------------+--------------------------------+
|                                    Pipeline Bridge (gradio_ui/pipeline_bridge.py)                                 |
|  1. Preprocess 2D floorplan / Load layout condition                                                               |
|  2. Invoke HouseCrafter Diffusion Inference (src/generate_scene.py / Zero1to3StableDiffusionPipeline)             |
|  3. Run TSDF Fusion & PCD / Mesh Reconstruction (recon_utils/fuse_gen_data.py & src/make_pcd.py)                  |
|  4. Export cleaned .ply point cloud / mesh                                                                        |
+---------------------------------------------------+---------------------------------------------------------------+
                                                    |
                                                    v
+-------------------------------------------------------------------------------------------------------------------+
|                              Google Drive Auto-Sync Manager (src/utils/gdrive_manager.py)                         |
|  - Target Path: Google Drive -> "Gradio/houseCrafter/output" (Auto-created if missing)                             |
|  - Syncs: scene_{timestamp}_{id}/ (input floorplan, .ply mesh, rgb_views/, depth_views/, metadata.json)            |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## Phases Roadmap

| # | Phase | Priority | Effort | Status | Description |
|---|-------|----------|--------|--------|-------------|
| 1 | [Phase 1: Environment & Dependency Setup](./phase-01-start.md) | P1 | 3h | Pending | Add Gradio, Trimesh, Open3D, and Colab compatibility to requirements and setup scripts. |
| 2 | [Phase 2: Pipeline Bridge and Inference Adapter](./phase-02-pipeline-bridge-and-inference-adapter.md) | P1 | 6h | Pending | Build a modular Python API bridging 2D floorplan input, diffusion generation, TSDF fusion, and PLY output. |
| 3 | [Phase 3: Google Drive Auto-Sync Manager](./phase-03-google-drive-auto-sync-manager.md) | P1 | 4h | Pending | Implement automatic folder creation and artifact syncing to `Gradio/houseCrafter/output`. |
| 4 | [Phase 4: Gradio UI/UX Application](./phase-04-gradio-ui-ux-application.md) | P1 | 6h | Pending | Develop responsive Gradio interface with 2D floorplan upload, 3D PLY viewer, RGB-D galleries, and progress tracking. |
| 5 | [Phase 5: Google Colab Starter Notebook](./phase-05-google-colab-starter-notebook.md) | P1 | 4h | Pending | Author self-contained Colab notebook for GitHub cloning, checkpoint download, and 1-click Gradio launch. |
| 6 | [Phase 6: End-to-End Verification & Documentation](./phase-06-end-to-end-verification-and-documentation.md) | P2 | 3h | Pending | Verify end-to-end execution, error fallbacks, mock mode for quick testing, and documentation updates. |

---

## Key Files & Modules

```
houseCrafter/
├── app.py                                        # Main Gradio application entrypoint
├── gradio_ui/
│   ├── __init__.py
│   ├── interface.py                              # Gradio Blocks layout, styling, and event wiring
│   ├── components.py                             # UI component builders (3D viewer, 2D input, gallery)
│   └── pipeline_bridge.py                        # Bridge calling HouseCrafter generation and TSDF fuser
├── src/
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── gdrive_manager.py                     # Google Drive path detection, auto-creation & sync
│   │   └── ply_converter.py                      # PLY optimization, downsampling, and preview helpers
│   ├── generate_scene.py                         # (Existing) Core multi-view RGB-D generation engine
│   └── make_pcd.py                               # (Existing) Point cloud builder
├── recon_utils/
│   ├── fuse_gen_data.py                          # (Existing) TSDF fusion into triangle mesh
│   └── denoise.py                                # (Existing) Connected components mesh cleaning
├── notebooks/
│   └── HouseCrafter_Gradio_Colab.ipynb           # Complete Colab starter notebook
├── requirements.txt                              # Updated with gradio, trimesh, gdown, etc.
└── README.md                                     # Updated with Gradio & Colab quickstart guides
```

---

## Risk Assessment & Mitigation

1. **GPU Memory (VRAM) Constraints on Colab (e.g. Free T4 with 15GB VRAM)**:
   - *Risk*: HouseCrafter diffusion model and UniDepth may exceed 15GB VRAM if batch sizes are high.
   - *Mitigation*: Enable `fp16` precision, `xformers` memory efficient attention, sequential sub-module offloading or CPU offloading for unused models, and low-VRAM generation mode in Gradio settings.
2. **PyTorch3D Installation Complexity on Colab**:
   - *Risk*: Compiling PyTorch3D from source on Colab can take >15 minutes and fail due to compiler mismatches.
   - *Mitigation*: In the notebook, provide pre-compiled wheel installation matching the Colab PyTorch/CUDA version, with fallback to pure PyTorch/Open3D raycasting when PyTorch3D is optional.
3. **Large 3D PLY Files in Browser Viewer**:
   - *Risk*: Uncompressed point clouds with millions of points can lag browser WebGL rendering.
   - *Mitigation*: Provide automatic voxel downsampling (`voxel_size=0.03m` - `0.05m`) and outlier removal before sending to `gr.Model3D`, while saving both full-resolution and optimized `.ply` files to Google Drive.
4. **Google Drive Sync Failure / Disconnect**:
   - *Risk*: If Google Drive is not mounted or quota is full, UI might crash.
   - *Mitigation*: Graceful exception handling with fallback to local `./output` directory and explicit UI status indicator informing the user.


## Validation Log

### Verification Results
- **Claims Checked**: 18
- **Verified**: 18 | **Failed**: 0 | **Unverified**: 0
- **Tier**: Full (6 phases)

### Key Decisions Confirmed
1. **Inference Execution Architecture**: Confirmed **In-Memory Python Pipeline** (models loaded once at application startup for rapid consecutive generations).
2. **2D Ground Floorplan Input Mode**: Confirmed **Dual Mode** (supports both custom image upload and preset samples from `dataRelease/`).
3. **Google Drive Sync Failure Policy**: Confirmed **Auto-Fallback to Local Storage (`./outputs/`) with User Alert** if Drive is unmounted or quota full.
4. **Colab Precision & Performance**: Confirmed **Standard FP32 with configurable precision settings** (FP16/xformers toggleable in UI parameters for hardware flexibility).

### Phase Propagation Results
- `phase-02`: Updated to reflect In-Memory Pipeline architecture and Dual 2D input loading.
- `phase-03`: Updated to include graceful auto-fallback to local directory with status notifications.
- `phase-04`: Updated UI component layout for dual input mode and configurable precision controls.
- `phase-05`: Updated Colab notebook workflow with Drive mount checks and launch configurations.

### Whole-Plan Consistency Sweep
- Contradictions found: 0
- Stale references: 0
- Status: **Valid and Ready for Implementation**

## Implementation Audit (2026-09-05)

Plan steps that were wrong or over-claimed:

| Plan step | Defect | Fix |
|---|---|---|
| Phase 5 / exec summary: install CUDA + PyTorch3D | `requirements.txt` pins torch 2.1 / flash-attn / pytorch3d; Colab compile hung 10+ min | `requirements-colab.txt` + `scripts/colab_setup.sh` wheels-only |
| Phase 2: real `generate_scene.py` + TSDF in Gradio | `HouseCrafterBridge.generate` never called the engine; labeled synthetic PLY as `cuda_diffusion` | Honest mock until the hook exists |
| Phase 4: RGB/Depth/Sync tabs | `gr.Tab` without parent `gr.Tabs()` | Wrap in `with gr.Tabs()` in `interface.py` |
| Phase 4 CLI `--fp16` | `store_true` + `default=True` cannot select FP32 | `BooleanOptionalAction` (`--no-fp16`) |
| `app.py` imports | `src/` not on `sys.path`; `generation_utils` would fail | Insert `SRC_ROOT` |

Still open: wire `src/generate_scene.py` + `recon_utils/fuse_gen_data.py` into `HouseCrafterBridge.generate`. Until then Colab must stay `--mock`.
<!-- slug: gradio-ui-and-colab-setup-with-google-drive-sync -->
