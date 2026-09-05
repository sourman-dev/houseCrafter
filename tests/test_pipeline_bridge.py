"""Unit tests for HouseCrafter Pipeline Bridge and 3D Converters."""

import os
import shutil
import tempfile
import unittest

from gradio_ui.pipeline_bridge import (
    GenerationResult,
    MockHouseCrafterBridge,
)
from gradio_ui.preset_loader import (
    PresetLoader,
    generate_fallback_floorplan_image,
)
from src.utils.ply_converter import (
    create_sample_room_ply,
    get_ply_metadata,
    optimize_ply_for_web,
)


class TestPipelineBridge(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sample_ply_creation_and_metadata(self):
        """Test generating synthetic room PLY and extracting metadata."""
        ply_path = os.path.join(self.test_dir, "sample_room.ply")
        created_path = create_sample_room_ply(ply_path, num_points=1000)
        self.assertTrue(os.path.exists(created_path))

        meta = get_ply_metadata(created_path)
        self.assertIn("point_count", meta)
        self.assertIn("file_size_mb", meta)

    def test_ply_optimization(self):
        """Test downsampling a PLY file."""
        ply_path = os.path.join(self.test_dir, "large_room.ply")
        create_sample_room_ply(ply_path, num_points=2000)

        opt_path = os.path.join(self.test_dir, "opt_room.ply")
        res_path = optimize_ply_for_web(
            ply_path, opt_path, voxel_size=0.05, max_points=500
        )
        self.assertTrue(os.path.exists(res_path))

    def test_preset_loader(self):
        """Test discovering and generating preset floorplans."""
        loader = PresetLoader(data_root=self.test_dir)
        presets = loader.get_presets()
        self.assertGreater(len(presets), 0)

        first_id = presets[0]["id"]
        found = loader.get_preset_by_id(first_id)
        self.assertIsNotNone(found)
        self.assertTrue(os.path.exists(found["image_path"]))

    def test_mock_pipeline_generation(self):
        """Test end-to-end mock generation generator."""
        bridge = MockHouseCrafterBridge(cache_dir=self.test_dir)
        demo_fp = os.path.join(self.test_dir, "floorplan.png")
        generate_fallback_floorplan_image(demo_fp, room_type="bedroom")

        gen = bridge.generate(
            floorplan_input=demo_fp,
            scene_id="test_mock_scene",
            num_steps=20,
        )

        final_result = None
        for frac, msg, res in gen:
            self.assertGreaterEqual(frac, 0.0)
            self.assertLessEqual(frac, 1.0)
            if res is not None:
                final_result = res

        self.assertIsInstance(final_result, GenerationResult)
        self.assertEqual(final_result.status, "success")
        self.assertTrue(os.path.exists(final_result.ply_path))
        self.assertGreater(len(final_result.rgb_images), 0)
        self.assertGreater(len(final_result.depth_images), 0)


if __name__ == "__main__":
    unittest.main()
