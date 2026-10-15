"""Pure CPU metric engine for V3 Packed128 Gate B1 (NOT a GPU runner).

Thresholds are Owner-frozen r2 on 2026-10-15, before any real GPU data. The engine
compares already captured *real* native FSDP rank-local tensors: it does not
perform DCP load, local scan, stochastic injection or optimizer steps.

Unverifiable/missing tensor and discrete inputs fail closed. A passing metric
report cannot authorize B1 GPU execution, checkpoint migration, or training.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

import torch

from v3_gateb1_authority import OWNER_FROZEN_NUMERIC_POLICY, assert_numeric_policy_frozen

assert_numeric_policy_frozen()


class EvidenceBlocked(ValueError):
    """Source/target evidence is insufficient to evaluate the numerical gate."""


FAMILIES = frozenset({"generation", "action", "local"})


@dataclass(frozen=True)
class Limits:
    atol: float
    rtol: float
    relative_l2: float
    min_cosine: float
    norm_floor: float

    def __post_init__(self) -> None:
        fields = (self.atol, self.rtol, self.relative_l2, self.min_cosine, self.norm_floor)
        if not all(math.isfinite(x) and x > 0 for x in fields) or self.min_cosine > 1:
            raise ValueError("invalid or non-finite pre-registered threshold")


# Single Owner-frozen r2 source; historical CANDIDATE_* names remain as
# backwards-compatible aliases and do NOT mean thresholds are still provisional.
_FROZEN = OWNER_FROZEN_NUMERIC_POLICY
CANDIDATE_GRADIENT: Mapping[torch.dtype, Limits] = {
    torch.float32: Limits(**_FROZEN["gradient_fp32_and_fast_state"]),
    torch.float64: Limits(**_FROZEN["gradient_fp32_and_fast_state"]),
    torch.bfloat16: Limits(**_FROZEN["gradient_bf16"]),
}
CANDIDATE_INCREMENT: Mapping[str, Limits] = {
    "delta_parameter": Limits(**_FROZEN["delta_parameter_fp32"]),
    "delta_m1": Limits(**_FROZEN["delta_m1_fp32"]),
    "delta_m2": Limits(**_FROZEN["delta_m2_fp32"]),
}
CANDIDATE_LOSS = (_FROZEN["loss_fp32"]["atol"], _FROZEN["loss_fp32"]["rtol"])
FROZEN_LOSS_BY_DTYPE = {
    torch.float32: CANDIDATE_LOSS,
    torch.float64: CANDIDATE_LOSS,
    torch.bfloat16: (_FROZEN["loss_bf16"]["atol"], _FROZEN["loss_bf16"]["rtol"]),
}


@dataclass(frozen=True)
class Metric:
    passed: bool
    reason: str
    dtype: str
    shape: tuple[int, ...]
    count: int
    reference_norm: float
    target_norm: float
    relative_l2: float
    cosine: float | None
    max_abs: float
    rms_difference: float
    elementwise_pass: bool
    near_zero: bool


def compare_tensor(reference: torch.Tensor | None, target: torch.Tensor | None, limits: Limits,
                   *, role: str) -> Metric:
    """No missing/shape/dtype/nonfinite tensors; strict AND of normal metrics."""
    if reference is None or target is None:
        raise EvidenceBlocked(f"{role}: required tensor is missing")
    if not isinstance(reference, torch.Tensor) or not isinstance(target, torch.Tensor):
        raise EvidenceBlocked(f"{role}: expected torch.Tensor")
    if reference.device.type != "cpu" or target.device.type != "cpu":
        raise EvidenceBlocked(f"{role}: only already-captured CPU copies are accepted")
    if reference.dtype != target.dtype or reference.shape != target.shape or reference.numel() == 0:
        raise EvidenceBlocked(f"{role}: dtype/shape mismatch or empty tensor")
    if not reference.is_floating_point() or not target.is_floating_point():
        raise EvidenceBlocked(f"{role}: non-floating evidence tensor")
    if not torch.isfinite(reference).all().item() or not torch.isfinite(target).all().item():
        raise EvidenceBlocked(f"{role}: NaN or infinity")

    a = reference.detach().reshape(-1).to(torch.float64)
    b = target.detach().reshape(-1).to(torch.float64)
    d = b - a
    n = a.numel()
    na = float(torch.linalg.vector_norm(a))
    nb = float(torch.linalg.vector_norm(b))
    nd = float(torch.linalg.vector_norm(d))
    max_abs = float(d.abs().max())
    rms = nd / math.sqrt(n)
    floor = limits.norm_floor * math.sqrt(n)
    rel = nd / max(na, nb, floor)
    element = bool((d.abs() <= limits.atol + limits.rtol * a.abs()).all().item())
    common = dict(dtype=str(reference.dtype), shape=tuple(reference.shape), count=n,
                  reference_norm=na, target_norm=nb, relative_l2=rel, max_abs=max_abs,
                  rms_difference=rms, elementwise_pass=element)
    za, zb = na <= floor, nb <= floor
    if za != zb:
        return Metric(passed=False, reason="one-sided-near-zero", cosine=None, near_zero=False, **common)
    if za:
        ok = max_abs <= limits.atol and rms <= limits.norm_floor
        return Metric(passed=ok, reason="both-near-zero" if ok else "near-zero-limit-exceeded",
                      cosine=None, near_zero=True, **common)
    cos = float(torch.dot(a, b) / (na * nb))
    ok = element and rel <= limits.relative_l2 and cos >= limits.min_cosine
    return Metric(passed=ok, reason="ok" if ok else "threshold-exceeded",
                  cosine=cos, near_zero=False, **common)


def compare_gradient(reference: torch.Tensor | None, target: torch.Tensor | None) -> Metric:
    if reference is None:
        raise EvidenceBlocked("gradient: missing selected FQN")
    try:
        limits = CANDIDATE_GRADIENT[reference.dtype]
    except (KeyError, AttributeError) as exc:
        raise EvidenceBlocked("gradient: unsupported observed dtype") from exc
    return compare_tensor(reference, target, limits, role="selected_gradient")


def compare_increment(reference_before: torch.Tensor | None, reference_after: torch.Tensor | None,
                      target_before: torch.Tensor | None, target_after: torch.Tensor | None,
                      *, role: str) -> Metric:
    """Compare FP32 *updates*, never the large unmodified parameter value."""
    if role not in CANDIDATE_INCREMENT:
        raise EvidenceBlocked(f"unknown optimizer increment role: {role}")
    tensors = (reference_before, reference_after, target_before, target_after)
    if any(not isinstance(t, torch.Tensor) for t in tensors):
        raise EvidenceBlocked(f"{role}: before/after state missing")
    if any(t.dtype != torch.float32 or t.device.type != "cpu" for t in tensors):
        raise EvidenceBlocked(f"{role}: authoritative fp32 CPU master/moment state required")
    if len({tuple(t.shape) for t in tensors}) != 1:
        raise EvidenceBlocked(f"{role}: before/after shape mismatch")
    if any(not torch.isfinite(t).all().item() for t in tensors):
        raise EvidenceBlocked(f"{role}: nonfinite optimizer state")
    source_delta = reference_after.detach().to(torch.float64) - reference_before.detach().to(torch.float64)
    target_delta = target_after.detach().to(torch.float64) - target_before.detach().to(torch.float64)
    # Lossless fp64 subtraction preserves tiny updates even if P_before is huge.
    return compare_tensor(source_delta, target_delta, CANDIDATE_INCREMENT[role], role=role)


@dataclass(frozen=True)
class FQNSnapshot:
    family: str
    shard_key: str  # exact same rank/mesh/FSDP shard descriptor on both legs
    gradient: torch.Tensor | None
    master_before: torch.Tensor | None
    master_after: torch.Tensor | None
    m1_before: torch.Tensor | None
    m1_after: torch.Tensor | None
    m2_before: torch.Tensor | None
    m2_after: torch.Tensor | None


@dataclass(frozen=True)
class FQNComparison:
    family: str
    shard_key: str
    gradient: Metric
    delta_parameter: Metric
    delta_m1: Metric
    delta_m2: Metric
    absolute_m1_after: Metric
    absolute_m2_after: Metric
    passed: bool


def compare_fqn_inventory(reference: Mapping[str, FQNSnapshot],
                          target: Mapping[str, FQNSnapshot]) -> dict[str, FQNComparison]:
    """Full selected-FQN inventory, no filtering of missing/None or small gradients."""
    if not reference or set(reference) != set(target):
        raise EvidenceBlocked("optimizer FQN inventory differs or empty")
    if not FAMILIES.issubset({x.family for x in reference.values()}):
        raise EvidenceBlocked("missing generation/action/local FQN coverage")
    comparisons: dict[str, FQNComparison] = {}
    for name in sorted(reference):
        if not name or not isinstance(name, str):
            raise EvidenceBlocked("invalid selected FQN")
        a, b = reference[name], target[name]
        if a.family not in FAMILIES or a.family != b.family:
            raise EvidenceBlocked(f"{name}: mismatched FQN family")
        if not a.shard_key or a.shard_key != b.shard_key:
            raise EvidenceBlocked(f"{name}: different/missing local FSDP shard identity")
        grad = compare_gradient(a.gradient, b.gradient)
        delta_p = compare_increment(a.master_before, a.master_after, b.master_before, b.master_after,
                                    role="delta_parameter")
        delta_m1 = compare_increment(a.m1_before, a.m1_after, b.m1_before, b.m1_after, role="delta_m1")
        delta_m2 = compare_increment(a.m2_before, a.m2_after, b.m2_before, b.m2_after, role="delta_m2")
        abs_m1 = compare_tensor(a.m1_after, b.m1_after, CANDIDATE_GRADIENT[torch.float32], role="moment1_after")
        abs_m2 = compare_tensor(a.m2_after, b.m2_after, CANDIDATE_GRADIENT[torch.float32], role="moment2_after")
        metrics = (grad, delta_p, delta_m1, delta_m2, abs_m1, abs_m2)
        comparisons[name] = FQNComparison(a.family, a.shard_key, *metrics, passed=all(m.passed for m in metrics))
    return comparisons


def compare_local_fast_state(reference: Mapping[str, tuple[torch.Tensor, ...]],
                             target: Mapping[str, tuple[torch.Tensor, ...]]) -> dict[str, tuple[Metric, ...]]:
    """Every active slot has all four fp32 Fast State tensors."""
    if not reference or set(reference) != set(target):
        raise EvidenceBlocked("fast state active-slot identity differs or empty")
    out: dict[str, tuple[Metric, ...]] = {}
    for slot in sorted(reference):
        a, b = reference[slot], target[slot]
        if len(a) != 4 or len(b) != 4:
            raise EvidenceBlocked(f"{slot}: four Fast State tensors are mandatory")
        if any(x is None or x.dtype != torch.float32 for x in (*a, *b)):
            raise EvidenceBlocked(f"{slot}: Fast State must be actual fp32 tensors")
        out[slot] = tuple(compare_tensor(x, y, CANDIDATE_GRADIENT[torch.float32], role=f"fast_state:{slot}:{i}")
                          for i, (x, y) in enumerate(zip(a, b, strict=True)))
    return out


def compare_losses(reference: Mapping[str, torch.Tensor],
                   target: Mapping[str, torch.Tensor]) -> dict[str, bool]:
    """All *active weighted* native losses must be present; no unknown aux omitted."""
    if not reference or set(reference) != set(target):
        raise EvidenceBlocked("loss components differ or none provided")
    out = {}
    for name in sorted(reference):
        a, b = reference[name], target[name]
        if not isinstance(a, torch.Tensor) or not isinstance(b, torch.Tensor) or a.shape != b.shape or a.numel() != 1:
            raise EvidenceBlocked(f"loss {name}: scalar tensor required")
        if a.dtype != b.dtype or a.device.type != "cpu" or b.device.type != "cpu":
            raise EvidenceBlocked(f"loss {name}: tensor dtype/device mismatch")
        if not torch.isfinite(a).all().item() or not torch.isfinite(b).all().item():
            raise EvidenceBlocked(f"loss {name}: nonfinite")
        try:
            atol, rtol = FROZEN_LOSS_BY_DTYPE[a.dtype]
        except KeyError as exc:
            raise EvidenceBlocked(f"loss {name}: unapproved storage dtype") from exc
        out[name] = abs(float(a) - float(b)) <= atol + rtol * abs(float(a))
    return out


def assert_discrete_identical(reference: Mapping[str, object], target: Mapping[str, object],
                              required_keys: frozenset[str]) -> None:
    if not required_keys or set(reference) != set(target) or not required_keys.issubset(reference):
        raise EvidenceBlocked("discrete contract keys missing or different")
    for key in sorted(reference):
        if reference[key] != target[key]:
            raise EvidenceBlocked(f"discrete contract differs: {key}")


def overall_candidate_pass(fqn: Mapping[str, FQNComparison], losses: Mapping[str, bool],
                           fast: Mapping[str, tuple[Metric, ...]]) -> bool:
    if not fqn or not losses or not fast:
        raise EvidenceBlocked("incomplete B1 metric evidence")
    return all(x.passed for x in fqn.values()) and all(losses.values()) and all(
        m.passed for slot in fast.values() for m in slot
    )
