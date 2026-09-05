"""Unit tests for HouseCrafter Gradio UI Interface."""

import shutil
import tempfile
import unittest

try:
    import gradio as gr
    from gradio_ui.interface import build_interface
    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

from gradio_ui.pipeline_bridge import MockHouseCrafterBridge
from gradio_ui.preset_loader import PresetLoader
from src.utils.gdrive_manager import GDriveSyncManager


class TestGradioInterface(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.gdrive_manager = GDriveSyncManager(
            custom_output_dir=self.test_dir
        )
        self.bridge = MockHouseCrafterBridge(cache_dir=self.test_dir)
        self.preset_loader = PresetLoader(data_root=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @unittest.skipUnless(HAS_GRADIO, "Gradio not installed in test env")
    def test_build_interface_structure(self):
        """Test constructing the Gradio Blocks app."""
        demo = build_interface(
            bridge=self.bridge,
            gdrive_manager=self.gdrive_manager,
            preset_loader=self.preset_loader,
            is_mock=True,
        )

        self.assertIsInstance(demo, gr.Blocks)
        self.assertEqual(demo.title, "HouseCrafter 3D")


if __name__ == "__main__":
    unittest.main()
