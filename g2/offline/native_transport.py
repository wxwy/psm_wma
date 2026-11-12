"""Source-bound F24 native transports, independent of simulator and paths.

The wire layout is shared with nav_sg direct_layer_reader.h. Initial batches
contain every visual geom; updates replace only changed geoms. Native views
are read from the C++ worker's composed map, never from a Python fallback.
"""
import hashlib
import re
import struct
from pathlib import Path

import numpy as np

from g2.io import ContractError

LAYER_HEADER = struct.Struct("<8sIIQIIQ64s64s64s64s")
GEOM_HEADER = struct.Struct("<IiII")
VIEW_HEADER = struct.Struct("<8sIIQQ64s64s64s")
POINT = np.dtype([(k, "<i4") for k in ("ix", "iy", "iz")]
                 + [(k, "u1") for k in ("r", "g", "b", "valid")])
COLOR = np.dtype(POINT.descr + [("owner", "<i4")])
LEAF = .01
MAX_GEOMS = 10000
MAX_CELLS = 10000000


def sha_file(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            result.update(block)
    return result.hexdigest()


def require_sha(value):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ContractError("expected lower-case SHA256")
    return value


def _ordered(keys):
    if len(keys) < 2:
        return True
    a, b = keys[:-1], keys[1:]
    return bool(np.all((b[:, 0] > a[:, 0]) | ((b[:, 0] == a[:, 0]) &
        ((b[:, 1] > a[:, 1]) | ((b[:, 1] == a[:, 1]) & (b[:, 2] > a[:, 2]))))))


def geom_records(layer, max_cells=5000000):
    if layer is None:
        return np.empty(0, dtype=POINT)
    keys, rgb = layer
    if (not isinstance(keys, np.ndarray) or keys.dtype != np.int32
            or keys.ndim != 2 or keys.shape[1] != 3
            or not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8
            or rgb.shape != keys.shape or len(keys) > max_cells
            or not _ordered(keys)):
        raise ContractError("geom color cells must be bounded, unique, lexsorted int32/uint8 Nx3")
    records = np.empty(len(keys), dtype=POINT)
    for i, key in enumerate(("ix", "iy", "iz")):
        records[key] = keys[:, i]
    for i, key in enumerate(("r", "g", "b")):
        records[key] = rgb[:, i]
    records["valid"] = 1
    return records


def composed_records(surface):
    xyz, rgb, valid, owners, _ = surface
    xyz = np.asarray(xyz)
    if (xyz.ndim != 2 or xyz.shape[1] != 3 or len(xyz) > MAX_CELLS
            or not np.isfinite(xyz).all()):
        raise ContractError("invalid composed surface points")
    floating = xyz / LEAF - .5
    rounded = np.rint(floating)
    if (not np.allclose(floating, rounded, rtol=0, atol=1e-6)
            or np.any(rounded < np.iinfo(np.int32).min)
            or np.any(rounded > np.iinfo(np.int32).max)):
        raise ContractError("composed points must be 10mm cell centers")
    keys = rounded.astype(np.int32)
    records = geom_records((keys, rgb), max_cells=MAX_CELLS)
    valid, owners = np.asarray(valid), np.asarray(owners)
    if (valid.shape != (len(keys),) or not np.all(valid == 1)
            or owners.shape != (len(keys),) or owners.dtype.kind not in "iu"
            or np.any(owners < -1) or np.any(owners > np.iinfo(np.int32).max)):
        raise ContractError("invalid composed color validity/ownership")
    result = np.empty(len(keys), dtype=COLOR)
    for name in POINT.names:
        result[name] = records[name]
    result["owner"] = owners
    return result


def composed_digest(surface):
    records = composed_records(surface)
    return (hashlib.sha256(records.tobytes()).hexdigest(), len(records),
            int(np.count_nonzero(records["owner"] == -1)))


def write_layer_batch(path, *, frame, scene_id, source_sha, state_sha,
                      expected_sha, specs, changed, static_ids, layers):
    """Write exactly the F24 layout; all validation precedes file creation."""
    if type(frame) is not int or frame < 0 or frame >= 2**64:
        raise ContractError("invalid frame")
    if not isinstance(scene_id, str) or not scene_id or len(scene_id) > 1024:
        raise ContractError("invalid source scene id")
    for value in (source_sha, state_sha, expected_sha):
        require_sha(value)
    if not 1 <= len(specs) <= MAX_GEOMS:
        raise ContractError("invalid visual geom inventory")
    ids = [s["g"] for s in specs]
    updates = [s["g"] for s in changed]
    if len(set(ids)) != len(ids) or len(set(updates)) != len(updates):
        raise ContractError("duplicate geom id")
    if not set(updates) <= set(ids) or not set(static_ids) <= set(ids):
        raise ContractError("unknown geom id")
    if frame == 0 and set(updates) != set(ids):
        raise ContractError("initial batch must contain every geom")
    if frame > 0 and set(updates) & set(static_ids):
        raise ContractError("dynamic batch modifies static geom")
    inventory = {s["g"]: s for s in specs}
    chunks = []
    count = 0
    for spec in sorted(changed, key=lambda s: s["g"]):
        geom, owner = spec["g"], spec["owner"]
        if (type(geom) is not int or not 0 <= geom <= 1000000
                or type(owner) is not int or not -1 <= owner <= 2147483647
                or inventory[geom]["owner"] != owner or geom not in layers):
            raise ContractError("invalid geom ownership/inventory")
        records = geom_records(layers[geom])
        count += len(records)
        if count > MAX_CELLS:
            raise ContractError("batch exceeds native cell limit")
        chunks.append((GEOM_HEADER.pack(geom, owner, int(geom in static_ids), len(records)), records))
    header = LAYER_HEADER.pack(b"G2DLAY1!", 1, 10, frame, int(frame == 0),
        len(specs), len(changed), hashlib.sha256(scene_id.encode()).hexdigest().encode(),
        source_sha.encode(), state_sha.encode(), expected_sha.encode())
    with Path(path).open("xb") as stream:
        stream.write(header)
        for geom_header, records in chunks:
            stream.write(geom_header)
            records.tofile(stream)
    return {"data_file": str(Path(path).resolve()), "binary_sha256": sha_file(path),
            "batch_direct_records": count, "changed_geoms": len(changed)}


def write_sequence(path, color, nav):
    """Bind both independently generated maps to the same source state."""
    if (color["source_sha256"] != nav["source_scene_sha256"]
            or nav.get("source_known_region_NOT_CERTIFIED") is not True
            or nav.get("training_ready") is not False):
        raise ContractError("native navigation provenance mismatch")
    rows, nav_rows = color["states"], nav["frames"]
    frames = [r["frame"] for r in rows]
    if (not 2 <= len(frames) <= 300 or frames[0] != 0 or frames != sorted(set(frames))
            or frames != [r["frame"] for r in nav_rows]):
        raise ContractError("color/nav frame coverage differs")
    layout = color["layout"]
    if type(layout) is not int or not 1 <= layout <= 10:
        raise ContractError("native adapter supports RoboCasa layouts 1..10")
    scene = rows[0]["source_scene_id"]
    if any(c.isspace() for c in scene):
        raise ContractError("native scene identifiers cannot contain whitespace")
    lines = ["F24_G2_NATIVE_COLOR_AND_NAV_SEQUENCE_V1", f"layout {layout}",
             f"scene {scene}", f"source {require_sha(color['source_sha256'])}",
             "known_free_region_TEST_ONLY 1", f"rows {len(rows)}"]
    for row, source in zip(rows, nav_rows):
        count, unknown = row["expected_full_color_voxels"], row["expected_unknown_owner_cells"]
        if (type(count) is not int or not 1 <= count <= 8000000
                or type(unknown) is not int or not 0 <= unknown <= count):
            raise ContractError("composed color counts exceed the native episode adapter contract")
        if (row["source_scene_id"] != scene or row["source_sha256"] != color["source_sha256"]
                or row["source_state_sha256"] != source["source_state_row_sha256"]
                or row["initial_all_static_and_dynamic"] != (row["frame"] == 0)):
            raise ContractError("color/nav scene or state row mismatch")
        for p, s in ((row["data_file"], row["binary_sha256"]),
                     (source["source_grid_file"], source["source_grid_sha256"]),
                     (source["source_objects_file"], source["source_objects_sha256"])):
            if sha_file(p) != require_sha(s):
                raise ContractError("native sequence input bytes changed")
        values = [row["frame"], source["source_grid_file"], source["source_objects_file"],
                  source["source_grid_sha256"], source["source_objects_sha256"],
                  row["data_file"], row["binary_sha256"], row["source_state_sha256"],
                  row["expected_full_color_sha256"], row["expected_full_color_voxels"],
                  row["expected_unknown_owner_cells"]]
        if any(any(c.isspace() for c in str(v)) for v in values):
            raise ContractError("native transport paths cannot contain whitespace")
        lines.append(" ".join(map(str, values)))
    text = "\n".join(lines) + "\n"
    if len(text.encode()) > 131072:
        raise ContractError("native episode sequence exceeds 128 KiB")
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(text)
    return sha_file(path)


def read_native_surface(path, expected, snapshot):
    """Verify the C++ composed map before giving it to the renderer."""
    path = Path(path)
    with path.open("rb") as stream:
        header = stream.read(VIEW_HEADER.size)
        if len(header) != VIEW_HEADER.size:
            raise ContractError("truncated native color header")
        magic, version, leaf, frame, count, scene_sha, source, state = VIEW_HEADER.unpack(header)
        if (magic != b"G2COL10!" or version != 1 or leaf != 10
                or frame != expected["frame"] or frame != snapshot["frame_id"]
                or count != expected["expected_full_color_voxels"] or count > MAX_CELLS
                or scene_sha != hashlib.sha256(snapshot["scene_id"].encode()).hexdigest().encode()
                or source != require_sha(snapshot["source_sha256"]).encode()
                or state != require_sha(expected["source_state_sha256"]).encode()
                or expected["source_scene_id"] != snapshot["scene_id"]
                or expected["source_sha256"] != snapshot["source_sha256"]
                or path.stat().st_size != VIEW_HEADER.size + COLOR.itemsize * count):
            raise ContractError("native color source/header mismatch")
        records = np.fromfile(stream, dtype=COLOR, count=count)
        if len(records) != count or stream.read(1):
            raise ContractError("native color payload size mismatch")
    if hashlib.sha256(records.tobytes()).hexdigest() != require_sha(expected["expected_full_color_sha256"]):
        raise ContractError("native composed color SHA mismatch")
    keys = np.column_stack([records[k] for k in ("ix", "iy", "iz")])
    owners = records["owner"].copy()
    if (not _ordered(keys) or not np.all(records["valid"] == 1)
            or np.any(owners < -1) or np.any(owners >= len(snapshot["entities"]))
            or np.count_nonzero(owners == -1) != expected["expected_unknown_owner_cells"]):
        raise ContractError("native color cells/order/ownership invalid")
    evidence = dict(scene_id=snapshot["scene_id"], source_sha256=snapshot["source_sha256"],
        frame_id=snapshot["frame_id"], world_frame=snapshot["world_frame"],
        entity_index_to_native_id=sorted(e["id"] for e in snapshot["entities"]),
        voxel_leaf_m=LEAF, dense_sample_spacing_m=LEAF, dense_small_sample_spacing_m=LEAF,
        dense_source_points=int(count), dense_valid_color_points=int(count),
        unassigned_source_instance_points=int(np.count_nonzero(owners == -1)),
        source_mode="NATIVE_LONG_LIVED_DIRECT_COLOR_WORKER_10MM_FULL_SOURCE")
    return ((keys.astype(np.float64) + .5) * LEAF,
            np.column_stack([records[k] for k in ("r", "g", "b")]),
            np.ones(count, bool), owners, evidence)
