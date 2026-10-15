"""Immutable B1 diagnostic authority: B0 fingerprint and Owner-frozen r2 limits.

Owner ratified the r2 policy 2026-10-15 BEFORE any real GPU numeric data.
This module is stdlib-only so --mode prepare does not import torch/Cosmos.
Numeric freeze does not authorize GPU execution.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

B0_FULL_SHARD_FINGERPRINT = "2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999"
FROZEN_NUMERIC_POLICY_SHA256 = "bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda"

OWNER_FROZEN_NUMERIC_POLICY: dict[str, Any] = {
    "schema": "psm_v3_gate_b1_r2_owner_numeric_policy_v1",
    "loss_fp32": {
        "atol": 0.000001,
        "rtol": 0.00001
    },
    "loss_bf16": {
        "atol": 0.02,
        "rtol": 0.02
    },
    "gradient_fp32_and_fast_state": {
        "atol": 0.000001,
        "rtol": 0.0001,
        "relative_l2": 0.002,
        "min_cosine": 0.9999,
        "norm_floor": 1e-7
    },
    "gradient_bf16": {
        "atol": 0.02,
        "rtol": 0.02,
        "relative_l2": 0.03,
        "min_cosine": 0.999,
        "norm_floor": 0.00002
    },
    "delta_parameter_fp32": {
        "atol": 1e-9,
        "rtol": 0.03,
        "relative_l2": 0.03,
        "min_cosine": 0.999,
        "norm_floor": 1e-10
    },
    "delta_m1_fp32": {
        "atol": 1e-8,
        "rtol": 0.03,
        "relative_l2": 0.03,
        "min_cosine": 0.999,
        "norm_floor": 1e-9
    },
    "delta_m2_fp32": {
        "atol": 1e-12,
        "rtol": 0.06,
        "relative_l2": 0.05,
        "min_cosine": 0.995,
        "norm_floor": 1e-13
    },
    "discrete": "exact",
    "near_zero": "one-sided-fails;both near-zero require maxabs<=atol and rms<=norm_floor",
    "coverage": "each selected FQN and each of four local fast state tensors; all full/terminal P0/P1 two repeats per leg",
    "rounding": "FP64 diagnostic calculations, fail closed on unexpected dtype"
}


def numeric_policy_sha256() -> str:
    """Canonical SHA256 of the Owner-approved, pre-GPU r2 policy values."""
    canonical = json.dumps(
        OWNER_FROZEN_NUMERIC_POLICY, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assert_numeric_policy_frozen() -> None:
    if numeric_policy_sha256() != FROZEN_NUMERIC_POLICY_SHA256:
        raise ValueError("B1 Owner-frozen numeric policy values changed")
