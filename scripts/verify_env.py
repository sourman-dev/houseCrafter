#!/usr/bin/env python3
"""HouseCrafter Environment & Dependency Verification Script.

Checks GPU/CUDA availability, 3D libraries, Gradio UI components,
and Google Drive access.
"""

import os
import platform
import sys


def print_header(title: str) -> None:
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def check_python() -> bool:
    print(f"[*] Python Version: {platform.python_version()} ({sys.executable})")
    if sys.version_info < (3, 9):
        print("  [!] Warning: Python 3.9+ is recommended.")
        return False
    print("  [OK] Python version compatible.")
    return True


def check_cuda() -> bool:
    print_header("CUDA & PyTorch Diagnostics")
    try:
        import torch
        print(f"[*] PyTorch Version: {torch.__version__}")
        cuda_avail = torch.cuda.is_available()
        print(f"[*] CUDA Available: {cuda_avail}")
        if cuda_avail:
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            mem_bytes = torch.cuda.get_device_properties(0).total_memory
            vram_gb = mem_bytes / (1024 ** 3)
            print(f"[*] Primary GPU: {device_name}")
            print(f"[*] GPU Device Count: {device_count}")
            print(f"[*] Total VRAM: {vram_gb:.2f} GB")
            if vram_gb < 14.0:
                print("  [!] Warning: VRAM < 14GB. Recommend low-VRAM mode.")
            else:
                print("  [OK] VRAM capacity is sufficient for full pipeline.")
        else:
            print("  [!] Running on CPU mode.")
        return True
    except ImportError as e:
        print(f"  [FAIL] PyTorch is not installed: {e}")
        return False


def check_3d_libraries() -> bool:
    print_header("3D Processing & Geometry Libraries")
    status = True

    # Open3D
    try:
        import open3d as o3d
        print(f"[*] Open3D Version: {o3d.__version__}")
        print("  [OK] Open3D initialized.")
    except ImportError:
        print("  [FAIL] Open3D is not installed.")
        status = False

    # Trimesh
    try:
        import trimesh
        print(f"[*] Trimesh Version: {trimesh.__version__}")
        print("  [OK] Trimesh initialized.")
    except ImportError:
        print("  [FAIL] Trimesh is not installed.")
        status = False

    # PyTorch3D
    try:
        import pytorch3d
        print(f"[*] PyTorch3D Version: {pytorch3d.__version__}")
        print("  [OK] PyTorch3D initialized.")
    except ImportError:
        print("  [*] PyTorch3D not found (optional/fallback available).")

    return status


def check_gradio_ui() -> bool:
    print_header("Gradio Web UI Components")
    try:
        import gradio as gr
        print(f"[*] Gradio Version: {gr.__version__}")
        if hasattr(gr, "Model3D"):
            print("  [OK] gr.Model3D is available for 3D viewing.")
        else:
            print("  [!] Warning: gr.Model3D missing in this Gradio version.")
        return True
    except ImportError:
        print("  [FAIL] Gradio is not installed.")
        return False


def check_gdrive_environment() -> bool:
    print_header("Google Drive Sync Detection")
    colab_gdrive_root = "/content/drive/MyDrive"
    is_colab = os.path.exists("/content")
    print(f"[*] Running in Colab environment: {is_colab}")

    if os.path.exists(colab_gdrive_root):
        target = os.path.join(
            colab_gdrive_root, "Gradio", "houseCrafter", "output"
        )
        print("[*] Google Drive Mounted: Yes")
        print(f"[*] Target Sync Path: {target}")
    else:
        target = os.path.abspath(
            os.path.join(os.getcwd(), "outputs", "Gradio", "houseCrafter", "output")
        )
        print("[*] Google Drive Mounted: No (using local fallback)")
        print(f"[*] Fallback Path: {target}")

    try:
        os.makedirs(target, exist_ok=True)
        test_file = os.path.join(target, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print(f"  [OK] Write permissions verified on: {target}")
        return True
    except Exception as e:
        print(f"  [FAIL] Cannot write to directory {target}: {e}")
        return False


def check_checkpoints_and_data() -> bool:
    print_header("Model Checkpoints & Sample Data Check")
    ckpt_dir = os.path.abspath("ckpts")
    data_dir = os.path.abspath("dataRelease")

    print(f"[*] Checkpoint Dir: {ckpt_dir} (Exists: {os.path.exists(ckpt_dir)})")
    print(f"[*] Sample Data Dir: {data_dir} (Exists: {os.path.exists(data_dir)})")

    if os.path.exists(ckpt_dir):
        files = os.listdir(ckpt_dir)
        print(f"    Found items in ckpts: {files[:5]}")
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        print(f"    Found items in dataRelease: {files[:5]}")
    return True


def main() -> None:
    print("============================================================")
    print(" HouseCrafter Pre-Flight Environment & Diagnostics Checker")
    print("============================================================")

    results = [
        ("Python", check_python()),
        ("CUDA / PyTorch", check_cuda()),
        ("3D Geometry Libs", check_3d_libraries()),
        ("Gradio UI", check_gradio_ui()),
        ("Google Drive Sync", check_gdrive_environment()),
        ("Checkpoints & Data", check_checkpoints_and_data()),
    ]

    print_header("Summary Report")
    all_passed = True
    for name, passed in results:
        status_str = "[PASS]" if passed else "[WARN/FAIL]"
        print(f"  {status_str:<12} {name}")
        if not passed and name in ["Python", "CUDA / PyTorch", "Gradio UI"]:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print(" System is ready for HouseCrafter Gradio Application.")
    else:
        print(" Please check warnings/errors before running full pipeline.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
