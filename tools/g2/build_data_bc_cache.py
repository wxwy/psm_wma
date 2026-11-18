"""Explicit G2 DATA_B 20Hz episode state writer and candidate DATA_C index CLI.

No background work, no GPU, no ROS/MuJoCo, no WAN encoding, no model training.
Runs only owner-selected task/episode ids and never overwrites complete assets.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from g2.data.episode_state import (
    VerifiedRawEpisodes,
    atomic_write_json,
    canonical,
    digest,
    json_load,
)
from g2.data.episode_state import write_episode_state
from g2.data.joint_index import build_episode_joint
from g2.data.pose5 import Pose5Recipe


def args_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--g1-verified-index", type=Path, required=True)
    parser.add_argument("--g1-cache-root", type=Path, required=True)
    parser.add_argument("--views-root", type=Path, required=True)
    parser.add_argument("--data-b-root", type=Path, required=True)
    parser.add_argument("--data-c-root", type=Path, required=True)
    parser.add_argument("--task-class", required=True)
    parser.add_argument("--episodes", type=int, nargs="+", required=True)
    parser.add_argument("--view-vae-recipe-id", required=True)
    parser.add_argument(
        "--top-view-variant", choices=("with_robot", "without_robot"), required=True
    )
    parser.add_argument("--only-b", action="store_true")
    parser.add_argument("--fail-on-existing", action="store_true")
    return parser


def main(argv=None):
    args = args_parser().parse_args(argv)
    if len(set(args.episodes)) != len(args.episodes) or not args.episodes:
        raise ValueError("episodes must be unique")
    for r in (
        args.source_root,
        args.g1_cache_root,
        args.g1_verified_index,
        args.views_root,
    ):
        if not r.is_dir():
            raise FileNotFoundError(r)
    if args.data_c_root == args.views_root or args.data_b_root == args.views_root:
        raise ValueError("owned DATA_B/C cannot be written into live View root")
    raw = VerifiedRawEpisodes(
        args.source_root, args.g1_verified_index, args.g1_cache_root
    )
    recipe = Pose5Recipe()
    results = []
    for ep in sorted(args.episodes):
        source = raw.read(args.task_class, ep)
        b = write_episode_state(
            args.data_b_root, source, recipe=recipe, resume=not args.fail_on_existing
        )
        c = None
        if not args.only_b:
            c = build_episode_joint(
                task_class=args.task_class,
                episode_index=ep,
                raw_source=source,
                state15_root=args.data_b_root,
                view_root=args.views_root,
                data_c_root=args.data_c_root,
                state_recipe_id=recipe.recipe_id,
                view_recipe_id=args.view_vae_recipe_id,
                top_variant=args.top_view_variant,
                resume=not args.fail_on_existing,
            )
        results.append(
            dict(
                task_class=args.task_class,
                episode_index=ep,
                raw_frames=b["frame_count"],
                state15_sha256=b["state15_sha256"],
                joint_sha256=None if c is None else c["joint_sha256"],
                decision_windows=None if c is None else c["window_count"],
                spatial_states=None if c is None else c["spatial_states"],
            )
        )
        print(
            f"DATA_B_C_EPISODE_PASS task={args.task_class} episode={ep} frames={b['frame_count']} "
            f"windows={c['window_count'] if c else '-'}",
            flush=True,
        )
    # These scoped-corpus manifests are snapshots of this invocation's listed
    # completed episodes, NOT an implied claim that all 9126 are ready.
    data_b_manifest = {
        "schema": "g2_data_b_scoped_corpus_v1",
        "source_binding_digest": raw.source_binding,
        "source_root": str(args.source_root),
        "pose5_recipe_id": recipe.recipe_id,
        "episodes": [
            dict(
                task_class=r["task_class"],
                episode_index=r["episode_index"],
                frames=r["raw_frames"],
                sha256=r["state15_sha256"],
            )
            for r in results
        ],
        "training_ready": False,
    }
    b_manifest_path = args.data_b_root / "manifest.json"
    if b_manifest_path.exists():
        if args.fail_on_existing:
            raise FileExistsError(b_manifest_path)
        old = json_load(b_manifest_path)
        if (
            old.get("schema") != data_b_manifest["schema"]
            or old.get("source_binding_digest")
            != data_b_manifest["source_binding_digest"]
            or old.get("pose5_recipe_id") != data_b_manifest["pose5_recipe_id"]
        ):
            raise ValueError("incremental DATA_B source/recipe changed")
        union = {(x["task_class"], x["episode_index"]): x for x in old["episodes"]}
        for item in data_b_manifest["episodes"]:
            key = (item["task_class"], item["episode_index"])
            if key in union and union[key] != item:
                raise ValueError("incremental DATA_B episode content changed")
            union[key] = item
        data_b_manifest["episodes"] = [union[k] for k in sorted(union)]
    atomic_write_json(b_manifest_path, data_b_manifest)
    if not args.only_b:
        recipe_ids = set()
        from g2.data.episode_state import episode_path

        for ep in args.episodes:
            j = json_load(
                episode_path(args.data_c_root, args.task_class, ep) / "joint_index.json"
            )
            recipe_ids.add(j["recipe_id"])
        if len(recipe_ids) != 1:
            raise ValueError("DATA_C episodes have conflicting joint recipes")
        c_recipe = next(iter(recipe_ids))
        inventory = {
            "schema": "g2_data_c_corpus_v1",
            "source_binding_digest": raw.source_binding,
            "state15_recipe_id": recipe.recipe_id,
            "view_recipe_id": args.view_vae_recipe_id,
            "top_view_variant": args.top_view_variant,
            "alignment_version": "g2_causal_latest_spatial_v1",
            "recipe_id": c_recipe,
            "split_identity": "SCOPED_EPISODES_SPLIT_NOT_FROZEN",
            "episodes": [
                {
                    "task_class": r["task_class"],
                    "episode_index": r["episode_index"],
                    "joint_sha256": r["joint_sha256"],
                    "window_count": r["decision_windows"],
                }
                for r in results
            ],
            "training_ready": False,
            "evidence_scope": "candidate_causal_20hz_view_gt_not_formal",
        }
        corpus = args.data_c_root / "manifest.json"
        if corpus.exists():
            if args.fail_on_existing:
                raise FileExistsError(corpus)
            old = json_load(corpus)
            for key in (
                "schema",
                "source_binding_digest",
                "state15_recipe_id",
                "view_recipe_id",
                "top_view_variant",
                "alignment_version",
                "recipe_id",
                "split_identity",
                "training_ready",
            ):
                if old.get(key) != inventory[key]:
                    raise ValueError(f"incremental DATA_C {key} changed")
            union = {(x["task_class"], x["episode_index"]): x for x in old["episodes"]}
            for item in inventory["episodes"]:
                key = (item["task_class"], item["episode_index"])
                if key in union and union[key] != item:
                    raise ValueError("incremental DATA_C episode content changed")
                union[key] = item
            inventory["episodes"] = [union[k] for k in sorted(union)]
        inventory["data_identity"] = canonical(inventory)
        atomic_write_json(corpus, inventory)
        atomic_write_json(
            args.data_c_root / "CORPUS_COMPLETE.json",
            {
                "schema": "g2_data_c_corpus_complete_v1",
                "manifest_sha256": digest(corpus),
                "complete": True,
                "episode_count": len(inventory["episodes"]),
                "window_count": sum(x["window_count"] for x in inventory["episodes"]),
                "training_ready": False,
            },
        )
        print(
            "DATA_C_CANDIDATE_COMPLETE episodes",
            len(inventory["episodes"]),
            "windows",
            sum(x["window_count"] for x in inventory["episodes"]),
            "data_identity",
            inventory["data_identity"],
            "training_ready",
            False,
            flush=True,
        )
    print(
        "DATA_B_SCOPED_COMPLETE",
        len(results),
        "pose5_recipe_id",
        recipe.recipe_id,
        flush=True,
    )


if __name__ == "__main__":
    main()
