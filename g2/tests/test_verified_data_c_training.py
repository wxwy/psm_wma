"""Offline-certified DATA_C formal Provider, original G1 split and snapshot drift.

Real test requires existing RoboCasa + G1 VerifiedIndex + G2 certified snapshot.
No producer files, GPU, model weights, or source checkpoints are modified.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from g2.data.episode_state import digest
from g2.data.joint_index import DataCError
from g2.data.verified_provider import open_verified_provider, open_verified_snapshot

SNAPSHOT = Path(
    "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_verified_training_snapshot_20261118"
)
BASE = Path("/mnt/data1/data_v2_0617/robocasa365_v3_flat")
INDEX = Path(
    "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/"
    "robocasa365-target-atomic-verified-index-r1"
)
RECIPE = "115569530be3d219d4ae3997b3ef5b05b10da701aebab4f184ea9912014cd8f6"


def _real_present():
    return (
        (SNAPSHOT / "receipt.json").is_file()
        and (BASE / "robocasa365-target-atomic-g2-data-c/manifest.json").is_file()
        and (INDEX / "receipt.json").is_file()
    )


def _acceptance(tmp=None):
    return open_verified_snapshot(
        SNAPSHOT if tmp is None else tmp,
        g1_index_root=INDEX,
        data_c_root=BASE / "robocasa365-target-atomic-g2-data-c",
    )


@pytest.mark.skipif(not _real_present(), reason="real G2 DATA_C snapshot unavailable")
def test_training_snapshot_has_exact_g1_train_val_original_partition():
    x = _acceptance()
    train = {tuple(pair) for pair in x["train_episode_keys"]}
    val = {tuple(pair) for pair in x["val_episode_keys"]}
    assert len(train) == 3156 and len(val) == 32
    assert not train & val
    assert x["language_recipe_id"] == RECIPE
    assert x["evidence_scope"] == "verified_data_c"
    assert x["training_ready"] is True
    # This is an approved immutable sidecar, NEVER a claim that the append-only
    # producer or review-only language files had their original flags flipped.
    assert x["snapshot"]["training_ready"] is False
    assert x["split_identity"] != x["data_identity"]
    assert x["train_windows"] == 783507
    assert x["val_windows"] == 8506


@pytest.mark.skipif(not _real_present(), reason="real G2 DATA_C snapshot unavailable")
def test_training_snapshot_rejects_modified_marker_and_body(tmp_path):
    marker = json.loads((SNAPSHOT / "COMPLETE.json").read_text())
    receipt = (SNAPSHOT / "receipt.json").read_bytes()
    (tmp_path / "receipt.json").write_bytes(receipt)
    marker["receipt_sha256"] = "0" * 64
    (tmp_path / "COMPLETE.json").write_text(json.dumps(marker))
    with pytest.raises(DataCError, match="unapproved or unsealed"):
        _acceptance(tmp_path)
    marker["receipt_sha256"] = digest(tmp_path / "receipt.json")
    (tmp_path / "COMPLETE.json").write_text(json.dumps(marker))
    assert (
        _acceptance(tmp_path)["snapshot_identity"] == _acceptance()["snapshot_identity"]
    )

    body = json.loads(receipt)
    body["train_episode_keys"][0][1] += 1
    (tmp_path / "receipt.json").write_text(json.dumps(body))
    marker["receipt_sha256"] = digest(tmp_path / "receipt.json")
    (tmp_path / "COMPLETE.json").write_text(json.dumps(marker))
    with pytest.raises(DataCError, match="snapshot identity"):
        _acceptance(tmp_path)


@pytest.mark.skipif(not _real_present(), reason="real G2 DATA_C snapshot unavailable")
def test_verified_provider_native_r1_r2_selected_views_and_immutable_text():
    common = dict(
        snapshot_root=SNAPSHOT,
        g1_verified_index_root=INDEX,
        data_c_root=BASE / "robocasa365-target-atomic-g2-data-c",
        state15_root=BASE / "robocasa365-target-atomic-state15",
        view_root=BASE / "robocasa365-target-atomic-6views",
        initial_language_root=BASE / "robocasa365-target-atomic-g2-language",
        initial_language_recipe_id=RECIPE,
    )
    r1 = open_verified_provider(**common, global_memory_enabled=False)
    r2 = open_verified_provider(**common, global_memory_enabled=True)
    try:
        assert r1.evidence_scope == r2.evidence_scope == "verified_data_c"
        assert r1.identity == r2.identity
        assert r1.split_identity == r2.split_identity
        assert len(r1.train_episode_keys) == 3156
        for frame in (16, 32, 48):
            a = r1.read_common(
                task_class="CloseBlenderLid",
                episode_index=104,
                decision_frame=frame,
            )
            b = r2.read_common(
                task_class="CloseBlenderLid",
                episode_index=104,
                decision_frame=frame,
            )
            assert a["static_task_text"] == b["static_task_text"]
            assert (
                "Initial spatial context" in b["static_task_text"].enhanced_instruction
            )
            assert a["state15"].equal(b["state15"])
            assert b["identity"].data_version == r2.identity
            with pytest.raises(DataCError, match="must not read"):
                r1.read_selected_views(a["identity"], top_view_variant="with_robot")
            views = r2.read_selected_views(b["identity"], top_view_variant="with_robot")
            assert len(views) == 3
    finally:
        r1.close()
        r2.close()
