"""Preset Floorplan Sample Loader for HouseCrafter Gradio UI.

Discovers layout samples and rendered floor samples in dataRelease/ directory
and provides metadata, names, and preview thumbnails for the UI dropdown.
"""

import os
from typing import Dict, List, Optional
from PIL import Image, ImageDraw


def generate_fallback_floorplan_image(
    output_path: str,
    room_type: str = "livingroom"
) -> str:
    """Generate a 2D floorplan visualization for demo presets if needed."""
    img = Image.new("RGB", (512, 512), color=(245, 243, 238))
    draw = ImageDraw.Draw(img)

    # Outer wall boundary
    draw.rectangle([40, 40, 472, 472], outline=(40, 40, 40), width=6)

    if room_type == "bedroom":
        draw.line([(40, 200), (250, 200)], fill=(40, 40, 40), width=4)
        # Bed
        draw.rectangle(
            [70, 70, 190, 180],
            fill=(70, 130, 180),
            outline=(30, 60, 90),
            width=2,
        )
        # Wardrobe
        draw.rectangle(
            [320, 60, 450, 120],
            fill=(139, 90, 43),
            outline=(60, 40, 20),
            width=2,
        )
        # Nightstands
        draw.rectangle([50, 70, 65, 110], fill=(180, 140, 100))
        draw.rectangle([195, 70, 210, 110], fill=(180, 140, 100))
    elif room_type == "livingroom":
        # Sofa L-shape
        draw.rectangle(
            [80, 100, 260, 160],
            fill=(50, 120, 110),
            outline=(20, 60, 50),
            width=2,
        )
        draw.rectangle(
            [80, 160, 140, 280],
            fill=(50, 120, 110),
            outline=(20, 60, 50),
            width=2,
        )
        # Coffee table
        draw.rectangle(
            [180, 190, 280, 250],
            fill=(180, 150, 110),
            outline=(90, 70, 50),
            width=2,
        )
        # TV unit
        draw.rectangle(
            [80, 420, 320, 450],
            fill=(80, 80, 80),
            outline=(40, 40, 40),
            width=2,
        )
        # Dining table
        draw.rectangle(
            [340, 260, 440, 380],
            fill=(160, 110, 60),
            outline=(70, 40, 20),
            width=2,
        )
    else:  # Multi-room / Whole Scene
        draw.line([(256, 40), (256, 472)], fill=(40, 40, 40), width=4)
        draw.line([(40, 256), (472, 256)], fill=(40, 40, 40), width=4)
        # Room 1 bed
        draw.rectangle([60, 60, 160, 160], fill=(70, 130, 180))
        # Room 2 sofa
        draw.rectangle([300, 60, 420, 120], fill=(50, 120, 110))
        # Room 3 table
        draw.rectangle([80, 320, 180, 400], fill=(160, 110, 60))
        # Room 4 counter
        draw.rectangle([280, 420, 450, 450], fill=(100, 100, 100))

    dest_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(dest_dir, exist_ok=True)
    img.save(output_path)
    return output_path


class PresetLoader:
    """Discovers available 2D floorplan datasets and presets."""

    def __init__(self, data_root: str = "dataRelease"):
        self.data_root = os.path.abspath(data_root)
        self.cache_dir = os.path.abspath(
            os.path.join("assets", "preset_previews")
        )

    def get_presets(self) -> List[Dict[str, str]]:
        """Return list of preset dicts with id, label, description, image_path."""
        presets = []

        rendered_floor_dir = os.path.join(
            self.data_root, "rendered_floor_sample"
        )
        if os.path.exists(rendered_floor_dir):
            for filename in sorted(os.listdir(rendered_floor_dir)):
                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    scene_id = os.path.splitext(filename)[0]
                    presets.append({
                        "id": scene_id,
                        "label": f"Dataset Scene: {scene_id[:16]}...",
                        "description": f"3D-Front scene ({filename})",
                        "image_path": os.path.join(
                            rendered_floor_dir, filename
                        ),
                    })

        default_demos = [
            (
                "demo_modern_livingroom",
                "Modern Living Room & Dining",
                "livingroom",
                "Open-plan living room with sofa, coffee table, and dining set",
            ),
            (
                "demo_master_bedroom",
                "Master Bedroom with Wardrobe",
                "bedroom",
                "Spacious bedroom with double bed, side tables, and wardrobe",
            ),
            (
                "demo_whole_apartment",
                "2-Bedroom Apartment Layout",
                "wholescene",
                "Multi-room floorplan with living, bedroom, and kitchen zones",
            ),
        ]

        for p_id, label, room_type, desc in default_demos:
            preview_img = os.path.join(self.cache_dir, f"{p_id}.png")
            if not os.path.exists(preview_img):
                generate_fallback_floorplan_image(
                    preview_img, room_type=room_type
                )
            presets.append({
                "id": p_id,
                "label": f"⭐ Preset: {label}",
                "description": desc,
                "image_path": preview_img,
            })

        return presets

    def get_preset_by_id(self, preset_id: str) -> Optional[Dict[str, str]]:
        for preset in self.get_presets():
            if preset["id"] == preset_id:
                return preset
        return None
