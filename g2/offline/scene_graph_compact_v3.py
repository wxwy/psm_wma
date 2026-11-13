"""Opt-in G2 v3 compact SG keyframe/delta and PNG ref packaging.

v1/v2 and active production stay immutable. Frame identity is stored inline;
unchanged SG bodies and views reference physical earlier artifacts without a
frame directory. Changed numeric bodies use exact deltas to physical keyframes.
All references are direct; legacy v3 metadata-in-delta packages remain readable.
"""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

from g2.offline.atomic_6views_compact import PackageError
from g2.offline.scene_view_event_index import resolve_indexed_png
from g2.offline.scene_view_index_package import validate_indexed_episode

SCHEMA = "g2_atomic_compact_6views_v3"
PATCH_SCHEMA = "g2_scene_graph_delta_v1"
DIFF_NUMERIC_FIELDS = {"distances_m", "direct_bbox_gap_m", "distance_m"}
DIFF_ENTITY_FIELDS = {"bbox_min", "bbox_max", "centroid"}
FRAME_ID_FIELDS = {"frame_id", "timestamp_ns", "original_state_row_sha256"}
SG_PHYSICAL = "scene_graph.json.gz"
SG_DELTA = "scene_graph_delta.json.gz"
LEGACY_METADATA_POLICY = "EXACT_DELTA_TO_PHYSICAL_SG_KEYFRAME"
INLINE_METADATA_POLICY = "INLINE_FRAME_METADATA_WITH_DIRECT_SG_BODY_REFS_V1"


def _canonical(value):
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _sha_graph(graph):
    return _sha_bytes(_canonical(graph))


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path, data):
    with Path(path).open("xb") as f:
        f.write(_canonical(data))


def _gzip_json(path, value):
    with gzip.open(path, "wb", compresslevel=3) as f:
        f.write(_canonical(value))


def _read_gzip_json(path):
    if not path.is_file() or path.is_symlink():
        raise PackageError("SG keyframe/delta missing or symlinked")
    with gzip.open(path, "rb") as f:
        return json.load(f)


def _semantic_identity(graph):
    """Strictly compare entity topology, room membership, relations, contact links.

    Only exact per-frame source identity, geometric numeric bboxes/centroids,
    and floating numeric edge lengths are omitted; all relationship/path IDs,
    threshold, connection type, and room/semantic properties are retained.
    """
    if (
        not isinstance(graph, dict)
        or "entities" not in graph
        or "connections" not in graph
    ):
        raise PackageError("SG schema/entities/connections missing")
    result = {
        k: v
        for k, v in graph.items()
        if k not in FRAME_ID_FIELDS and k not in ("entities", "connections")
    }
    if not isinstance(graph["entities"], list):
        raise PackageError("SG entities not a list")
    result["entities"] = [
        {k: v for k, v in entry.items() if k not in DIFF_ENTITY_FIELDS}
        for entry in graph["entities"]
    ]

    def strip_connection_metrics(value):
        if isinstance(value, dict):
            return {
                k: strip_connection_metrics(v)
                for k, v in value.items()
                if k not in DIFF_NUMERIC_FIELDS
            }
        if isinstance(value, list):
            return [strip_connection_metrics(x) for x in value]
        return value

    result["connections"] = strip_connection_metrics(graph["connections"])
    return _sha_graph(result)


class _StructuralDelta(Exception):
    """A list/field shape changed; force new physical SG keyframe."""


def _changes(a, b):
    """Complete, exact, leaf-level substitutions from a physical SG keyframe."""
    output = []

    def visit(a, b, path):
        if type(a) is dict and type(b) is dict:
            if a.keys() != b.keys():
                raise _StructuralDelta("SG dictionary keys changed")
            for key in sorted(a):
                visit(a[key], b[key], path + [key])
        elif type(a) is list and type(b) is list:
            if len(a) != len(b):
                raise _StructuralDelta("SG list length changed")
            for i, (x, y) in enumerate(zip(a, b)):
                visit(x, y, path + [i])
        elif type(a) is not type(b) or a != b:
            output.append([path, b])

    visit(a, b, [])
    return output


def _apply_changes(base, changes):
    graph = copy.deepcopy(base)
    if not isinstance(changes, list):
        raise PackageError("invalid SG delta changes")
    seen = set()
    for entry in changes:
        if not isinstance(entry, list) or len(entry) != 2:
            raise PackageError("malformed SG patch operation")
        path, value = entry
        if not isinstance(path, list) or not path or len(path) > 64:
            raise PackageError("invalid SG patch path")
        try:
            key = json.dumps(path, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as error:
            raise PackageError("invalid SG patch key") from error
        if key in seen:
            raise PackageError("duplicate SG patch operation")
        seen.add(key)
        node = graph
        for segment in path[:-1]:
            if type(node) is dict and type(segment) is str and segment in node:
                node = node[segment]
            elif (
                type(node) is list and type(segment) is int and 0 <= segment < len(node)
            ):
                node = node[segment]
            else:
                raise PackageError("SG delta path escapes keyframe")
        last = path[-1]
        if type(node) is dict and type(last) is str and last in node:
            node[last] = value
        elif type(node) is list and type(last) is int and 0 <= last < len(node):
            node[last] = value
        else:
            raise PackageError("SG delta points to nonexistent leaf")
    return graph


def _original_graph(graph_file, frame):
    graph_file = Path(graph_file)
    graph = _read_gzip_json(graph_file)
    if (
        not isinstance(graph, dict)
        or graph.get("frame_id") != frame
        or type(graph.get("timestamp_ns")) is not int
        or not isinstance(graph.get("scene_id"), str)
        or not isinstance(graph.get("source_sha256"), str)
        or not isinstance(graph.get("original_state_row_sha256"), str)
        or len(graph.get("original_state_row_sha256", "")) != 64
    ):
        raise PackageError("original SG frame identity/provenance invalid")
    return graph


def _graph_body(graph):
    """Frame identity lives in the manifest; the reusable SG body stays exact."""
    return {key: value for key, value in graph.items() if key not in FRAME_ID_FIELDS}


def _inline_metadata(row):
    metadata = row.get("scene_graph_frame_metadata")
    if (
        not isinstance(metadata, dict)
        or set(metadata) != FRAME_ID_FIELDS
        or type(metadata.get("frame_id")) is not int
        or metadata["frame_id"] != row.get("frame")
        or type(metadata.get("timestamp_ns")) is not int
        or not isinstance(metadata.get("original_state_row_sha256"), str)
        or len(metadata["original_state_row_sha256"]) != 64
    ):
        raise PackageError("invalid inline SG frame metadata")
    return metadata


def _state_directory(root, state_id, row, *, required):
    frame = row.get("frame")
    if type(frame) is not int or frame < 0:
        raise PackageError("invalid SG source frame")
    folder = root / f"state_{state_id:06d}_frame_{frame:06d}"
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise PackageError("invalid or symlinked SG state directory")
    if required and not folder.is_dir():
        raise PackageError("missing SG state directory")
    return folder


def _sg_rows(staging, source_rows, copy_view):
    rows = []
    prev_sg_owner = None
    prev_graph = None
    prev_semantic = None
    # Within one physical keyframe, map each exact body to a physical delta
    # owner, or None for the keyframe body itself. References never chain.
    body_owners = {}
    physical_sgs = 0
    indexed_sgs = 0
    reused_sgs = 0
    physically_stored_pngs = 0
    png_refs = 0
    seen_floor = {}
    # Floor PNG dedup can change an original physical owner's location.
    old_physical_to_owner = {}

    for i, item in enumerate(source_rows):
        previous = item["row"]
        frame = previous["frame"]
        if type(frame) is not int:
            raise PackageError("invalid v2 source frame")
        state = staging / f"state_{i:06d}_frame_{frame:06d}"
        graph = _original_graph(item["graph"], frame)
        body = _graph_body(graph)
        body_sha = _sha_graph(body)
        signature = _semantic_identity(graph)
        changes = None
        own = (
            prev_sg_owner is None
            or previous.get("update_mode") == "FULL"
            or signature != prev_semantic
        )
        if not own:
            try:
                changes = _changes(_graph_body(prev_graph), body)
            except _StructuralDelta:
                own = True
        row = dict(previous)
        row.pop("scene_graph", None)
        row["scene_graph_sha256"] = _sha_graph(graph)
        row["scene_graph_frame_metadata"] = {
            name: graph[name] for name in sorted(FRAME_ID_FIELDS)
        }
        _inline_metadata(row)
        if own:
            state.mkdir()
            shutil.copyfile(item["graph"], state / SG_PHYSICAL)
            row["scene_graph"] = SG_PHYSICAL
            row["scene_graph_ref"] = None
            prev_sg_owner = i
            prev_graph = graph
            prev_semantic = signature
            body_owners = {body_sha: None}
            physical_sgs += 1
        else:
            assert prev_sg_owner is not None and changes is not None
            row["scene_graph"] = None
            if body_sha in body_owners:
                ref = {"ref_state": prev_sg_owner}
                delta_owner = body_owners[body_sha]
                if delta_owner is not None:
                    ref["delta_ref_state"] = delta_owner
                row["scene_graph_ref"] = ref
                reused_sgs += 1
            else:
                state.mkdir()
                patch = {
                    "schema": PATCH_SCHEMA,
                    "ref_state": prev_sg_owner,
                    "frame": frame,
                    "changes": changes,
                }
                _gzip_json(state / SG_DELTA, patch)
                if _apply_changes(_graph_body(prev_graph), changes) != body:
                    raise PackageError("SG body delta failed strict roundtrip")
                row["scene_graph_ref"] = {
                    "ref_state": prev_sg_owner,
                    "delta": SG_DELTA,
                }
                body_owners[body_sha] = i
                indexed_sgs += 1
        row["view_pngs"] = []
        row["view_refs"] = {}
        for relative, ref in previous.get("view_refs", {}).items():
            old_owner = ref.get("ref_state")
            owner = old_physical_to_owner.get((old_owner, relative))
            if owner is None or owner >= i or ref.get("path") != relative:
                raise PackageError(
                    "indexed v2 PNG ref cannot be mapped to physical v3 owner"
                )
            row["view_refs"][relative] = {"ref_state": owner, "path": relative}
        for relative in previous["view_pngs"]:
            source = item["folder"] / relative
            if source.is_symlink() or not source.is_file():
                raise PackageError("source PNG missing or symlinked")
            # Content dedup only affects floor_top. GT still owns scene events.
            floor = Path(relative).name == "floor_top.png"
            if floor:
                sha = _sha_bytes(source.read_bytes())
                last = seen_floor.get((relative, sha))
                if last is not None:
                    row["view_refs"][relative] = {
                        "ref_state": last,
                        "path": relative,
                    }
                    old_physical_to_owner[(i, relative)] = last
                    png_refs += 1
                    continue
            dest = state / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            copy_view(source, dest)
            row["view_pngs"].append(relative)
            old_physical_to_owner[(i, relative)] = i
            physically_stored_pngs += 1
            if floor:
                seen_floor[(relative, sha)] = i
        png_refs += len(previous.get("view_refs", {}))
        rows.append(row)
    return rows, dict(
        sg_keyframes=physical_sgs,
        sg_deltas=indexed_sgs,
        sg_reused=reused_sgs,
        physical_pngs=physically_stored_pngs,
        image_refs=png_refs,
    )


def _publish(source, dest, summary, source_rows, *, robot_policy=None):
    source = Path(source).resolve(strict=True)
    dest = Path(dest).absolute()
    if (
        dest.exists()
        or dest.is_symlink()
        or dest == source
        or source in dest.parents
        or dest in source.parents
    ):
        raise PackageError("SG v3 destination overlaps or exists")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="._g2_sg_index_", dir=dest.parent))
    good = False
    try:
        rows, stats = _sg_rows(tmp, source_rows, shutil.copyfile)
        summary = dict(summary)
        # Old published v2 Episodes used a 1e-10m/rad marker threshold
        # relative to the previous sample. A converter must not falsely
        # claim that their views were rendered under the NEW 1mm/1degree gate.
        if robot_policy is None:
            robot_policy = dict(
                xy=1e-10,
                yaw_deg=math.degrees(1e-10),
                reference="PREVIOUS_SAMPLED_STATE_LEGACY",
            )
        if robot_policy.get("reference") not in (
            "PREVIOUS_SAMPLED_STATE_LEGACY",
            "LAST_DRAWN_FLOOR_MARKER",
        ):
            raise PackageError("unknown source robot update policy")
        summary.update(
            schema=SCHEMA,
            states=rows,
            state_count=len(rows),
            complete=True,
            indexed_views_enabled=True,
            indexed_sg_enabled=True,
            sg_reuse_basis="NONROBOT_GT_VISUAL_POSE_WITH_SG_TOPOLOGY_GUARD",
            sg_frame_metadata_policy=INLINE_METADATA_POLICY,
            sg_delta_schema=PATCH_SCHEMA,
            robot_motion_xy_tol_m=robot_policy["xy"],
            robot_motion_yaw_tol_deg=robot_policy["yaw_deg"],
            robot_motion_reference_policy=robot_policy["reference"],
        )
        _write_json(tmp / "episode_manifest.json", summary)
        marker = {
            "schema": SCHEMA,
            "complete": True,
            "episode_id": summary["episode_id"],
            "state_count": len(rows),
            "renderer": "f27",
            "training_ready": False,
            "source_fingerprint": summary["source_fingerprint"],
            "episode_manifest_sha256": _sha_bytes(
                (tmp / "episode_manifest.json").read_bytes()
            ),
        }
        _write_json(tmp / "COMPLETE.json", marker)
        validate_sg_indexed_episode(tmp)
        os.rename(tmp, dest)
        good = True
        return summary, stats
    finally:
        if not good:
            shutil.rmtree(tmp, ignore_errors=True)


def convert_v2_to_v3(source, dest, *, _verified_robot_policy=None):
    """Exact offline repackage of published v2, never alters either original.

    If called by a verified new F27 Worker, preserve its approved robot
    policy. Existing v2 files have the historical near-zero robot threshold.
    """
    source = Path(source).resolve(strict=True)
    count = validate_indexed_episode(source)
    original = _read_json(source / "episode_manifest.json")
    rows = []
    for i, entry in enumerate(original["states"]):
        folder = source / f"state_{i:06d}_frame_{entry['frame']:06d}"
        rows.append(
            dict(
                row=entry,
                folder=folder,
                graph=folder / SG_PHYSICAL,
            )
        )
    if len(rows) != count:
        raise PackageError("source v2 state count mismatch")
    return _publish(source, dest, original, rows, robot_policy=_verified_robot_policy)


def _physical_graph(root, state_id, rows):
    entry = rows[state_id]
    if (
        not isinstance(entry, dict)
        or entry.get("scene_graph") != SG_PHYSICAL
        or entry.get("scene_graph_ref") is not None
    ):
        raise PackageError("SG reference does not point to a physical keyframe")
    folder = _state_directory(root, state_id, entry, required=True)
    graph = _read_gzip_json(folder / SG_PHYSICAL)
    if (
        not isinstance(graph, dict)
        or graph.get("frame_id") != entry["frame"]
        or _sha_graph(graph) != entry.get("scene_graph_sha256")
    ):
        raise PackageError("physical SG frame/hash mismatch")
    return graph


def resolve_scene_graph(root, state_id, manifest=None):
    """Rebuild one exact SG from a physical keyframe and optional physical delta."""
    root = Path(root).resolve(strict=True)
    if manifest is None:
        manifest = _read_json(root / "episode_manifest.json")
    policy = manifest.get("sg_frame_metadata_policy")
    if policy not in (None, LEGACY_METADATA_POLICY, INLINE_METADATA_POLICY):
        raise PackageError("unknown SG frame metadata policy")
    inline = policy == INLINE_METADATA_POLICY
    rows = manifest["states"]
    if type(state_id) is not int or not 0 <= state_id < len(rows):
        raise PackageError("invalid SG state id")
    entry = rows[state_id]
    if not isinstance(entry, dict):
        raise PackageError("invalid SG state entry")
    # Reject a symlink even when a pure-reference state needs no directory.
    _state_directory(root, state_id, entry, required=False)
    metadata = _inline_metadata(entry) if inline else None
    physical = entry.get("scene_graph")
    ref = entry.get("scene_graph_ref")
    if physical == SG_PHYSICAL:
        graph = _physical_graph(root, state_id, rows)
        if inline and any(graph.get(key) != value for key, value in metadata.items()):
            raise PackageError("physical SG inline metadata mismatch")
    elif physical is None and isinstance(ref, dict):
        owner = ref.get("ref_state")
        if type(owner) is not int or not 0 <= owner < state_id:
            raise PackageError("SG reference must point to prior keyframe")
        graph = _physical_graph(root, owner, rows)
        if inline:
            graph = _graph_body(graph)
            fields = set(ref)
            if fields == {"ref_state"}:
                delta_owner = None
            elif fields == {"ref_state", "delta"} and ref["delta"] == SG_DELTA:
                delta_owner = state_id
            elif fields == {"ref_state", "delta_ref_state"}:
                delta_owner = ref["delta_ref_state"]
                if type(delta_owner) is not int or not owner < delta_owner < state_id:
                    raise PackageError("SG delta reference must point to prior physical delta")
                delta_row = rows[delta_owner]
                delta_ref = delta_row.get("scene_graph_ref")
                if (
                    delta_row.get("scene_graph") is not None
                    or not isinstance(delta_ref, dict)
                    or type(delta_ref.get("ref_state")) is not int
                    or delta_ref != {"ref_state": owner, "delta": SG_DELTA}
                ):
                    raise PackageError("SG chained or mismatched delta reference forbidden")
            else:
                raise PackageError("invalid SG delta reference fields/path")
        else:
            if ref.get("delta") != SG_DELTA:
                raise PackageError("SG delta path incorrect")
            delta_owner = state_id
        if delta_owner is not None:
            delta_row = rows[delta_owner]
            folder = _state_directory(root, delta_owner, delta_row, required=True)
            patch = _read_gzip_json(folder / SG_DELTA)
            if (
                not isinstance(patch, dict)
                or patch.get("schema") != PATCH_SCHEMA
                or type(patch.get("ref_state")) is not int
                or patch["ref_state"] != owner
                or type(patch.get("frame")) is not int
                or patch["frame"] != delta_row["frame"]
            ):
                raise PackageError("SG delta provenance incorrect")
            graph = _apply_changes(graph, patch.get("changes"))
        if inline:
            graph.update(metadata)
    else:
        raise PackageError("SG state missing physical graph or reference")
    if graph.get("frame_id") != entry["frame"] or _sha_graph(graph) != entry.get(
        "scene_graph_sha256"
    ):
        raise PackageError("SG reconstructed frame/hash mismatch")
    return graph


def validate_sg_indexed_episode(root):
    root = Path(root).resolve(strict=True)
    manifest_path = root / "episode_manifest.json"
    complete = _read_json(root / "COMPLETE.json")
    doc = _read_json(manifest_path)
    rows = doc.get("states")
    policy = doc.get("sg_frame_metadata_policy")
    if policy not in (None, LEGACY_METADATA_POLICY, INLINE_METADATA_POLICY):
        raise PackageError("unknown SG frame metadata policy")
    inline = policy == INLINE_METADATA_POLICY
    if (
        doc.get("schema") != SCHEMA
        or complete.get("schema") != SCHEMA
        or doc.get("complete") is not True
        or complete.get("complete") is not True
        or doc.get("indexed_views_enabled") is not True
        or doc.get("indexed_sg_enabled") is not True
        or (
            doc.get("robot_motion_reference_policy")
            not in ("PREVIOUS_SAMPLED_STATE_LEGACY", "LAST_DRAWN_FLOOR_MARKER")
        )
        or (
            doc.get("robot_motion_xy_tol_m")
            != (
                0.001
                if doc.get("robot_motion_reference_policy") == "LAST_DRAWN_FLOOR_MARKER"
                else 1e-10
            )
        )
        or (
            doc.get("robot_motion_yaw_tol_deg")
            != (
                1.0
                if doc.get("robot_motion_reference_policy") == "LAST_DRAWN_FLOOR_MARKER"
                else math.degrees(1e-10)
            )
        )
        or doc.get("scene_motion_translation_tol_m") != 0.001
        or doc.get("scene_motion_rotation_tol_deg") != 1.0
        or not isinstance(rows, list)
        or len(rows) != doc.get("state_count")
        or len(rows) != complete.get("state_count")
        or complete.get("episode_id") != doc.get("episode_id")
        or complete.get("source_fingerprint") != doc.get("source_fingerprint")
        or complete.get("episode_manifest_sha256")
        != _sha_bytes(manifest_path.read_bytes())
    ):
        raise PackageError("invalid completed v3 SG package identity")
    previous_frame = -1
    for i, row in enumerate(rows):
        frame = row.get("frame")
        if type(frame) is not int or frame <= previous_frame:
            raise PackageError("nonmonotonic source frame")
        previous_frame = frame
        files = row.get("view_pngs")
        refs = row.get("view_refs")
        if not isinstance(files, list) or not isinstance(refs, dict):
            raise PackageError("invalid v3 PNG inventory")
        sg_ref = row.get("scene_graph_ref")
        materialized = (
            bool(files)
            or row.get("scene_graph") == SG_PHYSICAL
            or (isinstance(sg_ref, dict) and sg_ref.get("delta") == SG_DELTA)
        )
        _state_directory(root, i, row, required=materialized if inline else True)
        graph = resolve_scene_graph(root, i, doc)
        if (
            graph.get("scene_id") is None
            or graph.get("source_sha256") is None
            or type(graph.get("timestamp_ns")) is not int
            or type(graph.get("original_state_row_sha256")) is not str
        ):
            raise PackageError("missing per-frame graph source identity")
        if len(files) != len(set(files)) or set(files) & set(refs):
            raise PackageError("duplicate physical/indexed PNG")
        paths = set(files) | set(refs)
        if not any(
            path.startswith("sixview/") and Path(path).name == "floor_top.png"
            for path in paths
        ):
            raise PackageError("missing top view")
        for path in paths:
            resolve_indexed_png(rows, i, path, root)
    return len(rows)


def completed_output_indexed_v3(plan_row, output_root):
    path = Path(output_root) / plan_row["expected_relative_output"]
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_symlink() or not path.is_dir():
        raise PackageError("invalid indexed v3 path")
    doc = _read_json(path / "episode_manifest.json")
    if (
        doc.get("schema") != SCHEMA
        or doc.get("source_fingerprint") != plan_row["source_fingerprint"]
        or doc.get("episode_id") != plan_row["episode_id"]
        or doc.get("task_class") != plan_row["task_class"]
        or [row.get("frame") for row in doc.get("states", [])]
        != plan_row["spatial_frames"]
    ):
        raise PackageError("indexed v3 source/recipe differs from immutable plan")
    return validate_sg_indexed_episode(path) == len(plan_row["spatial_frames"])


def package_indexed_sg_v3(
    source, destination, *, episode_id, task_class, selection=None
):
    """Direct opt-in F27 publisher. V2 staging is private and never committed.

    The additional package pass is intentionally conservative: both the
    proven P1 v2 packager and the v3 exact-SG converter validate their inputs.
    It can later be fused after a separate equivalence/performance gate.
    """
    from g2.offline.atomic_6views_compact_v2 import package_indexed

    source = Path(source).resolve(strict=True)
    dest = Path(destination).absolute()
    source_receipt = _read_json(source / "episode_receipt.json")
    if (
        source_receipt.get("scene_event_index_enabled") is not True
        or source_receipt.get("robot_motion_xy_tol_m") != 0.001
        or source_receipt.get("robot_motion_yaw_tol_deg") != 1.0
    ):
        raise PackageError(
            "SG v3 requires explicit F27 1mm/1degree robot marker policy"
        )
    if dest.exists() or dest.is_symlink():
        raise PackageError("SG v3 destination already exists")
    for row in source_receipt.get("states", []):
        distance = row.get("robot_xy_delta_m")
        angle = row.get("robot_yaw_delta_rad")
        if (
            type(distance) not in (int, float)
            or type(angle) not in (int, float)
            or not math.isfinite(distance)
            or not math.isfinite(angle)
            or distance < 0
            or angle < 0
        ):
            raise PackageError("P3 source missing robot motion evidence")
        if row.get("scene_event_mode") == "REUSE_ALL" and (
            distance >= 0.001 or angle >= math.radians(1.0)
        ):
            raise PackageError("P3 cannot reuse robot-arrow PNG beyond 1mm/1degree")
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix="._g2_sg_proven_", dir=dest.parent))
    try:
        v2 = temp / "v2"
        package_indexed(
            source,
            v2,
            episode_id=episode_id,
            task_class=task_class,
            selection=selection,
        )
        summary, stats = convert_v2_to_v3(
            v2,
            dest,
            _verified_robot_policy={
                "xy": 0.001,
                "yaw_deg": 1.0,
                "reference": "LAST_DRAWN_FLOOR_MARKER",
            },
        )
        print("G2_SG_V3_PACKAGE_PASS", dest, stats, flush=True)
        return summary
    finally:
        shutil.rmtree(temp, ignore_errors=True)
