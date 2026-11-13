"""Compact accepted F27 sixviews + independent island views + scene graph.

Only invoked by the owner's manual production command. No automatic launch.
The F27 episode renderer deliberately retains diagnostic numeric evidence; this
writer creates a small durable dataset artifact instead of copying diagnostics.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


class PackageError(ValueError):
    pass


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _relative(path):
    if type(path) is not str or not path or "\x00" in path:
        raise PackageError("invalid relative view path")
    p = Path(path)
    if p.is_absolute() or ".." in p.parts or len(p.parts) < 2:
        raise PackageError("unsafe view path")
    if p.parts[0] not in ("sixview", "islands") or p.suffix.lower() != ".png":
        raise PackageError("only room/island view PNGs may be published")
    if p.parts[0] == "islands" and len(p.parts) < 3:
        raise PackageError("island views require a separate island ID")
    return p


def inspect_episode(source, *, require_graph=True):
    """Inspect only receipts and state manifests; never rehash source images."""
    source = Path(source).resolve(strict=True)
    receipt = read_json(source / "episode_receipt.json")
    if (receipt.get("schema") != "g2_repository_native_view_episode_v1"
            or receipt.get("complete") is not True
            or receipt.get("training_ready") is not False
            or receipt.get("view_opaque_geometry_source") != "SURFACE_REGISTRY_VISUAL_GEOMETRY"
            or receipt.get("source_material_identity_per_pixel") is not True
            or type(receipt.get("spatial_state_count")) is not int
            or receipt["spatial_state_count"] < 1):
        raise PackageError("source episode is not complete F27 output")
    rows = receipt.get("states")
    if not isinstance(rows, list) or len(rows) != receipt["spatial_state_count"]:
        raise PackageError("source episode state list incomplete")
    states = []
    for index, row in enumerate(rows):
        if (type(row.get("frame")) is not int or type(row.get("state_id")) is not int
                or row["state_id"] != index or type(row.get("view_count")) is not int
                or row["view_count"] < 1):
            raise PackageError("source F27 frame/sequence invalid")
        root = source / f"state_{index:06d}_frame_{row['frame']:06d}"
        if not root.is_dir():
            raise PackageError("source state directory missing")
        dc = read_json(root / "direct_color_views.json")
        if (dc.get("frame_id") != row["frame"]
                or dc.get("view_count") != row["view_count"]
                or dc.get("visual_geometry_source") != "SURFACE_REGISTRY_VISUAL_GEOMETRY"
                or dc.get("surface_material_identity_per_pixel") is not True
                or dc.get("training_ready") is not False):
            raise PackageError("source view manifest differs from F27 receipt")
        views = dc.get("views")
        if not isinstance(views, list) or len(views) != row["view_count"]:
            raise PackageError("source view count mismatch")
        output_files, island_ids = [], set()
        for image in views:
            relative = _relative(image.get("rgb_file"))
            p = root / relative
            if not p.is_file() or p.is_symlink():
                raise PackageError("missing or symlinked source PNG: " + str(p))
            output_files.append((relative, p))
            if relative.parts[0] == "islands":
                island_ids.add(relative.parts[1])
        graph = root / "scene_graph.json"
        if require_graph and (not graph.is_file() or graph.is_symlink()):
            raise PackageError("F27 source scene graph missing")
        states.append({
            "frame": row["frame"], "source_state": root, "views": output_files,
            "graph": graph if graph.is_file() and not graph.is_symlink() else None,
            "islands": sorted(island_ids),
        })
    return receipt, states


def _write_json(path, body):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        f.write("\n")


def package(source, destination, *, episode_id, task_class,
            require_graph=True, selection=None):
    """Write one compact episode atomically; never touch source or prior output."""
    receipt, states = inspect_episode(source, require_graph=require_graph)
    fingerprint = None
    if selection is not None:
        if not isinstance(selection, dict):
            raise PackageError("selection record must be a dictionary")
        fingerprint = selection.get("source_fingerprint")
        if (selection.get("episode_id") != episode_id
                or selection.get("task_class") != task_class
                or not isinstance(fingerprint, str) or len(fingerprint) != 64
                or any(c not in "0123456789abcdef" for c in fingerprint)
                or selection.get("spatial_frames") != [row["frame"] for row in states]
                or selection.get("spatial_state_count") != len(states)):
            raise PackageError("F27 source output differs from pinned selection")
    destination = Path(destination).absolute()
    if (destination.exists() or destination.is_symlink()
            or destination == Path(source).resolve()
            or Path(source).resolve() in destination.parents
            or destination in Path(source).resolve().parents):
        raise PackageError("destination overlaps source or already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="._g2_stage_", dir=destination.parent))
    succeeded = False
    try:
        rows = []
        for idx, state in enumerate(states):
            frame = state["frame"]
            root = tmp / f"state_{idx:06d}_frame_{frame:06d}"
            outputs = []
            for rel, original in state["views"]:
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, target)
                outputs.append(str(rel))
            has_graph = state["graph"] is not None
            if has_graph:
                graph = read_json(state["graph"])
                if (graph.get("frame_id") != frame
                        or graph.get("source_sha256") is None
                        or graph.get("scene_id") is None):
                    raise PackageError("source scene graph not bound to current frame/scene")
                with gzip.open(root / "scene_graph.json.gz", "wb", compresslevel=3) as out:
                    out.write(state["graph"].read_bytes())
            rows.append({
                "frame": frame,
                "view_pngs": outputs,
                "islands": state["islands"],
                "scene_graph": "scene_graph.json.gz" if has_graph else None,
            })
        summary = {
            "schema": "g2_atomic_compact_6views_v1",
            "episode_id": episode_id, "task_class": task_class,
            "source_inputs_sha256": receipt["source_inputs_sha256"],
            "source_fingerprint": fingerprint,
            "selection_pinned_for_resume": fingerprint is not None,
            "source_renderer": "f27", "source_mode": "full_map_mujoco_source",
            "source_20hz": True, "spatial_frequency_hz": 2,
            "view_resolution_mpp": .01, "island_four_views_enabled": True,
            "robot_pose_marker_enabled": receipt.get("robot_pose_marker_enabled") is True,
            "robot_pose_marker_style": receipt.get("robot_pose_marker_style"),
            "states": rows, "state_count": len(rows), "complete": True,
            "training_ready": False,
            "native_voxels_saved": False, "colored_point_cloud_saved": False,
            "audit_source_kept_separately": True,
        }
        _write_json(tmp / "episode_manifest.json", summary)
        manifest_sha256 = hashlib.sha256(
            (tmp / "episode_manifest.json").read_bytes()).hexdigest()
        _write_json(tmp / "COMPLETE.json", {
            "schema": summary["schema"], "complete": True,
            "episode_id": episode_id, "state_count": len(rows),
            "renderer": "f27", "training_ready": False,
            "source_fingerprint": fingerprint,
            "episode_manifest_sha256": manifest_sha256})
        os.rename(tmp, destination)
        succeeded = True
        return summary
    finally:
        if not succeeded:
            shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("inspect", "package"))
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--destination", type=Path)
    p.add_argument("--episode-id", type=int)
    p.add_argument("--task-class")
    p.add_argument("--selection-record", type=Path,
                   help="one pinned per-episode planner record; required for resumable production")
    args = p.parse_args(argv)
    if args.action == "inspect":
        _, states = inspect_episode(args.source)
        result = {"state_count": len(states), "views": sum(len(s["views"]) for s in states),
                  "island_views": sum(sum(1 for rel, _ in s["views"]
                      if rel.parts[0] == "islands") for s in states),
                  "written": False}
    else:
        if args.destination is None or args.episode_id is None or not args.task_class:
            p.error("package requires --destination, --episode-id, --task-class")
        result = package(args.source, args.destination,
                         episode_id=args.episode_id, task_class=args.task_class,
                         selection=read_json(args.selection_record)
                                   if args.selection_record else None)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
