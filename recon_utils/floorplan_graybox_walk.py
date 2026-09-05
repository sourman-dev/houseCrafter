#!/usr/bin/env python3
"""2D floorplan image -> extruded graybox -> POV walkthrough frames/mp4.

No HouseCrafter weights. Input is a top-down plan (dark walls on light floor).
"""
from __future__ import annotations

import argparse
import os

import cv2
import numpy as np
import open3d as o3d
from skimage import measure


def load_wall_mask(path: str, invert: bool) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    _, mask = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    walls = mask < 127
    if invert:
        walls = ~walls
    walls = cv2.morphologyEx(
        walls.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)
    ).astype(bool)
    return walls


def occupancy_volume(walls: np.ndarray, meters: float, wall_h: float, cell_y: float):
    h, w = walls.shape
    cell = meters / float(max(w, h))
    n_y = max(4, int(round(wall_h / cell_y)))
    vol = np.zeros((h, n_y, w), dtype=np.uint8)
    floor = ~walls
    vol[:, 0, :] = floor
    vol[:, -1, :] = floor
    vol[:, 1:-1, :] = walls[:, None, :]
    spacing = (cell, cell_y, cell)
    return vol, spacing, cell


def volume_to_mesh(vol: np.ndarray, spacing) -> o3d.geometry.TriangleMesh:
    verts, faces, normals, _ = measure.marching_cubes(vol.astype(np.float32), level=0.5, spacing=spacing)
    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(verts[:, [2, 1, 0]])  # x, y, z
    mesh.triangles = o3d.utility.Vector3iVector(faces)
    mesh.vertex_normals = o3d.utility.Vector3dVector(normals[:, [2, 1, 0]])
    mesh.remove_duplicated_vertices()
    mesh.remove_degenerate_triangles()
    mesh.compute_vertex_normals()
    n = np.asarray(mesh.vertex_normals)
    light = np.array([0.3, 0.9, 0.25])
    light /= np.linalg.norm(light)
    shade = 0.2 + 0.8 * np.clip(n @ light, 0, 1)
    color = np.array([0.75, 0.75, 0.77])
    mesh.vertex_colors = o3d.utility.Vector3dVector(shade[:, None] * color)
    return mesh


def free_path(walls: np.ndarray, cell: float, stride: int) -> np.ndarray:
    free = (~walls).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    free = cv2.erode(free, k)
    ys, xs = np.where(free > 0)
    if len(xs) < 8:
        raise RuntimeError("not enough free space for a camera path — check invert")
    pts = np.stack([xs, ys], axis=1)
    pts = pts[(pts[:, 0] % stride == 0) & (pts[:, 1] % stride == 0)]
    if len(pts) < 4:
        pts = np.stack([xs[:: max(1, len(xs) // 80)], ys[:: max(1, len(ys) // 80)]], axis=1)
    leftover = pts.tolist()
    path = [leftover.pop(0)]
    while leftover:
        last = np.array(path[-1])
        d = [np.sum((np.array(p) - last) ** 2) for p in leftover]
        path.append(leftover.pop(int(np.argmin(d))))
    xz = np.array(path, dtype=np.float64)
    xz[:, 0] *= cell
    xz[:, 1] *= cell
    return xz


def poses_from_path(xz: np.ndarray, eye_y: float, interp: int) -> list:
    if len(xz) == 1:
        P = np.eye(4)
        P[:3, 3] = [xz[0, 0], eye_y, xz[0, 1]]
        return [P]
    dense = []
    for a, b in zip(xz[:-1], xz[1:]):
        for k in range(interp):
            t = k / float(interp)
            dense.append((1 - t) * a + t * b)
    dense.append(xz[-1])
    dense = np.asarray(dense)
    poses = []
    for i, p in enumerate(dense):
        nxt = dense[min(i + 1, len(dense) - 1)]
        d = nxt - p
        if np.linalg.norm(d) < 1e-6:
            d = np.array([0.0, 1.0])
        d = d / (np.linalg.norm(d) + 1e-8)
        forward = np.array([d[0], 0.0, d[1]])
        up = np.array([0.0, 1.0, 0.0])
        right = np.cross(up, forward)
        right /= np.linalg.norm(right) + 1e-8
        up = np.cross(forward, right)
        R = np.stack([right, up, -forward], axis=1)
        P = np.eye(4)
        P[:3, :3] = R
        P[:3, 3] = [p[0], eye_y, p[1]]
        poses.append(P)
    return poses


def render_raycast(mesh, poses, size: int):
    tmesh = o3d.t.geometry.TriangleMesh.from_legacy(mesh)
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(tmesh)
    fx = fy = size / (2 * np.tan(np.deg2rad(90) / 2))
    cx = cy = size / 2
    intrinsic = o3d.core.Tensor([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=o3d.core.Dtype.Float64)
    bg = np.array([0.91, 0.91, 0.93], dtype=np.float32)
    frames = []
    opencv_flip = np.diag([1.0, -1.0, -1.0, 1.0])
    for i, c2w in enumerate(poses):
        w2c = opencv_flip @ np.linalg.inv(c2w)
        extrinsic = o3d.core.Tensor(w2c, dtype=o3d.core.Dtype.Float64)
        rays = scene.create_rays_pinhole(intrinsic, extrinsic, size, size)
        ans = scene.cast_rays(rays)
        hit = np.isfinite(ans["t_hit"].numpy())
        n = ans["primitive_normals"].numpy()
        light = np.array([0.3, 0.9, 0.25], dtype=np.float32)
        light /= np.linalg.norm(light)
        shade = 0.18 + 0.82 * np.clip(n @ light, 0, 1)
        img = np.where(hit[..., None], (shade[..., None] * np.array([0.76, 0.76, 0.78])), bg)
        frame = np.clip(img * 255, 0, 255).astype(np.uint8)[..., ::-1]
        frames.append(frame)
        if i % 15 == 0:
            print(f"  render {i+1}/{len(poses)}")
    return frames


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--floorplan", required=True)
    p.add_argument("--out_dir", required=True)
    p.add_argument("--meters", type=float, default=12.0, help="real width of the longer image side")
    p.add_argument("--wall_height", type=float, default=2.7)
    p.add_argument("--eye_y", type=float, default=1.55)
    p.add_argument("--invert", action="store_true", help="use if walls are light on dark")
    p.add_argument("--image_size", type=int, default=768)
    p.add_argument("--interp", type=int, default=4)
    p.add_argument("--stride", type=int, default=6)
    p.add_argument("--max_frames", type=int, default=120)
    p.add_argument("--fps", type=int, default=12)
    args = p.parse_args()

    walls = load_wall_mask(args.floorplan, args.invert)
    vol, spacing, cell = occupancy_volume(walls, args.meters, args.wall_height, cell_y=0.12)
    mesh = volume_to_mesh(vol, spacing)
    os.makedirs(args.out_dir, exist_ok=True)
    ply = os.path.join(args.out_dir, "graybox.ply")
    o3d.io.write_triangle_mesh(ply, mesh)
    print("graybox", ply, "verts", len(mesh.vertices))

    xz = free_path(walls, cell, args.stride)
    poses = poses_from_path(xz, args.eye_y, args.interp)
    if len(poses) > args.max_frames:
        idx = np.linspace(0, len(poses) - 1, args.max_frames).astype(int)
        poses = [poses[i] for i in idx]
    print("poses", len(poses))

    frames_dir = os.path.join(args.out_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    frames = render_raycast(mesh, poses, args.image_size)
    for i, f in enumerate(frames):
        cv2.imwrite(os.path.join(frames_dir, f"walk_{i:04d}.png"), f)
    mp4 = os.path.join(args.out_dir, "walkthrough.mp4")
    h, w = frames[0].shape[:2]
    writer = cv2.VideoWriter(mp4, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (w, h))
    for f in frames:
        writer.write(f)
    writer.release()
    print("video", mp4)


if __name__ == "__main__":
    main()
