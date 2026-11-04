"""Explicit camera conventions and checked, losslessly compressed depth payloads.

Images are upright, with pixel centers (column + .5, row + .5). CV axes are
right/down/forward; GL axes are right/up/backward. A T_world_camera matrix maps
camera coordinates into world coordinates, never the inverse transform.
"""

from __future__ import annotations

import numpy as np

GL_FROM_CV = np.diag([1.0, -1.0, -1.0, 1.0])
DEPTH_FORMATS = ("uint16_mm", "float32_m")
CONVENTIONS = {
    "image_origin": "top_left",
    "pixel_center": "column_plus_0.5_row_plus_0.5",
    "depth": "metric_optical_axis_Z_not_ray_distance",
    "camera_gl": "X_right_Y_up_minusZ_forward",
    "camera_cv": "X_right_Y_down_Z_forward",
    "pose_direction": "T_world_camera_maps_camera_to_world",
    "T_world_camera_cv": "T_world_camera_gl @ diag(1,-1,-1,1)",
    "invalid_depth": "zero_storage_plus_explicit_false_valid_mask",
    "uint16_valid_range_m": [0.001, 65.535],
    "uint16_max_quantization_error_m": 0.0005001,
}


def pose(value, *, atol=1e-5):
    value = np.asarray(value, dtype=np.float64)
    if value.shape != (4, 4) or not np.isfinite(value).all():
        raise ValueError("camera pose must be a finite 4x4 matrix")
    rotation = value[:3, :3]
    if (
        not np.allclose(value[3], [0, 0, 0, 1], atol=atol, rtol=0)
        or not np.allclose(rotation.T @ rotation, np.eye(3), atol=atol, rtol=0)
        or not np.isclose(np.linalg.det(rotation), 1, atol=atol, rtol=0)
    ):
        raise ValueError("camera pose must contain a proper rigid rotation")
    return value


def intrinsics(value):
    value = np.asarray(value, dtype=np.float64)
    if (
        value.shape != (3, 3)
        or not np.isfinite(value).all()
        or value[0, 0] <= 0
        or value[1, 1] <= 0
        or not np.allclose(value[2], [0, 0, 1], atol=1e-7, rtol=0)
        or abs(np.linalg.det(value)) < 1e-12
    ):
        raise ValueError("K must be a finite invertible optical intrinsic matrix")
    return value


def check_calibration(K, T_gl, T_cv):
    K, T_gl, T_cv = intrinsics(K), pose(T_gl), pose(T_cv)
    if not np.allclose(T_gl @ GL_FROM_CV, T_cv, atol=1e-5, rtol=0):
        raise ValueError("GL/CV camera poses disagree; possible double axis correction")
    return K, T_gl, T_cv


def depth_buffer_to_z(buffer, near, far):
    """MuJoCo perspective buffer -> optical-axis meters; background is invalid."""
    buffer = np.asarray(buffer, dtype=np.float64)
    if buffer.ndim != 2 or not buffer.size:
        raise ValueError("depth buffer must be a nonempty HxW image")
    if not np.isfinite([near, far]).all() or not 0 < near < far:
        raise ValueError("invalid metric clipping planes")
    finite = np.isfinite(buffer)
    if np.any(finite & ((buffer < 0) | (buffer > 1))):
        raise ValueError("expected a normalized OpenGL depth buffer, not metric depth")
    valid = finite & (buffer < 1)
    safe = np.where(valid, buffer, 0)
    depth = near / (1 - safe * (1 - near / far))
    return np.where(valid, depth, 0), valid


def encode_depth(depth_m, valid, storage):
    depth = np.asarray(depth_m, dtype=np.float64)
    valid = np.asarray(valid)
    if valid.dtype != np.bool_ or depth.shape != valid.shape or depth.ndim != 2:
        raise ValueError("depth/boolean-valid shapes must match HxW")
    if np.any(valid & (~np.isfinite(depth) | (depth <= 0))):
        raise ValueError("valid depth must be finite and positive")
    if storage == "uint16_mm":
        if np.any(valid & ((depth < 0.001) | (depth > 65.535))):
            raise ValueError(
                "uint16_mm depth overflow/underflow; use explicit float32_m"
            )
        encoded = np.rint(np.where(valid, depth, 0) * 1000).astype(np.uint16)
    elif storage == "float32_m":
        if np.any(valid & (depth > np.finfo(np.float32).max)):
            raise ValueError("float32_m depth overflow")
        encoded = np.where(valid, depth, 0).astype(np.float32)
        if np.any(valid & (~np.isfinite(encoded) | (encoded <= 0))):
            raise ValueError("float32_m depth not representable")
    else:
        raise ValueError(f"unsupported depth storage: {storage}")
    restored = decode_depth(encoded, valid, storage)
    error = (
        float(np.max(np.abs(restored[valid] - depth[valid]))) if valid.any() else 0.0
    )
    if storage == "uint16_mm" and error > 0.0005001:
        raise ValueError("millimeter quantization exceeded half a millimeter")
    return encoded, valid.copy(), error


def decode_depth(encoded, valid, storage):
    encoded, valid = np.asarray(encoded), np.asarray(valid)
    expected = {"uint16_mm": np.dtype("uint16"), "float32_m": np.dtype("float32")}
    if (
        storage not in expected
        or encoded.dtype != expected[storage]
        or valid.dtype != np.bool_
        or encoded.shape != valid.shape
        or encoded.ndim not in (2, 3)
        or not np.isfinite(encoded).all()
        or np.any(encoded[~valid] != 0)
        or np.any(encoded[valid] <= 0)
    ):
        raise ValueError("corrupt depth payload, dtype or invalid-pixel mask")
    return encoded.astype(np.float64) / (1000 if storage == "uint16_mm" else 1)


def rays_cv(K, pixels):
    pixels = np.asarray(pixels, dtype=np.float64)
    if pixels.ndim != 2 or pixels.shape[1] != 2 or not np.isfinite(pixels).all():
        raise ValueError("pixel centers must be finite Nx2")
    return np.c_[pixels, np.ones(len(pixels))] @ np.linalg.inv(intrinsics(K)).T


def backproject_world(K, T_world_camera_cv, pixels, depth_z):
    rays = rays_cv(K, pixels)
    depth_z = np.asarray(depth_z, dtype=np.float64)
    if (
        depth_z.shape != (len(rays),)
        or not np.isfinite(depth_z).all()
        or np.any(depth_z <= 0)
    ):
        raise ValueError("one finite positive optical Z per pixel is required")
    T = pose(T_world_camera_cv)
    return (rays * depth_z[:, None]) @ T[:3, :3].T + T[:3, 3]


def project_world(K, T_world_camera_cv, points):
    T = pose(T_world_camera_cv)
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("world points must be finite Nx3")
    # Float32 serialization slightly perturbs orthogonality; solve the stored
    # transform instead of treating its transpose as an exact matrix inverse.
    camera = np.linalg.solve(T[:3, :3], (points - T[:3, 3]).T).T
    if np.any(camera[:, 2] <= 0):
        raise ValueError("world point is behind optical camera")
    projected = camera @ intrinsics(K).T
    return projected[:, :2] / projected[:, 2:3]


def depth_statistics(depth, valid):
    values = np.asarray(depth)[valid]
    return {
        "valid_pixels": int(valid.sum()),
        "total_pixels": int(valid.size),
        "valid_fraction": float(valid.mean()),
        "min_m": float(values.min()) if len(values) else None,
        "median_m": float(np.median(values)) if len(values) else None,
        "max_m": float(values.max()) if len(values) else None,
    }


def rgb_metrics(original, rendered):
    """No video encoding: MAE/PSNR plus explicitly specified uniform-window SSIM."""
    from scipy.ndimage import uniform_filter

    original, rendered = np.asarray(original), np.asarray(rendered)
    if (
        original.dtype != np.uint8
        or rendered.dtype != np.uint8
        or original.shape != rendered.shape
        or original.ndim != 3
        or original.shape[-1] != 3
        or min(original.shape[:2]) < 7
    ):
        raise ValueError("RGB comparison requires matching uint8 HxWx3, H/W >=7")
    a, b = original.astype(np.float64), rendered.astype(np.float64)
    ma, mb = (uniform_filter(x, size=(7, 7, 1), mode="reflect") for x in (a, b))
    covariance = 49 / 48
    va = covariance * (uniform_filter(a * a, size=(7, 7, 1)) - ma * ma)
    vb = covariance * (uniform_filter(b * b, size=(7, 7, 1)) - mb * mb)
    cov = covariance * (uniform_filter(a * b, size=(7, 7, 1)) - ma * mb)
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    ssim = ((2 * ma * mb + c1) * (2 * cov + c2)) / (
        (ma * ma + mb * mb + c1) * (va + vb + c2)
    )
    mse = float(np.mean((a - b) ** 2))
    return {
        "mae": float(np.mean(np.abs(a - b))),
        "psnr_db": float(10 * np.log10(255**2 / mse)) if mse else None,
        "psnr_exact_match": mse == 0,
        "ssim": float(np.mean(ssim[3:-3, 3:-3])),
        "ssim_definition": "uniform_7x7_sample_covariance_rgb_mean_valid_crop",
    }
