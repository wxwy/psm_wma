"""G2 v2 full snapshot certification is source-bound, scoped and non-mutating."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from g2.data.episode_state import digest
from g2.data.joint_index import DataCError
from g2.data.verified_provider import (
    APPROVAL,
    LANGUAGE_RECIPE,
    open_verified_snapshot,
)

BASE = Path("/mnt/data1/data_v2_0617/robocasa365_v3_flat")
INDEX = Path(
    "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/"
    "robocasa365-target-atomic-verified-index-r1"
)
SNAPSHOT = Path(
    "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/"
    ".g2_verified_training_snapshot_v2_full_cap2_20261119"
)
DATA_C = BASE / "robocasa365-target-atomic-g2-data-c"


def test_fixed_recipe_and_approval_are_not_legacy_variants():
    assert (
        LANGUAGE_RECIPE
        == "fc08163abc675abfde0e885e5a4c66c7c47d8d49d7226bae6b38c076659efd2e"
    )
    assert "dualtop_cap2" in APPROVAL


@pytest.mark.skipif(
    not (SNAPSHOT / "COMPLETE.json").is_file(),
    reason="formal full G2 v2 snapshot has not yet been sealed",
)
def test_real_full_snapshot_preserves_exact_g1_split():
    receipt = open_verified_snapshot(
        SNAPSHOT, g1_index_root=INDEX, data_c_root=DATA_C
    )
    train = {tuple(x) for x in receipt["train_episode_keys"]}
    val = {tuple(x) for x in receipt["val_episode_keys"]}
    assert len(train) == 9036
    assert len(val) == 90
    assert not train & val
    assert len(receipt["snapshot"]["episodes"]) == 9126
    assert receipt["snapshot"]["schema"] == "g2_data_c_corpus_v2"
    assert receipt["snapshot"]["top_view_variant"] == "both"
    assert receipt["language_recipe_id"] == LANGUAGE_RECIPE
    assert receipt["training_ready"] is True
    assert receipt["online_full_map_gt_parity_certified"] is False
    assert receipt["train_windows"] + receipt["val_windows"] == 2_085_331


@pytest.mark.skipif(
    not (SNAPSHOT / "COMPLETE.json").is_file(),
    reason="formal full G2 v2 snapshot has not yet been sealed",
)
def test_unauthorized_marker_or_language_identity_rejected(tmp_path):
    original = (SNAPSHOT / "receipt.json").read_bytes()
    marker = json.loads((SNAPSHOT / "COMPLETE.json").read_text())
    (tmp_path / "receipt.json").write_bytes(original)
    marker["receipt_sha256"] = "0" * 64
    (tmp_path / "COMPLETE.json").write_text(json.dumps(marker))
    with pytest.raises(DataCError, match="unapproved or unsealed"):
        open_verified_snapshot(tmp_path, g1_index_root=INDEX, data_c_root=DATA_C)
    receipt = json.loads(original)
    receipt["language_recipe_id"] = "0" * 64
    (tmp_path / "receipt.json").write_text(json.dumps(receipt))
    marker["receipt_sha256"] = digest(tmp_path / "receipt.json")
    (tmp_path / "COMPLETE.json").write_text(json.dumps(marker))
    with pytest.raises(DataCError, match="snapshot identity|unapproved"):
        open_verified_snapshot(tmp_path, g1_index_root=INDEX, data_c_root=DATA_C)
