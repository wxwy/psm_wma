"""Bounded vectorized transport verification for *simulation* Full Map source.

This checks EVERY 5cm transport row against the original MUJOCO source
precolored export, preserving the float32 round-trip used by nav_sg C++.
It does not make semantic ownership claims. Native C++ produced owner labels
with its original BVH/triangle-distance semantics; do not infer them from
visual Geom IDs.

This module is used only from the opt-in Full Map native-owner capture path.
No perception, real RGB-D, or regular Bundle verification calls it.
"""
from __future__ import annotations

from itertools import zip_longest
from pathlib import Path

import numpy as np

from g2.io import ContractError


SOURCE_COLUMNS = ("x", "y", "z", "red", "green", "blue", "color_valid")
NATIVE_COLUMNS = SOURCE_COLUMNS + ("entity_id",)
CHUNK_ROWS = 100_000


def verify_native_color_transport(source_cloud, native_surfaces, entities, count):
    """Verify exact source/native XYZ, RGB, valid flags and bounded owner IDs.

    Returns None if pandas is unavailable, so the caller can run its original
    Python row comparison. All other exceptions mean an invalid transport.
    """
    try:
        import pandas as pd
    except ImportError:
        return None
    if type(count) is not int or not 0 < count <= 5_000_000:
        raise ContractError("Full Map color source row budget invalid")
    if not isinstance(entities, set) or not entities or not all(
            isinstance(x, str) for x in entities):
        raise ContractError("Full Map entity identity set invalid")
    source_cloud, native_surfaces = Path(source_cloud), Path(native_surfaces)
    with native_surfaces.open("r", encoding="utf-8", newline="") as handle:
        if handle.readline().rstrip("\r\n") != ",".join(NATIVE_COLUMNS):
            raise ContractError("native surface header mismatch")
    dtype_native = dict(zip(SOURCE_COLUMNS[3:], ["int64"] * 4))
    dtype_native["entity_id"] = "category"
    dtype_source = dict(zip(SOURCE_COLUMNS[3:], ["int64"] * 4))
    scanned = 0
    try:
        src = pd.read_csv(
            source_cloud, sep=" ", skiprows=7, names=list(SOURCE_COLUMNS),
            header=None, skipinitialspace=True, index_col=False,
            chunksize=CHUNK_ROWS, dtype=dtype_source, na_filter=False,
            skip_blank_lines=False, float_precision="round_trip",
            engine="c", on_bad_lines="error",
        )
        dst = pd.read_csv(
            native_surfaces, chunksize=CHUNK_ROWS, dtype=dtype_native,
            index_col=False, na_filter=False, skip_blank_lines=False,
            float_precision="round_trip", engine="c", on_bad_lines="error",
        )
        for original, native in zip_longest(src, dst):
            if original is None or native is None or len(original) != len(native):
                raise ContractError("Full Map source/native surface count mismatch")
            if list(original.columns) != list(SOURCE_COLUMNS) or (
                    list(native.columns) != list(NATIVE_COLUMNS)):
                raise ContractError("Full Map transport column inventory mismatch")
            if not len(native) or scanned + len(native) > count:
                raise ContractError("Full Map point transport exceeds expected count")
            a = native[list(SOURCE_COLUMNS[:3])].to_numpy(dtype=np.float64)
            b = original[list(SOURCE_COLUMNS[:3])].to_numpy(
                dtype=np.float64).astype(np.float32).astype(np.float64)
            if (not np.isfinite(a).all() or not (np.abs(a) < 1e9).all()
                    or not np.allclose(a, b, rtol=1e-9, atol=1e-7)):
                raise ContractError("Full Map source/native surface XYZ differ")
            colors = native[list(SOURCE_COLUMNS[3:])].to_numpy(dtype=np.int64)
            origin_colors = original[list(SOURCE_COLUMNS[3:])].to_numpy(
                dtype=np.int64)
            if (not np.array_equal(colors, origin_colors) or
                    not np.all((colors[:, :3] >= 0) & (colors[:, :3] <= 255))
                    or not np.all((colors[:, 3] == 0) | (colors[:, 3] == 1))):
                raise ContractError("Full Map source/native RGB/validity differ")
            # Pandas' category codes are inferred per chunk. Validate the
            # category dictionary itself; no per-point Python string loop.
            known = set(native["entity_id"].cat.categories)
            if not known.issubset(entities | {"unknown"}):
                raise ContractError("Full Map source/native entity label differs")
            scanned += len(native)
        if scanned != count:
            raise ContractError("Full Map point transport row count differs")
    except (OSError, ValueError, TypeError, OverflowError, UnicodeError,
            pd.errors.ParserError) as exc:
        raise ContractError("invalid native source color transport") from exc
    return scanned
