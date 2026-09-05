"""Google Drive Auto-Sync Manager for HouseCrafter.

Automatically detects Google Drive in Google Colab (/content/drive/MyDrive),
creates the target directory 'Gradio/houseCrafter/output' if not present,
and synchronizes 3D PLY models, multi-view RGB-D views, and metadata.
"""

import datetime
import json
import os
import shutil
from typing import Any, Dict, List, Optional


class GDriveSyncManager:
    """Manages automatic persistence and synchronization to Google Drive."""

    COLAB_DRIVE_ROOT = "/content/drive/MyDrive"
    DEFAULT_REL_PATH = os.path.join("Gradio", "houseCrafter", "output")

    def __init__(self, custom_output_dir: Optional[str] = None):
        self.is_colab = os.path.exists("/content")
        self.output_dir = self._resolve_target_directory(custom_output_dir)
        self.ensure_output_directory()

    def _resolve_target_directory(self, custom_dir: Optional[str]) -> str:
        """Determine target storage directory based on environment."""
        if custom_dir:
            return os.path.abspath(custom_dir)

        env_dir = os.getenv("GDRIVE_OUTPUT_DIR")
        if env_dir:
            return os.path.abspath(env_dir)

        # Check if running in Colab with mounted Drive
        if os.path.exists(self.COLAB_DRIVE_ROOT):
            return os.path.join(self.COLAB_DRIVE_ROOT, self.DEFAULT_REL_PATH)

        # Local fallback
        return os.path.abspath(
            os.path.join("outputs", "Gradio", "houseCrafter", "output")
        )

    def is_gdrive_mounted(self) -> bool:
        """Check if Google Drive is actively mounted."""
        return os.path.exists(self.COLAB_DRIVE_ROOT)

    def ensure_output_directory(self) -> str:
        """Create target output directory if it does not already exist."""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            return self.output_dir
        except Exception as e:
            fallback = os.path.abspath(os.path.join("outputs", "fallback"))
            os.makedirs(fallback, exist_ok=True)
            self.output_dir = fallback
            print(
                f"[Warning] Failed to create {self.output_dir}: {e}. "
                f"Using {fallback}"
            )
            return self.output_dir

    def sync_generation(
        self,
        scene_id: str,
        ply_path: str,
        floorplan_image_path: Optional[str] = None,
        rgb_images: Optional[List[str]] = None,
        depth_images: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Synchronize all artifacts of a completed scene generation.

        Creates:
            Gradio/houseCrafter/output/scene_{timestamp}_{scene_id}/
                ├── scene_3d.ply
                ├── input_floorplan.png
                ├── rgb_views/
                ├── depth_views/
                └── metadata.json
        """
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"scene_{now_str}_{scene_id}"
        dest_scene_dir = os.path.join(self.output_dir, folder_name)

        try:
            os.makedirs(dest_scene_dir, exist_ok=True)

            synced_files = {}

            # 1. Copy 3D PLY model
            if os.path.exists(ply_path):
                dest_ply = os.path.join(dest_scene_dir, f"{scene_id}.ply")
                shutil.copyfile(ply_path, dest_ply)
                synced_files["ply"] = dest_ply

            # 2. Copy 2D Floorplan input image
            if floorplan_image_path and os.path.exists(floorplan_image_path):
                ext = os.path.splitext(floorplan_image_path)[1] or ".png"
                dest_fp = os.path.join(dest_scene_dir, f"input_floorplan{ext}")
                shutil.copyfile(floorplan_image_path, dest_fp)
                synced_files["floorplan"] = dest_fp

            # 3. Copy Multi-View RGB images
            if rgb_images:
                dest_rgb_dir = os.path.join(dest_scene_dir, "rgb_views")
                os.makedirs(dest_rgb_dir, exist_ok=True)
                copied_rgb = []
                for i, img_p in enumerate(rgb_images):
                    if os.path.exists(img_p):
                        dest_f = os.path.join(
                            dest_rgb_dir, f"view_{i:02d}.png"
                        )
                        shutil.copyfile(img_p, dest_f)
                        copied_rgb.append(dest_f)
                synced_files["rgb_views"] = copied_rgb

            # 4. Copy Depth colormaps
            if depth_images:
                dest_depth_dir = os.path.join(dest_scene_dir, "depth_views")
                os.makedirs(dest_depth_dir, exist_ok=True)
                copied_depth = []
                for i, img_p in enumerate(depth_images):
                    if os.path.exists(img_p):
                        dest_f = os.path.join(
                            dest_depth_dir, f"depth_{i:02d}.png"
                        )
                        shutil.copyfile(img_p, dest_f)
                        copied_depth.append(dest_f)
                synced_files["depth_views"] = copied_depth

            # 5. Write metadata.json
            meta_record = {
                "scene_id": scene_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "destination_dir": dest_scene_dir,
                "synced_files": synced_files,
                **(metadata or {}),
            }
            meta_file = os.path.join(dest_scene_dir, "metadata.json")
            with open(meta_file, "w") as f:
                json.dump(meta_record, f, indent=2)

            # 6. Update master history index
            self._update_history_index(meta_record)

            return {
                "status": "success",
                "folder_path": dest_scene_dir,
                "folder_name": folder_name,
                "is_gdrive": self.is_gdrive_mounted(),
                "file_count": len(synced_files),
            }

        except Exception as e:
            print(f"[Error] Failed to sync to Google Drive: {e}")
            return {
                "status": "error",
                "message": str(e),
                "folder_path": dest_scene_dir,
                "is_gdrive": self.is_gdrive_mounted(),
            }

    def _update_history_index(self, record: Dict[str, Any]) -> None:
        """Append scene metadata entry to output_index.json."""
        index_file = os.path.join(self.output_dir, "output_index.json")
        try:
            history = []
            if os.path.exists(index_file):
                with open(index_file, "r") as f:
                    history = json.load(f)
            history.append({
                "scene_id": record.get("scene_id"),
                "timestamp": record.get("timestamp"),
                "folder": os.path.basename(record.get("destination_dir", "")),
                "point_count": record.get("point_count", 0),
            })
            with open(index_file, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"[Warning] Failed to update history index: {e}")
