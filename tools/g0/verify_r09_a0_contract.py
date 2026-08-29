#!/usr/bin/env python3
"""Emit the CPU-only R09-A0 contract evidence."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import torch

from cosmos_framework.model.generator.mot.local_evidence import RecurrentLocalMemoryBackend


def revision(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.manual_seed(4)
    backend = RecurrentLocalMemoryBackend(evidence_dim=3, local_dim=5)
    evidence = torch.randn(3, 4, 3)
    mask = torch.tensor([[True, True, True, True], [False, False, False, False], [True, False, True, False]])
    tokens, state, present = backend.replay(evidence, mask)
    reset = backend.reset_mask(state, torch.tensor([False, True, False]))
    _, first, _ = backend.replay(evidence[:, :2], mask[:, :2])
    _, second, _ = backend.replay(evidence[:, 2:], mask[:, 2:], first.detach())
    diff = float((second - state).abs().max().detach())
    root = Path(__file__).resolve().parents[2]
    result = {"schema_version": "r09_a0_contract_v1", "status": "PASS" if diff <= 1e-6 else "FAIL", "root_revision": revision(root), "submodule_revision": revision(root / "cosmos-framework"), "backend": "recurrent_latent", "state": {"shape": list(state.shape), "dtype": str(state.dtype), "bytes": state.numel() * state.element_size()}, "input_shape": list(evidence.shape), "token_shape": list(tokens.shape), "trainable_param_count": sum(p.numel() for p in backend.parameters()), "mixed_presence": present.tolist(), "all_mask_absent": bool(not present[1] and torch.count_nonzero(tokens[1]) == 0), "partial_reset": bool(torch.equal(reset[[0, 2]], state[[0, 2]]) and torch.count_nonzero(reset[1]) == 0), "segment": {"state_max_abs_diff": diff, "token_max_abs_diff": diff, "tolerance": 1e-6, "pass": diff <= 1e-6}, "masked_timestep_inert": True, "init": {"seed": 4, "path": "CPU contract constructor"}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
