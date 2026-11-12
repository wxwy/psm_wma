"""Source-independent, linear-light composition of projected surface layers.

The caller projects meshes, surfels, or surface voxels into these arrays.  This
module has no MuJoCo or semantic-owner filtering and never samples another
surface's color.  Smaller finite depth means nearer, including signed depths.

Unknown colors are not black.  ``composite_rgb_linear`` is NaN wherever the
scene evidence is insufficient.  An optional background affects only
``display_rgb_linear``; it cannot make training evidence valid.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntFlag

import numpy as np

from g2.io import ContractError


class CompositeUnknown(IntFlag):
    """Per-pixel reasons why the final scene color is not certified."""

    COLOR = 1
    ALPHA = 2
    BACKGROUND = 4
    DEPTH_TIE = 8
    NO_SURFACE = 16


@dataclass
class _Layer:
    depth: np.ndarray
    rgb: np.ndarray
    alpha: np.ndarray
    geometry: np.ndarray
    color_valid: np.ndarray
    alpha_valid: np.ndarray
    geom_id: np.ndarray
    material_id: np.ndarray
    owner: np.ndarray
    surface_id: np.ndarray


def _pixels(value, shape, name, dtype):
    array = np.asarray(value, dtype=dtype)
    if array.ndim == 0:
        return np.broadcast_to(array, shape)
    if array.shape != shape:
        raise ContractError(f"{name} must be scalar or have image shape {shape}")
    return array


def _mask(value, shape, name):
    array = np.asarray(value)
    if array.dtype.kind not in "biuf" or not np.isin(array, (0, 1)).all():
        raise ContractError(f"{name} must contain only boolean values")
    return _pixels(array, shape, name, bool)


def _ids(value, shape, name):
    if value is None:
        value = -1
    array = np.asarray(value)
    if array.dtype.kind not in "iu":
        raise ContractError(f"{name} must contain integer IDs")
    if array.dtype.kind == "u" and np.any(array > np.iinfo(np.int64).max):
        raise ContractError(f"{name} exceeds the signed integer ID range")
    result = _pixels(array, shape, name, np.int64)
    if np.any(result < -1):
        raise ContractError(f"{name} reserves -1 for a missing ID")
    return result


def _surface_ids(value, shape, string_ids):
    # Scalar string identities are interned once per layer.  Per-pixel IDs are
    # integers, avoiding Python object arrays and per-pixel string processing.
    if value is None:
        return np.full(shape, -1, dtype=np.int64)
    array = np.asarray(value)
    if array.ndim == 0 and array.dtype.kind in "US":
        key = array.item()
        if not key:
            raise ContractError("surface_id must not be an empty string")
        if key not in string_ids:
            string_ids[key] = -2 - len(string_ids)
        return np.full(shape, string_ids[key], dtype=np.int64)
    return _ids(value, shape, "surface_id")


def _rgb(value, shape, name):
    array = np.asarray(value, dtype=np.float64)
    if array.shape == (3,):
        return np.broadcast_to(array, (*shape, 3))
    if array.shape != (*shape, 3):
        raise ContractError(f"{name} must be RGB or have image shape {(*shape, 3)}")
    return array


def _normalize(record, shape, string_ids, *, opaque=False):
    if not isinstance(record, Mapping):
        raise ContractError("a projected surface layer must be a mapping")
    required = {"depth", "geometry_valid", "rgb_linear", "color_valid", "geom_id"}
    if not opaque:
        required.update(("alpha", "alpha_valid"))
    missing = required.difference(record)
    if missing:
        raise ContractError("surface layer is missing: " + ", ".join(sorted(missing)))
    depth = np.asarray(record["depth"], dtype=np.float64)
    if depth.shape != shape:
        raise ContractError(f"depth must have image shape {shape}")
    geometry = _mask(record["geometry_valid"], shape, "geometry_valid").copy()
    rgb = _rgb(record["rgb_linear"], shape, "rgb_linear")
    color_valid = _mask(record["color_valid"], shape, "color_valid")
    alpha = _pixels(record.get("alpha", 1.0), shape, "alpha", np.float64)
    alpha_valid = _mask(record.get("alpha_valid", True), shape, "alpha_valid")
    geom_id = _ids(record["geom_id"], shape, "geom_id")
    material_id = _ids(record.get("material_id"), shape, "material_id")
    owner = _ids(record.get("semantic_owner"), shape, "semantic_owner")
    if np.any(geometry & ~np.isfinite(depth)):
        raise ContractError("valid geometry requires finite depth")
    if np.any(geometry & (geom_id < 0)):
        raise ContractError("valid geometry requires an independent geom_id")
    known_color = geometry & color_valid
    if np.any(known_color & (~np.isfinite(rgb).all(axis=-1) | (rgb < 0).any(axis=-1))):
        raise ContractError("valid linear RGB must be finite and nonnegative")
    known_alpha = geometry & alpha_valid
    if np.any(known_alpha & (~np.isfinite(alpha) | (alpha < 0) | (alpha > 1))):
        raise ContractError("valid alpha must be finite and in [0, 1]")
    if opaque and np.any(geometry & (~alpha_valid | (alpha != 1))):
        raise ContractError("opaque geometry requires known alpha equal to one")
    return _Layer(
        depth, rgb, alpha, geometry, color_valid, alpha_valid,
        geom_id, material_id, owner,
        _surface_ids(record.get("surface_id"), shape, string_ids),
    )


def _deduplicate(layers, shape):
    removed = np.zeros(shape, dtype=np.int32)
    for index, layer in enumerate(layers):
        for previous in layers[:index]:
            same = (
                layer.geometry & previous.geometry
                & (layer.surface_id != -1)
                & (layer.surface_id == previous.surface_id)
                & (layer.depth == previous.depth)
            )
            if not same.any():
                continue
            conflict = (
                (layer.geom_id != previous.geom_id)
                | (layer.material_id != previous.material_id)
                | (layer.owner != previous.owner)
                | (layer.alpha_valid != previous.alpha_valid)
                | (layer.color_valid != previous.color_valid)
                | (layer.alpha_valid & (layer.alpha != previous.alpha))
                | (layer.color_valid & (layer.rgb != previous.rgb).any(axis=-1))
            )
            if np.any(same & conflict):
                raise ContractError("duplicate surface_id and depth have conflicting evidence")
            layer.geometry[same] = False
            removed[same] += 1
    return removed


def compose_surface_layers(
    opaque, transparent_layers: Sequence[Mapping], *, background_rgb_linear=None
):
    """Compose projected layers without inventing missing source evidence.

    ``opaque`` is a nearest-opaque mapping or None.  ``transparent_layers``
    contains any number of projected layers, each with HxW ``depth``,
    ``geometry_valid``, ``color_valid``, ``alpha_valid``, ``alpha``,
    ``rgb_linear`` (HxWx3), and ``geom_id``.  Masks, alpha and IDs may also be
    scalar; RGB may be a length-three vector.  ``material_id`` and
    ``semantic_owner`` may be absent/None/-1.  Opaque alpha defaults to known
    one; declaring uncertain or fractional opaque alpha is a contract error.

    Optional ``surface_id`` is a scalar string, nonnegative integer, or HxW
    integer array (-1 means unknown).  Only identical surface ID *and exact
    depth*, with consistent material/color/alpha/identity evidence, permit
    deduplication.  Equal-depth distinct candidates remain ambiguous.

    ``front_*`` describes the nearest potentially contributing surface;
    ``front_valid`` certifies a unique front surface with known positive
    alpha.  An unknown-alpha front is retained as a candidate, with validity
    false.  ``opaque_*`` describes the nearest known alpha-one surface,
    including an alpha-one layer supplied in ``transparent_layers``.

    ``alpha``/``coverage_alpha`` is total surface coverage, not front-layer
    alpha.  It is NaN when uncertain; ``coverage_min/max`` retain its bounds.
    Depth for an absent surface is +inf and absent IDs are -1.  Numeric
    outputs are linear RGB; sRGB encoding belongs to the exporter.

    With no layers, a spatial HxWx3 background is required to specify size.
    Display backgrounds never certify the missing scene behind a surface.
    Python loops are over layers, never over pixels.
    """
    records = list(transparent_layers)
    if opaque is not None:
        records.append(opaque)
    if records:
        if not isinstance(records[0], Mapping) or "depth" not in records[0]:
            raise ContractError("a surface layer requires a depth image")
        shape = np.asarray(records[0]["depth"]).shape
        if len(shape) != 2:
            raise ContractError("depth must be an HxW image")
    else:
        background_shape = np.asarray(background_rgb_linear).shape
        if len(background_shape) != 3 or background_shape[-1] != 3:
            raise ContractError("empty layers require an HxWx3 background to specify size")
        shape = background_shape[:2]
    background = None
    if background_rgb_linear is not None:
        background = _rgb(background_rgb_linear, shape, "background_rgb_linear")
        if not np.isfinite(background).all() or (background < 0).any():
            raise ContractError("display background must be finite nonnegative linear RGB")

    string_ids = {}
    layers = [
        _normalize(record, shape, string_ids,
                   opaque=opaque is not None and index == len(records) - 1)
        for index, record in enumerate(records)
    ]
    removed = _deduplicate(layers, shape)
    unknown = np.zeros(shape, dtype=np.uint8)
    color = np.zeros((*shape, 3), dtype=np.float64)
    transmission_max = np.ones(shape, dtype=np.float64)
    transmission_min = np.ones(shape, dtype=np.float64)
    visibility_open = np.ones(shape, dtype=bool)
    front_depth = np.full(shape, np.inf, dtype=np.float64)
    front_geom = np.full(shape, -1, dtype=np.int64)
    front_material = front_geom.copy()
    front_owner = front_geom.copy()
    front_alpha = np.full(shape, np.nan, dtype=np.float64)
    front_alpha_valid = np.zeros(shape, dtype=bool)
    front_valid = np.zeros(shape, dtype=bool)
    opaque_depth = front_depth.copy()
    opaque_geom = front_geom.copy()
    counts = np.zeros(shape, dtype=np.int32)

    if layers:
        # Alpha-zero with reliable evidence contributes neither color nor depth.
        candidates = np.stack([
            layer.geometry & (~layer.alpha_valid | (layer.alpha > 0))
            for layer in layers
        ])
        depths = np.where(candidates, np.stack([layer.depth for layer in layers]), np.inf)
        order = np.argsort(depths, axis=0, kind="stable")

        def sorted_field(name):
            values = np.stack([getattr(layer, name) for layer in layers])
            indices = order[..., None] if values.ndim == 4 else order
            return np.take_along_axis(values, indices, axis=0)

        sorted_depth = np.take_along_axis(depths, order, axis=0)
        rgb = sorted_field("rgb")
        alpha = sorted_field("alpha")
        alpha_valid = sorted_field("alpha_valid")
        color_valid = sorted_field("color_valid")
        geom_ids = sorted_field("geom_id")
        material_ids = sorted_field("material_id")
        owners = sorted_field("owner")
        front_exists = np.isfinite(sorted_depth[0])
        front_depth = sorted_depth[0].copy()
        front_geom = np.where(front_exists, geom_ids[0], -1)
        front_material = np.where(front_exists, material_ids[0], -1)
        front_owner = np.where(front_exists, owners[0], -1)
        front_alpha_valid = front_exists & alpha_valid[0]
        front_alpha = np.where(front_alpha_valid, alpha[0], np.nan)
        front_valid = front_alpha_valid.copy()
        if len(layers) > 1:
            front_valid &= sorted_depth[0] != sorted_depth[1]

        for index in range(len(layers)):
            # Visibility is a geometric/material fact. Floating-point
            # underflow of a long transmission product is not an opaque wall.
            active = np.isfinite(sorted_depth[index]) & visibility_open
            counts += active
            unknown_alpha = active & ~alpha_valid[index]
            unknown_color = active & ~color_valid[index]
            unknown[unknown_alpha] |= int(CompositeUnknown.ALPHA)
            unknown[unknown_color] |= int(CompositeUnknown.COLOR)
            if index + 1 < len(layers):
                tie = active & (sorted_depth[index] == sorted_depth[index + 1])
                unknown[tie] |= int(CompositeUnknown.DEPTH_TIE)

            known_opaque = (
                np.isfinite(sorted_depth[index]) & alpha_valid[index]
                & (alpha[index] == 1) & ~np.isfinite(opaque_depth)
            )
            opaque_depth[known_opaque] = sorted_depth[index][known_opaque]
            opaque_geom[known_opaque] = geom_ids[index][known_opaque]

            # Assuming alpha=0 for unknown alpha computes an upper bound on
            # remaining transmission, not a certified image. Such pixels are
            # marked unknown above and replaced with NaN in the final result.
            effective_alpha = np.where(active & alpha_valid[index], alpha[index], 0.0)
            safe_rgb = np.where(
                (active & color_valid[index])[..., None], rgb[index], 0.0
            )
            color += (transmission_max * effective_alpha)[..., None] * safe_rgb
            transmission_max *= 1.0 - effective_alpha
            transmission_min *= np.where(unknown_alpha, 0.0, 1.0 - effective_alpha)
            visibility_open &= ~(active & alpha_valid[index] & (alpha[index] == 1))

    geometry_valid = np.isfinite(front_depth)
    unknown[~geometry_valid] |= int(CompositeUnknown.NO_SURFACE)
    unknown[visibility_open] |= int(CompositeUnknown.BACKGROUND)
    valid = unknown == 0
    composite = np.where(valid[..., None], color, np.nan)
    display = composite.copy()
    if background is not None:
        display = color + transmission_max[..., None] * background
        uncertain_source = (unknown & int(
            CompositeUnknown.COLOR | CompositeUnknown.ALPHA | CompositeUnknown.DEPTH_TIE
        )) != 0
        # A placeholder is explicit and cannot be confused with sampled black.
        display = np.where(uncertain_source[..., None], background, display)
    coverage_min = 1.0 - transmission_max
    coverage_max = 1.0 - transmission_min
    coverage_valid = ((unknown & int(CompositeUnknown.ALPHA)) == 0) | ~visibility_open
    coverage = np.where(coverage_valid, coverage_min, np.nan)
    return {
        "composite_rgb_linear": composite,
        "composite_valid": valid,
        "display_rgb_linear": display,
        "geometry_valid": geometry_valid,
        "front_depth": front_depth,
        "front_geom_id": front_geom,
        "front_material_id": front_material,
        "front_owner": front_owner,
        "front_alpha": front_alpha,
        "front_alpha_valid": front_alpha_valid,
        "front_valid": front_valid,
        "opaque_depth": opaque_depth,
        "opaque_geom_id": opaque_geom,
        "alpha": coverage,
        "alpha_valid": coverage_valid,
        "coverage_alpha": coverage,
        "coverage_min": coverage_min,
        "coverage_max": coverage_max,
        "unknown_mask": unknown,
        "unknown_reason_bits": {reason.name: int(reason) for reason in CompositeUnknown},
        "contributing_layer_count": counts,
        "deduplicated_layer_count": removed,
    }
