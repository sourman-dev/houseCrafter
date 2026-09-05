"""Tests for 2D floorplan lift and Pinterest og:image parsing."""

import os
import tempfile
import unittest

from src.utils.floorplan_lift import (
    OG_IMAGE_RE,
    OG_IMAGE_RE_REV,
    lift_floorplan_to_ply,
    make_preview_views,
    resolve_image_url,
)
from gradio_ui.preset_loader import generate_fallback_floorplan_image


class TestFloorplanLift(unittest.TestCase):

    def test_og_image_meta_parsed(self):
        html = (
            '<html><meta property="og:image" '
            'content="https://i.pinimg.com/originals/ab/cd.jpg"></html>'
        )
        match = OG_IMAGE_RE.search(html)
        self.assertIsNotNone(match)
        self.assertIn("i.pinimg.com", match.group(1))

    def test_og_image_meta_reversed_attrs(self):
        html = (
            '<meta content="https://i.pinimg.com/x.png" '
            'property="og:image">'
        )
        match = OG_IMAGE_RE_REV.search(html)
        self.assertIsNotNone(match)
        self.assertTrue(match.group(1).endswith(".png"))

    def test_direct_pinimg_url_passthrough(self):
        url = "https://i.pinimg.com/736x/aa/bb/cc/plan.jpg"
        self.assertEqual(resolve_image_url(url), url)

    def test_lift_writes_ply_from_drawn_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            img = os.path.join(tmp, "plan.png")
            generate_fallback_floorplan_image(img, room_type="bedroom")
            ply = os.path.join(tmp, "out.ply")
            lift_floorplan_to_ply(img, ply, max_side=128)
            self.assertTrue(os.path.exists(ply))
            text = open(ply).read()
            self.assertIn("element vertex", text)
            self.assertGreater(os.path.getsize(ply), 200)

            rgb, depth = make_preview_views(img, tmp)
            self.assertTrue(os.path.exists(rgb[0]))
            self.assertTrue(os.path.exists(depth[0]))


if __name__ == "__main__":
    unittest.main()
