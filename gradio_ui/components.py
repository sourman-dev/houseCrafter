"""Modular UI Components for HouseCrafter Gradio Application."""

from typing import Dict, Tuple
import gradio as gr
from gradio_ui.preset_loader import PresetLoader


def create_header_html(
    is_colab: bool = False,
    is_gdrive: bool = False,
    device_name: str = "CUDA",
    is_mock: bool = False
) -> str:
    """Generate the styled HTML header with status badges."""
    env_label = "Google Colab" if is_colab else "Local Workstation"
    gdrive_status = "Google Drive Connected" if is_gdrive else "Local Storage"
    mode_label = "Mock Mode (CPU Test)" if is_mock else f"GPU: {device_name}"

    html = f"""
    <div class="app-header">
        <h1>🏠 HouseCrafter: 2D Floorplan to 3D Indoor Scene Generator</h1>
        <p>Lifting 2D floorplans to 3D .ply with diffusion (ICCV 2025)</p>
        <div class="badge-row">
            <span class="badge-item">📍 Runtime: {env_label}</span>
            <span class="badge-item highlight">⚡ Engine: {mode_label}</span>
            <span class="badge-item">💾 Storage: {gdrive_status}</span>
            <span class="badge-item">🎯 Output: .PLY 3D Scene</span>
        </div>
    </div>
    """
    return html


def build_input_components(preset_loader: PresetLoader):
    """Build floorplan inputs: URL, upload, and presets."""
    presets = preset_loader.get_presets()
    preset_choices = [(p["label"], p["id"]) for p in presets]
    default_preset_id = presets[0]["id"] if presets else None
    default_preset_img = presets[0]["image_path"] if presets else None

    input_mode_radio = gr.Radio(
        choices=[
            "Paste image URL",
            "Upload image",
            "Preset sample",
        ],
        value="Paste image URL",
        label="Input method",
        interactive=True,
    )

    with gr.Group(visible=True) as url_group:
        url_box = gr.Textbox(
            label="Floorplan image URL",
            placeholder="https://i.pinimg.com/...jpg  or any PNG/JPG URL",
            lines=1,
        )
        fetch_btn = gr.Button("Load image from URL", variant="secondary")
        url_preview = gr.Image(
            type="filepath",
            label="Preview",
            interactive=False,
        )

    with gr.Group(visible=False) as upload_group:
        custom_image_input = gr.Image(
            type="filepath",
            label="Upload 2D ground floor plan (PNG / JPG)",
            interactive=True,
        )

    with gr.Group(visible=False) as preset_group:
        preset_dropdown = gr.Dropdown(
            choices=preset_choices,
            value=default_preset_id,
            label="Select preset scene",
            interactive=True,
        )
        preset_preview_image = gr.Image(
            value=default_preset_img,
            type="filepath",
            label="Selected floorplan preview",
            interactive=False,
        )

    return (
        input_mode_radio,
        custom_image_input,
        preset_dropdown,
        preset_preview_image,
        upload_group,
        preset_group,
        url_group,
        url_box,
        url_preview,
        fetch_btn,
    )


def build_advanced_settings() -> Dict[str, gr.components.Component]:
    """Build the accordion with fine-grained inference and 3D parameters."""
    with gr.Accordion("⚙️ Advanced Inference & 3D Settings", open=False):
        num_steps_slider = gr.Slider(
            minimum=10,
            maximum=100,
            value=50,
            step=5,
            label="DDIM Diffusion Steps",
            info="Higher steps improve visual fidelity"
        )
        guidance_scale_slider = gr.Slider(
            minimum=1.0,
            maximum=15.0,
            value=7.5,
            step=0.5,
            label="Classifier-Free Guidance Scale"
        )
        depth_threshold_slider = gr.Slider(
            minimum=1.0,
            maximum=5.0,
            value=2.5,
            step=0.1,
            label="Max Depth Mask (meters)",
            info="Filters out points farther than threshold during TSDF fusion"
        )
        tsdf_voxel_slider = gr.Slider(
            minimum=0.02,
            maximum=0.10,
            value=0.05,
            step=0.01,
            label="TSDF Fusion Voxel Size (meters)",
            info="0.05 is optimal for fast web viewing"
        )
        seed_input = gr.Number(
            value=-1,
            label="Random Seed (-1 for random)",
            precision=0
        )
        auto_sync_checkbox = gr.Checkbox(
            value=True,
            label="Auto-sync to Google Drive (Gradio/houseCrafter/output)",
            info="Automatically save .ply, RGB-D images, and metadata to Drive"
        )

    return {
        "num_steps": num_steps_slider,
        "guidance_scale": guidance_scale_slider,
        "depth_threshold": depth_threshold_slider,
        "tsdf_voxel_size": tsdf_voxel_slider,
        "seed": seed_input,
        "auto_sync": auto_sync_checkbox,
    }


def build_output_viewer() -> Tuple[gr.Model3D, gr.File]:
    """Build the 3D interactive viewer and file download button."""
    model_viewer = gr.Model3D(
        label="🎮 Interactive 3D Scene Viewer (.ply)",
        display_mode="solid",
        clear_color=[0.06, 0.08, 0.12, 1.0],
        elem_classes=["viewer-3d-box"],
        interactive=True
    )
    download_file = gr.File(
        label="⬇️ Download 3D .PLY Model",
        file_count="single",
        interactive=False
    )
    return model_viewer, download_file


def build_multi_view_galleries() -> Tuple[gr.Gallery, gr.Gallery]:
    """Build galleries for generated RGB viewpoints and depth maps."""
    with gr.Tab("🖼️ Multi-View RGB Generation"):
        rgb_gallery = gr.Gallery(
            label="Generated Camera Views",
            columns=3,
            rows=2,
            height=320,
            object_fit="contain",
            show_label=False
        )
    with gr.Tab("🗺️ Depth Maps (Fused)"):
        depth_gallery = gr.Gallery(
            label="Depth Estimation Maps",
            columns=3,
            rows=2,
            height=320,
            object_fit="contain",
            show_label=False
        )
    return rgb_gallery, depth_gallery


def build_sync_and_metadata_panel() -> gr.Markdown:
    """Build the status and Google Drive sync reporting panel."""
    with gr.Tab("💾 Google Drive Sync & Metadata"):
        sync_markdown = gr.Markdown(
            value="*No generation completed yet. Outputs logged here.*",
            elem_classes=["sync-card"]
        )
    return sync_markdown
