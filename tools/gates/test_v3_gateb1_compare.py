"""CPU-only strict Source/Target native evidence key alignment, no GPU tensors."""
from __future__ import annotations

from copy import deepcopy
import pytest

from v3_gateb1_compare import (
    CompareBlocked, canonical_consumers, validate_pair, SCHEMA, SOURCE_ROOT, SOURCE_CHILD,
    TARGET_ROOT, TARGET_CHILD, SOURCE_DIGEST, TARGET_DIGEST,
)


def report(leg="index8", case="full"):
    count = 128 if case == "full" else 7
    return with_sites({
        "schema": SCHEMA, "leg": leg,
        "root": SOURCE_ROOT if leg == "index8" else TARGET_ROOT,
        "child": SOURCE_CHILD if leg == "index8" else TARGET_CHILD,
        "profile": "P0_FIXED", "repeat": 0, "rank": 0,
        "completed_iteration": 1301, "checkpoint_write_authorized": False,
        "status": "RAW_NATIVE_B1_EVIDENCE_ONLY_NOT_PARITY_PASS",
        "checkpoint_fingerprint": "a" * 64, "approval_reference": "owner-B1",
        "case": case, "ga_counts": [count, count],
        "restore": {"iteration": 1300,
                    "effective_config_digest": SOURCE_DIGEST if leg == "index8" else TARGET_DIGEST,
                    "source_checkpoint_fingerprint": "a" * 64},
        "consumers": [
            {"ga": ga, "slot_id": slot, "local_t": t,
             "identity": {"episode_id": "same"}, "absolute_step": t}
            for ga in (0, 1) for slot in range(8) for t in range(16 if case == "full" else (7 if slot == 0 else 0))
        ],
    })


def with_sites(data):
    data["model_site_witnesses"] = [
        {"consumer": {"ga_member": c["ga"], "slot_id": c["slot_id"], "absolute_step": c["absolute_step"]},
         "vision_sigma_sha256": "a" * 64, "action_sigma_sha256": "b" * 64,
         "vision_epsilon_sha256": "c" * 64, "action_epsilon_sha256": "d" * 64,
         "action_condition_mask_sha256": "e" * 64,
         "vision_condition_mask_sha256": "a" * 64} for c in data["consumers"]]
    data["cfg_transform_witnesses"] = [
        {"consumer": {"ga_member": c["ga"], "slot_id": c["slot_id"], "absolute_step": c["absolute_step"]},
         "transformed_payload_sha256": "f" * 64} for c in data["consumers"]]
    return data


def test_full_source_and_packed_canonical_consumer_identity_parity():
    a = report(); b = report("packed128")
    b["consumers"].reverse()  # source index-major, packed slot-major; order irrelevant
    assert validate_pair(a, b, rank=0, iteration=1301, profile="P0_FIXED", repeat=0) == "full"
    assert canonical_consumers(a) == canonical_consumers(b)


def test_changed_real_consumer_identity_blocks_even_with_matching_counts():
    a, b = report(), report("packed128")
    b["consumers"][0]["identity"]["episode_id"] = "OTHER"
    with pytest.raises(CompareBlocked, match="Consumer identity"):
        validate_pair(a, b, rank=0, iteration=1301, profile="P0_FIXED", repeat=0)


@pytest.mark.parametrize("key,value,pattern", [
    ("checkpoint_fingerprint", "b" * 64, "checkpoint"),
    ("approval_reference", "other", "approval"),
    ("child", SOURCE_CHILD, "schema/pair"),
    ("profile", "P1_MATCHED_STOCHASTIC", "schema/pair"),
    ("completed_iteration", 1302, "schema/pair"),
    ("checkpoint_write_authorized", True, "schema/pair"),
])
def test_frozen_pair_and_execution_authority_mismatch_fails(key, value, pattern):
    a, b = report(), report("packed128")
    b[key] = value
    with pytest.raises(CompareBlocked, match=pattern):
        validate_pair(a, b, rank=0, iteration=1301, profile="P0_FIXED", repeat=0)


def test_duplicate_or_missing_consumer_count_fails():
    a, b = report(), report("packed128")
    b["consumers"][1] = deepcopy(b["consumers"][0])
    with pytest.raises(CompareBlocked, match="duplicate"):
        validate_pair(a, b, rank=0, iteration=1301, profile="P0_FIXED", repeat=0)


def test_full_label_with_partial_count_fails():
    a, b = report(), report("packed128")
    b["ga_counts"] = [7, 7]
    with pytest.raises(CompareBlocked, match="ga_counts"):
        validate_pair(a, b, rank=0, iteration=1301, profile="P0_FIXED", repeat=0)


def test_missing_actual_sigma_or_cfg_site_fails_before_numeric_metrics():
    a, b = report(), report("packed128")
    b["model_site_witnesses"].pop()
    with pytest.raises(CompareBlocked, match="model_site_witnesses"):
        validate_pair(a, b, rank=0, iteration=1301, profile="P0_FIXED", repeat=0)
    b = report("packed128")
    b["cfg_transform_witnesses"][0]["transformed_payload_sha256"] = "0" * 64
    with pytest.raises(CompareBlocked, match="cfg_transform_witnesses"):
        validate_pair(a, b, rank=0, iteration=1301, profile="P0_FIXED", repeat=0)
