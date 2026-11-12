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
EXPECTED = None  # open-source datasets need not have the same number of episodes
MAX_BATCH = 100


class PlanError(ValueError):
    pass


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def selection_fingerprint(row, originals_sha256, depth_digest, frames):
    """Pinned per-episode source and rendering recipe, not a filesystem path."""
    identity = {
        "schema": "g2_atomic_6views_source_selection_v1",
        "episode_id": row["global_episode_index"],
        "task_class": row["task_class"],
        "local_episode_index": row["local_episode_index"],
        "layout_id": row["layout_id"],
        "source_frames": row["length"],
        "spatial_frames": frames,
        "original_sha256": originals_sha256,
        "depth_export_digest": depth_digest,
        "renderer": "f27",
        "source_fps": 20,
        "spatial_stride": 10,
        "occupancy_resolution_m": 0.1,
        "surface_resolution_m": 0.01,
        "view_resolution_mpp": 0.01,
        "island_four_views": True,
    }
    return hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def normalize_tasks(tasks):
    """None/empty => all. Repeat --task or comma-separate values."""
    if tasks is None or tasks == []:
        return None
    if isinstance(tasks, str):
        tasks = [tasks]
    if not isinstance(tasks, (list, tuple)) or not tasks:
        raise PlanError("invalid task selection")
    names = []
    for arg in tasks:
        if not isinstance(arg, str):
            raise PlanError("task names must be text")
        names.extend(chunk.strip() for chunk in arg.split(","))
    if any(not x or "/" in x or "\\\\" in x for x in names) or len(names) != len(set(names)):
        raise PlanError("empty, duplicate or unsafe task selection")
    return set(names)


def select(rows, *, tasks=None, episodes_per_task=None):
    """Stable first N global IDs per selected task. N=None => all."""
    names = normalize_tasks(tasks)
    if episodes_per_task is not None and (
            type(episodes_per_task) is not int or episodes_per_task <= 0):
        raise PlanError("--episodes-per-task must be a positive integer or omitted (all)")
    available = {row["task_class"] for row in rows}
    if names is not None and names - available:
        raise PlanError("unknown task(s): " + ", ".join(sorted(names - available)))
    taken = Counter()
    chosen = []
    for row in sorted(rows, key=lambda x: x["episode_id"]):
        task = row["task_class"]
        if names is not None and task not in names:
            continue
        if episodes_per_task is not None and taken[task] >= episodes_per_task:
            continue
        taken[task] += 1
        chosen.append(row)
    return chosen, dict(sorted(taken.items()))


def selection_sha256(rows):
    """Order-independent immutable selection and episode source recipe."""
    entries = sorted((r["episode_id"], r["source_fingerprint"]) for r in rows)
    return hashlib.sha256(json.dumps(
        entries, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def reuse_pinned_plan(plan_root, *, selection, mapping_sha, target_root,
                      pending, skipped, episodes_per_task, counts):
    """Resume the exact existing immutable plan; do not rewrite batch manifests."""
    index_path = plan_root / "index.json"
    if not index_path.is_file() or index_path.is_symlink():
        raise PlanError("existing plan has no immutable index")
    index = read_json(index_path)
    if (
        index.get("schema") != SCHEMA
        or index.get("target_root") != str(target_root)
        or index.get("mapping_sha256") != mapping_sha
        or index.get("selection_sha256") != selection_sha256(selection)
        or index.get("episodes_per_task") != episodes_per_task
        or index.get("task_episode_counts") != counts
        or index.get("renderer") != "f27"
        or index.get("training_ready") is not False
    ):
        raise PlanError("existing plan selection or source recipe changed")
    known = {r["episode_id"] for r in selection}
    visited = set()
    for record in index.get("batches", []):
        name = record.get("path")
        if (type(name) is not str or not name.startswith("batch_")
                or not name.endswith(".json") or "/" in name):
            raise PlanError("invalid pinned batch filename")
        path = plan_root / name
        if not path.is_file() or path.is_symlink() or sha_file(path) != record.get("sha256"):
            raise PlanError("pinned batch file changed: " + str(path))
        data = read_json(path)
        if (data.get("schema") != SCHEMA or data.get("target_root") != str(target_root)
                or data.get("renderer") != "f27"
                or data.get("training_ready") is not False
                or not isinstance(data.get("episodes"), list)
                or record.get("episode_count") != len(data["episodes"])):
            raise PlanError("existing plan batch schema or size changed")
        for row in data["episodes"]:
            eid = row.get("episode_id")
            if eid not in known or eid in visited:
                raise PlanError("existing plan contains duplicate/foreign episode")
            visited.add(eid)
    current_completed = set(skipped)
    if (not visited <= known
            or visited != (known - set(index.get("skipped_completed_ids", [])))
            or any(eid not in known for eid in current_completed)):
        raise PlanError("existing batch selection differs from original plan")
    return {
        **index,
        "resume": True,
        "plan_reused": True,
        "episodes_skipped_completed_now": len(skipped),
        "episodes_pending_now": len(pending),
        "previously_pinned_batches_unchanged": True,
    }


def completed_output(row, target_root):
    """Check only the small completion marker and manifest, not every PNG.

    A visible destination with incomplete or mismatched identity is a conflict;
    never silently mark it DONE and never delete user data.
    """
    final = Path(target_root) / row["expected_relative_output"]
    if not final.exists() and not final.is_symlink():
        return False
    if final.is_symlink() or not final.is_dir():
        raise PlanError("invalid existing episode output: " + str(final))
    complete = final / "COMPLETE.json"
    manifest = final / "episode_manifest.json"
    if (not complete.is_file() or not manifest.is_file()
            or complete.is_symlink() or manifest.is_symlink()):
        raise PlanError("incomplete output conflicts with resume: " + str(final))
    marker = read_json(complete)
    data = read_json(manifest)
    expected_frames = row["spatial_frames"]
    actual_states = data.get("states")
    if (
        marker.get("schema") != "g2_atomic_compact_6views_v1"
        or data.get("schema") != marker["schema"]
        or marker.get("complete") is not True
        or data.get("complete") is not True
        or marker.get("training_ready") is not False
        or data.get("training_ready") is not False
        or marker.get("renderer") != "f27"
        or data.get("source_renderer") != "f27"
        or data.get("island_four_views_enabled") is not True
        or marker.get("episode_id") != row["episode_id"]
        or data.get("episode_id") != row["episode_id"]
        or data.get("task_class") != row["task_class"]
        or marker.get("state_count") != len(expected_frames)
        or data.get("state_count") != len(expected_frames)
        or marker.get("source_fingerprint") != row["source_fingerprint"]
        or data.get("source_fingerprint") != row["source_fingerprint"]
        or marker.get("episode_manifest_sha256") != sha_file(manifest)
        or not isinstance(actual_states, list)
        or [x.get("frame") for x in actual_states if isinstance(x, dict)] != expected_frames
    ):
        raise PlanError("existing episode output identity/recipe differs: " + str(final))
    return True


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
            "export_digest": receipt["export_digest"],
            "original_sha256": {kind: sources[kind]["sha256"]
                                for kind in ("states.npz", "model.xml.gz", "ep_meta.json")}}



def discover(mapping=FLAT / "flat_v3_mapping.parquet", raw_root=RAW,
             depth_root=DEPTH, expected=EXPECTED, stride=10, *,
             require_depth=False, log=print):
    from .atomic_6views_catalog import CatalogError, discover_flat
    raw_root = Path(raw_root).resolve(strict=True)
    mapping = Path(mapping)
    if not mapping.is_file() and expected is not None:
        # The count is checked below, never used as a fallback identity.
        pass
    try:
        raw_rows, roots, catalog_origin = discover_flat(mapping, raw_root, log=log)
    except CatalogError as error:
        raise PlanError(str(error)) from error
    if expected is not None and len(raw_rows) != expected:
        raise PlanError(f"mapping has {len(raw_rows)} episodes, expected {expected}")
    depth_root = Path(depth_root)
    has_depth = depth_root.is_dir()
    if require_depth and not has_depth:
        raise PlanError("required depth root is missing: " + str(depth_root))
    if log is not None:
        log(f"G2_SOURCE_INDEX source={catalog_origin} depth_available={has_depth} "
            f"require_depth={require_depth}", flush=True)
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
        if type(layout) is not int or layout <= 0:
            raise PlanError(f"invalid official layout_id for {ep}: {layout}")
        depth_dir = depth_root / "tasks" / task / "episodes" / f"episode_{ep:06d}"
        if has_depth and (depth_dir / "COMPLETE.json").is_file():
            depth = _check_depth(row, depth_dir, originals)
        elif require_depth:
            raise PlanError("required episode depth absent: " + str(depth_dir))
        else:
            depth = None  # full-map MuJoCo does not require previously exported RGB-D.
        frames = frame_ids(row["length"], stride)
        row_for_digest = {**row, "layout_id": layout}
        provenance = (depth["original_sha256"] if depth is not None else
                      {kind: sha_file(path) for kind, path in originals.items()})
        fingerprint = selection_fingerprint(
            row_for_digest, provenance,
            depth["export_digest"] if depth is not None else None, frames)
        result.append({
            "episode_id": ep, "task_class": task, "local_episode_index": local,
            "layout_id": layout, "source_frames": row["length"],
            "spatial_frames": frames, "spatial_state_count": len(frames),
            "original": {k: str(p) for k, p in originals.items()},
            "depth": depth,
            "source_fingerprint": fingerprint,
            "expected_relative_output": f"tasks/{task}/episodes/episode_{ep:06d}",
            "upstream_scene_status": "REQUIRES_PER_EPISODE_FULL_MAP_BUILD",
            "training_ready": False,
        })
        counter[layout] += 1
    if log is not None:
        log(f"G2_SOURCE_INDEX_COMPLETE episodes={len(result)} "
            f"layouts={len(counter)}", flush=True)
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


def build(mapping, raw_root, depth_root, plan_root, target_root, *,
          expected=EXPECTED, batch_size=100, tasks=None,
          episodes_per_task=None, resume=False, require_depth=False):
    if type(batch_size) is not int or not 1 <= batch_size <= MAX_BATCH:
        raise PlanError("batch_size must be in [1, 100]")
    if type(resume) is not bool:
        raise PlanError("resume must be boolean")
    rows, layouts = discover(mapping, raw_root, depth_root,
                              expected=expected, require_depth=require_depth)
    chosen, counts = select(rows, tasks=tasks, episodes_per_task=episodes_per_task)
    target_root = Path(target_root).resolve()
    skipped = []
    pending = []
    for row in chosen:
        if completed_output(row, target_root):
            if not resume:
                raise PlanError("existing complete episode requires explicit --resume: " +
                                row["expected_relative_output"])
            skipped.append(row["episode_id"])
        else:
            pending.append(row)

    plan_root = Path(plan_root).absolute()
    if plan_root.exists() and not resume:
        raise PlanError("plan_root already exists; use --resume to reuse the pinned plan")
    if (plan_root == target_root or target_root in plan_root.parents
            or plan_root in target_root.parents):
        raise PlanError("keep pre-production plan outside the production output tree")
    protected = [Path(raw_root).resolve()]
    if Path(depth_root).exists():
        protected.append(Path(depth_root).resolve())
    if Path(mapping).is_file():
        protected.append(Path(mapping).resolve().parent)
    if any(plan_root == source or source in plan_root.parents
           for source in protected):
        raise PlanError("plan_root may not overlap protected inputs")
    # The source index is re-derived from official metadata if no flat cache exists.
    # A missing flat parquet is an expected open-source dataset state.
    mapping_sha = (sha_file(mapping) if Path(mapping).is_file()
                   else selection_sha256(rows))
    if plan_root.exists():
        if not plan_root.is_dir() or plan_root.is_symlink():
            raise PlanError("invalid existing plan_root")
        return reuse_pinned_plan(
            plan_root, selection=chosen, mapping_sha=mapping_sha,
            target_root=target_root, pending=pending, skipped=skipped,
            episodes_per_task=episodes_per_task, counts=counts)
    plan_root.mkdir(parents=True)
    batches = []
    for begin in range(0, len(pending), batch_size):
        num = begin // batch_size
        name = f"batch_{num:03d}.json"
        pack = manifest_for_batch(pending[begin:begin + batch_size], num, target_root)
        write_json(plan_root / name, pack)
        batches.append({"path": name, "episode_count": len(pack["episodes"]),
                        "first_id": pack["episodes"][0]["episode_id"],
                        "last_id": pack["episodes"][-1]["episode_id"],
                        "sha256": sha_file(plan_root / name)})
    summary = {
        "schema": SCHEMA, "target_root": str(target_root),
        "mapping": str(Path(mapping).absolute()) if Path(mapping).is_file() else None,
        "mapping_source": "flat_v3_mapping.parquet" if Path(mapping).is_file()
                          else "official_episodes_jsonl",
        "mapping_sha256": mapping_sha,
        "selection_sha256": selection_sha256(chosen),
        "raw_root": str(Path(raw_root).resolve()),
        "depth_root": str(Path(depth_root).resolve()),
        "dataset_episodes_total": len(rows),
        "episodes_total": len(chosen),
        "episodes_pending": len(pending),
        "episodes_skipped_completed": len(skipped),
        "skipped_completed_ids": skipped,
        "task_episode_counts": counts,
        "tasks_selected": sorted(counts),
        "episodes_per_task": episodes_per_task,
        "resume": resume,
        "batches_total": len(batches),
        "layout_counts": {str(k): layouts[k] for k in sorted(layouts)},
        "spatial_state_total": sum(r["spatial_state_count"] for r in chosen),
        "spatial_state_pending": sum(r["spatial_state_count"] for r in pending),
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
    p.add_argument("--expected", type=int, default=EXPECTED,
                   help="optional expected total episode count (default: accept any dataset size)")
    p.add_argument("--require-depth", action="store_true",
                   help="only for RGB-D experiments; Full Map can build without Depth")
    p.add_argument("--task", action="append", default=[],
                   help="task name; repeat or comma-separate (default: all tasks)")
    p.add_argument("--episodes-per-task", type=int, default=None,
                   help="maximum first episodes per chosen task (default: ALL)")
    p.add_argument("--resume", action="store_true",
                   help="skip only completed, recipe-matching episodes in the fixed selection")
    args = p.parse_args(argv)
    if args.action == "scan":
        rows, layouts = discover(args.mapping, args.raw_root, args.depth_root,
                                 expected=args.expected,
                                 require_depth=args.require_depth)
        chosen, counts = select(rows, tasks=args.task,
                                episodes_per_task=args.episodes_per_task)
        skipped = [r["episode_id"] for r in chosen
                   if completed_output(r, args.target_root)]
        if skipped and not args.resume:
            raise PlanError("some selected outputs exist; use --resume")
        output = {"dataset_episodes": len(rows), "episodes": len(chosen),
                  "episodes_pending": len(chosen) - len(skipped),
                  "episodes_skipped_completed": len(skipped),
                  "task_episode_counts": counts,
                  "episodes_per_task": args.episodes_per_task,
                  "resume": args.resume, "layouts": dict(layouts),
                  "spatial_states": sum(x["spatial_state_count"] for x in chosen),
                  "target_root": str(args.target_root), "production_started": False}
    else:
        if args.plan_root is None:
            p.error("--plan-root required for plan")
        output = build(args.mapping, args.raw_root, args.depth_root,
                       args.plan_root, args.target_root,
                       expected=args.expected, batch_size=args.batch_size,
                       tasks=args.task, episodes_per_task=args.episodes_per_task,
                       resume=args.resume, require_depth=args.require_depth)
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
