"""Explicitly started, resumable full RoboCasa DATA_B-only 20Hz state15 producer.

No G2 View/Png/SG/VAE production or model training in this process. The owner
must invoke --all to process the corpus; --max-episodes can bound a gate.
One foreground process, minimal CPU and disk; never starts other workers.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from g2.data.episode_state import (
    VerifiedRawEpisodes,
    atomic_write_json,
    digest,
    json_load,
    write_episode_state,
)
from g2.data.pose5 import Pose5Recipe


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--g1-verified-index", required=True, type=Path)
    parser.add_argument("--g1-cache-root", required=True, type=Path)
    parser.add_argument("--data-b-root", required=True, type=Path)
    parser.add_argument(
        "--all", action="store_true", help="acknowledge full-corpus build"
    )
    parser.add_argument("--max-episodes", type=int, default=None)
    parser.add_argument("--stop-file", type=Path, default=None)
    parser.add_argument("--flush-every", type=int, default=100)
    args = parser.parse_args(argv)
    if not args.all and args.max_episodes is None:
        parser.error("explicit --all or bounded --max-episodes is required")
    if args.max_episodes is not None and args.max_episodes <= 0:
        parser.error("--max-episodes must be positive")
    if args.flush_every <= 0:
        parser.error("--flush-every must be positive")
    raw = VerifiedRawEpisodes(
        args.source_root, args.g1_verified_index, args.g1_cache_root
    )
    recipe = Pose5Recipe()
    all_keys = sorted(raw.by_episode.items(), key=lambda x: x[0])
    if len(all_keys) != 9126:
        raise ValueError(
            "current RoboCasa target-atomic corpus must have exactly 9126 episodes"
        )
    selection = all_keys if args.max_episodes is None else all_keys[: args.max_episodes]
    args.data_b_root.mkdir(parents=True, exist_ok=True)
    existing_manifest = args.data_b_root / "manifest.json"
    completed = {}
    if existing_manifest.exists():
        previous = json_load(existing_manifest)
        if (
            previous.get("source_binding_digest") != raw.source_binding
            or previous.get("pose5_recipe_id") != recipe.recipe_id
        ):
            raise ValueError(
                "DATA_B root manifest incompatible with current G1/pose recipe"
            )
        completed = {
            (e["task_class"], e["episode_index"]): e for e in previous["episodes"]
        }
    failure = []
    started = time.monotonic()
    processed = 0

    def flush():
        total = sum(r["frames"] for r in completed.values())
        atomic_write_json(
            existing_manifest,
            {
                "schema": "g2_data_b_scoped_corpus_v1",
                "source_binding_digest": raw.source_binding,
                "source_root": str(args.source_root),
                "pose5_recipe_id": recipe.recipe_id,
                "episodes": [completed[k] for k in sorted(completed)],
                "training_ready": False,
            },
        )
        atomic_write_json(
            args.data_b_root / "PROGRESS.json",
            {
                "schema": "g2_data_b_production_progress_v1",
                "source_episode_count": len(all_keys),
                "requested_episode_count": len(selection),
                "completed_episode_count": len(completed),
                "completed_source_frames": total,
                "failed": failure,
                "elapsed_seconds": round(time.monotonic() - started, 2),
                "training_ready": False,
            },
        )

    for ep, record in selection:
        if args.stop_file is not None and args.stop_file.exists():
            print("DATA_B_SAFE_STOP_REQUESTED", args.stop_file, flush=True)
            break
        task = record["task_class"]
        try:
            src = raw.read(task, ep)
            r = write_episode_state(args.data_b_root, src, recipe=recipe, resume=True)
            x = {
                "task_class": task,
                "episode_index": ep,
                "frames": r["frame_count"],
                "sha256": r["state15_sha256"],
            }
            key = (task, ep)
            if key in completed and completed[key] != x:
                raise ValueError("DATA_B manifest episode changed during resume")
            completed[key] = x
        except Exception as exc:
            failure.append(
                {
                    "task_class": task,
                    "episode_index": ep,
                    "error": f"{type(exc).__name__}: {exc}"[:320],
                }
            )
            print(
                f"DATA_B_EPISODE_FAILED task={task} episode={ep} reason={exc}",
                flush=True,
            )
        processed += 1
        if processed % args.flush_every == 0 or processed == len(selection):
            flush()
            print(
                "DATA_B_PROGRESS",
                processed,
                "/",
                len(selection),
                "complete",
                len(completed),
                "failed",
                len(failure),
                "elapsed_s",
                round(time.monotonic() - started, 2),
                flush=True,
            )
    flush()
    all_done = (
        len(completed) == len(all_keys)
        and not failure
        and (args.stop_file is None or not args.stop_file.exists())
    )
    if all_done:
        atomic_write_json(
            args.data_b_root / "CORPUS_COMPLETE.json",
            {
                "schema": "g2_data_b_corpus_complete_v1",
                "complete": True,
                "source_episode_count": len(all_keys),
                "manifest_sha256": digest(existing_manifest),
                "recipe_id": recipe.recipe_id,
                "training_ready": False,
            },
        )
    print(
        "DATA_B_EXECUTION",
        json.dumps(
            {
                "requested": len(selection),
                "processed": processed,
                "completed": len(completed),
                "errors": len(failure),
                "source_corpus_complete": all_done,
                "training_ready": False,
            }
        ),
        flush=True,
    )
    if failure:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
