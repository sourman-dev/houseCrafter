"""Gradio Blocks Layout and Event Handlers for HouseCrafter."""

import os
from typing import Generator, Tuple
import gradio as gr

from gradio_ui.components import (
    build_advanced_settings,
    build_input_components,
    build_multi_view_galleries,
    build_output_viewer,
    build_sync_and_metadata_panel,
    create_header_html,
)
from gradio_ui.pipeline_bridge import BaseHouseCrafterBridge, GenerationResult
from gradio_ui.preset_loader import PresetLoader
from gradio_ui.styles import CUSTOM_CSS
from src.utils.gdrive_manager import GDriveSyncManager


def build_interface(
    bridge: BaseHouseCrafterBridge,
    gdrive_manager: GDriveSyncManager,
    preset_loader: PresetLoader,
    is_mock: bool = False
) -> gr.Blocks:
    """Construct and wire the complete HouseCrafter Gradio web interface."""
    device_name = getattr(bridge, "device", "CUDA")
    is_colab = gdrive_manager.is_colab
    is_gdrive = gdrive_manager.is_gdrive_mounted()

    theme = gr.themes.Soft(
        primary_hue="sky",
        secondary_hue="slate",
        neutral_hue="slate"
    )

    with gr.Blocks(
        theme=theme, css=CUSTOM_CSS, title="HouseCrafter 3D"
    ) as demo:
        # Header banner
        header_html = create_header_html(
            is_colab=is_colab,
            is_gdrive=is_gdrive,
            device_name=device_name,
            is_mock=is_mock
        )
        gr.HTML(header_html)

        with gr.Row():
            # ----------------- LEFT COLUMN: INPUTS -----------------
            with gr.Column(scale=5):
                gr.Markdown("### 1️⃣ Provide 2D Ground Floor Plan")
                (
                    input_mode_radio,
                    custom_image_input,
                    preset_dropdown,
                    preset_preview_image,
                    upload_group,
                    preset_group,
                ) = build_input_components(preset_loader)

                settings = build_advanced_settings()

                with gr.Row():
                    generate_btn = gr.Button(
                        "🚀 Generate 3D Scene",
                        variant="primary",
                        elem_classes=["generate-btn"],
                        scale=3
                    )
                    reset_btn = gr.Button(
                        "🧹 Reset", variant="secondary", scale=1
                    )

                status_output = gr.Markdown(
                    value="*Ready to generate 3D indoor scene.*",
                    elem_classes=["status-box"]
                )

            # ----------------- RIGHT COLUMN: 3D VIEWER & OUTPUTS -----------------
            with gr.Column(scale=7):
                gr.Markdown("### 2️⃣ 3D Model & Multi-View Inspection")
                model_viewer, download_file = build_output_viewer()
                with gr.Tabs():
                    rgb_gallery, depth_gallery = (
                        build_multi_view_galleries()
                    )
                    sync_markdown = build_sync_and_metadata_panel()

        # ==================== EVENT HANDLERS ====================

        def on_input_mode_change(mode: str):
            is_upload = mode == "Upload Custom 2D Floorplan"
            return (
                gr.update(visible=is_upload),
                gr.update(visible=not is_upload),
            )

        input_mode_radio.change(
            fn=on_input_mode_change,
            inputs=[input_mode_radio],
            outputs=[upload_group, preset_group]
        )

        def on_preset_select(preset_id: str):
            preset = preset_loader.get_preset_by_id(preset_id)
            if preset and os.path.exists(preset["image_path"]):
                return preset["image_path"]
            return None

        preset_dropdown.change(
            fn=on_preset_select,
            inputs=[preset_dropdown],
            outputs=[preset_preview_image]
        )

        def run_generation(
            mode: str,
            custom_img: str,
            preset_id: str,
            num_steps: int,
            guidance_scale: float,
            depth_threshold: float,
            tsdf_voxel_size: float,
            seed: int,
            auto_sync: bool,
            progress=gr.Progress(track_tqdm=False)
        ) -> Generator[Tuple, None, None]:
            # Determine active floorplan path
            if mode == "Upload Custom 2D Floorplan":
                floorplan_path = custom_img
                if custom_img and os.path.exists(custom_img):
                    mtime = int(os.path.getmtime(custom_img))
                    scene_name = f"custom_{mtime}"
                else:
                    scene_name = "custom_upload"
            else:
                preset = preset_loader.get_preset_by_id(preset_id)
                floorplan_path = preset["image_path"] if preset else None
                scene_name = preset_id

            if not floorplan_path or not os.path.exists(floorplan_path):
                yield (
                    "⚠️ **Error**: Please upload a floorplan or choose a preset.",
                    None,
                    None,
                    [],
                    [],
                    "❌ Invalid or missing 2D floorplan input."
                )
                return

            # Execute generation generator
            final_res: GenerationResult = None
            gen = bridge.generate(
                floorplan_input=floorplan_path,
                scene_id=scene_name,
                num_steps=int(num_steps),
                guidance_scale=float(guidance_scale),
                depth_threshold=float(depth_threshold),
                tsdf_voxel_size=float(tsdf_voxel_size),
                seed=int(seed),
            )

            for frac, message, result in gen:
                progress(frac, desc=message)
                if result is not None:
                    final_res = result
                yield (
                    f"**Progress**: {message} ({int(frac * 100)}%)",
                    final_res.ply_path if final_res else None,
                    final_res.ply_path if final_res else None,
                    final_res.rgb_images if final_res else [],
                    final_res.depth_images if final_res else [],
                    "⏳ Finalizing 3D processing..."
                )

            if not final_res or not os.path.exists(final_res.ply_path):
                yield (
                    "❌ **Error**: Generation pipeline failed to produce PLY.",
                    None,
                    None,
                    [],
                    [],
                    "❌ 3D generation failed."
                )
                return

            # Optional Auto-Sync to Google Drive
            sync_info_md = "Google Drive sync was disabled."
            if auto_sync:
                progress(0.95, desc="Syncing artifacts to Google Drive...")
                sync_res = gdrive_manager.sync_generation(
                    scene_id=final_res.scene_id,
                    ply_path=final_res.ply_path,
                    floorplan_image_path=floorplan_path,
                    rgb_images=final_res.rgb_images,
                    depth_images=final_res.depth_images,
                    metadata=final_res.metadata
                )
                if sync_res.get("status") == "success":
                    loc = "Google Drive" if sync_res.get("is_gdrive") else "Local"
                    dst = sync_res.get("folder_path")
                    pts = final_res.metadata.get("point_count", "N/A")
                    sz = final_res.metadata.get("file_size_mb", "N/A")
                    dur = final_res.metadata.get("duration_seconds", "N/A")
                    fc = sync_res.get("file_count", 0)
                    sync_info_md = f"""
### ✅ Generation Synced Successfully!
- **Destination ({loc})**: `{dst}`
- **Scene ID**: `{final_res.scene_id}`
- **Points / Vertices**: `{pts}`
- **File Size**: `{sz} MB`
- **Execution Time**: `{dur}s`
- **Synced Files**: `{fc} files`
"""
                else:
                    err_msg = sync_res.get('message', 'Unknown error')
                    sync_info_md = f"⚠️ **Sync Warning**: {err_msg}"

            yield (
                f"🎉 **Generation Complete!** "
                f"({final_res.metadata.get('duration_seconds', 0)}s)",
                final_res.ply_path,
                final_res.ply_path,
                final_res.rgb_images,
                final_res.depth_images,
                sync_info_md
            )

        generate_btn.click(
            fn=run_generation,
            inputs=[
                input_mode_radio,
                custom_image_input,
                preset_dropdown,
                settings["num_steps"],
                settings["guidance_scale"],
                settings["depth_threshold"],
                settings["tsdf_voxel_size"],
                settings["seed"],
                settings["auto_sync"],
            ],
            outputs=[
                status_output,
                model_viewer,
                download_file,
                rgb_gallery,
                depth_gallery,
                sync_markdown,
            ]
        )

        def on_reset():
            return (
                None,
                None,
                None,
                [],
                [],
                "*Ready to generate 3D indoor scene.*",
                "*No generation completed yet.*"
            )

        reset_btn.click(
            fn=on_reset,
            inputs=[],
            outputs=[
                custom_image_input,
                model_viewer,
                download_file,
                rgb_gallery,
                depth_gallery,
                status_output,
                sync_markdown,
            ]
        )

    return demo
