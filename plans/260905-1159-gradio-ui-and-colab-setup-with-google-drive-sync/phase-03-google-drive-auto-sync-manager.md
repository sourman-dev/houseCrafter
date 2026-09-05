---
phase: 3
title: "Google Drive Auto-Sync Manager"
status: pending
priority: P1
effort: "4h"
dependencies: ["phase-01-start.md"]
---

# Phase 3: Google Drive Auto-Sync Manager

## Overview
Implement an automated synchronization service (`src/utils/gdrive_manager.py`) that detects the Google Colab environment or local environment, automatically creates the target folder `Gradio/houseCrafter/output` if it does not exist, and syncs all generated 3D models (`.ply`), 2D inputs, multi-view RGB-D images, and metadata.

## Requirements
- Functional:
  - Auto-detect Google Drive mount point in Google Colab (`/content/drive/MyDrive`).
  - Automatically create target folder: `Gradio/houseCrafter/output` (e.g. `/content/drive/MyDrive/Gradio/houseCrafter/output`) on initialization.
  - Support fallback local output folder (`./outputs/Gradio/houseCrafter/output`) when running locally or if Google Drive is not mounted.
  - Allow user configuration via `--gdrive_dir` CLI flag or `GDRIVE_OUTPUT_DIR` environment variable.
  - Per-generation sync protocol:
    - Create timestamped scene directory: `scene_{YYYYMMDD_HHMMSS}_{scene_id}/`.
    - Save 3D files: `scene_3d.ply`, `scene_3d_cleaned.ply`, and optional `scene_3d.glb`.
    - Save 2D floorplan input: `input_floorplan.png`.
    - Save multi-view subfolders: `rgb_views/` (PNGs) and `depth_views/` (PNGs + colormaps).
    - Save metadata: `metadata.json` containing generation timestamp, prompt/settings, bounding box metrics, vertex count, and execution time.
    - Append entry to `output_index.json` in the root of the output directory for historical tracking.
  - Expose API methods:
    - `is_gdrive_available() -> bool`
    - `ensure_output_dir() -> Path`
    - `sync_generation_artifacts(scene_id, floorplan_path, ply_path, rgb_list, depth_list, metadata) -> Dict[str, str]`
- Non-functional:
  - Non-blocking error handling: generation must not fail if Google Drive sync experiences a transient write error.
  - Safe path sanitization to prevent invalid character collisions across operating systems.

## Architecture & File Changes
- Create: `src/utils/gdrive_manager.py` (Core synchronization and path manager).
- Create: `tests/test_gdrive_manager.py` (Unit test verifying folder creation, fallback detection, and artifact copying).

## Implementation Steps
1. **Develop `src/utils/gdrive_manager.py`**:
   - Define class `GDriveSyncManager`:
     - Path resolution logic:
       - Check if `/content/drive/MyDrive` exists. If so, default target is `/content/drive/MyDrive/Gradio/houseCrafter/output`.
       - Else check `os.getenv("GDRIVE_OUTPUT_DIR")`.
       - Else fallback to `os.path.abspath("./outputs/Gradio/houseCrafter/output")`.
     - Implement `ensure_directory(path)` using `os.makedirs(path, exist_ok=True)`.
     - Implement `sync_generation(...)`:
       - Construct destination folder `scene_{timestamp}_{scene_id}`.
       - Copy `.ply` files and verify checksum / file existence.
       - Copy multi-view RGB and depth images.
       - Write formatted `metadata.json`.
       - Return summary dict with sync status and destination URLs / paths for display in Gradio UI.
2. **Develop Unit Tests in `tests/test_gdrive_manager.py`**:
   - Test folder creation in temporary directory.
   - Test artifact copying with dummy `.ply` and `.png` files.
   - Test metadata formatting and JSON serialization.

## Success Criteria
- [x] Target directory `Gradio/houseCrafter/output` is automatically verified and created if missing.
- [x] Generation outputs (3D `.ply`, 2D images, metadata) are cleanly copied and structured.
- [x] Sync status and destination paths are returned for Gradio display.
- [x] Unit tests pass without error.

## Risk Assessment
- **Risk**: User runs on Colab but forgets to run the `drive.mount('/content/drive')` cell.
- **Mitigation**: Manager detects that `/content/drive/MyDrive` is not mounted, falls back to `/content/houseCrafter_output`, and alerts the user with a helpful instruction in the Gradio UI.
