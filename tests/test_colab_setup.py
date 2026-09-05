"""Guards Colab setup against the slow compile path."""

import os
import unittest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestColabSetup(unittest.TestCase):

    def test_colab_requirements_do_not_pin_torch_or_compile_pkgs(self):
        path = os.path.join(ROOT, "requirements-colab.txt")
        self.assertTrue(os.path.exists(path))
        lines = []
        with open(path) as fh:
            for raw in fh:
                line = raw.split("#", 1)[0].strip().lower()
                if line:
                    lines.append(line)
        text = "\n".join(lines)
        for banned in (
            "torch==",
            "torchvision==",
            "pytorch3d",
            "flash-attn",
            "xformers==",
            "open3d",
        ):
            self.assertNotIn(banned, text, banned)

    def test_colab_setup_uses_overlay_not_full_requirements(self):
        path = os.path.join(ROOT, "scripts", "colab_setup.sh")
        with open(path) as fh:
            text = fh.read()
        self.assertIn("requirements-colab.txt", text)
        self.assertNotIn("pip install -r requirements.txt", text)
        self.assertNotIn("facebookresearch/pytorch3d", text)
        self.assertIn("try_install", text)
        self.assertIn("one-by-one", text)

    def test_notebook_cells_are_isolated(self):
        import json
        path = os.path.join(
            ROOT, "notebooks", "HouseCrafter_Gradio_Colab.ipynb"
        )
        nb = json.load(open(path))
        code = "\n".join(
            "".join(c["source"])
            for c in nb["cells"]
            if c["cell_type"] == "code"
        )
        self.assertNotIn("Clone the repository", code)
        self.assertNotIn("pip install -r requirements.txt", code)
        self.assertIn("scripts/colab_setup.sh", code)
        self.assertIn("app.py --share", code)


if __name__ == "__main__":
    unittest.main()
