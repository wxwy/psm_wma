"""Audited BEHAVIOR-1K *initial* source binding, upstream of native GT.

This module does not generate Room geometry, occupancy, SG or View assets.
Never label its output as a nav_sg_spatial_snapshot_v1; the latter must be
produced from independently verified runtime geometry in OmniGibson.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCENE_SCHEMA = "g3_b1k_initial_scene_source_v1"
INDEX_SCHEMA = "g3_b1k_initial_task_binding_index_v1"


class SourceBindingError(ValueError):
    """Input data cannot be bound without guessing source identities."""


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise SourceBindingError(f"missing or unsafe source: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SourceBindingError(f"expected JSON object: {path}")
    return value


def _sha(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise SourceBindingError(f"source unavailable for hash: {path}")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError as exc:
        raise SourceBindingError("source must remain inside declared B1K root") from exc


def _vector(value: Any, size: int, label: str) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != size
        or any(type(n) not in (int, float) or not math.isfinite(n) for n in value)
    ):
        raise SourceBindingError(f"{label} must be a finite {size}-vector")
    return value


def _pose(state: Any, label: str) -> dict[str, Any]:
    if not isinstance(state, dict) or not isinstance(state.get("root_link"), dict):
        raise SourceBindingError(f"{label}: missing OmniGibson root_link")
    root = state["root_link"]
    return {
        "pos_raw": _vector(root.get("pos"), 3, label + ".pos"),
        "ori_raw": _vector(root.get("ori"), 4, label + ".ori"),
        "frame_and_quaternion_convention_verified_in_sim": False,
    }


def initial_scene(root: Path, scene_template: Path) -> dict[str, Any]:
    """Parse only static template roster and task bindings; no scene asset decoding."""
    src = _read(scene_template)
    try:
        task_bindings = src["metadata"]["task"]["inst_to_name"]
        instances = src["objects_info"]["init_info"]
        initial_states = src["state"]["registry"]["object_registry"]
    except (KeyError, TypeError) as exc:
        raise SourceBindingError("missing B1K task-object/initial-state structure") from exc

    if (
        not isinstance(task_bindings, dict)
        or not isinstance(instances, dict)
        or not isinstance(initial_states, dict)
        or set(instances) != set(initial_states)
        or not instances
        or len(set(task_bindings.values())) != len(task_bindings)
    ):
        raise SourceBindingError("scene roster or BDDL mapping inconsistent")
    if task_bindings.get("agent.n.01_1") != "robot":
        raise SourceBindingError("robot BDDL binding absent")

    for role, name in task_bindings.items():
        if name != "robot" and name not in instances:
            raise SourceBindingError(f"missing bound BDDL object: {role} -> {name}")

    roster = []
    for name in sorted(instances):
        source = instances[name]
        args = source.get("args") if isinstance(source, dict) else None
        if (
            not isinstance(args, dict)
            or args.get("name") != name
            or not isinstance(args.get("category"), str)
            or not args["category"]
            or not isinstance(args.get("model"), str)
            or not args["model"]
        ):
            raise SourceBindingError(f"object identity/category/model invalid: {name}")
        roster.append({
            "source_object_id": name,
            "category": args["category"],
            "model": args["model"],
            "scale_raw": _vector(args.get("scale"), 3, name + ".scale"),
            "template_pose_raw": _pose(initial_states[name], name),
            "geometry": None,
            "room": None,
            "geometry_status": "PENDING_OMNIGIBSON_GT_RUNTIME",
        })
    return {
        "schema": SCENE_SCHEMA,
        "source_file": _relative(scene_template, root),
        "source_sha256": _sha(scene_template),
        "task_bindings": task_bindings,
        "objects": roster,
        "full_map_ready": False,
        "native_room_geometry": None,
        "tri_state_occupancy": None,
        "rgb_surface_mesh": None,
        "provenance": "B1K_OFFICIAL_PUBLIC_TASK_INSTANCE_TEMPLATE_NOT_RUNTIME_FULL_MAP",
    }


def bind_episodes(
    *,
    root: Path,
    scene: dict[str, Any],
    rows: list[dict[str, Any]],
    task_name: str,
    task_index: int,
    scene_model: str,
    scene_instance_dir: Path,
    raw_data_dir: Path,
    annotations_dir: Path,
) -> dict[str, Any]:
    """Bind independent task-instance state for every episode.

    Missing public task-state files are explicitly blocked, never replaced by
    a nearby instance or static base scene. This is not a whole-frame HDF5
    dynamic state decoder.
    """
    targets = {k: v for k, v in scene["task_bindings"].items() if v != "robot"}
    roster = {o["source_object_id"]: o for o in scene["objects"]}
    seen: set[int] = set()
    seen_raw: set[int] = set()
    result = []
    for n, row in enumerate(rows):
        if (
            row.get("episode_index") != n
            or row.get("task_index") != task_index
            or row.get("tasks") != [task_name]
        ):
            raise SourceBindingError(f"incorrect ordered episode task/index at {n}")
        instance_id, raw_id = row.get("task_instance_id"), row.get("raw_episode_id")
        if (
            type(instance_id) is not int
            or instance_id < 0
            or type(raw_id) is not int
            or raw_id < 0
            or instance_id in seen
            or raw_id in seen_raw
        ):
            raise SourceBindingError(f"invalid or repeated instance ID at {n}")
        seen.add(instance_id)
        seen_raw.add(raw_id)
        anno = row.get("annotation_path")
        if (
            not isinstance(anno, str)
            or Path(anno).parts[:2] != ("annotations", f"task-{task_index:04d}")
            or ".." in Path(anno).parts
        ):
            raise SourceBindingError(f"invalid annotation path at episode {n}")
        annotation_path = root / "datasets/2026-challenge-demos" / anno
        if not annotation_path.is_file():
            raise SourceBindingError(f"missing annotation: {anno}")
        raw = raw_data_dir / f"episode_{raw_id:08d}.hdf5"
        if not raw.is_file() or raw.is_symlink():
            raise SourceBindingError(f"raw HDF5 absent for {raw_id}")

        state_file = scene_instance_dir / (
            f"{scene_model}_task_{task_name}_0_{instance_id}_template-tro_state.json"
        )
        entry = {
            "episode_index": n,
            "raw_episode_id": raw_id,
            "task_instance_id": instance_id,
            "annotation_file": _relative(annotation_path, root),
            "state_file": _relative(state_file, root),
            "state_file_sha256": None,
            "source_status": "BLOCKED_MISSING_PUBLIC_TASK_INSTANCE_STATE",
            "task_object_states": None,
            "robot_base_pose_raw": None,
            "full_map_ready": False,
        }
        if state_file.is_file():
            source = _read(state_file)
            if not set(targets).issubset(source):
                raise SourceBindingError(f"missing BDDL target state: instance={instance_id}")
            poses = {}
            for role, obj in sorted(targets.items()):
                poses[role] = {
                    "source_object_id": obj,
                    "pose_raw": _pose(source[role], f"instance{instance_id}/{role}"),
                    "category": roster[obj]["category"],
                }
            r1 = source.get("robot_poses", {}).get("R1Pro")
            if not isinstance(r1, list) or len(r1) != 1:
                raise SourceBindingError(f"R1Pro initial pose missing: {instance_id}")
            entry.update({
                "source_status": "TASK_INITIAL_STATE_ONLY",
                "state_file_sha256": _sha(state_file),
                "task_object_states": poses,
                "robot_base_pose_raw": {
                    "pos_raw": _vector(r1[0].get("position"), 3, "R1Pro.position"),
                    "ori_raw": _vector(r1[0].get("orientation"), 4, "R1Pro.orientation"),
                    "frame_and_quaternion_convention_verified_in_sim": False,
                },
            })
        result.append(entry)

    statuses = {e["source_status"] for e in result}
    return {
        "schema": INDEX_SCHEMA,
        "scene_template_source_sha256": scene["source_sha256"],
        "task_name": task_name,
        "task_index": task_index,
        "episodes": result,
        "counts": {
            "total": len(result),
            "task_initial_state_present": sum(
                e["source_status"] == "TASK_INITIAL_STATE_ONLY" for e in result
            ),
            "missing_public_task_state": sum(
                e["source_status"] == "BLOCKED_MISSING_PUBLIC_TASK_INSTANCE_STATE"
                for e in result
            ),
        },
        "gate": "SOURCE_BINDING_PARTIAL" if len(statuses) > 1 else (
            "SOURCE_BINDING_ONLY" if statuses == {"TASK_INITIAL_STATE_ONLY"}
            else "BLOCKED_NO_TASK_INITIAL_STATE"
        ),
        "full_map_ready": False,
        "explicit_limitations": [
            "requires actual OmniGibson runtime geometry and native Room",
            "not a nav_sg_spatial_snapshot_v1",
            "not per-frame scene state or renderable Voxel/SG",
            "no future trajectory information",
        ],
    }


def build_task0(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """First B1K-2026 integration: Task 0 only, exact official local layout."""
    root = Path(root)
    task, model = "turning_on_radio", "house_double_floor_lower"
    scene_dir = root / (
        "assets/omnigibson/2026-challenge-task-instances/scenes/"
        f"{model}/json"
    )
    scene = initial_scene(
        root, scene_dir / f"{model}_task_{task}_0_0_template.json"
    )
    episodes = root / "datasets/2026-challenge-demos/meta/episodes/chunk-000/file-000.parquet"
    import pyarrow.parquet as pq  # optional dependency limited to the CLI/real-data path
    rows = pq.read_table(episodes).to_pylist()
    binding = bind_episodes(
        root=root,
        scene=scene,
        rows=rows,
        task_name=task,
        task_index=0,
        scene_model=model,
        scene_instance_dir=scene_dir / f"{model}_task_{task}_instances",
        raw_data_dir=root / "datasets/2026-challenge-rawdata/task-0000",
        annotations_dir=root / "datasets/2026-challenge-demos/annotations/task-0000",
    )
    binding["episode_metadata_source_sha256"] = _sha(episodes)
    return scene, binding


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b1k-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    scene, binding = build_task0(args.b1k_root)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in (
        ("task0_initial_scene_source.json", scene),
        ("task0_initial_episode_bindings.json", binding),
    ):
        (args.output_dir / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({"gate": binding["gate"], "counts": binding["counts"],
                      "full_map_ready": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
