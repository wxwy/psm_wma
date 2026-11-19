"""Explicitly certified, immutable G2 train-snapshot provider for native Phase5.

Certification is separate from the append-only DATA_C writer and review-only
language files. A certified snapshot records an exact G1 episode selection
and strong per-episode content digests; it never changes the producer's flags.
"""

from __future__ import annotations

from pathlib import Path

from g2.data.aligned_provider import CandidateAlignedG2Provider
from g2.data.episode_state import canonical, digest, json_load, require_regular
from g2.data.joint_index import DataCError

SCHEMA = "g2_verified_training_snapshot_v2"
COMPLETE_SCHEMA = "g2_verified_training_snapshot_complete_v2"
LANGUAGE_RECIPE = "fc08163abc675abfde0e885e5a4c66c7c47d8d49d7226bae6b38c076659efd2e"
APPROVAL = "owner_requested_full_dualtop_cap2_certification_20261119"


def open_verified_snapshot(snapshot_root, *, g1_index_root, data_c_root):
    """Fail closed on missing certification, source drift or spoofed split."""
    from cosmos_framework.data.generator.action.datasets.cosmos3_action_lerobot import (
        split_episode_ids,
    )

    folder = Path(snapshot_root)
    receipt_path = folder / "receipt.json"
    marker_path = folder / "COMPLETE.json"
    require_regular(receipt_path)
    require_regular(marker_path)
    receipt = json_load(receipt_path)
    marker = json_load(marker_path)
    if (
        receipt.get("schema") != SCHEMA
        or marker.get("schema") != COMPLETE_SCHEMA
        or marker.get("complete") is not True
        or marker.get("receipt_sha256") != digest(receipt_path)
        or receipt.get("approval") != APPROVAL
        or receipt.get("evidence_scope") != "verified_data_c"
        or receipt.get("training_ready") is not True
        or not isinstance(receipt.get("snapshot"), dict)
        or not isinstance(receipt.get("train_episode_keys"), list)
        or not isinstance(receipt.get("val_episode_keys"), list)
    ):
        raise DataCError("unapproved or unsealed G2 training snapshot")

    body = dict(receipt)
    identity = body.pop("snapshot_identity", None)
    if identity != canonical(body) or marker.get("snapshot_identity") != identity:
        raise DataCError("G2 snapshot identity mismatch")

    g1_path = Path(g1_index_root) / "receipt.json"
    require_regular(g1_path)
    g1 = json_load(g1_path)
    if (
        digest(g1_path) != receipt["g1_verified_receipt_sha256"]
        or g1["source_binding_digest"] != receipt["source_binding_digest"]
        or len(g1["bindings"]) != 9126
    ):
        raise DataCError("G1 verified-index source drift")
    import inspect
    from cosmos_framework.data.generator.action.datasets import (
        cosmos3_action_lerobot as g1_splits,
    )

    split_code = Path(inspect.getfile(g1_splits))
    if digest(split_code) != receipt["g1_split_source_sha256"]:
        raise DataCError("G1 original split implementation drift")
    if receipt["split_seed"] != 42 or receipt["val_ratio"] != 0.01:
        raise DataCError("G2 must exactly reuse original G1 Train/Val rules")
    groups = {}
    for row in g1["bindings"]:
        groups.setdefault(row["task_class"], []).append(row["episode_index"])
    train, val = set(), set()
    for task, ids in groups.items():
        ids.sort()
        train.update(
            (task, ids[i]) for i in split_episode_ids(len(ids), 42, 0.01, "train")
        )
        val.update((task, ids[i]) for i in split_episode_ids(len(ids), 42, 0.01, "val"))
    if len(train) != 9036 or len(val) != 90 or train & val:
        raise DataCError("original G1 split is not the expected 9036/90")
    selected_train = {(task, ep) for task, ep in receipt["train_episode_keys"]}
    selected_val = {(task, ep) for task, ep in receipt["val_episode_keys"]}
    rows = receipt["snapshot"]["episodes"]
    selected_all = {(x["task_class"], x["episode_index"]) for x in rows}
    if (
        not selected_train
        or selected_train - train
        or selected_val - val
        or selected_train & selected_val
        or selected_train | selected_val != selected_all
        or len(rows) != len(selected_all)
        or len(rows) != 9126
        or selected_train != train
        or selected_val != val
        or receipt["language_recipe_id"] != LANGUAGE_RECIPE
    ):
        raise DataCError("snapshot contains unauthorized G1 episode selection")
    if receipt["split_identity"] != canonical(
        {
            "g1_verified_receipt_sha256": receipt["g1_verified_receipt_sha256"],
            "g1_split_source_sha256": receipt["g1_split_source_sha256"],
            "seed": 42,
            "val_ratio": 0.01,
        }
    ):
        raise DataCError("G1 exact split identity invalid")
    snapshot = receipt["snapshot"]
    if (
        snapshot.get("schema") != "g2_data_c_corpus_v2"
        or snapshot.get("top_view_variant") != "both"
        or snapshot.get("source_binding_digest") != g1["source_binding_digest"]
        or snapshot.get("recipe_id") != receipt["joint_recipe_id"]
        or snapshot.get("training_ready") is not False
        or snapshot.get("data_identity")
        != canonical({k: v for k, v in snapshot.items() if k != "data_identity"})
    ):
        raise DataCError("snapshot DATA_C corpus or recipe identity mismatch")
    if receipt["data_identity"] != canonical(
        {
            "snapshot_identity": canonical(snapshot),
            "split_identity": receipt["split_identity"],
            "language_recipe_id": receipt["language_recipe_id"],
        }
    ):
        raise DataCError("formal data identity mismatch")
    # Growth of the live DATA_C manifest is intentional. The sealed individual
    # episode records, not its changing manifest, form the training authority.
    for row in rows:
        task, ep = row["task_class"], row["episode_index"]
        ep_path = Path(data_c_root) / "tasks" / task / "episodes" / f"episode_{ep:06d}"
        source = ep_path / "joint_index.json"
        marker_source = ep_path / "COMPLETE.json"
        require_regular(source)
        require_regular(marker_source)
        if (
            digest(source) != row["joint_sha256"]
            or json_load(marker_source).get("joint_sha256") != row["joint_sha256"]
        ):
            raise DataCError("sealed DATA_C episode changed after certification")
        content = json_load(source)
        if (
            content.get("schema") != "g2_data_c_joint_episode_v2"
            or content.get("recipe_id") != snapshot["recipe_id"]
            or content.get("source_binding_digest") != g1["source_binding_digest"]
            or len(content.get("windows", [])) != row["window_count"]
        ):
            raise DataCError("certified DATA_C joint identity differs")
        for state in content["spatial_states"]:
            tops = state.get("top_views")
            if (
                not isinstance(tops, dict)
                or set(tops) != {"with_robot", "without_robot"}
                or any(
                    tops[variant]["physical_owner_frame"] > state["frame"]
                    for variant in tops
                )
            ):
                raise DataCError("certified dual-top spatial state invalid")
    if receipt["train_windows"] != sum(
        row["window_count"]
        for row in rows
        if (row["task_class"], row["episode_index"]) in train
    ) or receipt["val_windows"] != sum(
        row["window_count"]
        for row in rows
        if (row["task_class"], row["episode_index"]) in val
    ):
        raise DataCError("certified train/val window budgets differ")
    return receipt


class VerifiedAlignedG2Provider(CandidateAlignedG2Provider):
    """Formal, fail-closed source-bound provider on a frozen subset of G1."""

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
        # Explicit source snapshots replace candidate-derived identities.
        self.identity = receipt["data_identity"]
        self.split_identity = receipt["split_identity"]
        self.train_episode_keys = frozenset(
            (task, ep) for task, ep in receipt["train_episode_keys"]
        )
        self.val_episode_keys = frozenset(
            (task, ep) for task, ep in receipt["val_episode_keys"]
        )
        self.snapshot_identity = receipt["snapshot_identity"]
        if (
            len(self.data) != len(receipt["snapshot"]["episodes"])
            or len(self.train_episode_keys) < 8
        ):
            self.close()
            raise DataCError("verified provider missing required episode payloads")


def open_verified_provider(**kwargs):
    """Stable factory for the existing G2RunRecipe provider_factory contract."""
    return VerifiedAlignedG2Provider(**kwargs)
