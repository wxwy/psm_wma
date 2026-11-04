"""Export original RGB references, metric Depth and camera Pose by episode.

Run from the Root checkout: python -m tools.g2.export_robocasa_rgbd_pose --help
Real replay is server-side only. --dry-run loads mapping/nonvisual source rows,
but never imports RoboCasa/MuJoCo or creates a renderer.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from .rgbd_pose import SCHEMA
from .rgbd_pose.cache import durable_json, ensure_cache_manifest, export_episode
from .rgbd_pose.geometry import CONVENTIONS, DEPTH_FORMATS
from .rgbd_pose.replay import Replay
from .rgbd_pose.source import (
    CAMERAS,
    digest,
    integer,
    load_episode,
    mapping_episodes,
    select,
    sha256,
    verify_selection_source,
    witness,
)


def code_identity():
    directory = Path(__file__).resolve().parent
    files = [
        directory / "export_robocasa_rgbd_pose.py",
        *sorted((directory / "rgbd_pose").glob("*.py")),
        directory.parent / "g0/robocasa_work_queue.py",
    ]
    return {p.relative_to(directory.parent.parent).as_posix(): sha256(p) for p in files}


def provenance():
    root = Path(__file__).resolve().parents[2]
    values = {}
    for name, ref in [("root", "HEAD"), ("child_gitlink", "HEAD:cosmos-framework")]:
        result = subprocess.run(
            ["git", "rev-parse", ref], cwd=root, capture_output=True, text=True
        )
        values[name] = result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
    return values


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--raw-root", type=Path, required=True)
    result.add_argument("--flat-root", type=Path, required=True)
    result.add_argument("--output-root", type=Path, required=True)
    result.add_argument("--mapping-file", type=Path)
    result.add_argument(
        "--source-dataset",
        type=Path,
        help="explicit original lerobot directory when Task has multiple datasets",
    )
    choice = result.add_mutually_exclusive_group(required=True)
    choice.add_argument(
        "--selection-manifest",
        type=Path,
        help="existing g0 accepted cache manifest or explicit global-ID manifest",
    )
    choice.add_argument("--global-episode", type=int)
    choice.add_argument("--local-episode", type=int)
    result.add_argument("--task-class")
    result.add_argument("--cameras", default="robot0_agentview_left,robot0_eye_in_hand")
    result.add_argument(
        "--state-index-policy",
        required=True,
        choices=["frame_index"],
        help="explicit assertion to be physically verified by DS; never inferred from timestamps",
    )
    result.add_argument("--depth-format", choices=DEPTH_FORMATS, default="uint16_mm")
    result.add_argument(
        "--frames",
        help="comma-separated frame indices; omitted exports the full mapped episode",
    )
    result.add_argument(
        "--image-size",
        type=int,
        help="optional assertion of original square RGB size; never resizes source RGB",
    )
    result.add_argument("--chunk-frames", type=int, default=32)
    result.add_argument(
        "--min-free-bytes",
        type=int,
        default=1024**3,
        help="disk reserve checked before replay and each chunk",
    )
    for label in ["task", "episode"]:
        result.add_argument(f"--{label}-shard", type=int)
        result.add_argument(f"--num-{label}-shards", type=int)
    result.add_argument("--dry-run", action="store_true")
    return result


def main(argv=None, *, replay_factory=Replay):
    args = parser().parse_args(argv)
    root, raw, flat = (
        p.resolve() for p in (args.output_root, args.raw_root, args.flat_root)
    )
    if any(root.is_relative_to(p) or p.is_relative_to(root) for p in (raw, flat)):
        raise ValueError("output-root must be separate from raw/Flat source trees")
    cameras = args.cameras.split(",")
    if not cameras or len(set(cameras)) != len(cameras) or set(cameras) - set(CAMERAS):
        raise ValueError("unsupported/duplicate camera list")
    integer(args.chunk_frames, "chunk_frames", minimum=1)
    integer(args.min_free_bytes, "min_free_bytes")
    if args.chunk_frames > 256:
        raise ValueError("chunk_frames must not exceed 256")
    requested_frames = (
        None if args.frames is None else [int(v) for v in args.frames.split(",")]
    )
    if requested_frames is not None and (
        not requested_frames or requested_frames != sorted(set(requested_frames))
    ):
        raise ValueError("--frames must be a sorted unique nonempty list")
    for name in ["global_episode", "local_episode", "image_size"]:
        if getattr(args, name) is not None:
            integer(getattr(args, name), name, minimum=1 if name == "image_size" else 0)
    mapping = (args.mapping_file or flat / "flat_v3_mapping.parquet").resolve()
    mapping_proof = witness(mapping)
    if args.selection_manifest is not None:
        verify_selection_source(args.selection_manifest, flat, mapping_proof["sha256"])
    episodes, selection_proof = select(
        mapping_episodes(mapping),
        manifest=args.selection_manifest,
        task=args.task_class,
        global_episode=args.global_episode,
        local_episode=args.local_episode,
        task_shard=args.task_shard,
        num_task_shards=args.num_task_shards,
        episode_shard=args.episode_shard,
        num_episode_shards=args.num_episode_shards,
    )
    frame_plan = {}
    for episode in episodes:
        frames = (
            list(range(episode.length))
            if requested_frames is None
            else requested_frames
        )
        for frame in frames:
            episode.frame(frame)
        frame_plan[episode.global_episode_index] = frames
    recipe = {"mapping": mapping_proof, "code": code_identity()}
    contract = {
        "schema": SCHEMA,
        "raw_root": str(raw),
        "flat_root": str(flat),
        "recipe": recipe,
        "cameras": cameras,
        "frames": requested_frames,
        "state_index_policy": args.state_index_policy,
        "depth_format": args.depth_format,
        "chunk_frames": args.chunk_frames,
        "image_size": args.image_size,
        "conventions": CONVENTIONS,
    }
    started = time.monotonic()
    if not args.dry_run:
        ensure_cache_manifest(root, contract)
    results, estimated_bytes = [], 0
    for episode in episodes:
        frames = frame_plan[episode.global_episode_index]
        try:
            source = load_episode(
                raw,
                flat,
                episode,
                cameras,
                state_index_policy=args.state_index_policy,
                source_dataset=args.source_dataset,
                image_size=args.image_size,
            )
            estimated_bytes += sum(
                len(frames)
                * (h * w * (3 if args.depth_format == "uint16_mm" else 5) + 41 * 4 + 8)
                for h, w in source.camera_shapes.values()
            )
            if args.dry_run:
                value = {
                    "status": "PLANNED_NONVISUAL_ALIGNMENT_VERIFIED",
                    "frame_count": len(frames),
                    "camera_shapes": {
                        k: list(v) for k, v in source.camera_shapes.items()
                    },
                }
            else:
                value = export_episode(
                    root,
                    source,
                    frames,
                    storage=args.depth_format,
                    chunk_frames=args.chunk_frames,
                    recipe=recipe,
                    replay_factory=replay_factory,
                    min_free_bytes=args.min_free_bytes,
                )
            value["episode"] = asdict(episode)
            results.append(value)
            if not args.dry_run:
                print(json.dumps({"g2_episode": value}, ensure_ascii=False), flush=True)
        except Exception as exc:
            value = {
                "status": "FAILED",
                "episode": asdict(episode),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            results.append(value)
            if not args.dry_run:
                print(json.dumps({"g2_episode": value}, ensure_ascii=False), flush=True)
    failed = sum(r["status"] == "FAILED" for r in results)
    report = {
        "schema": SCHEMA,
        "mode": "dry_run" if args.dry_run else "export",
        "status": "FAILED"
        if failed
        else "COMPLETED_EXPORT_NOT_PHYSICAL_GATE_ACCEPTANCE",
        "selected_episode_count": len(episodes),
        "selected_frame_count": sum(map(len, frame_plan.values())),
        "completed_frame_count": sum(r.get("frame_count", 0) for r in results),
        "failed_episode_count": failed,
        "uncompressed_array_bytes_estimate": estimated_bytes,
        "compression_estimate": "NOT_ASSUMED_measure_actual_episode_manifests",
        "selection_manifest": selection_proof,
        "selection_policy": "existing_manifest_or_explicit_ID_no_sampling",
        "state_index_policy": "frame_index_explicit_pending_DS_physical_validation",
        "contract_digest": digest(contract),
        "code_provenance": provenance(),
        "duration_s": time.monotonic() - started,
        "episodes": results,
        "geometry_gate": "PENDING_DS_GATE_B_C",
        "min_free_bytes": args.min_free_bytes,
    }
    if not args.dry_run:
        durable_json(root / "_runs" / f"{uuid.uuid4().hex}.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
