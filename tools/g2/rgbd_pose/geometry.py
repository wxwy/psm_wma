"""Explicit camera conventions and checked, losslessly compressed depth payloads.

Images are upright, with pixel centers (column + .5, row + .5). CV axes are
right/down/forward; GL axes are right/up/backward. A T_world_camera matrix maps
camera coordinates into world coordinates, never the inverse transform.
"""

from __future__ import annotations

import numpy as np

GL_FROM_CV = np.diag([1.0, -1.0, -1.0, 1.0])
DEPTH_FORMATS = ("uint16_mm", "float32_m")
ENCODING_COUNTS = (
    "total_pixels",
    "renderer_invalid",
    "below_1mm",
    "above_65_535m",
    "encoded_valid",
)
RANGE_WARNING_FRACTION = 0.01
CONVENTIONS = {
    "image_origin": "top_left",
    "pixel_center": "column_plus_0.5_row_plus_0.5",
    "depth": "metric_optical_axis_Z_not_ray_distance",
    "camera_gl": "X_right_Y_up_minusZ_forward",
    "camera_cv": "X_right_Y_down_Z_forward",
    "pose_direction": "T_world_camera_maps_camera_to_world",
    "T_world_camera_cv": "T_world_camera_gl @ diag(1,-1,-1,1)",
    "invalid_depth": "zero_sentinel_valid_is_depth_gt_zero_no_persisted_mask",
    "uint16_out_of_range": "zero_not_saturated_or_wrapped",
    "range_exclusion_warning_fraction": RANGE_WARNING_FRACTION,
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


def _storage_mask(depth_m, valid, storage):
    depth = np.asarray(depth_m, dtype=np.float64)
    valid = np.asarray(valid)
    if (
        valid.dtype != np.bool_
        or depth.shape != valid.shape
        or depth.ndim != 2
        or not depth.size
    ):
        raise ValueError("depth/boolean-valid shapes must match HxW")
    if np.any(valid & ~np.isfinite(depth)):
        raise ValueError("renderer-valid depth must be finite")
    if storage == "uint16_mm":
        mask = valid & (depth >= 0.001) & (depth <= 65.535)
    elif storage == "float32_m":
        if np.any(valid & ((depth <= 0) | (depth > np.finfo(np.float32).max))):
            raise ValueError("float32_m depth overflow")
        mask = valid.copy()
    else:
        raise ValueError(f"unsupported depth storage: {storage}")
    return depth, valid, mask


def encode_depth(depth_m, valid, storage):
    """Encode v2 depth; the returned mask is transient, never a chunk array."""
    depth, _, valid = _storage_mask(depth_m, valid, storage)
    if storage == "uint16_mm":
        encoded = np.rint(np.where(valid, depth, 0) * 1000).astype(np.uint16)
    else:
        encoded = np.where(valid, depth, 0).astype(np.float32)
        if np.any(valid & (~np.isfinite(encoded) | (encoded <= 0))):
            raise ValueError("float32_m depth not representable")
    restored = decode_depth(encoded, valid, storage)
    error = (
        float(np.max(np.abs(restored[valid] - depth[valid]))) if valid.any() else 0.0
    )
    if storage == "uint16_mm" and error > 0.0005001:
        raise ValueError("millimeter quantization exceeded half a millimeter")
    return encoded, valid.copy(), error


def decode_depth(encoded, valid_or_storage, storage=None):
    """Depth-only reader; optional old calling form checks a transient mask."""
    encoded = np.asarray(encoded)
    supplied_mask = None if storage is None else np.asarray(valid_or_storage)
    storage = valid_or_storage if storage is None else storage
    expected = {"uint16_mm": np.dtype("uint16"), "float32_m": np.dtype("float32")}
    if (
        storage not in expected
        or encoded.dtype != expected[storage]
        or encoded.ndim not in (2, 3)
        or not encoded.size
        or not np.isfinite(encoded).all()
        or np.any(encoded < 0)
    ):
        raise ValueError("corrupt depth payload, dtype or invalid-pixel mask")
    if supplied_mask is not None and (
        supplied_mask.dtype != np.bool_
        or supplied_mask.shape != encoded.shape
        or not np.array_equal(supplied_mask, encoded > 0)
    ):
        raise ValueError("transient mask disagrees with zero-sentinel depth")
    return encoded.astype(np.float64) / (1000 if storage == "uint16_mm" else 1)


def _encoding_summary(counts, storage, minimum, maximum):
    renderer_valid = counts["total_pixels"] - counts["renderer_invalid"]
    fraction = (counts["below_1mm"] + counts["above_65_535m"]) / max(renderer_valid, 1)
    return {
        **counts,
        "range_filter_applied": storage == "uint16_mm",
        "finite_raw_min_m": minimum,
        "finite_raw_max_m": maximum,
        "range_excluded_fraction_of_renderer_valid": fraction,
        "warning_threshold_fraction": RANGE_WARNING_FRACTION,
        "warning": "RANGE_EXCLUSION_GT_1_PERCENT"
        if fraction > RANGE_WARNING_FRACTION
        else None,
    }


def encoding_statistics(depth_m, renderer_valid, storage):
    """Disjoint source classifications, including values not stored in v2."""
    depth, renderer_valid, valid = _storage_mask(depth_m, renderer_valid, storage)
    counts = {
        "total_pixels": int(valid.size),
        "renderer_invalid": int((~renderer_valid).sum()),
        "below_1mm": int((renderer_valid & (depth < 0.001)).sum())
        if storage == "uint16_mm"
        else 0,
        "above_65_535m": int((renderer_valid & (depth > 65.535)).sum())
        if storage == "uint16_mm"
        else 0,
        "encoded_valid": int(valid.sum()),
    }
    values = depth[renderer_valid]
    return _encoding_summary(
        counts,
        storage,
        float(values.min()) if values.size else None,
        float(values.max()) if values.size else None,
    )


def validate_encoding_statistics(stats, encoded, storage):
    """Offline consistency only; native replay validates source classifications."""
    decode_depth(encoded, storage)
    required = set(ENCODING_COUNTS) | {"finite_raw_min_m", "finite_raw_max_m"}
    if not isinstance(stats, dict) or not required.issubset(stats):
        raise ValueError("missing depth encoding counts")
    counts = {key: stats[key] for key in ENCODING_COUNTS}
    if any(type(value) is not int or value < 0 for value in counts.values()):
        raise ValueError("invalid depth encoding counts")
    if (
        counts["total_pixels"] != encoded.size
        or counts["encoded_valid"] != int((encoded > 0).sum())
        or sum(counts[k] for k in ENCODING_COUNTS[1:]) != encoded.size
        or (storage == "float32_m" and (counts["below_1mm"] or counts["above_65_535m"]))
    ):
        raise ValueError("depth encoding counts disagree with payload")
    minimum, maximum = stats["finite_raw_min_m"], stats["finite_raw_max_m"]
    renderer_valid = counts["total_pixels"] - counts["renderer_invalid"]
    if renderer_valid:
        if (
            not all(
                type(v) in (int, float) and np.isfinite(v) for v in (minimum, maximum)
            )
            or minimum > maximum
        ):
            raise ValueError("invalid finite raw depth range")
        if storage == "uint16_mm" and (
            (minimum < 0.001) != bool(counts["below_1mm"])
            or (maximum > 65.535) != bool(counts["above_65_535m"])
        ):
            raise ValueError("range exclusions disagree with raw extrema")
    elif minimum is not None or maximum is not None:
        raise ValueError("renderer-invalid frame cannot declare raw depth extrema")
    if stats != _encoding_summary(counts, storage, minimum, maximum):
        raise ValueError("depth encoding diagnostic contract mismatch")


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


def pose_motion(values):
    values = [pose(value) for value in values]
    if not values:
        raise ValueError("pose motion requires at least one calibrated pose")
    first = values[0]
    translations, angles = [], []
    for value in values:
        translations.append(float(np.linalg.norm(value[:3, 3] - first[:3, 3])))
        relative = np.linalg.solve(first[:3, :3], value[:3, :3])
        # Float32 perturbs orthogonality. Measure the nearest proper relative
        # rotation instead of R.T @ R of an already rounded matrix.
        u, _, vt = np.linalg.svd(relative)
        rotation = u @ vt
        angles.append(float(np.arccos(np.clip((np.trace(rotation) - 1) / 2, -1, 1))))
    return {
        "max_translation_m": max(translations),
        "max_rotation_rad": max(angles),
        "changed": max(translations) > 1e-6 or max(angles) > 1e-5,
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
