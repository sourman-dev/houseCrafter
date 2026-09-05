---
phase: 4
title: "Gradio UI/UX Application"
status: pending
priority: P1
effort: "6h"
dependencies: ["phase-02-pipeline-bridge-and-inference-adapter.md", "phase-03-google-drive-auto-sync-manager.md"]
---

# Phase 4: Gradio UI/UX Application

## Overview
Develop the complete Gradio web application (`app.py`, `gradio_ui/interface.py`, and `gradio_ui/components.py`) providing an intuitive, modern interface to upload 2D ground floor plans, tune inference and reconstruction settings, interactively inspect 3D `.ply` models in-browser, explore multi-view RGB-D generations, and monitor Google Drive synchronization.

## Requirements
- Functional:
  - **Header Banner**:
    - Project title: "HouseCrafter: 2D Floorplan to 3D Indoor Scene Generator".
    - System status badges: GPU device name, VRAM available, active checkpoint path, and Google Drive target directory.
  - **Input Panel (Left Column)**:
    - Mode Tab 1: "Upload 2D Floorplan" (`gr.Image(type="filepath", label="2D Floorplan Layout")`).
    - Mode Tab 2: "Preset Samples" (Dropdown with thumbnails from `dataRelease/`).
    - Accordion: "Advanced Generation Settings":
      - `DDIM Steps` (Slider: 10 - 100, default 50).
      - `Guidance Scale` (Slider: 1.0 - 15.0, default 7.5).
      - `Depth Threshold` (Slider: 1.0 - 5.0m, default 2.5m).
      - `TSDF Voxel Size` (Slider: 0.02 - 0.10m, default 0.05m).
      - `Random Seed` (Number input, -1 for random).
      - `Auto-sync to Google Drive` (Checkbox, default True).
    - CTA Buttons:
      - "🚀 Generate 3D Scene" (Primary highlighted button).
      - "🧹 Clear / Reset" (Secondary button).
  - **Output Panel (Right Column)**:
    - Interactive 3D Model Viewer:
      - `gr.Model3D(label="Interactive 3D Scene (.ply)", display_mode="solid", clear_color=[0.08, 0.08, 0.12, 1.0])`.
      - Download `.ply` file button.
    - Secondary Output Tabs:
      - Tab 1: "Multi-View RGB Gallery" (`gr.Gallery` with grid preview).
      - Tab 2: "Depth Maps" (`gr.Gallery` with colormapped depths).
      - Tab 3: "Google Drive Sync & Metadata" (Markdown table with saved folder path, file sizes, point count, and JSON download).
  - **Asynchronous Execution & Streaming**:
    - Implement streaming progress reporting via `gr.Progress()`:
      1. Preprocessing 2D floorplan layout.
      2. Diffusion sampling multi-view RGB-D images.
      3. Running TSDF volume fusion & mesh extraction.
      4. Denoising & optimizing 3D `.ply` point cloud.
      5. Synchronizing artifacts to `Gradio/houseCrafter/output`.
- Non-functional:
  - Clean responsive design adapting to both desktop and mobile viewports.
  - Gradio queue enabled (`demo.queue()`) for reliable long-running job processing.
  - CLI argument parsing (`--share`, `--port`, `--server_name`, `--mock`, `--gdrive_dir`, `--ckpt_path`).

## Architecture & File Changes
- Create: `app.py` (CLI entrypoint and application launcher).
- Create: `gradio_ui/__init__.py`
- Create: `gradio_ui/interface.py` (Layout construction and event wiring).
- Create: `gradio_ui/components.py` (Modular UI component definitions).
- Create: `gradio_ui/styles.py` (Custom CSS styling and theme configuration).

## Implementation Steps
1. **Develop `gradio_ui/styles.py`**:
   - Define custom CSS for clean typography, container card styling, and 3D canvas viewport sizing.
2. **Develop `gradio_ui/components.py`**:
   - Build reusable component blocks (System status bar, 2D input controls, 3D viewer wrapper, RGB-D galleries).
3. **Develop `gradio_ui/interface.py`**:
   - Assemble the Gradio Blocks layout.
   - Wire input changes to preview handlers (e.g. updating floorplan thumbnail on preset select).
   - Wire generate button to `pipeline_bridge.generate(...)` with progress generator yielding intermediate states.
   - Wire Google Drive manager to trigger automatic upload on completion.
4. **Develop `app.py`**:
   - Parse CLI arguments: `--share`, `--port`, `--server_name`, `--gdrive_dir`, `--ckpt_path`, `--mock`.
   - Initialize `GDriveSyncManager` and `HouseCrafterBridge` (or `MockHouseCrafterBridge` if `--mock`).
   - Launch `demo.queue().launch(share=args.share, server_name=args.server_name, server_port=args.port)`.

## Success Criteria
- [x] `python app.py --mock` launches Gradio UI successfully on `http://localhost:7860`.
- [x] 2D floorplan upload and preset selection populate input cleanly.
- [x] 3D `.ply` model renders interactively inside `gr.Model3D`.
- [x] Multi-view RGB and depth galleries display properly.
- [x] Download buttons deliver valid `.ply` files.
- [x] Google Drive sync status updates dynamically on UI.

## Risk Assessment
- **Risk**: Some browser WebGL implementations might struggle with raw point clouds exceeding 500k vertices.
- **Mitigation**: Automatically voxel-downsample the preview `.ply` sent to `gr.Model3D` while keeping the full-fidelity `.ply` available for download and Google Drive storage.
