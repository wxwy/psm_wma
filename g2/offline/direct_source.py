"""Source-bound direct 10 mm MuJoCo visual surface construction.

The surface builder and dynamic classification preserve the validated F21/F22
algorithms. All episode inputs are explicit hashed references.
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import numpy as np

from g2.io import ContractError, canonical, digest, parse_json, sha

LEAF = 0.01
INPUT_SCHEMA = "g2_direct_color_episode_inputs_v1"
_JSON_LIMIT = 128 * 1024 * 1024


def _reference_path(reference, label):
    if not isinstance(reference, dict):
        raise ContractError(label + " must be an explicit path/sha256 reference")
    raw = reference.get("path")
    if not isinstance(raw, str) or not raw or any(ord(c) < 32 for c in raw):
        raise ContractError(label + " path must be nonempty text without controls")
    path = Path(raw)
    if not path.is_absolute():
        raise ContractError(label + " path must be absolute")
    sha(reference.get("sha256"), label + ".sha256")
    try:
        path = path.resolve(strict=True)
    except OSError as exc:
        raise ContractError(label + " file is unavailable") from exc
    if not path.is_file():
        raise ContractError(label + " must reference a regular file")
    return path


def _read_json_reference(reference, label):
    path = _reference_path(reference, label)
    if path.stat().st_size > _JSON_LIMIT:
        raise ContractError(label + " JSON exceeds byte limit")
    payload = path.read_bytes()
    if len(payload) > _JSON_LIMIT:
        raise ContractError(label + " JSON exceeds byte limit")
    if hashlib.sha256(payload).hexdigest() != reference["sha256"]:
        raise ContractError(label + " SHA256 mismatch")
    if "bytes" in reference and reference["bytes"] != len(payload):
        raise ContractError(label + " byte count mismatch")
    result = parse_json(payload.decode("utf-8"))
    if not isinstance(result, dict):
        raise ContractError(label + " JSON must contain an object")
    return result


def _nonempty_text(value, label):
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise ContractError(label + " must be nonempty text without controls")
    return value


def _source_records(gt):
    from g2.sim.source_geometry import model_source_hash

    records = gt.get("sources")
    if not isinstance(records, list) or not records:
        raise ContractError("source manifest needs the complete model closure")
    logical_ids = []
    for record in records:
        if not isinstance(record, dict):
            raise ContractError("model closure record must be an object")
        logical_ids.append(_nonempty_text(record.get("logical_id"), "logical_id"))
        _nonempty_text(record.get("path"), "source path")
        if not Path(record["path"]).is_absolute():
            raise ContractError("model closure source paths must be absolute")
        sha(record.get("sha256"), "source file SHA256")
        if type(record.get("bytes")) is not int or record["bytes"] < 0:
            raise ContractError("model closure source byte count is invalid")
    if len(set(logical_ids)) != len(logical_ids) or logical_ids.count("root.xml") != 1:
        raise ContractError("model closure requires unique logical IDs and one root.xml")
    expected = sha(gt["source_identity"].get("model_source_sha256"), "model source SHA256")
    if model_source_hash(records) != expected:
        raise ContractError("embedded model closure SHA256 mismatch")
    return records


def verify_input_config(config):
    """Verify JSON references and snapshots without compiling MuJoCo.

    Returns source_manifest, visual_inventory, role_map, snapshots.
    Snapshots retain the strictly increasing config states order.
    A visual inventory from another frame of the same model is allowed: it
    supplies the selected geom roster, never current world poses.
    """
    if not isinstance(config, dict) or config.get("schema") != INPUT_SCHEMA:
        raise ContractError("explicit " + INPUT_SCHEMA + " input config required")
    gt = _read_json_reference(config.get("source_manifest"), "source_manifest")
    dense = _read_json_reference(config.get("visual_inventory"), "visual_inventory")
    role = _read_json_reference(config.get("role_map"), "role_map")
    identity = gt.get("source_identity")
    if not isinstance(identity, dict) or identity.get("schema") != "nav_sg_mujoco_oracle_v1":
        raise ContractError("source manifest requires the original MuJoCo oracle identity")
    source_hash = sha(gt.get("source_sha256"), "source SHA256")
    if hashlib.sha256(canonical(identity)).hexdigest() != source_hash:
        raise ContractError("source identity SHA256 mismatch")
    scene_id = _nonempty_text(gt.get("scene_id"), "scene_id")
    _source_records(gt)
    state = gt.get("state")
    if (not isinstance(state, dict) or state.get("format") != "mujoco_fullphysics"
            or type(state.get("frame_id")) is not int or state["frame_id"] != 0):
        raise ContractError("source manifest must bind fullphysics frame zero")
    if "frame_id" in gt and gt["frame_id"] != 0:
        raise ContractError("source manifest top-level frame differs")
    _nonempty_text(state.get("path"), "state archive path")
    if not Path(state["path"]).is_absolute():
        raise ContractError("state archive path must be absolute")
    sha(state.get("file_sha256"), "state archive SHA256")
    sha(state.get("row_sha256"), "initial state row SHA256")
    _nonempty_text(identity.get("mujoco_version"), "mujoco_version")
    if (dense.get("source_sha256") != source_hash
            or dense.get("model_source_sha256") != identity["model_source_sha256"]):
        raise ContractError("visual inventory source/model binding differs")
    if "scene_id" in dense and dense["scene_id"] != scene_id:
        raise ContractError("visual inventory scene differs")
    if not isinstance(dense.get("sampled_geoms"), list) or not dense["sampled_geoms"]:
        raise ContractError("visual inventory must explicitly list sampled geoms")
    if not isinstance(role.get("geoms"), dict) or not role["geoms"]:
        raise ContractError("role map must explicitly classify geoms")
    # Exact config SHA binds legacy role files. Optional provenance is checked
    # when present; no unknown legacy metadata field is made mandatory.
    if "scene_id" in role and role["scene_id"] != scene_id:
        raise ContractError("role map scene differs")
    role_state = role.get("state_source")
    if role_state is not None and role_state != {
        "model_source_sha256": identity["model_source_sha256"],
        "states_sha256": state["file_sha256"],
    }:
        raise ContractError("role map model/state binding differs")
    configured = config.get("states")
    if not isinstance(configured, list) or not configured:
        raise ContractError("states must be a nonempty explicit snapshot sequence")
    frames = []
    for item in configured:
        frame = item.get("frame") if isinstance(item, dict) else None
        if type(frame) is not int or frame < 0:
            raise ContractError("state frame must be a nonnegative integer")
        frames.append(frame)
    if frames[0] != 0 or any(a >= b for a, b in zip(frames, frames[1:])):
        raise ContractError("state frames must be strictly increasing and start at zero")

    from g2.nav_bridge.connections import verify_connection_evidence

    snapshots = []
    world_frame = None
    entity_ids = None
    for item in configured:
        snap = _read_json_reference(item.get("snapshot"), "snapshot")
        if (type(snap.get("frame_id")) is not int or snap["frame_id"] != item["frame"]
                or snap.get("scene_id") != scene_id
                or snap.get("source_sha256") != source_hash):
            raise ContractError("snapshot scene/source/frame binding differs")
        current_world = _nonempty_text(snap.get("world_frame"), "snapshot world_frame")
        if world_frame is None:
            world_frame = current_world
        if current_world != world_frame:
            raise ContractError("snapshot world frame changed within the episode")
        entities, rooms = snap.get("entities"), snap.get("rooms")
        if not isinstance(entities, list) or not entities or not isinstance(rooms, list) or not rooms:
            raise ContractError("snapshot requires explicit native entities and rooms")
        ids = [_nonempty_text(e.get("id"), "native entity ID") for e in entities if isinstance(e, dict)]
        if len(ids) != len(entities) or len(ids) != len(set(ids)):
            raise ContractError("native entity IDs must be unique")
        if entity_ids is None:
            entity_ids = sorted(ids)
        if sorted(ids) != entity_ids:
            raise ContractError("native entity index roster changed within the episode")
        verify_connection_evidence(snap)
        snapshots.append(snap)
    return gt, dense, role, snapshots


def _hash_stream(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(block)
    return result.hexdigest()


def load_source(input_config):
    """Return model, initial_snapshot, dense_inventory, role_map, state_array."""
    import mujoco

    from g2.sim.source_geometry import load_model, model_source_hash

    gt, dense, role, snapshots = verify_input_config(input_config)
    identity = gt["source_identity"]
    if identity["mujoco_version"] != mujoco.__version__:
        raise ContractError("actual MuJoCo compiler version differs from source")
    records = _source_records(gt)
    for record in records:
        path = _reference_path(record, "model source")
        if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
            raise ContractError("model source file hash/size changed")
    original_root = next(record["path"] for record in records if record["logical_id"] == "root.xml")
    roots = sorted({str(Path(record["path"]).parent) for record in records})
    model, actual_sources = load_model(original_root, roots)
    if model_source_hash(actual_sources) != identity["model_source_sha256"]:
        raise ContractError("actual compiled model closure differs")
    state = gt["state"]
    state_path = _reference_path(
        {"path": state["path"], "sha256": state["file_sha256"]}, "state archive"
    )
    # Hash the same open file that NumPy reads, then recheck after loading.
    with state_path.open("rb") as stream:
        before = _hash_stream(stream)
        if before != state["file_sha256"]:
            raise ContractError("state archive SHA256 mismatch")
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as archive:
            if "states" not in archive:
                raise ContractError("fullphysics archive is missing states")
            recorded = archive["states"].copy()
        stream.seek(0)
        if _hash_stream(stream) != before:
            raise ContractError("state archive changed while loading")
    expected = mujoco.mj_stateSize(model, mujoco.mjtState.mjSTATE_FULLPHYSICS)
    if (recorded.ndim != 2 or recorded.shape[1] != expected
            or recorded.dtype.kind != "f" or not np.isfinite(recorded).all()):
        raise ContractError("fullphysics state shape/dtype/nonfinite mismatch")
    if input_config["states"][-1]["frame"] >= len(recorded):
        raise ContractError("snapshot frame exceeds the fullphysics archive")
    initial_row = np.asarray(recorded[0], dtype="<f8")
    if hashlib.sha256(initial_row.tobytes()).hexdigest() != state["row_sha256"]:
        raise ContractError("initial fullphysics row SHA256 mismatch")
    metadata = identity.get("metadata")
    metadata_state = metadata.get("state_source") if isinstance(metadata, dict) else None
    if metadata_state is not None and metadata_state != {
        "model_source_sha256": identity["model_source_sha256"],
        "states_sha256": state["file_sha256"],
    }:
        raise ContractError("source identity model/state archive binding differs")
    return model, snapshots[0], dense, role, recorded


def prepare_visual_specs(model, snap, dense, role):
    """Preserve the original visual geom roster and native owner index mapping."""
    import mujoco

    from g2.sim.prescan import geom_surface_mesh, geometry_type_names

    instance_index = {e["source_instance_id"]: e["id"] for e in snap["entities"]}
    numeric = {name: i for i, name in enumerate(sorted(e["id"] for e in snap["entities"]))}
    types = geometry_type_names()
    specs = []
    seen = set()
    for visual in dense["sampled_geoms"]:
        g = visual.get("geom_id")
        if type(g) is not int or g < 0 or g >= model.ngeom or g in seen:
            raise ContractError("visual geom ID is invalid or duplicated")
        seen.add(g)
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g)
        if not name or visual.get("geom_name") != name:
            raise ContractError("visual geom name differs from compiled source")
        original_role = role["geoms"].get(name, {}).get("role")
        if original_role != "visual":
            raise ContractError("selected geom is not an explicitly classified visual")
        kind = types[int(model.geom_type[g])]
        source_instance = visual.get("source_instance")
        if not isinstance(source_instance, (list, tuple)) or len(source_instance) < 2:
            raise ContractError("visual geom needs its original source_instance binding")
        group = source_instance[1]
        if group is not None and not isinstance(group, str):
            raise ContractError("visual source instance group must be text or null")
        possibilities = [key for key in instance_index if group and key.endswith(":" + group)]
        if len(possibilities) > 1:
            raise ContractError("ambiguous native source identity " + repr((name, group, possibilities)))
        owner = numeric[instance_index[possibilities[0]]] if possibilities else -1
        structure = group if isinstance(group, str) and group.startswith(("floor_", "wall_", "ceiling_")) else None
        if structure is None and name.startswith(("floor_", "wall_", "ceiling_")):
            structure = name.split("_g")[0]
        mesh_vertices, mesh_faces = geom_surface_mesh(model, g, kind)
        specs.append(dict(
            g=g, name=name, kind=kind, instance=group, owner=owner,
            role=original_role, structure=structure,
            source_kind=source_instance[0], source_instance=list(source_instance),
            source_category=role["geoms"].get(name, {}).get("source_category"),
            vertices=mesh_vertices, faces=mesh_faces,
            original_dense_samples=int(visual["points"]),
            original_valid_samples=int(visual["valid_color_points"]),
        ))
    return specs


def build_one(model, data, info, room_center):
    """Rasterize one geom with the original UV and mean-color arithmetic."""
    from g2.offline.fast_surface_cells import raster_world_triangles
    from g2.sim.dense_visual_cloud import select_room_interior_shell_faces
    from g2.sim.prescan import analytic_surface
    from g2.sim.source_geometry import surface_colors

    start = time.perf_counter()
    g = info["g"]
    vertices, faces, kind = info["vertices"], info["faces"], info["kind"]
    rotation = np.asarray(data.geom_xmat[g]).reshape(3, 3)
    position = np.asarray(data.geom_xpos[g])
    if info["structure"]:
        selection, policy = select_room_interior_shell_faces(
            vertices, faces, kind, info["structure"], position, rotation, room_center
        )
        if selection is None:
            raise ContractError("structural visual face selection is unavailable")
        keep = np.asarray(selection, bool)
        if not keep.any():
            if policy != "EXCLUDED_DUPLICATE_BACKING_SKIN":
                raise ContractError("empty structural face selection lacks backing-skin evidence")
            return None, dict(
                source_geom=info["name"], policy=policy, skipped_backing=True,
                generated_voxels=0, elapsed_s=round(time.perf_counter() - start, 6),
            )
    else:
        keep = np.ones(len(faces), bool)
        policy = "ALL_VISUAL_OBJECT_SURFACES"
    triangles = np.ascontiguousarray(vertices[faces], dtype=np.float64)
    world_triangles = triangles @ rotation.T + position
    face_indices, weights = raster_world_triangles(world_triangles, keep, LEAF, max_points=12_000_000)
    if not len(face_indices):
        return None, dict(
            source_geom=info["name"], policy=policy, empty_raster=True,
            generated_voxels=0, elapsed_s=round(time.perf_counter() - start, 6),
        )
    entries, colors = [], []
    raw_valid = 0
    for offset in range(0, len(face_indices), 200_000):
        face_ids = face_indices[offset:offset + 200_000]
        barycentric = weights[offset:offset + 200_000]
        local_triangles = triangles[face_ids]
        points = np.einsum("bi,bij->bj", barycentric, local_triangles)
        if kind != "mesh":
            points = analytic_surface(points, kind, model.geom_size[g], face_ids)
        rgba, valid, _, _ = surface_colors(
            model, g, kind, face_ids, barycentric,
            local_points=points, with_diagnostics=True,
        )
        rgba = np.rint(np.clip(rgba, 0, 1) * 255).astype(np.uint8)
        selected = np.asarray(valid, bool) & (rgba[:, 3] == 255)
        raw_valid += int(selected.sum())
        if not np.any(selected):
            continue
        world = points[selected] @ rotation.T + position
        entries.append(np.floor(world / LEAF).astype(np.int32))
        colors.append(rgba[selected, :3])
    if not entries:
        return None, dict(
            source_geom=info["name"], policy=policy, invalid_color=True,
            raw_face_candidates=len(face_indices), generated_voxels=0,
            elapsed_s=round(time.perf_counter() - start, 6),
        )
    keys, rgb = np.concatenate(entries), np.concatenate(colors)
    unique, inverse = np.unique(keys, axis=0, return_inverse=True)
    counts = np.bincount(inverse, minlength=len(unique))
    sums = np.column_stack([
        np.bincount(inverse, weights=rgb[:, channel], minlength=len(unique))
        for channel in range(3)
    ])
    rgb = np.rint(sums / counts[:, None]).astype(np.uint8)
    unique.flags.writeable = False
    rgb.flags.writeable = False
    return (unique, rgb), dict(
        source_geom=info["name"], g=g, source_owner=info["owner"], policy=policy,
        triangles_total=len(faces), selected_faces=int(keep.sum()),
        raw_face_candidates=len(face_indices), valid_color_samples=raw_valid,
        generated_voxels=len(unique),
        original_f14_dense_samples=info["original_dense_samples"],
        elapsed_s=round(time.perf_counter() - start, 5),
    )


def get_data(model, row):
    """Restore one exact FULLPHYSICS state; no simulator rollout is performed."""
    import mujoco

    row = np.asarray(row)
    expected = mujoco.mj_stateSize(model, mujoco.mjtState.mjSTATE_FULLPHYSICS)
    if row.shape != (expected,) or row.dtype.kind != "f" or not np.isfinite(row).all():
        raise ContractError("invalid fullphysics state row")
    data = mujoco.MjData(model)
    mujoco.mj_setState(model, data, row, mujoco.mjtState.mjSTATE_FULLPHYSICS)
    mujoco.mj_forward(model, data)
    return data


def identify_dynamic_geoms(model, states, frames, specs):
    """Preclassify the fixed episode with the original 1e-10 pose threshold."""
    started = time.perf_counter()
    frames = list(frames)
    if (not frames or any(type(frame) is not int or frame < 0 or frame >= len(states) for frame in frames)
            or any(a >= b for a, b in zip(frames, frames[1:]))):
        raise ContractError("dynamic classification requires ordered valid frame indices")
    model_geoms = np.array([spec["g"] for spec in specs], dtype=np.int32)
    if not len(model_geoms) or len(np.unique(model_geoms)) != len(model_geoms):
        raise ContractError("dynamic classification requires unique selected geoms")
    initial = get_data(model, states[frames[0]])
    first_position = np.asarray(initial.geom_xpos)[model_geoms].copy()
    first_rotation = np.asarray(initial.geom_xmat)[model_geoms].copy()
    dynamic = np.zeros(len(specs), bool)
    for frame in frames[1:]:
        current = get_data(model, states[frame])
        position = np.asarray(current.geom_xpos)[model_geoms]
        rotation = np.asarray(current.geom_xmat)[model_geoms]
        dynamic |= (
            (np.max(np.abs(position - first_position), axis=1) > 1e-10)
            | (np.max(np.abs(rotation - first_rotation), axis=1) > 1e-10)
        )
    moving = set(model_geoms[dynamic].tolist())
    stationary = set(model_geoms[~dynamic].tolist())
    return moving, stationary, round(time.perf_counter() - started, 6)


def certified_opaque_color_owner_indices(model, specs, snapshot):
    """Only completely opaque source GT objects with some verified native RGB.

    The caller must use load_source() / prepare_visual_specs() on the
    same complete checked model closure and scene manifest.
    A translucent geom anywhere in the same native entity excludes it;
    this prevents filling transparent glass from adjacent opaque surfaces.
    """
    from g2.sim.source_geometry import effective_rgba
    import math

    native_ids = sorted(e["id"] for e in snapshot["entities"])
    objects = {i for i, eid in enumerate(native_ids)
               if next(e for e in snapshot["entities"] if e["id"] == eid)["kind"] == "object"}
    material = {}
    for spec in specs:
        idx = spec["owner"]
        if idx < 0 or idx not in objects:
            continue
        opacity = float(effective_rgba(model, spec["g"])[3])
        if not math.isfinite(opacity) or not 0 <= opacity <= 1:
            raise ContractError("nonfinite or invalid compiled source alpha")
        material.setdefault(idx, []).append((opacity, spec["original_valid_samples"]))
    return sorted(idx for idx, rows in material.items()
                  if rows and all(alpha >= 1 - 1.e-7 for alpha, _ in rows)
                  and any(count > 0 for _, count in rows))
