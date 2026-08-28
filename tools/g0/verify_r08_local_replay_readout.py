#!/usr/bin/env python3
"""CPU-only contract evidence for the R08 stateless Local replay readout."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import torch

from cosmos_framework.model.generator.mot.local_evidence import StatelessLocalReplayReadout


def _git_head(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    torch.manual_seed(8)
    readout = StatelessLocalReplayReadout(evidence_dim=4, local_dim=32, hidden_dim=8)
    evidence = torch.arange(3 * 4 * 4, dtype=torch.float32).reshape(3, 4, 4) / 16.0
    mask = torch.tensor([[True, True, True, True], [False, False, False, False], [False, True, True, True]])
    mean, latest, has_valid = readout.summarize(evidence, mask)
    output = readout(evidence, mask)
    output.sum().backward()
    checks = {
        "output_shape": tuple(output.shape) == (3, 1, 32),
        "output_finite": bool(torch.isfinite(output).all()),
        "all_mask_exact_zero": bool(torch.count_nonzero(output[1]) == 0),
        "masked_mean_exact": bool(torch.equal(mean[1], torch.zeros(4))),
        "latest_valid_exact": bool(torch.equal(latest[2], evidence[2, 3])),
        "all_trainable_params_have_finite_grad": all(
            parameter.grad is not None and torch.isfinite(parameter.grad).all() for parameter in readout.parameters()
        ),
        "stateless_no_recurrent_modules": not any(
            "gru" in name.lower() or "recurrent" in name.lower() for name, _ in readout.named_modules()
        ),
        "valid_flags": has_valid.tolist() == [True, False, True],
    }
    result = {
        "schema_version": 1,
        "gate": "G0-R08-STEP5-STATELESS-LOCAL-REPLAY-READOUT",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "root_commit": _git_head(root),
        "submodule_commit": _git_head(root / "cosmos-framework"),
        "checks": checks,
        "output": {
            "shape": list(output.shape),
            "sha256": hashlib.sha256(output.detach().contiguous().numpy().tobytes()).hexdigest(),
        },
    }
    output_path = root / "artifacts/g0/r08/step5_stateless_local_replay_readout.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if result["status"] != "PASS":
        raise SystemExit("R08 StatelessLocalReplayReadout contract failed")


if __name__ == "__main__":
    main()
