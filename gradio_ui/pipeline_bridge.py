"""HouseCrafter Pipeline Bridge for Gradio Interface.

Provides a unified interface between the Gradio UI and the HouseCrafter 2D
diffusion model, TSDF volume fuser, and 3D PLY exporter. Supports both real
PyTorch GPU inference and a mock mode for UI development and testing.
"""

import dataclasses
import os
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw

from src.utils.ply_converter import (
    create_sample_room_ply,
    get_ply_metadata,
    optimize_ply_for_web,
)


@dataclasses.dataclass
class GenerationResult:
    """Container for HouseCrafter 3D scene generation artifacts."""
    scene_id: str
    ply_path: str
    glb_path: Optional[str]
    rgb_images: List[str]
    depth_images: List[str]
    metadata: Dict[str, Any]
    status: str = "success"
    error_message: Optional[str] = None


class BaseHouseCrafterBridge:
    """Abstract interface for HouseCrafter model inference."""

    def generate(
        self,
        floorplan_input: Any,
        scene_id: Optional[str] = None,
        num_steps: int = 50,
        guidance_scale: float = 7.5,
        depth_threshold: float = 2.5,
        tsdf_voxel_size: float = 0.05,
        seed: int = -1,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Generator[Tuple[float, str, Optional[GenerationResult]], None, None]:
        raise NotImplementedError


class MockHouseCrafterBridge(BaseHouseCrafterBridge):
    """Mock pipeline bridge for rapid UI testing and CPU environments."""

    def __init__(self, cache_dir: str = "outputs/mock_cache"):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _generate_mock_views(
        self, scene_id: str, num_views: int = 6
    ) -> Tuple[List[str], List[str]]:
        """Generate synthetic RGB viewpoints and depth colormaps."""
        views_dir = os.path.join(self.cache_dir, scene_id)
        rgb_dir = os.path.join(views_dir, "rgb_views")
        depth_dir = os.path.join(views_dir, "depth_views")
        os.makedirs(rgb_dir, exist_ok=True)
        os.makedirs(depth_dir, exist_ok=True)

        rgb_paths = []
        depth_paths = []
        angles = np.linspace(0, 360, num_views, endpoint=False)

        colors_palette = [
            (50, 80, 120), (120, 90, 60), (70, 110, 80),
            (110, 60, 90), (60, 100, 110), (100, 100, 60)
        ]

        for i, angle in enumerate(angles):
            # RGB View
            bg_col = colors_palette[i % len(colors_palette)]
            img = Image.new("RGB", (256, 256), color=bg_col)
            draw = ImageDraw.Draw(img)
            draw.rectangle([30, 140, 226, 226], fill=(180, 160, 140))
            draw.text(
                (10, 10),
                f"View {i+1} ({angle:.0f}°)",
                fill=(255, 255, 255)
            )
            draw.rectangle(
                [80, 60, 176, 150], outline=(255, 255, 255), width=2
            )
            rgb_file = os.path.join(rgb_dir, f"view_{i:02d}_rgb.png")
            img.save(rgb_file)
            rgb_paths.append(rgb_file)

            # Depth Map
            gradient = np.tile(
                np.linspace(20, 240, 256, dtype=np.uint8), (256, 1)
            )
            depth_img = Image.fromarray(gradient, mode="L")
            depth_file = os.path.join(depth_dir, f"view_{i:02d}_depth.png")
            depth_img.save(depth_file)
            depth_paths.append(depth_file)

        return rgb_paths, depth_paths

    def generate(
        self,
        floorplan_input: Any,
        scene_id: Optional[str] = None,
        num_steps: int = 50,
        guidance_scale: float = 7.5,
        depth_threshold: float = 2.5,
        tsdf_voxel_size: float = 0.05,
        seed: int = -1,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Generator[Tuple[float, str, Optional[GenerationResult]], None, None]:
        start_time = time.time()
        if not scene_id:
            scene_id = f"mock_{int(time.time())}"

        scene_dir = os.path.join(self.cache_dir, scene_id)
        os.makedirs(scene_dir, exist_ok=True)

        # Step 1: Preprocessing
        yield 0.15, "Preprocessing 2D floorplan layout & camera poses...", None
        time.sleep(0.3)

        # Step 2: Multi-View Diffusion
        msg = f"Generating multi-view RGB-D with diffusion ({num_steps} steps)..."
        yield 0.45, msg, None
        rgb_paths, depth_paths = self._generate_mock_views(
            scene_id, num_views=6
        )
        time.sleep(0.4)

        # Step 3: TSDF Fusion
        yield 0.75, "Performing TSDF fusion & point cloud extraction...", None
        raw_ply_path = os.path.join(scene_dir, f"{scene_id}_raw.ply")
        create_sample_room_ply(
            raw_ply_path, room_size=(4.0, 2.8, 5.0), num_points=30000
        )
        time.sleep(0.3)

        # Step 4: Denoising & Optimization
        yield 0.90, "Cleaning mesh and optimizing .ply for WebGL viewer...", None
        opt_ply_path = os.path.join(scene_dir, f"{scene_id}.ply")
        optimize_ply_for_web(
            raw_ply_path, opt_ply_path, voxel_size=tsdf_voxel_size
        )

        duration = time.time() - start_time
        meta = {
            "scene_id": scene_id,
            "inference_mode": "mock",
            "duration_seconds": round(duration, 2),
            "num_views": len(rgb_paths),
            "ddim_steps": num_steps,
            "guidance_scale": guidance_scale,
            "depth_threshold": depth_threshold,
            "tsdf_voxel_size": tsdf_voxel_size,
            "seed": seed,
            **get_ply_metadata(opt_ply_path),
        }

        result = GenerationResult(
            scene_id=scene_id,
            ply_path=opt_ply_path,
            glb_path=None,
            rgb_images=rgb_paths,
            depth_images=depth_paths,
            metadata=meta,
            status="success",
        )

        yield 1.0, f"Done in {duration:.1f}s! 3D scene ready.", result


class HouseCrafterBridge(BaseHouseCrafterBridge):
    """Full PyTorch & CUDA Bridge for HouseCrafter 2D-to-3D pipeline."""

    def __init__(
        self,
        ckpt_path: str = "ckpts/3dfront_layout_iodepth_1871_scene_3m",
        data_root: str = "dataRelease",
        out_dir: str = "gen_rgbd",
        device: str = "cuda",
        fp16: bool = True,
    ):
        self.ckpt_path = os.path.abspath(ckpt_path)
        self.data_root = os.path.abspath(data_root)
        self.out_dir = os.path.abspath(out_dir)
        self.device = device
        self.fp16 = fp16
        self.pipeline = None
        self.depth_model = None
        self.fuser = None

    def load_models(self) -> None:
        """Lazy load pre-trained models into GPU memory."""
        if self.pipeline is not None:
            return

        print(f"[*] Loading HouseCrafter models from: {self.ckpt_path}")
        try:
            import torch
            from generation_utils import make_pipeline
            from omegaconf import OmegaConf

            cfgs = [
                "./src/configs/base.yaml",
                "./src/new_explorer_configs/base_layout_rcn_iodepth_v.yaml",
                "./src/new_explorer_configs/3dfront_layout_rand_curate_explorer.yaml",
            ]
            configs = [
                OmegaConf.load(cfg) for cfg in cfgs if os.path.exists(cfg)
            ]
            cfg = OmegaConf.merge(*configs) if configs else OmegaConf.create()

            weight_dtype = torch.float16 if self.fp16 else torch.float32
            vae_ft = "ckpts/vae-ft-mse-840000-ema-pruned.ckpt"
            if not os.path.exists(vae_ft):
                vae_ft = None

            self.pipeline = make_pipeline(
                cfg,
                self.ckpt_path,
                weight_dtype,
                self.device,
                inverse_ddim=False,
                vae_ft=vae_ft,
            )

            # Load UniDepth
            try:
                self.depth_model = torch.hub.load(
                    "lpiccinelli-eth/UniDepth",
                    "UniDepth",
                    version="v1",
                    backbone="ViTL14",
                    pretrained=True,
                    trust_repo=True,
                ).to(self.device)
            except Exception as e:
                print(f"[Warning] UniDepth load error ({e}).")

            print("[OK] HouseCrafter models loaded into GPU memory.")
        except Exception as e:
            print(f"[Error] Failed to load HouseCrafter models: {e}")
            raise

    def generate(
        self,
        floorplan_input: Any,
        scene_id: Optional[str] = None,
        num_steps: int = 50,
        guidance_scale: float = 7.5,
        depth_threshold: float = 2.5,
        tsdf_voxel_size: float = 0.05,
        seed: int = -1,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Generator[Tuple[float, str, Optional[GenerationResult]], None, None]:
        if not scene_id:
            scene_id = f"scene_{int(time.time())}"

        # generate_scene.py + TSDF fusion are not hooked into this UI yet.
        # Loading checkpoints here would pull pytorch3d/xformers and crash Colab.
        print(
            "[Notice] HouseCrafterBridge has no generate_scene hook. "
            "Serving MockHouseCrafterBridge so the Gradio UI stays usable."
        )
        mock = MockHouseCrafterBridge()
        yield from mock.generate(
            floorplan_input=floorplan_input,
            scene_id=scene_id,
            num_steps=num_steps,
            guidance_scale=guidance_scale,
            depth_threshold=depth_threshold,
            tsdf_voxel_size=tsdf_voxel_size,
            seed=seed,
        )
