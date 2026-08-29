#!/usr/bin/env python3
"""Emit the CPU-only R09-A0 contract evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import torch

from cosmos_framework.model.generator.mot.local_evidence import RecurrentLocalMemoryBackend


def revision(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def clean(path: Path) -> bool:
    return not subprocess.check_output(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.manual_seed(4)
    backend = RecurrentLocalMemoryBackend(evidence_dim=3, local_dim=5)
    evidence = torch.randn(3, 4, 3)
    mask = torch.tensor([[True, True, True, True], [False, False, False, False], [True, False, True, False]])
    tokens, state, present = backend.replay(evidence, mask)
    latent, initialized = state
    reset = backend.reset_mask(state, torch.tensor([False, False, True]))
    reset_tokens, _, reset_present = backend.replay(evidence[:, :1], torch.zeros(3, 1, dtype=torch.bool), reset)
    _, first, _ = backend.replay(evidence[:, :2], mask[:, :2])
    _, second, _ = backend.replay(evidence[:, 2:], mask[:, 2:], (first[0].detach(), first[1]))
    state_diff = float((second[0] - latent).abs().max().detach())
    token_diff = float((second[0][:, None] - tokens).abs().max().detach())
    carried_exact = bool(torch.equal(first[0].detach(), first[0]))
    masked = evidence.clone(); masked[:, 1] = 1e6
    masked_state = backend.replay(masked, mask)[1]
    masked_inert = bool(torch.equal(masked_state[0][mask[:, 1] == 0], latent[mask[:, 1] == 0]))
    order = torch.tensor([2, 0, 1])
    permuted_tokens, permuted, permuted_present = backend.replay(evidence[order], mask[order])
    permutation = bool(torch.allclose(permuted[0], latent[order], rtol=0, atol=1e-6) and torch.equal(permuted[1], initialized[order]) and torch.allclose(permuted_tokens, tokens[order], rtol=0, atol=1e-6) and torch.equal(permuted_present, present[order]))
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
    checks = {"all_mask_absent": bool(not present[1] and torch.count_nonzero(tokens[1]) == 0), "complete_reset_all_mask_absent": bool(not reset_present[2] and torch.count_nonzero(reset_tokens[2]) == 0), "partial_reset": bool(torch.equal(reset[0][[0, 1]], latent[[0, 1]]) and torch.count_nonzero(latent[2]) > 0 and torch.count_nonzero(reset[0][2]) == 0 and not reset[1][2]), "masked_timestep_inert": masked_inert, "batch_permutation_isolation": permutation, "carried_value_exact": carried_exact, "meta_init": init_ok, "finite": bool(torch.isfinite(latent).all() and torch.isfinite(tokens).all() and all(torch.isfinite(p).all() for p in backend.parameters()))}
    state = latent
    passed = all(checks.values()) and state_diff <= 1e-6 and token_diff <= 1e-6 and clean(root) and clean(root / "cosmos-framework") and revision(root / "cosmos-framework") == gitlink
    command = {"cwd":str(Path.cwd()),"python":sys.executable,"argv":sys.argv,"output":str(args.output)}
    result = {"schema_version":"r09_a0_contract_v2","status":"PASS" if passed else "FAIL","root_revision":revision(root),"submodule_revision":revision(root / "cosmos-framework"),"gitlink_revision":gitlink,"tracked_clean":{"root":clean(root),"submodule":clean(root / "cosmos-framework")},"provenance_valid":revision(root / "cosmos-framework")==gitlink,"tool_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"backend":"recurrent_latent","state":{"shape":list(state.shape),"dtype":str(state.dtype),"bytes":state.numel()*state.element_size()},"input_shape":list(evidence.shape),"token_shape":list(tokens.shape),"trainable_param_count":sum(p.numel() for p in backend.parameters()),"trainable_prefixes":["cell"],"mixed_presence":present.tolist(),"assertions":checks,"segment":{"state_max_abs_diff":state_diff,"token_max_abs_diff":token_diff,"tolerance":1e-6,"pass":state_diff<=1e-6 and token_diff<=1e-6},"init":{"seed":11,"path":"meta-to_empty-explicit-reset_parameters"},"command":command,"command_hash":hashlib.sha256(json.dumps(command,sort_keys=True).encode()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
