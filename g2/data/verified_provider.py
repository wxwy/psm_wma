"""Open a sealed G2 training snapshot and verify its native G1 partition."""

from __future__ import annotations

import inspect
from pathlib import Path

from g2.data.aligned_provider import CandidateAlignedG2Provider, corpus_rows
from g2.data.episode_state import (
    DataBError,
    canonical,
    digest,
    episode_path,
    read_bound_json,
)
from g2.data.joint_index import DataCError, make_joint_recipe, read_joint_episode

SCHEMA = "g2_verified_training_snapshot_v3"
COMPLETE_SCHEMA = "g2_verified_training_snapshot_complete_v3"
_LEGACY_SCHEMA = "g2_verified_training_snapshot_v2"
_LEGACY_COMPLETE = "g2_verified_training_snapshot_complete_v2"
LANGUAGE_RECIPE = "fc08163abc675abfde0e885e5a4c66c7c47d8d49d7226bae6b38c076659efd2e"
APPROVAL = "owner_requested_full_dualtop_cap2_certification_20261119"
CERTIFICATION_SCOPE = "full_9126_complete_review_recipe_not_online_full_map"
SPLIT_SEED = 42
VAL_RATIO = 0.01


def g1_partition(root, *, expected_sha256=None):
    """Use the same per-task split implementation as the pinned G1 dataset."""
    from cosmos_framework.data.generator.action.datasets import cosmos3_action_lerobot

    root = Path(root)
    g1, receipt_sha, _ = read_bound_json(
        root / "receipt.json", expected_sha256=expected_sha256
    )
    if g1.get("schema") != "psm_v3_robocasa_verified_index_v1":
        raise DataCError("G1 original receipt schema differs")
    groups = {}
    bindings = {}
    global_ids = set()
    for row in g1["bindings"]:
        task, ep = row["task_class"], row["episode_index"]
        episode_path(root, task, ep)
        if ep in global_ids:
            raise DataCError("duplicate G1 source episode index")
        global_ids.add(ep)
        bindings[task, ep] = row
        groups.setdefault(task, []).append(ep)
    train, val = set(), set()
    for task, episodes in groups.items():
        ids = sorted(episodes)
        train.update(
            (task, ids[i])
            for i in cosmos3_action_lerobot.split_episode_ids(
                len(ids), SPLIT_SEED, VAL_RATIO, "train"
            )
        )
        val.update(
            (task, ids[i])
            for i in cosmos3_action_lerobot.split_episode_ids(
                len(ids), SPLIT_SEED, VAL_RATIO, "val"
            )
        )
    if (
        len(train) != 9036
        or len(val) != 90
        or train & val
        or train | val != bindings.keys()
    ):
        raise DataCError(
            "G1 original Train/Val partition is not the complete 9036/90 split"
        )
    split = {
        "g1_verified_receipt_sha256": receipt_sha,
        "g1_split_source_sha256": digest(Path(inspect.getfile(cosmos3_action_lerobot))),
        "seed": SPLIT_SEED,
        "val_ratio": VAL_RATIO,
    }
    return g1, split, bindings, train, val


def language_bindings(receipt, rows):
    """Validate the exact CAP2 content and completion-file pins for every episode."""
    bindings = {}
    values = receipt.get("language_bindings")
    if not isinstance(values, list):
        raise DataCError("certified language file identities missing")
    for row in values:
        key = (row["task_class"], row["episode_index"])
        if (
            key in bindings
            or key not in rows
            or type(key[1]) is not int
            or any(
                not isinstance(row.get(name), str)
                or len(row[name]) != 64
                or any(ch not in "0123456789abcdef" for ch in row[name])
                for name in ("content_sha256", "complete_sha256")
            )
        ):
            raise DataCError("invalid or duplicate certified language file identity")
        bindings[key] = row
    if bindings.keys() != rows.keys():
        raise DataCError("certified language bindings do not cover the snapshot")
    return bindings


def data_identity(receipt):
    fields = {
        "snapshot_identity": canonical(receipt["snapshot"]),
        "split_identity": receipt["split_identity"],
        "language_recipe_id": receipt["language_recipe_id"],
    }
    if receipt["schema"] == SCHEMA:
        fields["language_bindings"] = receipt["language_bindings"]
    return canonical(fields)


def open_verified_snapshot(
    snapshot_root,
    *,
    g1_index_root,
    data_c_root,
    verify_episodes=True,
    inspect_legacy_v2=False,
):
    """Verify a snapshot seal. Historical v2 is available for explicit inspection."""
    folder = Path(snapshot_root)
    try:
        marker, _, _ = read_bound_json(folder / "COMPLETE.json")
        expected_sha = marker.get("receipt_sha256")
        if not expected_sha:
            raise DataCError("unapproved or unsealed G2 training snapshot")
        receipt, _, _ = read_bound_json(
            folder / "receipt.json", expected_sha256=expected_sha
        )
    except (DataBError, OSError) as exc:
        raise DataCError("unapproved or unsealed G2 training snapshot") from exc
    version = receipt.get("schema")
    if version == _LEGACY_SCHEMA and not inspect_legacy_v2:
        raise DataCError(
            "legacy snapshot lacks per-episode CAP2 hashes; recertification required"
        )
    if (
        (version, marker.get("schema"))
        not in {
            (SCHEMA, COMPLETE_SCHEMA),
            (_LEGACY_SCHEMA, _LEGACY_COMPLETE),
        }
        or marker.get("complete") is not True
        or receipt.get("approval") != APPROVAL
        or receipt.get("evidence_scope") != "verified_data_c"
        or receipt.get("training_ready") is not True
        or receipt.get("online_full_map_gt_parity_certified") is not False
        or receipt.get("language_review_source_unchanged") is not True
        or receipt.get("top_view_variants") != ["with_robot", "without_robot"]
        or receipt.get("certification_scope") != CERTIFICATION_SCOPE
        or receipt.get("language_recipe_id") != LANGUAGE_RECIPE
    ):
        raise DataCError("unapproved or unsealed G2 training snapshot")
    identity = receipt.get("snapshot_identity")
    if (
        identity
        != canonical({k: v for k, v in receipt.items() if k != "snapshot_identity"})
        or marker.get("snapshot_identity") != identity
    ):
        raise DataCError("G2 snapshot identity mismatch")

    g1, split, source_rows, train, val = g1_partition(
        g1_index_root, expected_sha256=receipt["g1_verified_receipt_sha256"]
    )
    snapshot = receipt["snapshot"]
    rows = corpus_rows(snapshot, data_c_root)
    if (
        snapshot.get("schema") != "g2_data_c_corpus_v2"
        or snapshot.get("top_view_variant") != "both"
        or snapshot.get("source_binding_digest") != g1["source_binding_digest"]
        or receipt.get("source_binding_digest") != g1["source_binding_digest"]
        or snapshot.get("recipe_id") != receipt["joint_recipe_id"]
        or snapshot["recipe_id"]
        != canonical(
            make_joint_recipe(
                state_recipe_id=snapshot["state15_recipe_id"],
                view_recipe_id=snapshot["view_recipe_id"],
                top_variant="both",
            )
        )
        or snapshot.get("training_ready") is not False
        or snapshot.get("data_identity")
        != canonical({k: v for k, v in snapshot.items() if k != "data_identity"})
        or rows.keys() != source_rows.keys()
    ):
        raise DataCError("snapshot DATA_C corpus or recipe identity mismatch")
    if (
        receipt["train_episode_keys"] != [list(k) for k in sorted(train)]
        or receipt["val_episode_keys"] != [list(k) for k in sorted(val)]
        or receipt["split_seed"] != SPLIT_SEED
        or receipt["val_ratio"] != VAL_RATIO
        or receipt["split_identity"] != canonical(split)
        or receipt["g1_split_source_sha256"] != split["g1_split_source_sha256"]
        or receipt["train_windows"] != sum(rows[key]["window_count"] for key in train)
        or receipt["val_windows"] != sum(rows[key]["window_count"] for key in val)
        or any(
            row["window_count"] != source_rows[key]["window_count"]
            for key, row in rows.items()
        )
    ):
        raise DataCError("snapshot contains an invalid G1 split or window budget")
    if version == SCHEMA:
        language_bindings(receipt, rows)
    if receipt["data_identity"] != data_identity(receipt):
        raise DataCError("formal data identity mismatch")
    if verify_episodes:
        for (task, ep), row in rows.items():
            content, _ = read_joint_episode(
                episode_path(data_c_root, task, ep),
                task=task,
                episode=ep,
                recipe_id=snapshot["recipe_id"],
                source_binding_digest=g1["source_binding_digest"],
                expected_sha256=row["joint_sha256"],
                window_count=row["window_count"],
            )
            if (
                content["source_frame_count"] != source_rows[task, ep]["length"]
                or content["g1_video_cache_manifest_sha256"]
                != g1["cache_manifest_sha256"]
            ):
                raise DataCError("certified DATA_C window or G1 cache identity differs")
    return receipt


class VerifiedAlignedG2Provider(CandidateAlignedG2Provider):
    """Formal provider on a sealed dataset with lazy, bounded payload reads."""

    evidence_scope = "verified_data_c"

    def __init__(
        self,
        *,
        snapshot_root,
        g1_verified_index_root,
        data_c_root,
        state15_root,
        view_root,
        initial_language_root,
        initial_language_recipe_id,
        global_memory_enabled=True,
    ):
        receipt = open_verified_snapshot(
            snapshot_root,
            g1_index_root=g1_verified_index_root,
            data_c_root=data_c_root,
            verify_episodes=False,
        )
        if receipt["language_recipe_id"] != initial_language_recipe_id:
            raise DataCError("formal G2 language version differs from certification")
        super().__init__(
            data_c_root=data_c_root,
            state15_root=state15_root,
            view_root=view_root,
            global_memory_enabled=global_memory_enabled,
            initial_language_root=initial_language_root,
            initial_language_recipe_id=initial_language_recipe_id,
            corpus_manifest_override=receipt["snapshot"],
        )
        self.identity = receipt["data_identity"]
        self.split_identity = receipt["split_identity"]
        self.snapshot_identity = receipt["snapshot_identity"]
        self.train_episode_keys = frozenset(map(tuple, receipt["train_episode_keys"]))
        self.val_episode_keys = frozenset(map(tuple, receipt["val_episode_keys"]))
        self._language_bindings = language_bindings(receipt, self.data)


def open_verified_provider(**kwargs):
    """Stable factory for the existing G2RunRecipe provider_factory contract."""
    return VerifiedAlignedG2Provider(**kwargs)
