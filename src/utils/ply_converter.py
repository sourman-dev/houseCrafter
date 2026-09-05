"""3D Point Cloud and Mesh Processing Utilities for HouseCrafter.

Handles PLY validation, downsampling for web viewers, conversion between
formats (PLY, OBJ, GLB), and synthetic room generation for mock tests.
"""

import os
import shutil
from typing import Optional, Tuple
import numpy as np


def optimize_ply_for_web(
    input_ply_path: str,
    output_ply_path: Optional[str] = None,
    voxel_size: float = 0.03,
    nb_neighbors: int = 20,
    std_ratio: float = 2.0,
    max_points: int = 300000,
) -> str:
    """Downsample and denoise a PLY point cloud or mesh for WebGL rendering.

    Args:
        input_ply_path: Path to the raw .ply file.
        output_ply_path: Optional destination path. If None, appends '_opt'.
        voxel_size: Voxel downsampling grid size in meters.
        nb_neighbors: Statistical outlier removal neighbor count.
        std_ratio: Statistical outlier standard deviation threshold.
        max_points: Hard cap on point count for web viewing.

    Returns:
        Path to the optimized .ply file.
    """
    if output_ply_path is None:
        base, ext = os.path.splitext(input_ply_path)
        output_ply_path = f"{base}_optimized{ext}"

    if not os.path.exists(input_ply_path):
        raise FileNotFoundError(f"Input PLY file not found: {input_ply_path}")

    try:
        import open3d as o3d

        # Try reading as point cloud
        pcd = o3d.io.read_point_cloud(input_ply_path)
        if len(pcd.points) == 0:
            # Try reading as triangle mesh
            mesh = o3d.io.read_triangle_mesh(input_ply_path)
            if len(mesh.vertices) > 0:
                pcd = o3d.geometry.PointCloud()
                pcd.points = mesh.vertices
                if mesh.has_vertex_colors():
                    pcd.colors = mesh.vertex_colors

        if len(pcd.points) > 0:
            # Denoise & downsample
            if voxel_size > 0:
                pcd = pcd.voxel_down_sample(voxel_size=voxel_size)
            if len(pcd.points) > nb_neighbors:
                pcd, _ = pcd.remove_statistical_outlier(
                    nb_neighbors=nb_neighbors, std_ratio=std_ratio
                )

            # Cap maximum points
            if len(pcd.points) > max_points:
                indices = np.random.choice(
                    len(pcd.points), size=max_points, replace=False
                )
                pcd = pcd.select_by_index(indices)

            dest_dir = os.path.dirname(os.path.abspath(output_ply_path))
            os.makedirs(dest_dir, exist_ok=True)
            o3d.io.write_point_cloud(output_ply_path, pcd)
            return output_ply_path

    except Exception as e:
        print(f"[Warning] Open3D optimization failed ({e}), copying instead.")

    # Fallback: copy original if processing fails
    if input_ply_path != output_ply_path:
        dest_dir = os.path.dirname(os.path.abspath(output_ply_path))
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copyfile(input_ply_path, output_ply_path)
    return output_ply_path


def convert_ply_to_glb(
    ply_path: str,
    output_glb_path: Optional[str] = None
) -> Optional[str]:
    """Convert a .ply mesh or point cloud to .glb format for web viewers.

    Args:
        ply_path: Path to source .ply file.
        output_glb_path: Path for output .glb file.

    Returns:
        Path to .glb file if successful, or None if conversion is unsupported.
    """
    if output_glb_path is None:
        base, _ = os.path.splitext(ply_path)
        output_glb_path = f"{base}.glb"

    try:
        import trimesh
        mesh_or_pcd = trimesh.load(ply_path)
        dest_dir = os.path.dirname(os.path.abspath(output_glb_path))
        os.makedirs(dest_dir, exist_ok=True)
        mesh_or_pcd.export(output_glb_path, file_type="glb")
        return output_glb_path
    except Exception as e:
        print(f"[Warning] PLY to GLB conversion failed: {e}")
        return None


def get_ply_metadata(ply_path: str) -> dict:
    """Extract summary metrics from a PLY file (point count, bounds)."""
    if not os.path.exists(ply_path):
        return {"error": "File not found", "point_count": 0}

    file_size_mb = os.path.getsize(ply_path) / (1024 * 1024)
    try:
        import open3d as o3d
        pcd = o3d.io.read_point_cloud(ply_path)
        num_points = len(pcd.points)
        if num_points == 0:
            mesh = o3d.io.read_triangle_mesh(ply_path)
            num_points = len(mesh.vertices)
            bbox = mesh.get_axis_aligned_bounding_box()
        else:
            bbox = pcd.get_axis_aligned_bounding_box()

        min_bound = bbox.get_min_bound().tolist()
        max_bound = bbox.get_max_bound().tolist()
        return {
            "point_count": num_points,
            "file_size_mb": round(file_size_mb, 2),
            "bounding_box_min": [round(x, 2) for x in min_bound],
            "bounding_box_max": [round(x, 2) for x in max_bound],
        }
    except Exception:
        return {
            "point_count": "Unknown",
            "file_size_mb": round(file_size_mb, 2),
        }


def create_sample_room_ply(
    output_path: str,
    room_size: Tuple[float, float, float] = (4.0, 2.8, 5.0),
    num_points: int = 50000
) -> str:
    """Generate a realistic synthetic 3D indoor room point cloud.

    Used for UI testing, mock mode, and unit tests without loading diffusion
    weights.
    """
    width, height, length = room_size
    points = []
    colors = []

    # 1. Floor (y = 0)
    n_floor = int(num_points * 0.25)
    fx = np.random.uniform(-width / 2, width / 2, n_floor)
    fz = np.random.uniform(-length / 2, length / 2, n_floor)
    fy = np.zeros(n_floor) + np.random.normal(0, 0.01, n_floor)
    floor_pts = np.stack([fx, fy, fz], axis=1)
    # Warm wood floor color
    floor_cols = np.tile([0.65, 0.45, 0.30], (n_floor, 1))
    floor_cols += np.random.normal(0, 0.03, (n_floor, 3))
    points.append(floor_pts)
    colors.append(np.clip(floor_cols, 0.0, 1.0))

    # 2. Walls (x = +-width/2, z = +-length/2, y in [0, height])
    n_walls = int(num_points * 0.35)
    n_w_sub = n_walls // 4

    # Back wall (z = length/2)
    wx = np.random.uniform(-width / 2, width / 2, n_w_sub)
    wy = np.random.uniform(0, height, n_w_sub)
    wz = np.full(n_w_sub, length / 2)
    points.append(np.stack([wx, wy, wz], axis=1))
    colors.append(np.tile([0.88, 0.88, 0.85], (n_w_sub, 1)))

    # Front wall (z = -length/2)
    wx = np.random.uniform(-width / 2, width / 2, n_w_sub)
    wy = np.random.uniform(0, height, n_w_sub)
    wz = np.full(n_w_sub, -length / 2)
    points.append(np.stack([wx, wy, wz], axis=1))
    colors.append(np.tile([0.88, 0.88, 0.85], (n_w_sub, 1)))

    # Left wall (x = -width/2)
    wx = np.full(n_w_sub, -width / 2)
    wy = np.random.uniform(0, height, n_w_sub)
    wz = np.random.uniform(-length / 2, length / 2, n_w_sub)
    points.append(np.stack([wx, wy, wz], axis=1))
    colors.append(np.tile([0.82, 0.85, 0.88], (n_w_sub, 1)))

    # Right wall (x = width/2)
    wx = np.full(n_w_sub, width / 2)
    wy = np.random.uniform(0, height, n_w_sub)
    wz = np.random.uniform(-length / 2, length / 2, n_w_sub)
    points.append(np.stack([wx, wy, wz], axis=1))
    colors.append(np.tile([0.82, 0.85, 0.88], (n_w_sub, 1)))

    # 3. Furniture: Bed in corner
    n_bed = int(num_points * 0.25)
    bx = np.random.uniform(-width / 2 + 0.2, -width / 2 + 2.0, n_bed)
    by = np.random.uniform(0, 0.7, n_bed)
    bz = np.random.uniform(length / 2 - 2.2, length / 2 - 0.2, n_bed)
    bed_pts = np.stack([bx, by, bz], axis=1)
    bed_cols = np.tile([0.25, 0.45, 0.70], (n_bed, 1))
    bed_cols += np.random.normal(0, 0.02, (n_bed, 3))
    points.append(bed_pts)
    colors.append(np.clip(bed_cols, 0.0, 1.0))

    # 4. Furniture: Table / Desk
    n_table = int(num_points * 0.15)
    tx = np.random.uniform(width / 2 - 1.5, width / 2 - 0.3, n_table)
    ty = np.random.uniform(0, 0.8, n_table)
    tz = np.random.uniform(-1.0, 1.0, n_table)
    tbl_pts = np.stack([tx, ty, tz], axis=1)
    tbl_cols = np.tile([0.50, 0.30, 0.18], (n_table, 1))
    tbl_cols += np.random.normal(0, 0.02, (n_table, 3))
    points.append(tbl_pts)
    colors.append(np.clip(tbl_cols, 0.0, 1.0))

    all_points = np.concatenate(points, axis=0)
    all_colors = np.concatenate(colors, axis=0)

    dest_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(dest_dir, exist_ok=True)

    with open(output_path, "w") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(all_points)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")
        for pt, col in zip(all_points, all_colors):
            r, g, b = (col * 255).astype(int)
            f.write(f"{pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f} {r} {g} {b}\n")

    return output_path
