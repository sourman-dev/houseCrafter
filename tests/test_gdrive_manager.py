"""Unit tests for GDriveSyncManager."""

import os
import shutil
import tempfile
import unittest
from src.utils.gdrive_manager import GDriveSyncManager
from src.utils.ply_converter import create_sample_room_ply


class TestGDriveSyncManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = os.path.join(
            self.test_dir, "Gradio", "houseCrafter", "output"
        )
        self.manager = GDriveSyncManager(custom_output_dir=self.target_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_directory_auto_creation(self):
        """Verify that the target output folder is created automatically."""
        self.assertTrue(os.path.exists(self.target_dir))
        self.assertEqual(self.manager.output_dir, self.target_dir)

    def test_sync_generation_artifacts(self):
        """Test syncing PLY, floorplan image, and metadata."""
        # Create dummy PLY
        ply_file = os.path.join(self.test_dir, "test_room.ply")
        create_sample_room_ply(ply_file, num_points=100)

        # Create dummy image
        img_file = os.path.join(self.test_dir, "floorplan.png")
        with open(img_file, "wb") as f:
            f.write(b"PNGDATA")

        res = self.manager.sync_generation(
            scene_id="test_scene_101",
            ply_path=ply_file,
            floorplan_image_path=img_file,
            metadata={"num_points": 100, "model": "mock"}
        )

        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(res["folder_path"]))

        # Verify synced PLY file
        synced_ply = os.path.join(res["folder_path"], "test_scene_101.ply")
        self.assertTrue(os.path.exists(synced_ply))

        # Verify synced metadata
        meta_json = os.path.join(res["folder_path"], "metadata.json")
        self.assertTrue(os.path.exists(meta_json))

        # Verify output index
        index_file = os.path.join(self.target_dir, "output_index.json")
        self.assertTrue(os.path.exists(index_file))


if __name__ == "__main__":
    unittest.main()
