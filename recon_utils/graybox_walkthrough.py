#!/usr/bin/env python3
"""Voxelize a TSDF .ply into an untextured graybox and render a room-to-room walkthrough.

HouseCrafter RGB frames are hop-graph views, not a tour. This uses the fused mesh
plus cam_Ts to fake a continuous camera walk for I2V refs (MiniMax H3 / Hailuo).
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

import cv2
import numpy as np
import open3d as o3d

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "src"))


def find_cleaned_ply(scene_dir: str) -> str:
    tsdf = os.path.join(scene_dir, "tsdf_fusion")
    hits = []
    if os.path.isdir(tsdf):
        for name in os.listdir(tsdf):
            if name.endswith(".ply") and "cleaned" in name:
                hits.append(os.path.join(tsdf, name))
    if hits:
        return sorted(hits)[-1]
    if os.path.isdir(tsdf):
        for name in os.listdir(tsdf):
            if name.endswith(".ply"):
                return os.path.join(tsdf, name)
    raise FileNotFoundError(f"no .ply under {tsdf}")


def voxel_graybox(mesh: o3d.geometry.TriangleMesh, voxel_size: float) -> o3d.geometry.TriangleMesh:
    mesh.remove_duplicated_vertices()
    mesh.remove_degenerate_triangles()
    mesh.remove_non_manifold_edges()
    vg = o3d.geometry.VoxelGrid.create_from_triangle_mesh(mesh, voxel_size=voxel_size)
    voxels = vg.get_voxels()
    if not voxels:
        raise RuntimeError("voxel grid empty — mesh too sparse")
    origin = np.asarray(vg.origin, dtype=np.float64)
    boxes = []
    for vox in voxels:
        cube = o3d.geometry.TriangleMesh.create_box(
            width=voxel_size, height=voxel_size, depth=voxel_size
        )
        cube.translate(origin + np.asarray(vox.grid_index, dtype=np.float64) * voxel_size)
        boxes.append(cube)
    gray = boxes[0]
    for cube in boxes[1:]:
        gray += cube
    gray.remove_duplicated_vertices()
    gray.remove_degenerate_triangles()
    gray.compute_vertex_normals()
    normals = np.asarray(gray.vertex_normals)
    light = np.array([0.35, 0.85, 0.35], dtype=np.float64)
    light /= np.linalg.norm(light)
    shade = 0.22 + 0.78 * np.clip(normals @ light, 0.0, 1.0)
    color = np.array([0.76, 0.76, 0.78], dtype=np.float64)
    gray.vertex_colors = o3d.utility.Vector3dVector(shade[:, None] * color)
    return gray


def clay_graybox(mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
    mesh = o3d.geometry.TriangleMesh(mesh)
    mesh.compute_vertex_normals()
    normals = np.asarray(mesh.vertex_normals)
    light = np.array([0.35, 0.85, 0.35], dtype=np.float64)
    light /= np.linalg.norm(light)
    shade = 0.22 + 0.78 * np.clip(normals @ light, 0.0, 1.0)
    color = np.array([0.76, 0.76, 0.78], dtype=np.float64)
    mesh.vertex_colors = o3d.utility.Vector3dVector(shade[:, None] * color)
    return mesh


def load_c2w_poses(cam_dir: str) -> List[np.ndarray]:
    poses = []
    for name in sorted(os.listdir(cam_dir)):
        if not name.endswith(".npy"):
            continue
        P = np.load(os.path.join(cam_dir, name)).astype(np.float64).reshape(4, 4)
        P[3, 3] = 1.0
        if not np.isfinite(P).all():
            continue
        poses.append(P)
    if not poses:
        raise FileNotFoundError(f"no cam_Ts in {cam_dir}")
    return poses


def downsample_poses(poses: List[np.ndarray], min_dist: float) -> List[np.ndarray]:
    kept = [poses[0]]
    for P in poses[1:]:
        if np.linalg.norm(P[:3, 3] - kept[-1][:3, 3]) >= min_dist:
            kept.append(P)
    return kept


def nn_tour(poses: List[np.ndarray]) -> List[np.ndarray]:
    leftover = poses[:]
    path = [leftover.pop(0)]
    while leftover:
        last = path[-1][:3, 3]
        dists = [np.linalg.norm(P[:3, 3] - last) for P in leftover]
        i = int(np.argmin(dists))
        path.append(leftover.pop(i))
    return path


def slerp_rot(R0: np.ndarray, R1: np.ndarray, t: float) -> np.ndarray:
    from scipy.spatial.transform import Rotation, Slerp

    key = Rotation.from_matrix(np.stack([R0, R1], axis=0))
    slerp = Slerp([0.0, 1.0], key)
    return slerp([t])[0].as_matrix()


def interpolate_path(poses: List[np.ndarray], steps: int) -> List[np.ndarray]:
    if len(poses) == 1:
        return poses
    out = []
    for a, b in zip(poses[:-1], poses[1:]):
        for k in range(steps):
            t = k / float(steps)
            P = np.eye(4)
            P[:3, :3] = slerp_rot(a[:3, :3], b[:3, :3], t)
            P[:3, 3] = (1.0 - t) * a[:3, 3] + t * b[:3, 3]
            out.append(P)
    out.append(poses[-1])
    return out


def render_pytorch3d(mesh, poses: List[np.ndarray], image_size: int, device: str):
    import torch
    from data_modules.mesh_renderer import TorchMeshRenderer

    renderer = TorchMeshRenderer(device=device, image_size=image_size, fov=90)
    torch_mesh = TorchMeshRenderer.o3d_mesh_to_torch(mesh, device)
    bg = np.array([0.91, 0.91, 0.93], dtype=np.float32)
    frames = []
    for i, P in enumerate(poses):
        P_t = torch.tensor(P, dtype=torch.float32, device=device).unsqueeze(0)
        rgb, depth = renderer.render(torch_mesh, P_t)
        img = rgb[0].detach().cpu().numpy()
        z = depth[0].detach().cpu().numpy()
        img[z <= 0] = bg
        frame = np.clip(img * 255.0, 0, 255).astype(np.uint8)
        frames.append(frame[..., ::-1])  # BGR for cv2
        if i % 10 == 0:
            print(f"  render {i+1}/{len(poses)}")
    return frames


def write_video(frames, out_mp4: str, fps: int):
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_mp4, fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"cannot open VideoWriter {out_mp4}")
    for f in frames:
        writer.write(f)
    writer.release()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scene_dir", required=True, help="generated_data_v0/<scene_id>")
    p.add_argument("--mode", choices=("voxel", "clay"), default="voxel")
    p.add_argument("--voxel_size", type=float, default=0.12)
    p.add_argument("--min_cam_dist", type=float, default=0.55)
    p.add_argument("--interp", type=int, default=6)
    p.add_argument("--max_frames", type=int, default=160)
    p.add_argument("--image_size", type=int, default=768)
    p.add_argument("--fps", type=int, default=12)
    p.add_argument("--device", default="cuda")
    args = p.parse_args()

    scene_dir = os.path.abspath(args.scene_dir)
    ply = find_cleaned_ply(scene_dir)
    print("mesh", ply)
    raw = o3d.io.read_triangle_mesh(ply)
    if raw.is_empty():
        raise RuntimeError("empty mesh")
    gray = voxel_graybox(raw, args.voxel_size) if args.mode == "voxel" else clay_graybox(raw)
    out_mesh = os.path.join(scene_dir, "graybox", "graybox.ply")
    os.makedirs(os.path.dirname(out_mesh), exist_ok=True)
    o3d.io.write_triangle_mesh(out_mesh, gray)
    print("graybox mesh", out_mesh, "verts", len(gray.vertices))

    poses = load_c2w_poses(os.path.join(scene_dir, "cam_Ts"))
    poses = downsample_poses(poses, args.min_cam_dist)
    poses = nn_tour(poses)
    poses = interpolate_path(poses, args.interp)
    if len(poses) > args.max_frames:
        idx = np.linspace(0, len(poses) - 1, args.max_frames).astype(int)
        poses = [poses[i] for i in idx]
    print("camera frames", len(poses))

    frames_dir = os.path.join(scene_dir, "graybox", "frames")
    os.makedirs(frames_dir, exist_ok=True)
    frames = render_pytorch3d(gray, poses, args.image_size, args.device)
    for i, f in enumerate(frames):
        cv2.imwrite(os.path.join(frames_dir, f"walk_{i:04d}.png"), f)
    mp4 = os.path.join(scene_dir, "graybox", "walkthrough.mp4")
    write_video(frames, mp4, args.fps)
    print("video", mp4)
    print("frames", frames_dir)


if __name__ == "__main__":
    main()
