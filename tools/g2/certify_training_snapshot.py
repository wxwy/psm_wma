"""Audit and publish a pinned G2 training episode snapshot; no source mutation.

Uses the exact G1 per-task Train/Val partition. DATA_C and independent
language may keep growing independently; certification freezes the current
verified episode set with per-file SHA256. This does NOT train, render or encode.
"""

from __future__ import annotations

import argparse
import inspect
import json
import time
from pathlib import Path

from cosmos_framework.data.generator.action.datasets import (
    cosmos3_action_lerobot as g1_splits,
)

from g2.data.episode_state import (
    atomic_write_json,
    canonical,
    digest,
    json_load,
    require_regular,
)
from g2.data.joint_index import DataCError, make_joint_recipe
from g2.data.verified_provider import (
    COMPLETE_SCHEMA,
    LANGUAGE_RECIPE,
    SCHEMA,
    open_verified_snapshot,
)
from g2.language.initial_context import read_versioned_initial_language


def g1_split(receipt: dict, g1_split_sha: str):
    groups: dict[str, list[dict]] = {}
    for row in receipt["bindings"]:
        groups.setdefault(row["task_class"], []).append(row)
    train, val, by_key = set(), set(), {}
    for task, rows in sorted(groups.items()):
        rows.sort(key=lambda x: x["episode_index"])
        indices = [row["episode_index"] for row in rows]
        if len(indices) != len(set(indices)):
            raise DataCError("G1 duplicate source episode index")
        tr = g1_splits.split_episode_ids(len(rows), 42, 0.01, "train")
        va = g1_splits.split_episode_ids(len(rows), 42, 0.01, "val")
        if set(tr) & set(va) or set(tr) | set(va) != set(range(len(rows))):
            raise DataCError("G1 original Train/Val partitions are incomplete")
        for i, row in enumerate(rows):
            key = (task, row["episode_index"])
            by_key[key] = row
            (train if i in tr else val).add(key)
    if len(train) != 9036 or len(val) != 90 or len(by_key) != 9126 or train & val:
        raise DataCError("G1 full-episode train/val partition is not 9036/90")
    return train, val, by_key


def _read_live_corpus(root):
    root = Path(root)
    for _ in range(4):
        manifest = root / "manifest.json"
        complete = root / "CORPUS_COMPLETE.json"
        require_regular(manifest)
        require_regular(complete)
        body = json_load(manifest)
        marker = json_load(complete)
        if (
            marker.get("complete") is True
            and marker.get("manifest_sha256") == digest(manifest)
            and body.get("schema") == "g2_data_c_corpus_v1"
            and body.get("training_ready") is False
            and body.get("data_identity")
            == canonical({k: v for k, v in body.items() if k != "data_identity"})
        ):
            return body
        time.sleep(0.3)
    raise DataCError("DATA_C writer did not expose a stable complete manifest")


def build_receipt(
    *,
    g1_verified_index_root,
    data_c_root,
    state15_root,
    view_root,
    initial_language_root,
    initial_language_recipe_id,
    approval,
):
    if initial_language_recipe_id != LANGUAGE_RECIPE:
        raise DataCError("language recipe must be explicit approved initial review-v1")
    if approval != "owner_accepted_review_v1_pinned_for_G2_training":
        raise DataCError(
            "review language needs explicit owner acceptance for this training snapshot"
        )
    g1_path = Path(g1_verified_index_root) / "receipt.json"
    require_regular(g1_path)
    g1 = json_load(g1_path)
    if g1.get("schema") != "psm_v3_robocasa_verified_index_v1":
        raise DataCError("G1 original receipt schema mismatch")
    sha_code = digest(Path(inspect.getfile(g1_splits)))
    train, val, by_key = g1_split(g1, sha_code)
    corpus = _read_live_corpus(data_c_root)
    if corpus.get("source_binding_digest") != g1["source_binding_digest"]:
        raise DataCError("G1 DATA_C source binding mismatch")
    if corpus.get("split_identity") != "SCOPED_EPISODES_SPLIT_NOT_FROZEN":
        raise DataCError("DATA_C original producer must stay candidate-only")
    if corpus.get("recipe_id") != canonical(
        make_joint_recipe(
            state_recipe_id=corpus["state15_recipe_id"],
            view_recipe_id=corpus["view_recipe_id"],
            top_variant=corpus["top_view_variant"],
        )
    ):
        raise DataCError("DATA_C producer recipe mutated")
    lang_root = Path(initial_language_root) / "recipes" / initial_language_recipe_id
    require_regular(lang_root / "RECIPE.json")
    train_selected, val_selected = [], []
    snapshots = []
    for entry in corpus["episodes"]:
        task, ep = entry["task_class"], entry["episode_index"]
        key = (task, ep)
        if key not in by_key:
            raise DataCError(f"DATA_C episode {key} absent from original G1")
        src = Path(data_c_root) / "tasks" / task / "episodes" / f"episode_{ep:06d}"
        b = Path(state15_root) / "tasks" / task / "episodes" / f"episode_{ep:06d}"
        require_regular(src / "joint_index.json")
        require_regular(src / "COMPLETE.json")
        require_regular(b / "state15.pt")
        joint = json_load(src / "joint_index.json")
        if (
            digest(src / "joint_index.json") != entry["joint_sha256"]
            or json_load(src / "COMPLETE.json").get("joint_sha256")
            != entry["joint_sha256"]
            or joint.get("schema") != "g2_data_c_joint_episode_v1"
            or joint.get("recipe_id") != corpus["recipe_id"]
            or joint.get("source_binding_digest") != g1["source_binding_digest"]
            or joint.get("g1_video_cache_manifest_sha256")
            != g1["cache_manifest_sha256"]
            or joint.get("source_frame_count") != by_key[key]["length"]
            or len(joint.get("windows", [])) != entry["window_count"]
            or entry["window_count"] != by_key[key]["window_count"]
            or joint.get("training_ready") is not False
        ):
            raise DataCError(f"DATA_C source/reference mismatch: {key}")
        if digest(b / "state15.pt") != joint["data_b_sha256"]:
            raise DataCError(f"DATA_B source changed: {key}")
        original = joint["original_instruction"]
        text = read_versioned_initial_language(
            initial_language_root,
            recipe_id=initial_language_recipe_id,
            task_class=task,
            episode_index=ep,
            source_binding_digest=g1["source_binding_digest"],
            original_instruction=original,
            view_root=view_root,
        )
        if (
            not text["augmented_instruction"].startswith("Task: " + original)
            or text["recipe"]["production_template_frozen"] is not False
        ):
            raise DataCError(f"initial language content/version mismatch {key}")
        # Current ViewVAE is a separate ready (not inferred from a file's
        # mere presence) producer state; verify its completion/recipe.
        vdir = Path(view_root) / "tasks" / task / "episodes" / f"episode_{ep:06d}"
        vae_manifest = vdir / "vae_cache/manifest.json"
        vae_complete = vdir / "vae_cache/COMPLETE.json"
        require_regular(vae_manifest)
        require_regular(vae_complete)
        if (
            digest(vae_manifest) != joint["view_vae_manifest_sha256"]
            or json_load(vae_complete).get("complete") is not True
            or json_load(vae_complete).get("recipe_id") != corpus["view_recipe_id"]
        ):
            raise DataCError(f"selected ViewVAE not complete or changed {key}")
        # Every decision window must have a causal selected spatial state.
        windows, states = joint["windows"], joint["spatial_states"]
        if (
            not states
            or windows[0]["decision_frame"] != 0
            or windows[-1]["decision_frame"] != len(windows) - 1
            or any(
                w["decision_frame"] != i
                or w["spatial_state_frame"] > i
                or w["state15_frame"] != i
                or w["action_last_frame"] != i + 15
                or w["observation_last_frame"] != i + 16
                or not 0 <= w["spatial_state_ordinal"] < len(states)
                for i, w in enumerate(windows)
            )
        ):
            raise DataCError(f"DATA_C 20Hz temporal causality broken {key}")
        sidecar = (
            lang_root
            / "tasks"
            / task
            / "episodes"
            / f"episode_{ep:06d}"
            / "initial_context.json"
        )
        require_regular(sidecar)
        snapshots.append(dict(entry))
        (train_selected if key in train else val_selected).append([task, ep])
    if not train_selected or len(snapshots) != len(
        set((x["task_class"], x["episode_index"]) for x in snapshots)
    ):
        raise DataCError("empty or duplicated certified G2 training episode set")
    if (
        train_selected
        and val_selected
        and set(map(tuple, train_selected)) & set(map(tuple, val_selected))
    ):
        raise DataCError("G1 train/val contamination")
    snapshot = dict(corpus)
    snapshot["episodes"] = snapshots
    snapshot["data_identity"] = canonical(
        {k: v for k, v in snapshot.items() if k != "data_identity"}
    )
    split_identity = canonical(
        {
            "g1_verified_receipt_sha256": digest(g1_path),
            "g1_split_source_sha256": sha_code,
            "seed": 42,
            "val_ratio": 0.01,
        }
    )
    info = dict(
        schema=SCHEMA,
        approval=approval,
        evidence_scope="verified_data_c",
        # Source producers retain training_ready=False and review flags.
        # Only this independently audited fixed-recipe snapshot is approved.
        training_ready=True,
        g1_verified_receipt_sha256=digest(g1_path),
        source_binding_digest=g1["source_binding_digest"],
        g1_split_source_sha256=sha_code,
        split_seed=42,
        val_ratio=0.01,
        split_identity=split_identity,
        language_recipe_id=initial_language_recipe_id,
        joint_recipe_id=corpus["recipe_id"],
        data_identity=canonical(
            {
                "snapshot_identity": canonical(snapshot),
                "split_identity": split_identity,
                "language_recipe_id": initial_language_recipe_id,
            }
        ),
        snapshot=snapshot,
        train_episode_keys=sorted(train_selected),
        val_episode_keys=sorted(val_selected),
        train_windows=sum(
            x["window_count"]
            for x in snapshots
            if (x["task_class"], x["episode_index"]) in train
        ),
        val_windows=sum(
            x["window_count"]
            for x in snapshots
            if (x["task_class"], x["episode_index"]) in val
        ),
        language_review_source_unchanged=True,
        online_full_map_gt_parity_certified=False,
    )
    info["snapshot_identity"] = canonical(info)
    return info


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in (
        "g1-verified-index-root",
        "data-c-root",
        "state15-root",
        "view-root",
        "initial-language-root",
        "snapshot-root",
    ):
        p.add_argument("--" + name, required=True, type=Path)
    p.add_argument("--initial-language-recipe-id", required=True)
    p.add_argument(
        "--approval",
        choices=["owner_accepted_review_v1_pinned_for_G2_training"],
        required=True,
    )
    args = p.parse_args(argv)
    dest = args.snapshot_root
    if dest.exists():
        raise FileExistsError("certification is never overwritten or resumed")
    info = build_receipt(
        g1_verified_index_root=args.g1_verified_index_root,
        data_c_root=args.data_c_root,
        state15_root=args.state15_root,
        view_root=args.view_root,
        initial_language_root=args.initial_language_root,
        initial_language_recipe_id=args.initial_language_recipe_id,
        approval=args.approval,
    )
    dest.mkdir(parents=True)
    atomic_write_json(dest / "receipt.json", info)
    atomic_write_json(
        dest / "COMPLETE.json",
        {
            "schema": COMPLETE_SCHEMA,
            "complete": True,
            "snapshot_identity": info["snapshot_identity"],
            "receipt_sha256": digest(dest / "receipt.json"),
        },
    )
    # Independent training-side open on the same sealed snapshot.
    result = open_verified_snapshot(
        dest,
        g1_index_root=args.g1_verified_index_root,
        data_c_root=args.data_c_root,
    )
    if result != info:
        raise DataCError("postpublish verification differs")
    print(
        "G2_VERIFIED_TRAINING_SNAPSHOT_PASS",
        json.dumps(
            {
                "snapshot_identity": info["snapshot_identity"],
                "data_identity": info["data_identity"],
                "split_identity": info["split_identity"],
                "training_episode_count": len(info["train_episode_keys"]),
                "val_episode_count": len(info["val_episode_keys"]),
                "train_windows": info["train_windows"],
                "val_windows": info["val_windows"],
                "language_recipe_id": info["language_recipe_id"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
