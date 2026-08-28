#!/usr/bin/env python3
"""CPU-only contract evidence for the stateless R08 LocalEvidenceEncoder."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import torch

from cosmos_framework.model.generator.mot.local_evidence import LocalEvidenceEncoder


def _git_head(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    torch.manual_seed(8)
    encoder = LocalEvidenceEncoder(evidence_dim=32, state_mean=torch.zeros(8), state_std=torch.ones(8))
    mask = torch.tensor([[True, True, True, True], [False, False, True, True]])
    inputs = {
        "history_visual_summary": torch.randn(2, 4, 96),
        "local_history_action": torch.randn(2, 4, 10),
        "history_age_steps": torch.tensor([[4, 3, 2, 1], [0, 0, 2, 1]]),
        "history_dt_s": torch.tensor([[[0.4], [0.3], [0.2], [0.1]], [[0.0], [0.0], [0.2], [0.1]]]),
        "history_mask": mask,
        "history_state": torch.randn(2, 4, 8),
    }
    output = encoder(**inputs)
    output.sum().backward()
    requires_stats = False
    try:
        LocalEvidenceEncoder(evidence_dim=16)(**inputs)
    except ValueError:
        requires_stats = True
    checks = {
        "output_shape": tuple(output.shape) == (2, 4, 32),
        "output_finite": bool(torch.isfinite(output).all()),
        "masked_output_exact_zero": bool(torch.count_nonzero(output[~mask]) == 0),
        "all_trainable_params_have_finite_grad": all(
            parameter.grad is not None and torch.isfinite(parameter.grad).all() for parameter in encoder.parameters()
        ),
        "state_requires_explicit_train_split_stats": requires_stats,
        "stateless_no_recurrent_modules": not any(
            "gru" in name.lower() or "recurrent" in name.lower() for name, _ in encoder.named_modules()
        ),
    }
    result = {
        "schema_version": 1,
        "gate": "G0-R08-STEP4-LOCAL-EVIDENCE-ENCODER",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "root_commit": _git_head(root),
        "submodule_commit": _git_head(root / "cosmos-framework"),
        "checks": checks,
        "state_runtime_status": "DISABLED_PENDING_TRAIN_SPLIT_STATS",
        "state_adapter_contract": "history_state is rejected unless explicit state_mean/state_std are provided.",
        "output": {
            "shape": list(output.shape),
            "sha256": hashlib.sha256(output.detach().contiguous().numpy().tobytes()).hexdigest(),
        },
    }
    output_path = root / "artifacts/g0/r08/step4_local_evidence_encoder.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if result["status"] != "PASS":
        raise SystemExit("R08 LocalEvidenceEncoder contract failed")


if __name__ == "__main__":
    main()
