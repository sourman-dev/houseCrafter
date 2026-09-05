---
phase: 2
title: "Pipeline Bridge and Inference Adapter"
status: pending
priority: P1
effort: "6h"
dependencies: ["phase-01-start.md"]
---

# Phase 2: Pipeline Bridge and Inference Adapter

## Overview
Design and implement a unified inference adapter (`gradio_ui/pipeline_bridge.py`) and 3D processing utilities (`src/utils/ply_converter.py`) that take a 2D floorplan input, coordinate the HouseCrafter diffusion model to generate multi-view RGB-D views, perform 3D TSDF fusion, and output optimized `.ply` files with progress reporting.

## Requirements
- Functional:
  - Provide an `InferencePipeline` class that loads and caches pre-trained diffusion models (`Zero1to3StableDiffusionPipeline`, `UNet2DConditionModel`, `AutoencoderKL`, `CN_encoder`, and `UniDepth`).
  - Accept either:
    - Custom 2D floorplan image (PNG/JPG) with automatic layout preprocessing.
    - Preset scene IDs from `dataRelease/` sample directory.
  - Coordinate the multi-step generation workflow:
    1. 2D Layout & Pose sampling: Generate camera viewpoints and trajectory across rooms/floorplan.
    2. Multi-view RGB-D Diffusion Generation: Progressive generation using DDIM scheduler and cross-frame conditioning.
    3. 3D Fusion & Mesh Extraction: TSDF fusion via `Open3DFuser` and point cloud extraction via `make_pcd_batch`.
    4. Post-processing & Cleaning: Mesh denoising with `denoise_mesh_by_connectedComponents` and height filtering.
    5. PLY File Export: Write `.ply` file compatible with Gradio 3D viewer (`gr.Model3D`).
  - Implement a `MockInferencePipeline` mode for development and testing without requiring 24GB GPU checkpoints.
  - Yield incremental progress events (`gr.Progress` callback) for UI feedback.
- Non-functional:
  - Clean error handling when VRAM is exceeded or input format is invalid.
  - Ensure temp directory cleanup and structured artifact organization.

## Architecture & File Changes
- Create: `gradio_ui/pipeline_bridge.py` (Core adapter and workflow coordinator).
- Create: `src/utils/ply_converter.py` (Helper for point cloud downsampling, mesh conversion, bounding box normalization, and preview rendering).
- Create: `gradio_ui/preset_loader.py` (Helper to list and preview preset sample floorplans from `dataRelease/`).

## Implementation Steps
1. **Develop `src/utils/ply_converter.py`**:
   - Write functions to validate `.ply` files (check vertex count, color channels, normals).
   - Implement `optimize_ply_for_web(ply_path, max_points=200000, voxel_size=0.03)` to ensure fast browser rendering.
   - Implement optional `.ply` to `.glb` converter using `trimesh` for cross-platform 3D viewer compatibility.
2. **Develop `gradio_ui/preset_loader.py`**:
   - Scan `dataRelease/` (`rendered_floor_sample`, `layout_samples`, `graph_poses_all`).
   - Extract scene metadata, thumbnails, and preview information for the UI dropdown.
3. **Develop `gradio_ui/pipeline_bridge.py`**:
   - Implement `HouseCrafterBridge`:
     - `__init__(ckpt_dir, device, fp16=True)`
     - `load_models()`: Lazy loading of UNet, VAE, CN_encoder, and UniDepth.
     - `run_inference(floorplan_input, num_steps=50, depth_mask=2.5, progress_callback=None) -> GenerationResult`
     - Return `GenerationResult` containing paths to:
       - `ply_path`: Cleaned 3D scene point cloud / mesh.
       - `rgb_images`: List of generated RGB views.
       - `depth_images`: List of colormapped depth views.
       - `meta`: Dict with scene ID, execution duration, and vertex count.
   - Implement `MockHouseCrafterBridge` returning sample `.ply` and sample multi-view images for UI dry-runs.

## Success Criteria
- [x] `gradio_ui/pipeline_bridge.py` successfully executes end-to-end generation from 2D floorplan to `.ply`.
- [x] Both real model inference and mock test mode function properly.
- [x] Exported `.ply` files can be read by `open3d` and rendered in web 3D viewers.

## Risk Assessment
- **Risk**: Diffusion inference execution time may trigger Gradio request timeout (>60s).
- **Mitigation**: Use Python generators / streaming progress in Gradio (`yield`) and configure Gradio queue (`app.queue()`) with appropriate timeout settings.
