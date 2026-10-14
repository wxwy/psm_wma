"""No-GPU contract tests for the FSDP2 optimizer snapshot seam."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v3_gateb1_fsdp_capture as cap  # noqa: E402
import v3_gateb1_metrics as numeric  # noqa: E402


class ToyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.moe_gen = nn.Parameter(torch.tensor([1.0, 2.0], dtype=torch.float32))
        self.action2llm = nn.Parameter(torch.tensor([1.0, 2.0], dtype=torch.float32))
        self.local_memory_runtime = nn.Parameter(torch.tensor([1.0, 2.0], dtype=torch.float32))


class FakeFusedAdam:
    def __init__(self, model):
        self.param_groups = [{"params": list(model.parameters()), "step": torch.tensor(1300, dtype=torch.int32)}]
        self.master_weights = False
        self.state = {p: {"exp_avg": torch.ones_like(p), "exp_avg_sq": torch.ones_like(p)}
                      for p in model.parameters()}
        for p in model.parameters():
            p.grad = torch.full_like(p, 0.2)

    def step(self):
        self.param_groups[0]["step"] += 1
        for p in self.param_groups[0]["params"]:
            p.data -= 0.001
            self.state[p]["exp_avg"] += 0.1
            self.state[p]["exp_avg_sq"] += 0.01


def setup():
    m = ToyModel(); o = FakeFusedAdam(m)
    return m, o


def test_real_parameter_and_moments_captured_at_correct_boundary():
    m, o = setup()
    s = cap.NativeOptimizerCapture(m, o, rank=0, expected_fqns=set(dict(m.named_parameters())))
    s.before_optimizer_step()
    o.step()
    results = s.after_optimizer_step()
    assert len(results) == 3
    assert all(v.family in numeric.FAMILIES for v in results.values())
    assert all(v.master_before.dtype == torch.float32 for v in results.values())
    assert all((v.master_after - v.master_before).abs().max().item() > 0 for v in results.values())
    r = numeric.compare_fqn_inventory(results, results)
    assert all(x.passed for x in r.values())


def test_capture_never_mutates_optimizer_or_model():
    m, o = setup()
    before = {k: p.detach().clone() for k, p in m.named_parameters()}
    s = cap.NativeOptimizerCapture(m, o, rank=0)
    s.before_optimizer_step()
    for name, p in m.named_parameters():
        torch.testing.assert_close(p, before[name], atol=0, rtol=0)
    assert o.param_groups[0]["step"].item() == 1300


def test_missing_optimizer_selected_group_fails():
    m, o = setup()
    with pytest.raises(cap.CaptureBlocked, match="coverage"):
        cap.NativeOptimizerCapture(m, o, rank=0, expected_fqns={"moe_gen"})


def test_after_without_pre_fails():
    m, o = setup()
    with pytest.raises(cap.CaptureBlocked, match="first capture"):
        cap.NativeOptimizerCapture(m, o, rank=0).after_optimizer_step()


def test_absent_moment_fails_not_zero_filled():
    m, o = setup()
    del o.state[m.action2llm]["exp_avg_sq"]
    with pytest.raises(cap.CaptureBlocked, match="missing restored"):
        cap.NativeOptimizerCapture(m, o, rank=0).before_optimizer_step()


def test_missing_gradient_fails():
    m, o = setup()
    m.moe_gen.grad = None
    with pytest.raises(cap.CaptureBlocked, match="required runtime"):
        cap.NativeOptimizerCapture(m, o, rank=0).before_optimizer_step()


def test_one_optimizer_step_exactly_required():
    m, o = setup(); s = cap.NativeOptimizerCapture(m, o, rank=0)
    s.before_optimizer_step()
    with pytest.raises(cap.CaptureBlocked, match="missing/multiple"):
        s.after_optimizer_step()
    o.step(); o.step()
    with pytest.raises(cap.CaptureBlocked, match="missing/multiple"):
        s.after_optimizer_step()


def test_fp32_master_missing_for_bf16_param_fails():
    m, o = setup()
    o.master_weights = True
    with pytest.raises(cap.CaptureBlocked, match="master unavailable"):
        cap.NativeOptimizerCapture(m, o, rank=0).before_optimizer_step()


def test_unsafe_param_dtype_fails():
    m, o = setup()
    # With master_weights disabled, the optimizer-owned param is the authoritative FP32 master.
    m.moe_gen.data = m.moe_gen.data.bfloat16()
    m.moe_gen.grad = torch.ones_like(m.moe_gen.data)
    with pytest.raises(cap.CaptureBlocked, match="FP32 optimizer parameter"):
        cap.NativeOptimizerCapture(m, o, rank=0).before_optimizer_step()


def test_no_selected_local_fqn_fails():
    m, o = setup()
    o.param_groups[0]["params"] = [m.moe_gen, m.action2llm]
    with pytest.raises(cap.CaptureBlocked, match="family"):
        cap.NativeOptimizerCapture(m, o, rank=0)


def test_captured_shard_keys_include_rank():
    m, o = setup()
    s = cap.NativeOptimizerCapture(m, o, rank=6)
    s.before_optimizer_step()
    assert all('"rank":6' in v.shard_key for v in s._pre.values())


def test_malformed_rank_fails_closed():
    m, o = setup()
    for rank in (-1, 8, "0"):
        with pytest.raises(cap.CaptureBlocked, match="rank"):
            cap.NativeOptimizerCapture(m, o, rank=rank)
