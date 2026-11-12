"""Plan RoboCasa365 target-atomic Full-Map F27 views without launching simulation.

Read-only scan of flat V3 mapping, official per-episode assets and the existing
Depth completeness receipts. A plan is NOT a native scene/snapshot certificate
and cannot be passed directly to g2.offline.batch_render, which consumes
already-materialized native/visual episode inputs. Missing upstream artifacts
remain explicitly BLOCKED; never substitute a layout-1/10 scene snapshot.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

DATA_ROOT = Path("/mnt/data1/data_v2_0617/robocasa365_v3_flat")
FLAT = DATA_ROOT / "robocasa365-target-atomic"
RAW = DATA_ROOT.parent / "robocasa365_official/v1.0/target/atomic"
DEPTH = DATA_ROOT / "robocasa365-target-atomic-depth"
OUTPUT = DATA_ROOT / "robocasa365-target-atomic-6views"
SCHEMA = "g2_robocasa365_atomic_6views_dataset_plan_v1"
EXPECTED = 9126
LAYOUTS = set(range(1, 11))
MAX_BATCH = 100


class PlanError(ValueError):
    pass


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        f.write("\n")


def frame_ids(length, stride=10):
    """20 Hz source -> 2 Hz spatial, always include the final source frame."""
    if type(length) is not int or length < 2 or type(stride) is not int or stride <= 0:
        raise PlanError("invalid episode length or spatial stride")
    result = list(range(0, length, stride))
    if result[-1] != length - 1:
        result.append(length - 1)
    if len(result) != len(set(result)) or len(result) > 300:
        raise PlanError("selected frames exceed pinned F27 adapter")
    return result


def _lerobot_task_roots(raw_root, tasks):
    roots = {}
    for task in tasks:
        candidates = list((raw_root / task).glob("*/lerobot"))
        if len(candidates) != 1 or not candidates[0].is_dir():
            raise PlanError("raw task root is absent or ambiguous: " + task)
        roots[task] = candidates[0]
    return roots


def _check_depth(row, depth_dir, originals):
    complete = depth_dir / "COMPLETE.json"
    manifest = depth_dir / "manifest.json"
    if not complete.is_file() or not manifest.is_file():
        raise PlanError("Depth COMPLETE or manifest missing: " + str(depth_dir))
    receipt = read_json(complete)
    info = read_json(manifest)
    if (info.get("status") != "COMPLETE"
            or receipt.get("export_digest") != info.get("export_digest")
            or receipt.get("schema") != "psm_wma_robocasa_rgbd_pose_v2"
            or info.get("schema") != receipt.get("schema")
            or receipt.get("manifest_sha256") != sha_file(manifest)):
        raise PlanError("Depth completion/provenance mismatch: " + str(depth_dir))
    identity = info.get("identity", {}).get("episode", {})
    keys = ("task_class", "local_episode_index", "global_episode_index", "length")
    if any(identity.get(k) != row.get(k) for k in keys) or info.get("frame_count") != row["length"]:
        raise PlanError("Depth episode mapping or frame count differs: " + str(depth_dir))
    sources = {Path(r["path"]).name: r for r in info["identity"]["source_files"]}
    for kind in ("states.npz", "model.xml.gz", "ep_meta.json"):
        expected = originals[kind]
        entry = sources.get(kind)
        if entry is None or Path(entry["path"]).resolve() != expected.resolve():
            raise PlanError("Depth source file identity differs: " + str(expected))
        if expected.stat().st_size != entry["size"]:
            raise PlanError("Depth source file size differs: " + str(expected))
    cameras = info.get("identity", {}).get("cameras", [])
    if "robot0_agentview_left" not in cameras:
        raise PlanError("Depth left camera missing: " + str(depth_dir))
    return {"manifest": str(manifest), "complete": str(complete),
            "export_digest": receipt["export_digest"]}


def discover(mapping=FLAT / "flat_v3_mapping.parquet", raw_root=RAW,
             depth_root=DEPTH, expected=EXPECTED, stride=10):
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise PlanError("pyarrow is required for flat V3 mapping") from error
    mapping = Path(mapping).resolve(strict=True)
    raw_root = Path(raw_root).resolve(strict=True)
    depth_root = Path(depth_root).resolve(strict=True)
    table = pq.read_table(mapping, columns=[
        "task_class", "local_episode_index", "global_episode_index", "length"])
    if table.num_rows != expected:
        raise PlanError(f"mapping has {table.num_rows} episodes, expected {expected}")
    raw_rows = table.to_pylist()
    tasks = sorted({r["task_class"] for r in raw_rows})
    roots = _lerobot_task_roots(raw_root, tasks)
    result = []
    counter = Counter()
    for global_id, row in enumerate(raw_rows):
        task, local, ep = row["task_class"], row["local_episode_index"], row["global_episode_index"]
        if (ep != global_id or type(ep) is not int or type(local) is not int
                or local < 0 or not task or "/" in task):
            raise PlanError(f"noncanonical global mapping at {global_id}")
        extra = roots[task] / "extras" / f"episode_{local:06d}"
        originals = {kind: extra / kind for kind in ("model.xml.gz", "states.npz", "ep_meta.json")}
        if any(not x.is_file() or x.stat().st_size <= 0 for x in originals.values()):
            raise PlanError("missing original official source: " + str(extra))
        meta = read_json(originals["ep_meta.json"])
        layout = meta.get("layout_id")
        if type(layout) is not int or layout not in LAYOUTS:
            raise PlanError(f"unsupported official layout_id for {ep}: {layout}")
        depth_dir = depth_root / "tasks" / task / "episodes" / f"episode_{ep:06d}"
        depth = _check_depth(row, depth_dir, originals)
        frames = frame_ids(row["length"], stride)
        result.append({
            "episode_id": ep, "task_class": task, "local_episode_index": local,
            "layout_id": layout, "source_frames": row["length"],
            "spatial_frames": frames, "spatial_state_count": len(frames),
            "original": {k: str(p) for k, p in originals.items()},
            "depth": depth,
            "expected_relative_output": f"tasks/{task}/episodes/episode_{ep:06d}",
            "upstream_scene_status": "REQUIRES_PER_EPISODE_FULL_MAP_BUILD",
            "training_ready": False,
        })
        counter[layout] += 1
    return result, counter


def manifest_for_batch(rows, batch_no, target_root):
    return {
        "schema": SCHEMA, "training_ready": False, "producer_only_manual_start": True,
        "batch_index": batch_no, "target_root": str(target_root),
        "output_schema": "g2_atomic_compact_6views_v1",
        "renderer": "f27",
        "source_mode": "full_map_mujoco_source",
        "occupancy_resolution_m": 0.1, "surface_resolution_m": 0.01,
        "view_resolution_mpp": 0.01, "source_fps": 20,
        "spatial_hz": 2, "island_four_views": True,
        "island_scope": "separate_from_room_wall_views",
        "save_native_voxels": False, "save_colored_cloud": False,
        "require_scene_graph": True, "episodes": rows,
    }


def build(mapping, raw_root, depth_root, plan_root, target_root, *, expected=EXPECTED, batch_size=100):
    if type(batch_size) is not int or not 1 <= batch_size <= MAX_BATCH:
        raise PlanError("batch_size must be in [1, 100]")
    rows, layouts = discover(mapping, raw_root, depth_root, expected=expected)
    target_root = Path(target_root).resolve()
    plan_root = Path(plan_root).absolute()
    if plan_root.exists():
        raise PlanError("plan_root already exists; immutable plans cannot be overwritten")
    if (plan_root == target_root or target_root in plan_root.parents
            or plan_root in target_root.parents):
        raise PlanError("keep pre-production plan outside the production output tree")
    if any(plan_root == source or source in plan_root.parents
           for source in (Path(raw_root).resolve(), Path(depth_root).resolve(), Path(mapping).resolve().parent)):
        raise PlanError("plan_root may not overlap protected inputs")
    plan_root.mkdir(parents=True)
    batches = []
    for begin in range(0, len(rows), batch_size):
        num = begin // batch_size
        name = f"batch_{num:03d}.json"
        pack = manifest_for_batch(rows[begin:begin + batch_size], num, target_root)
        write_json(plan_root / name, pack)
        batches.append({"path": name, "episode_count": len(pack["episodes"]),
                        "first_id": pack["episodes"][0]["episode_id"],
                        "last_id": pack["episodes"][-1]["episode_id"],
                        "sha256": sha_file(plan_root / name)})
    summary = {
        "schema": SCHEMA, "target_root": str(target_root),
        "mapping": str(Path(mapping).resolve()), "mapping_sha256": sha_file(mapping),
        "raw_root": str(Path(raw_root).resolve()),
        "depth_root": str(Path(depth_root).resolve()),
        "episodes_total": len(rows), "batches_total": len(batches),
        "layout_counts": {str(k): layouts[k] for k in sorted(layouts)},
        "spatial_state_total": sum(r["spatial_state_count"] for r in rows),
        "island_four_views": True, "renderer": "f27",
        "training_ready": False, "ready_for_direct_batch_render": False,
        "requires_per_episode_source_preparation": True,
        "production_started": False,
        "batches": batches,
    }
    write_json(plan_root / "index.json", summary)
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["scan", "plan"])
    p.add_argument("--mapping", type=Path, default=FLAT / "flat_v3_mapping.parquet")
    p.add_argument("--raw-root", type=Path, default=RAW)
    p.add_argument("--depth-root", type=Path, default=DEPTH)
    p.add_argument("--target-root", type=Path, default=OUTPUT)
    p.add_argument("--plan-root", type=Path)
    p.add_argument("--batch-size", type=int, default=100)
    p.add_argument("--expected", type=int, default=EXPECTED)
    args = p.parse_args(argv)
    if args.action == "scan":
        rows, layouts = discover(args.mapping, args.raw_root, args.depth_root,
                                 expected=args.expected)
        output = {"episodes": len(rows), "layouts": dict(layouts),
                  "spatial_states": sum(x["spatial_state_count"] for x in rows),
                  "target_root": str(args.target_root), "production_started": False}
    else:
        if args.plan_root is None:
            p.error("--plan-root required for plan")
        output = build(args.mapping, args.raw_root, args.depth_root,
                       args.plan_root, args.target_root,
                       expected=args.expected, batch_size=args.batch_size)
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
