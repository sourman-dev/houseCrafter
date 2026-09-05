#!/usr/bin/env python3
"""HouseCrafter Gradio Web Application Entrypoint.

Lifts 2D ground floor plans into interactive 3D .ply representations
and synchronizes outputs to Google Drive (Gradio/houseCrafter/output).
"""

import argparse
import os
import sys

# Ensure project root and src/ are on sys.path (generation_utils lives in src/)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")
for path in (PROJECT_ROOT, SRC_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from gradio_ui.interface import build_interface  # noqa: E402
from gradio_ui.pipeline_bridge import (  # noqa: E402
    HouseCrafterBridge,
    MockHouseCrafterBridge,
)
from gradio_ui.preset_loader import PresetLoader  # noqa: E402
from src.utils.gdrive_manager import GDriveSyncManager  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(
        description="HouseCrafter 2D Floorplan to 3D Scene Gradio Web App"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        default=False,
        help="Create a publicly shareable Gradio link (recommended on Colab)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run the Gradio web server on (default: 7860)",
    )
    parser.add_argument(
        "--server_name",
        type=str,
        default="0.0.0.0",
        help="Server binding address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--gdrive_dir",
        type=str,
        default=None,
        help="Custom Google Drive output folder path",
    )
    parser.add_argument(
        "--ckpt_path",
        type=str,
        default="ckpts/3dfront_layout_iodepth_1871_scene_3m",
        help="Path to pre-trained diffusion checkpoint directory",
    )
    parser.add_argument(
        "--data_root",
        type=str,
        default="dataRelease",
        help="Path to sample floorplans and layout dataset directory",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=False,
        help="Run in mock mode without requiring CUDA or heavy model weights",
    )
    parser.add_argument(
        "--fp16",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="FP16 diffusion weights (use --no-fp16 for FP32)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 65)
    print(" 🏠 Starting HouseCrafter 2D-to-3D Gradio Web Application")
    print("=" * 65)
    print(f"[*] Mock Mode: {args.mock}")
    print(f"[*] Port: {args.port} | Host: {args.server_name}")
    print(f"[*] Public Share: {args.share}")

    # Initialize Google Drive sync manager
    gdrive_manager = GDriveSyncManager(custom_output_dir=args.gdrive_dir)
    print(f"[*] Storage Output Directory: {gdrive_manager.output_dir}")
    print(f"[*] Google Drive Mounted: {gdrive_manager.is_gdrive_mounted()}")

    # Initialize preset discovery
    preset_loader = PresetLoader(data_root=args.data_root)

    # Initialize pipeline bridge
    if args.mock:
        bridge = MockHouseCrafterBridge()
    else:
        bridge = HouseCrafterBridge(
            ckpt_path=args.ckpt_path,
            data_root=args.data_root,
            fp16=args.fp16,
        )

    # Build interface
    demo = build_interface(
        bridge=bridge,
        gdrive_manager=gdrive_manager,
        preset_loader=preset_loader,
        is_mock=args.mock,
    )

    print("\n[🚀] Launching Gradio Server...")
    demo.queue().launch(
        server_name=args.server_name,
        server_port=args.port,
        share=args.share,
        show_error=True,
    )


if __name__ == "__main__":
    main()
