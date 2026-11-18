"""Incremental G2 DATA_C: consume only already-complete independent ViewVAE.

Never invokes a producer or changes original View/SG/Wan/cache or DATA_B files.
The DATA_B full-corpus CPU writer may safely run concurrently; this tool only
reads already published B COMPLETE files and writes exclusively DATA_C.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from g2.data.episode_state import (
    VerifiedRawEpisodes,
    atomic_write_json,
    canonical,
    digest,
    json_load,
)
from g2.data.joint_index import build_episode_joint, make_joint_recipe
from g2.data.pose5 import Pose5Recipe


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in (
        "source-root",
        "g1-verified-index",
        "g1-cache-root",
        "views-root",
        "data-b-root",
        "data-c-root",
    ):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--view-vae-recipe-id", required=True)
    p.add_argument(
        "--top-view-variant", choices=("with_robot", "without_robot"), required=True
    )
    p.add_argument("--max-episodes", type=int, default=None)
    p.add_argument("--flush-every", type=int, default=20)
    p.add_argument("--stop-file", type=Path, default=None)
    args = p.parse_args(argv)
    if args.max_episodes is not None and args.max_episodes <= 0:
        p.error("--max-episodes must be positive")
    if args.flush_every <= 0:
        p.error("--flush-every must be positive")
    start = time.monotonic()
    raw = VerifiedRawEpisodes(
        args.source_root, args.g1_verified_index, args.g1_cache_root
    )
    pose = Pose5Recipe()
    root = args.data_c_root
    root.mkdir(parents=True, exist_ok=True)
    current = root / "manifest.json"
    expected = dict(
        schema="g2_data_c_corpus_v1",
        source_binding_digest=raw.source_binding,
        state15_recipe_id=pose.recipe_id,
        view_recipe_id=args.view_vae_recipe_id,
        recipe_id=canonical(
            make_joint_recipe(
                state_recipe_id=pose.recipe_id,
                view_recipe_id=args.view_vae_recipe_id,
                top_variant=args.top_view_variant,
            )
        ),
        top_view_variant=args.top_view_variant,
        alignment_version="g2_causal_latest_spatial_v1",
        split_identity="SCOPED_EPISODES_SPLIT_NOT_FROZEN",
        training_ready=False,
        evidence_scope="candidate_causal_20hz_view_gt_not_formal",
    )
    completed = {}
    if current.exists():
        old = json_load(current)
        for k, v in expected.items():
            if k == "recipe_id" and k not in old:
                continue  # legacy corpus omission: verify *all* episode recipes below
            if old.get(k) != v:
                raise ValueError(f"existing DATA_C corpus incompatible {k}")
        for e in old["episodes"]:
            if "recipe_id" not in old:
                from g2.data.episode_state import episode_path

                episode = episode_path(
                    args.data_c_root, e["task_class"], e["episode_index"]
                )
                current_joint = json_load(episode / "joint_index.json")
                if (
                    current_joint.get("recipe_id") != expected["recipe_id"]
                    or current_joint.get("recipe_id")
                    != canonical(current_joint["recipe"])
                    or digest(episode / "joint_index.json") != e["joint_sha256"]
                ):
                    raise ValueError("legacy DATA_C episode recipe/source disagrees")
            completed[(e["task_class"], e["episode_index"])] = e
    ready = []
    for marker in sorted(
        args.views_root.glob("tasks/*/episodes/episode_*/vae_cache/COMPLETE.json")
    ):
        try:
            x = json_load(marker)
            epdir = marker.parent.parent
            ep = int(epdir.name.split("_")[-1])
            task = marker.parents[3].name
            if (
                x["complete"] is not True
                or x["recipe_id"] != args.view_vae_recipe_id
                or not (epdir / "COMPLETE.json").is_file()
                or not (
                    args.data_b_root
                    / "tasks"
                    / task
                    / "episodes"
                    / epdir.name
                    / "COMPLETE.json"
                ).is_file()
            ):
                continue
            # Source exact task and episode identity are checked during actual read.
            ready.append((task, ep))
        except (KeyError, ValueError, TypeError):
            continue
    ready = sorted(set(ready), key=lambda q: (q[0], q[1]))
    if args.max_episodes is not None:
        ready = ready[: args.max_episodes]
    if not ready:
        raise ValueError("no fully published ViewVAE + DATA_B candidate episodes")
    errors = []
    processed = 0

    def flush():
        body = dict(expected)
        body["episodes"] = [completed[k] for k in sorted(completed)]
        body["data_identity"] = canonical(body)
        atomic_write_json(current, body)
        atomic_write_json(
            root / "CORPUS_COMPLETE.json",
            {
                "schema": "g2_data_c_corpus_complete_v1",
                "complete": True,
                "manifest_sha256": digest(current),
                "episode_count": len(body["episodes"]),
                "window_count": sum(x["window_count"] for x in body["episodes"]),
                "training_ready": False,
            },
        )
        atomic_write_json(
            root / "PROGRESS.json",
            {
                "schema": "g2_data_c_incremental_progress_v1",
                "ready_episodes_at_snapshot": len(ready),
                "processed_episodes_in_run": processed,
                "indexed_episodes": len(completed),
                "indexed_legal_windows": sum(
                    x["window_count"] for x in completed.values()
                ),
                "failures": errors,
                "elapsed_seconds": round(time.monotonic() - start, 2),
                "training_ready": False,
            },
        )

    for task, ep in ready:
        if args.stop_file is not None and args.stop_file.exists():
            print("DATA_C_SAFE_STOP_REQUESTED", args.stop_file, flush=True)
            break
        try:
            s = raw.read(task, ep)
            r = build_episode_joint(
                task_class=task,
                episode_index=ep,
                raw_source=s,
                state15_root=args.data_b_root,
                view_root=args.views_root,
                data_c_root=args.data_c_root,
                state_recipe_id=pose.recipe_id,
                view_recipe_id=args.view_vae_recipe_id,
                top_variant=args.top_view_variant,
            )
            item = {
                "task_class": task,
                "episode_index": ep,
                "joint_sha256": r["joint_sha256"],
                "window_count": r["window_count"],
            }
            key = task, ep
            if key in completed and completed[key] != item:
                raise ValueError("previous DATA_C episode digest changed")
            completed[key] = item
        except Exception as exc:
            errors.append(
                {
                    "task_class": task,
                    "episode_index": ep,
                    "error": f"{type(exc).__name__}: {exc}"[:300],
                }
            )
            print("DATA_C_EP_FAILED", task, ep, errors[-1]["error"], flush=True)
        processed += 1
        if processed % args.flush_every == 0 or processed == len(ready):
            flush()
            print(
                "DATA_C_PROGRESS",
                processed,
                "/",
                len(ready),
                "indexed",
                len(completed),
                "windows",
                sum(x["window_count"] for x in completed.values()),
                "errors",
                len(errors),
                "elapsed_s",
                round(time.monotonic() - start, 1),
                flush=True,
            )
    flush()
    print("DATA_C_RUN_COMPLETED", len(completed), "errors", len(errors), flush=True)
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
