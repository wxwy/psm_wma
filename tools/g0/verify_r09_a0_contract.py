#!/usr/bin/env python3
"""Emit the CPU-only R09-A0 contract evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import torch

from cosmos_framework.model.generator.mot.local_evidence import RecurrentLocalMemoryBackend


def revision(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def clean(path: Path) -> bool:
    return not subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.manual_seed(4)
    backend = RecurrentLocalMemoryBackend(evidence_dim=3, local_dim=5)
    evidence = torch.randn(3, 4, 3)
    mask = torch.tensor([[True, True, True, True], [False, False, False, False], [True, False, True, False]])
    tokens, state, present = backend.replay(evidence, mask)
    reset = backend.reset_mask(state, torch.tensor([False, False, True]))
    _, first, _ = backend.replay(evidence[:, :2], mask[:, :2])
    _, second, _ = backend.replay(evidence[:, 2:], mask[:, 2:], first.detach())
    state_diff = float((second - state).abs().max().detach())
    token_diff = float((second[:, None] - tokens).abs().max().detach())
    carried_exact = bool(torch.equal(first.detach(), first))
    masked = evidence.clone(); masked[:, 1] = 1e6
    masked_state = backend.replay(masked, mask)[1]
    masked_inert = bool(torch.equal(masked_state[mask[:, 1] == 0], state[mask[:, 1] == 0]))
    order = torch.tensor([2, 0, 1])
    permuted = backend.replay(evidence[order], mask[order])[1]
    permutation = bool(torch.allclose(permuted, state[order], rtol=0, atol=1e-6))
    torch.manual_seed(11)
    with torch.device("meta"):
        meta = RecurrentLocalMemoryBackend(evidence_dim=3, local_dim=5)
    meta.to_empty(device="cpu")
    meta.cell.reset_parameters()
    values = [p.detach().clone() for p in meta.parameters()]
    torch.manual_seed(11)
    with torch.device("meta"):
        repeat = RecurrentLocalMemoryBackend(evidence_dim=3, local_dim=5)
    repeat.to_empty(device="cpu"); repeat.cell.reset_parameters()
    init_ok = all(torch.isfinite(p).all() and torch.equal(p, q) for p, q in zip(values, repeat.parameters(), strict=True))
    root = Path(__file__).resolve().parents[2]
    gitlink = subprocess.check_output(["git", "-C", str(root), "ls-tree", "HEAD", "cosmos-framework"], text=True).split()[2]
    checks = {"all_mask_absent": bool(not present[1] and torch.count_nonzero(tokens[1]) == 0), "partial_reset": bool(torch.equal(reset[[0, 1]], state[[0, 1]]) and torch.count_nonzero(reset[2]) == 0), "masked_timestep_inert": masked_inert, "batch_permutation_isolation": permutation, "carried_value_exact": carried_exact, "meta_init": init_ok}
    passed = all(checks.values()) and state_diff <= 1e-6 and token_diff <= 1e-6
    result = {"schema_version":"r09_a0_contract_v2","status":"PASS" if passed else "FAIL","root_revision":revision(root),"submodule_revision":revision(root / "cosmos-framework"),"gitlink_revision":gitlink,"tracked_clean":{"root":clean(root),"submodule":clean(root / "cosmos-framework")},"provenance_valid":revision(root / "cosmos-framework")==gitlink,"tool_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"backend":"recurrent_latent","state":{"shape":list(state.shape),"dtype":str(state.dtype),"bytes":state.numel()*state.element_size()},"input_shape":list(evidence.shape),"token_shape":list(tokens.shape),"trainable_param_count":sum(p.numel() for p in backend.parameters()),"trainable_prefixes":["cell"],"mixed_presence":present.tolist(),"assertions":checks,"segment":{"state_max_abs_diff":state_diff,"token_max_abs_diff":token_diff,"tolerance":1e-6,"pass":state_diff<=1e-6 and token_diff<=1e-6},"init":{"seed":11,"path":"meta-to_empty-explicit-reset_parameters"},"command_hash":hashlib.sha256("verify_r09_a0_contract".encode()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
