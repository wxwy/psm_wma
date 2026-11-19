"""Certify read-only DATA_C, DATA_B, View VAE and frame-0 CAP2 artifacts."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from g2.data.aligned_provider import corpus_rows, open_corpus_manifest
from g2.data.episode_state import canonical, digest, episode_path, read_episode_state
from g2.data.joint_index import (
    DataCError,
    make_joint_recipe,
    open_joint_view_source,
    read_joint_episode,
    verify_joint_view_refs,
)
from g2.data.verified_provider import (
    APPROVAL,
    CERTIFICATION_SCOPE,
    COMPLETE_SCHEMA,
    LANGUAGE_RECIPE,
    SCHEMA,
    SPLIT_SEED,
    VAL_RATIO,
    data_identity,
    g1_partition,
    open_verified_snapshot,
)
from g2.language.initial_context import (
    load_initial_episode_language,
    read_versioned_initial_language,
)
from g2.latent_cache.storage import _fsync_directory, atomic_json, build_lock


def _audit_episode(
    key,
    entry,
    *,
    corpus,
    g1,
    raw,
    raw_file,
    data_c_root,
    state15_root,
    view_root,
    initial_language_root,
    initial_language_recipe_id,
):
    task, ep = key
    source_binding = g1["source_binding_digest"]
    source_range = [raw["dataset_from_index"], raw["dataset_to_index"]]
    joint, _ = read_joint_episode(
        episode_path(data_c_root, task, ep),
        task=task,
        episode=ep,
        recipe_id=corpus["recipe_id"],
        source_binding_digest=source_binding,
        expected_sha256=entry["joint_sha256"],
        window_count=raw["window_count"],
    )
    if (
        joint["schema"] != "g2_data_c_joint_episode_v2"
        or joint["source_frame_count"] != raw["length"]
        or joint["g1_video_cache_manifest_sha256"] != g1["cache_manifest_sha256"]
    ):
        raise DataCError("DATA_C original G1 frame or cache identity differs")
    _, meta, _ = read_episode_state(
        episode_path(state15_root, task, ep),
        task=task,
        episode=ep,
        frame_count=raw["length"],
        recipe_id=corpus["state15_recipe_id"],
        source_binding_digest=source_binding,
        expected_sha256=joint["data_b_sha256"],
    )
    original_instruction = joint["original_instruction"]
    if (
        meta["original_instruction"] != original_instruction
        or meta["source_range"] != source_range
        or meta["raw_source_file_stat"]
        != {k: raw_file[k] for k in ("size", "mtime_ns")}
        or not Path(meta["raw_source_path"]).as_posix().endswith("/" + raw["data_file"])
    ):
        raise DataCError(
            "DATA_B original G1 caption, range or raw Parquet witness differs"
        )

    manifest, index, _ = open_joint_view_source(
        episode_path(view_root, task, ep), joint
    )
    verify_joint_view_refs(joint, manifest, index)
    expected = load_initial_episode_language(
        view_root=view_root,
        raw_source={
            "task_class": task,
            "episode_index": ep,
            "source_frame_count": raw["length"],
            "source_range": source_range,
            "source_binding_digest": source_binding,
            "instruction": original_instruction,
        },
        expected_view_manifest_sha256=joint["view_episode_manifest_sha256"],
    )
    witnesses = {}
    stored = read_versioned_initial_language(
        initial_language_root,
        recipe_id=initial_language_recipe_id,
        task_class=task,
        episode_index=ep,
        source_binding_digest=source_binding,
        original_instruction=original_instruction,
        file_witnesses=witnesses,
    )
    if stored != expected:
        raise DataCError(
            "published CAP2 differs from frame-0 SG/task/caption reconstruction"
        )
    dirname = episode_path(
        Path(initial_language_root) / "recipes" / initial_language_recipe_id, task, ep
    )
    return {
        "task_class": task,
        "episode_index": ep,
        "content_sha256": witnesses[dirname / "initial_context.json"][0],
        "complete_sha256": witnesses[dirname / "COMPLETE.json"][0],
    }


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
    if initial_language_recipe_id != LANGUAGE_RECIPE or approval != APPROVAL:
        raise DataCError("this certificate requires the approved CAP2 review recipe")
    g1, split, by_key, train, val = g1_partition(g1_verified_index_root)
    corpus = open_corpus_manifest(data_c_root)
    rows = corpus_rows(corpus, data_c_root)
    if (
        corpus["schema"] != "g2_data_c_corpus_v2"
        or corpus["source_binding_digest"] != g1["source_binding_digest"]
        or corpus.get("split_identity") != "SCOPED_EPISODES_SPLIT_NOT_FROZEN"
        or corpus["recipe_id"]
        != canonical(
            make_joint_recipe(
                state_recipe_id=corpus["state15_recipe_id"],
                view_recipe_id=corpus["view_recipe_id"],
                top_variant="both",
            )
        )
        or rows.keys() != by_key.keys()
        or any(
            row["window_count"] != by_key[key]["window_count"]
            for key, row in rows.items()
        )
    ):
        raise DataCError("DATA_C full-corpus G1 split, source or recipe differs")
    raw_files = {row["path"]: row for row in g1["files"]["source_data"]}
    bindings = []
    for key in sorted(rows):
        try:
            raw = by_key[key]
            bindings.append(
                _audit_episode(
                    key,
                    rows[key],
                    corpus=corpus,
                    g1=g1,
                    raw=raw,
                    raw_file=raw_files[raw["data_file"]],
                    data_c_root=data_c_root,
                    state15_root=state15_root,
                    view_root=view_root,
                    initial_language_root=initial_language_root,
                    initial_language_recipe_id=initial_language_recipe_id,
                )
            )
        except (KeyError, ValueError, OSError) as exc:
            raise DataCError(
                f"snapshot audit failed for {key[0]}/{key[1]:06d}: {exc}"
            ) from exc
    info = dict(
        schema=SCHEMA,
        approval=approval,
        evidence_scope="verified_data_c",
        training_ready=True,
        g1_verified_receipt_sha256=split["g1_verified_receipt_sha256"],
        source_binding_digest=g1["source_binding_digest"],
        g1_split_source_sha256=split["g1_split_source_sha256"],
        split_seed=SPLIT_SEED,
        val_ratio=VAL_RATIO,
        split_identity=canonical(split),
        language_recipe_id=initial_language_recipe_id,
        joint_recipe_id=corpus["recipe_id"],
        snapshot=corpus,
        train_episode_keys=[list(k) for k in sorted(train)],
        val_episode_keys=[list(k) for k in sorted(val)],
        train_windows=sum(rows[key]["window_count"] for key in train),
        val_windows=sum(rows[key]["window_count"] for key in val),
        language_bindings=bindings,
        language_review_source_unchanged=True,
        online_full_map_gt_parity_certified=False,
        top_view_variants=["with_robot", "without_robot"],
        certification_scope=CERTIFICATION_SCOPE,
    )
    info["data_identity"] = data_identity(info)
    info["snapshot_identity"] = canonical(info)
    return info


def publish_snapshot(dest, info, *, g1_index_root, data_c_root):
    """Publish both files together after readback. A failed transaction has no final directory."""
    dest = Path(dest)
    with build_lock(dest.parent / f".{dest.name}.publish"):
        if os.path.lexists(dest):
            raise FileExistsError("certification is never overwritten")
        with tempfile.TemporaryDirectory(
            prefix=f".{dest.name}-", dir=dest.parent
        ) as tmp:
            staged = Path(tmp) / "snapshot"
            atomic_json(staged / "receipt.json", info)
            atomic_json(
                staged / "COMPLETE.json",
                {
                    "schema": COMPLETE_SCHEMA,
                    "complete": True,
                    "snapshot_identity": info["snapshot_identity"],
                    "receipt_sha256": digest(staged / "receipt.json"),
                },
            )
            result = open_verified_snapshot(
                staged,
                g1_index_root=g1_index_root,
                data_c_root=data_c_root,
                verify_episodes=False,
            )
            if result != info:
                raise DataCError("snapshot verification differs before publication")
            os.rename(staged, dest)
            _fsync_directory(dest.parent)


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
    p.add_argument("--approval", choices=[APPROVAL], required=True)
    args = p.parse_args(argv)
    if os.path.lexists(args.snapshot_root):
        raise FileExistsError("certification is never overwritten")
    info = build_receipt(
        g1_verified_index_root=args.g1_verified_index_root,
        data_c_root=args.data_c_root,
        state15_root=args.state15_root,
        view_root=args.view_root,
        initial_language_root=args.initial_language_root,
        initial_language_recipe_id=args.initial_language_recipe_id,
        approval=args.approval,
    )
    publish_snapshot(
        args.snapshot_root,
        info,
        g1_index_root=args.g1_verified_index_root,
        data_c_root=args.data_c_root,
    )
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
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
