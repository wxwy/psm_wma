"""CPU-only negative fixtures. No Cosmos model, distributed runtime or DCP load."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v3_gateb1_metrics as metric  # noqa: E402


def fp(values):
    return torch.tensor(values, dtype=torch.float32)


def bf(values):
    return torch.tensor(values, dtype=torch.bfloat16)


def state(family: str, *, grad=None, master_delta=0.001, m1_delta=0.003, m2_delta=1e-5):
    base = fp([1000.0, -200.0, 4.0])
    m1 = fp([0.1, -0.2, 0.4])
    m2 = fp([0.01, 0.1, 0.4])
    return metric.FQNSnapshot(
        family=family, shard_key="rank0:dp-shard8:0/8:bf16-reduce",
        gradient=grad if grad is not None else bf([0.4, -0.3, 0.2]),
        master_before=base, master_after=base + fp([master_delta, -master_delta, master_delta]),
        m1_before=m1, m1_after=m1 + fp([m1_delta, -m1_delta, m1_delta]),
        m2_before=m2, m2_after=m2 + fp([m2_delta, m2_delta, m2_delta]),
    )


def inventory():
    return {
        "net.moe_gen.w": state("generation"),
        "net.action2llm.w": state("action"),
        "net.local_memory_runtime.core.w": state("local"),
    }


def test_identical_comparison_full_inventory_passes():
    a = inventory()
    b = inventory()
    r = metric.compare_fqn_inventory(a, b)
    assert len(r) == 3 and all(x.passed for x in r.values())
    assert all(x.delta_parameter.passed and x.absolute_m1_after.passed for x in r.values())
    assert r["net.moe_gen.w"].shard_key.startswith("rank0:")


def test_large_initial_weight_must_not_mask_wrong_tiny_update():
    a = fp([1000.0])
    b = fp([1000.0])
    source_after = fp([1000.0001])
    result = metric.compare_increment(a, source_after, b, b, role="delta_parameter")
    assert result.passed is False and result.reason == "one-sided-near-zero"
    # A whole-weight relative check would have misleadingly passed.
    assert metric.compare_tensor(source_after, b, metric.CANDIDATE_GRADIENT[torch.float32], role="wrong_full_weights").passed


@pytest.mark.parametrize("role,before,update", [
    ("delta_m1", 10.0, 1e-3), ("delta_m2", 5.0, 1e-4),
    ("delta_parameter", 1000.0, 1e-4),
])
def test_one_sided_missing_optimizer_update_fails(role, before, update):
    init = fp([before])
    updated = fp([before + update])
    result = metric.compare_increment(init, updated, init, init, role=role)
    assert not result.passed and result.relative_l2 > 0.99


def test_bf16_small_nonzero_vs_zero_gradient_fails_even_if_elementwise_passes():
    r = metric.compare_gradient(bf([0.004, 0.005]), bf([0.0, 0.0]))
    assert not r.passed
    assert r.elementwise_pass
    assert r.reason == "one-sided-near-zero"


def test_bf16_nonzero_gradient_strong_direction_mismatch_fails():
    r = metric.compare_gradient(bf([0.5, 0.2]), bf([-0.5, -0.2]))
    assert not r.passed and r.cosine < 0


def test_near_zero_double_zero_is_allowed_without_cosine_nan():
    result = metric.compare_gradient(torch.zeros(4, dtype=torch.float32), torch.zeros(4, dtype=torch.float32))
    assert result.passed and result.near_zero and result.cosine is None


def test_one_side_near_zero_is_not_allowed():
    r = metric.compare_tensor(fp([1e-4]), fp([0]), metric.CANDIDATE_GRADIENT[torch.float32], role="tiny")
    assert not r.passed


@pytest.mark.parametrize("bad", [None, torch.tensor([], dtype=torch.float32),
                                  torch.tensor([float("nan")]), torch.tensor([float("inf")])])
def test_missing_empty_nonfinite_tensor_fail_closed(bad):
    with pytest.raises(metric.EvidenceBlocked):
        metric.compare_gradient(fp([1.0]), bad)


def test_dtype_or_shape_difference_fails_closed():
    with pytest.raises(metric.EvidenceBlocked, match="dtype/shape"):
        metric.compare_gradient(fp([1.0]), bf([1.0]))
    with pytest.raises(metric.EvidenceBlocked, match="dtype/shape"):
        metric.compare_gradient(fp([1.0]), fp([1.0, 2.0]))


@pytest.mark.parametrize("role", ["delta_parameter", "delta_m1", "delta_m2"])
def test_optimizer_state_requires_fp32_master_and_moments(role):
    with pytest.raises(metric.EvidenceBlocked, match="fp32"):
        metric.compare_increment(bf([1]), bf([2]), bf([1]), bf([2]), role=role)


def test_optimizer_before_after_full_shape_must_match():
    with pytest.raises(metric.EvidenceBlocked, match="shape"):
        metric.compare_increment(fp([1]), fp([1, 2]), fp([1]), fp([1]), role="delta_parameter")


def test_misnamed_role_fails_closed():
    with pytest.raises(metric.EvidenceBlocked, match="unknown optimizer"):
        metric.compare_increment(fp([1]), fp([2]), fp([1]), fp([2]), role="unregistered")


def test_missing_action_local_and_generation_selected_fqn_fails():
    a = inventory()
    b = inventory()
    del b["net.action2llm.w"]
    with pytest.raises(metric.EvidenceBlocked, match="inventory"):
        metric.compare_fqn_inventory(a, b)
    with pytest.raises(metric.EvidenceBlocked, match="coverage"):
        metric.compare_fqn_inventory({"net.action2llm.w": state("action")},
                                    {"net.action2llm.w": state("action")})


def test_required_selected_fqn_gradient_none_not_filtered():
    a = inventory()
    b = inventory()
    a["net.moe_gen.w"] = replace(a["net.moe_gen.w"], gradient=None)
    with pytest.raises(metric.EvidenceBlocked, match="missing selected FQN"):
        metric.compare_fqn_inventory(a, b)


def test_mismatched_shard_identity_fails_before_values():
    a = inventory()
    b = inventory()
    b["net.action2llm.w"] = replace(b["net.action2llm.w"], shard_key="rank1:dp-shard8:1/8")
    with pytest.raises(metric.EvidenceBlocked, match="shard"):
        metric.compare_fqn_inventory(a, b)


def test_mismatched_family_fails():
    a = inventory()
    b = inventory()
    b["net.action2llm.w"] = replace(b["net.action2llm.w"], family="generation")
    with pytest.raises(metric.EvidenceBlocked, match="family"):
        metric.compare_fqn_inventory(a, b)


def test_optimizer_delta_difference_must_fail_even_if_gradients_match():
    a = inventory()
    b = inventory()
    v = b["net.local_memory_runtime.core.w"]
    b["net.local_memory_runtime.core.w"] = replace(v, master_after=v.master_before)
    result = metric.compare_fqn_inventory(a, b)
    assert result["net.local_memory_runtime.core.w"].gradient.passed
    assert not result["net.local_memory_runtime.core.w"].delta_parameter.passed
    assert not result["net.local_memory_runtime.core.w"].passed


def test_fast_state_requires_all_four_fp32_for_each_slot():
    vals = tuple(fp([1.0, 2.0]) for _ in range(4))
    assert len(metric.compare_local_fast_state({"rank0-slot0": vals}, {"rank0-slot0": vals})["rank0-slot0"]) == 4
    with pytest.raises(metric.EvidenceBlocked, match="four"):
        metric.compare_local_fast_state({"rank0-slot0": vals[:3]}, {"rank0-slot0": vals})
    with pytest.raises(metric.EvidenceBlocked, match="identity"):
        metric.compare_local_fast_state({"rank0-slot0": vals}, {"rank0-slot1": vals})
    with pytest.raises(metric.EvidenceBlocked, match="fp32"):
        metric.compare_local_fast_state({"rank0-slot0": vals}, {"rank0-slot0": (bf([1]), *vals[1:])})


def test_loss_components_must_match_not_just_total():
    a = {"vision": fp([1.5]), "action": fp([0.2]), "weighted_total": fp([1.7])}
    b = {"vision": fp([1.5]), "action": fp([0.25]), "weighted_total": fp([1.7])}
    res = metric.compare_losses(a, b)
    assert res["weighted_total"] and not res["action"]
    with pytest.raises(metric.EvidenceBlocked, match="components"):
        metric.compare_losses(a, {"weighted_total": fp([1.7])})


def test_discrete_matched_identity_and_stochastic_witness():
    contract = {"ConsumerKey": "r0-w0-0", "cfg_caption_sha": "a", "epsilon_sha": "b", "mask_sha": "c"}
    required = frozenset(contract)
    metric.assert_discrete_identical(contract, contract.copy(), required)
    altered = {**contract, "cfg_caption_sha": "DIFFERENT"}
    with pytest.raises(metric.EvidenceBlocked, match="cfg_caption_sha"):
        metric.assert_discrete_identical(contract, altered, required)
    with pytest.raises(metric.EvidenceBlocked, match="keys"):
        metric.assert_discrete_identical(contract, {"ConsumerKey": "r0-w0-0"}, required)


def test_metric_result_cannot_be_complete_without_loss_fast_or_selected_fqn():
    with pytest.raises(metric.EvidenceBlocked, match="incomplete"):
        metric.overall_candidate_pass({}, {"loss": True}, {})


def test_complete_candidate_metrics_produce_candidate_only_status():
    inv = metric.compare_fqn_inventory(inventory(), inventory())
    f = (fp([0]), fp([0]), fp([0]), fp([0]))
    fast = metric.compare_local_fast_state({"slot": f}, {"slot": f})
    losses = metric.compare_losses({"weighted_outer": fp([3])}, {"weighted_outer": fp([3])})
    assert metric.overall_candidate_pass(inv, losses, fast)


def test_nonfinite_numeric_limits_are_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        metric.Limits(float("nan"), 1e-4, 1e-3, 0.999, 1e-7)
