"""JSON-only identity and path contract for independent spatial View caches."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

from g2.io import ContractError, canonical

INDEX_SCHEMA = "g2_spatial_view_vae_index_v1"
PAYLOAD_SCHEMA = "g2_spatial_view_vae_payload_v1"
COMPLETE_SCHEMA = "g2_spatial_view_vae_complete_v1"
RECIPE_SCHEMA = "g2_spatial_view_vae_recipe_v1"
STORAGE_DTYPES = ("float32", "float16", "bfloat16")


class CacheError(ContractError):
    """Invalid, incomplete, conflicting or changed spatial-cache evidence."""


def fingerprint(value):
    """Content identity, independent of instruction, scheduling and paths."""
    return hashlib.sha256(canonical(value)).hexdigest()


def safe_relative(text, suffix=None):
    if (
        not isinstance(text, str)
        or not text
        or "\\" in text
        or any(ord(c) < 32 or ord(c) == 127 for c in text)
    ):
        raise CacheError("invalid relative cache path")
    path = PurePosixPath(text)
    if (
        not path.parts
        or path.is_absolute()
        or str(path) != text
        or any(part in (".", "..") for part in path.parts)
    ):
        raise CacheError("cache path must be canonical, relative and contained")
    if suffix is not None and path.suffix != suffix:
        raise CacheError("unexpected cache path suffix")
    return path


def contained(root, relative, allow_missing=False):
    """Do not silently follow a symlink anywhere inside a cache namespace."""
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise CacheError("cache root must be an existing real directory")
    rel = safe_relative(str(relative))
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise CacheError("symbolic links are forbidden in cache paths")
        if not allow_missing and not current.exists():
            raise CacheError("cache path is missing: " + str(rel))
    if root.resolve(strict=True) not in current.resolve(strict=False).parents:
        raise CacheError("cache path escapes its root")
    return current


def preprocessing_recipe(height=256, width=256, interpolation="lanczos"):
    result = dict(
        height=height,
        width=width,
        interpolation=interpolation,
        padding_rgb=[255, 255, 255],
        aspect="fit",
        rounding="floor_half_up",
        layout="RGB_HWC",
    )
    validate_preprocessing(result)
    return result


def validate_preprocessing(value):
    if not isinstance(value, dict) or set(value) != {
        "height",
        "width",
        "interpolation",
        "padding_rgb",
        "aspect",
        "rounding",
        "layout",
    }:
        raise CacheError("unknown or missing preprocessing recipe field")
    if any(type(value[k]) is not int or value[k] <= 0 for k in ("height", "width")):
        raise CacheError("canvas height and width must be positive integers")
    if (
        value["interpolation"] not in ("lanczos", "bilinear", "nearest")
        or value["padding_rgb"] != [255, 255, 255]
        or value["aspect"] != "fit"
        or value["rounding"] != "floor_half_up"
        or value["layout"] != "RGB_HWC"
    ):
        raise CacheError("unsupported spatial image preprocessing")
    return value


def make_recipe(encoder, preprocessing=None, *, storage_dtype="float32", batch_size=1):
    """The initial candidate intentionally supports independent B=1 only.

    Lower precision is an explicit candidate storage conversion, not a claim
    of lossless quantization or an accepted production recipe.
    """
    if type(batch_size) is not int or batch_size != 1:
        raise CacheError("only B=1 is supported; real mixed-batch parity is NOT_RUN")
    if not isinstance(encoder, dict) or not encoder:
        raise CacheError("encoder computational identity is required")
    if storage_dtype not in STORAGE_DTYPES:
        raise CacheError("unsupported storage dtype")
    preprocessing = preprocessing_recipe() if preprocessing is None else preprocessing
    validate_preprocessing(preprocessing)
    value = dict(
        schema=RECIPE_SCHEMA,
        encoder=encoder,
        preprocessing=preprocessing,
        storage_dtype=storage_dtype,
        batch_size=1,
        independent_frames=True,
        input_layout="BCTHW",
        input_shape=[1, 3, 1, preprocessing["height"], preprocessing["width"]],
        record_layout="CHW",
        view_layout="UCHW",
    )
    # Canonical round-trip rejects non-JSON dependency identities and detaches
    # the caller's mutable dictionaries before a recipe_id is published.
    import json

    value = json.loads(canonical(value))
    value["recipe_id"] = fingerprint(value)
    return value


def validate_recipe(value):
    if not isinstance(value, dict) or value.get("schema") != RECIPE_SCHEMA:
        raise CacheError("unknown spatial VAE recipe")
    try:
        rebuilt = make_recipe(
            value["encoder"],
            value["preprocessing"],
            storage_dtype=value["storage_dtype"],
            batch_size=value["batch_size"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise CacheError("invalid spatial VAE recipe") from error
    if value != rebuilt:
        raise CacheError("spatial VAE recipe identity mismatch")
    return value
