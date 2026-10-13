"""Proposed Gate B0 CPU numerical-metric contracts, NOT frozen B1 acceptance.

No implicit averaged-FQN PASS, no hidden NaN/Inf filtering, and no GPU work.
The Owner must freeze or change these proposed thresholds before Gate B1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import torch


@dataclass(frozen=True)
class ComparisonLimits:
    atol: float
    rtol: float
    relative_l2: float
    min_cosine: float
    norm_floor: float

    def __post_init__(self) -> None:
        if not (self.atol > 0 and self.rtol > 0 and self.relative_l2 > 0 and
                0 < self.min_cosine <= 1 and self.norm_floor > 0):
            raise ValueError("invalid predeclared numeric limits")


# Provisional numbers from GPT Round2 Design §6: NOT frozen by the Owner.
PROPOSED_GRAD_LIMITS: Mapping[torch.dtype, ComparisonLimits] = {
    torch.float32: ComparisonLimits(1e-6, 1e-4, 2e-3, 0.9999, 1e-7),
    torch.float64: ComparisonLimits(1e-6, 1e-4, 2e-3, 0.9999, 1e-7),
    torch.bfloat16: ComparisonLimits(2e-2, 2e-2, 3e-2, 0.999, 2e-5),
}


@dataclass(frozen=True)
class MetricEvidence:
    shape: tuple[int, ...]
    dtype: str
    elements: int
    relative_l2: float
    max_abs: float
    cosine: float | None
    reference_norm: float
    target_norm: float
    near_zero: bool
    elementwise_pass: bool
    passed: bool
    reason: str


def compare_selected_gradient(reference: torch.Tensor | None,
                              target: torch.Tensor | None, *,
                              limits: Mapping[torch.dtype, ComparisonLimits] = PROPOSED_GRAD_LIMITS,
                              required: bool = True) -> MetricEvidence:
    """Per-FQN pass requires *all* metrics, not aggregate-group smoothing."""
    if reference is None or target is None:
        raise ValueError("gradient missing for selected FQN" if required else "optional gradient missing: separate inventory policy required")
    if reference.shape != target.shape or reference.dtype != target.dtype:
        raise ValueError("FQN gradient shape/dtype mismatch")
    if reference.dtype not in limits or reference.numel() == 0:
        raise ValueError("unsupported gradient storage dtype or empty gradient")
    if reference.device.type != "cpu" or target.device.type != "cpu":
        raise ValueError("CPU metric accepts only read-only CPU tensor copies")
    if not bool(torch.isfinite(reference).all()) or not bool(torch.isfinite(target).all()):
        raise ValueError("nonfinite gradient")
    config = limits[reference.dtype]
    a = reference.reshape(-1).to(torch.float64)
    b = target.reshape(-1).to(torch.float64)
    d = b - a
    na, nb = float(torch.linalg.vector_norm(a)), float(torch.linalg.vector_norm(b))
    nd = float(torch.linalg.vector_norm(d))
    n = a.numel()
    threshold = config.norm_floor * (n ** 0.5)
    z_a, z_b = na <= threshold, nb <= threshold
    maxabs = float(d.abs().max())
    elementwise = bool(torch.all(d.abs() <= config.atol + config.rtol * a.abs()))
    rel = nd / max(na, nb, threshold)
    if z_a != z_b:
        return MetricEvidence(tuple(reference.shape), str(reference.dtype), n, rel, maxabs, None,
                              na, nb, False, elementwise, False, "one-sided-near-zero")
    if z_a and z_b:
        rms = nd / (n ** 0.5)
        passed = maxabs <= config.atol and rms <= config.norm_floor
        return MetricEvidence(tuple(reference.shape), str(reference.dtype), n, rel, maxabs, None,
                              na, nb, True, elementwise, passed, "both-near-zero" if passed else "near-zero-exceeds-floor")
    cosine = float(torch.dot(a, b) / (na * nb))
    passed = elementwise and rel <= config.relative_l2 and cosine >= config.min_cosine
    return MetricEvidence(tuple(reference.shape), str(reference.dtype), n, rel, maxabs,
                          cosine, na, nb, False, elementwise, passed, "ok" if passed else "numerical-threshold-exceeded")
