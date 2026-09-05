"""Lift a 2D ground-floor image (file or URL) into a colored 3D PLY.

Pinterest pin pages are HTML; this module resolves og:image / pinimg CDN
URLs, then extrudes walls and furniture from the drawing. No Open3D.
"""

from __future__ import annotations

import os
import re
import time
import urllib.request
from typing import Tuple
from urllib.parse import urlparse

import numpy as np
from PIL import Image


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
OG_IMAGE_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+'
    r'content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
OG_IMAGE_RE_REV = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+'
    r'(?:property|name)=["\'](?:og:image|twitter:image)["\']',
    re.IGNORECASE,
)
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")


def _http_get(url: str, timeout: int = 30) -> Tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "image/avif,image/webp,image/*,text/html,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        ctype = resp.headers.get("Content-Type", "")
        return resp.read(), ctype


def resolve_image_url(url: str) -> str:
    """Return a direct image URL. Pin pages → og:image."""
    url = (url or "").strip()
    if not url:
        raise ValueError("Empty image URL")
    lower = url.lower().split("?", 1)[0]
    if lower.endswith(IMAGE_EXT) or "i.pinimg.com" in lower:
        return url
    body, ctype = _http_get(url)
    if ctype.startswith("image/"):
        return url
    html = body.decode("utf-8", errors="ignore")
    match = OG_IMAGE_RE.search(html) or OG_IMAGE_RE_REV.search(html)
    if not match:
        raise ValueError(
            "Could not find an image at that URL. "
            "On Pinterest: open the pin → right-click the image → "
            "Copy image address (i.pinimg.com/...)."
        )
    return match.group(1)


def fetch_floorplan_image(url: str, dest_dir: str) -> str:
    """Download a floorplan image from a URL to dest_dir. Returns file path."""
    os.makedirs(dest_dir, exist_ok=True)
    image_url = resolve_image_url(url)
    data, ctype = _http_get(image_url)
    ext = ".jpg"
    path_part = urlparse(image_url).path.lower()
    for candidate in IMAGE_EXT:
        if path_part.endswith(candidate):
            ext = candidate
            break
    if "png" in ctype:
        ext = ".png"
    elif "webp" in ctype:
        ext = ".webp"
    dest = os.path.join(dest_dir, f"url_{int(time.time())}{ext}")
    with open(dest, "wb") as fh:
        fh.write(data)
    Image.open(dest).convert("RGB").save(dest)
    return dest


def _write_ascii_ply(path: str, points: np.ndarray, colors: np.ndarray) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    rgb = np.clip(colors * 255.0, 0, 255).astype(np.uint8)
    with open(path, "w") as fh:
        fh.write("ply\nformat ascii 1.0\n")
        fh.write(f"element vertex {len(points)}\n")
        fh.write("property float x\nproperty float y\nproperty float z\n")
        fh.write("property uchar red\nproperty uchar green\n")
        fh.write("property uchar blue\n")
        fh.write("end_header\n")
        for (x, y, z), (r, g, b) in zip(points, rgb):
            fh.write(f"{x:.4f} {y:.4f} {z:.4f} {int(r)} {int(g)} {int(b)}\n")
    return path


def lift_floorplan_to_ply(
    image_path: str,
    ply_path: str,
    wall_height: float = 2.8,
    meters_per_image: float = 12.0,
    max_side: int = 320,
) -> str:
    """Extrude a 2D floorplan drawing into a colored point cloud."""
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError(f"Floorplan image not found: {image_path}")

    img = Image.open(image_path).convert("RGB")
    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    arr = np.asarray(img).astype(np.float32) / 255.0
    h, w, _ = arr.shape
    scale = meters_per_image / max(h, w)

    brightness = arr.mean(axis=2)
    maxc = arr.max(axis=2)
    minc = arr.min(axis=2)
    sat = np.where(maxc > 1e-6, (maxc - minc) / np.clip(maxc, 1e-6, None), 0.0)

    paper = (brightness > 0.88) & (sat < 0.12)
    walls = brightness < 0.38
    furniture = (~paper) & (~walls) & (sat > 0.18)
    interior = ~paper

    ys, xs = np.indices((h, w))
    world_x = (xs - w / 2.0) * scale
    world_z = (h / 2.0 - ys) * scale

    chunks_p = []
    chunks_c = []

    floor_m = interior
    if floor_m.any():
        chunks_p.append(
            np.stack(
                [world_x[floor_m], np.zeros(floor_m.sum()), world_z[floor_m]],
                axis=1,
            )
        )
        chunks_c.append(arr[floor_m])

    if walls.any():
        n_wall = int(walls.sum())
        layers = np.linspace(0.05, wall_height, 10)
        wx = np.repeat(world_x[walls], len(layers))
        wz = np.repeat(world_z[walls], len(layers))
        wy = np.tile(layers, n_wall)
        chunks_p.append(np.stack([wx, wy, wz], axis=1))
        chunks_c.append(np.repeat(arr[walls], len(layers), axis=0))

    if furniture.any():
        n_f = int(furniture.sum())
        layers = np.linspace(0.05, 0.75, 5)
        fx = np.repeat(world_x[furniture], len(layers))
        fz = np.repeat(world_z[furniture], len(layers))
        fy = np.tile(layers, n_f)
        chunks_p.append(np.stack([fx, fy, fz], axis=1))
        chunks_c.append(np.repeat(arr[furniture], len(layers), axis=0))

    if not chunks_p:
        raise ValueError("No floorplan structure found in the image.")

    points = np.concatenate(chunks_p, axis=0)
    colors = np.concatenate(chunks_c, axis=0)
    max_pts = 180000
    if len(points) > max_pts:
        rng = np.random.default_rng(0)
        idx = rng.choice(len(points), size=max_pts, replace=False)
        points = points[idx]
        colors = colors[idx]
    return _write_ascii_ply(ply_path, points, colors)


def make_preview_views(
    image_path: str,
    out_dir: str,
    wall_height: float = 2.8,
) -> Tuple[list, list]:
    """Save RGB + depth-style previews derived from the input floorplan."""
    os.makedirs(os.path.join(out_dir, "rgb_views"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "depth_views"), exist_ok=True)
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((512, 512), Image.Resampling.LANCZOS)
    rgb_path = os.path.join(out_dir, "rgb_views", "view_00_rgb.png")
    img.save(rgb_path)

    gray = np.asarray(img.convert("L")).astype(np.float32) / 255.0
    height_img = (1.0 - gray) * (wall_height / wall_height)
    depth = (height_img * 255.0).astype(np.uint8)
    depth_path = os.path.join(out_dir, "depth_views", "depth_00.png")
    Image.fromarray(depth, mode="L").save(depth_path)
    return [rgb_path], [depth_path]
