"""Emit the CPU-only R09-B0 TTT contract artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import torch

from cosmos_framework.model.generator.mot.local_evidence import TTTLocalMemoryBackend


ROOT = Path(__file__).resolve().parents[2]
SUBMODULE = ROOT / "cosmos-framework"
BYTES_LIMIT = 18_953  # source_audit_v0.1 §2.2: approved five-member logical payload.


def _git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def _state_equal(left: tuple[torch.Tensor, ...], right: tuple[torch.Tensor, ...]) -> bool:
    return all(torch.equal(a, b) for a, b in zip(left, right, strict=True))


def _state_max_abs(left: tuple[torch.Tensor, ...], right: tuple[torch.Tensor, ...]) -> float:
    return max(
        float((a - b).abs().max()) if a.dtype.is_floating_point else float((a != b).any())
        for a, b in zip(left, right, strict=True)
    )


def _member(value: torch.Tensor) -> dict[str, object]:
    return {
        "shape_per_sample": list(value.shape[1:]),
        "dtype": str(value.dtype).removeprefix("torch."),
        "bytes_per_sample": value[0].numel() * value.element_size(),
    }


def _state_members(state: tuple[torch.Tensor, ...]) -> dict[str, dict[str, object]]:
    names = ("W", "pending_evidence", "last_evidence", "initialized", "segment_progress")
    return {name: _member(value) for name, value in zip(names, state, strict=True)}


def _tail_checks(backend: TTTLocalMemoryBackend) -> tuple[dict[str, dict[str, int | bool]], bool]:
    cases: dict[str, dict[str, int | bool]] = {}
    all_pass = True
    for valid_count in (1, 2, 3, 5, 6, 7):
        evidence = torch.randn(1, valid_count, backend.evidence_dim)
        mask = torch.ones(1, valid_count, dtype=torch.bool)
        with mock.patch("torch.autograd.grad", wraps=torch.autograd.grad) as gradient:
            token, state, present = backend.replay(evidence, mask)
        expected_updates = valid_count // backend.segment_steps
        passed = bool(
            gradient.call_count == expected_updates
            and int(state[4].item()) == valid_count % backend.segment_steps
            and bool(present.item())
            and (expected_updates > 0 or (torch.count_nonzero(state[0]) == 0 and torch.count_nonzero(token) == 0))
        )
        cases[str(valid_count)] = {
            "expected_update_count": expected_updates,
            "observed_update_count": gradient.call_count,
            "terminal_progress": int(state[4].item()),
            "present": bool(present.item()),
            "pass": passed,
        }
        all_pass &= passed
    return cases, all_pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()

    torch.manual_seed(11)
    backend = TTTLocalMemoryBackend()
    evidence = torch.randn(3, 7, 256)
    mask = torch.tensor([[True] * 7, [True, True, True, True, False, False, False], [False] * 7])
    token, state, present = backend.replay(evidence, mask)
    members = _state_members(state)
    logical = sum(int(item["bytes_per_sample"]) for item in members.values())

    torch.manual_seed(11)
    deterministic_token, deterministic_state, deterministic_present = TTTLocalMemoryBackend().replay(evidence, mask)
    _, split_state, _ = backend.replay(evidence[:, :2], mask[:, :2])
    split_token, split_state, split_present = backend.replay(evidence[:, 2:], mask[:, 2:], split_state)
    segment_state_max_abs = _state_max_abs(state, split_state)
    segment_token_max_abs = float((token - split_token).abs().max())

    masked_changed = evidence.clone()
    masked_changed[~mask] = 1e6
    masked_token, masked_state, masked_present = backend.replay(masked_changed, mask)
    all_mask_token, all_mask_state, all_mask_present = backend.replay(evidence, torch.zeros_like(mask))
    permutation = torch.tensor([1, 0, 2])
    perm_token, perm_state, perm_present = backend.replay(evidence[permutation], mask[permutation])
    inverse = torch.argsort(permutation)
    changed = evidence.clone()
    changed[1] = -1e6
    isolated_token, isolated_state, _ = backend.replay(changed, mask)
    continued_token, continued_state, continued_present = backend.replay(torch.zeros(3, 2, 256), torch.zeros(3, 2, dtype=torch.bool), state)
    partial_state = backend.reset_mask(state, torch.tensor([False, True, False]))
    full_state = backend.reset_mask(state, torch.ones(3, dtype=torch.bool))
    boundary_token, boundary_state, boundary_present = backend.replay(torch.zeros(3, 2, 256), torch.zeros(3, 2, dtype=torch.bool))
    tail_cases, tail_pass = _tail_checks(backend)

    root_revision = _git("rev-parse", "HEAD")
    submodule_revision = _git("rev-parse", "HEAD", cwd=SUBMODULE)
    gitlink_revision = _git("rev-parse", "HEAD:cosmos-framework")
    root_clean = not _git("status", "--porcelain", "--untracked-files=no")
    submodule_clean = not _git("status", "--porcelain", "--untracked-files=no", cwd=SUBMODULE)
    provenance_pass = (root_clean and submodule_clean and gitlink_revision == submodule_revision) if args.require_clean else True
    checks = {
        "deterministic": torch.equal(token, deterministic_token) and _state_equal(state, deterministic_state) and torch.equal(present, deterministic_present),
        "finite": bool(torch.isfinite(token).all()) and all(bool(torch.isfinite(value).all()) for value in state[:3]),
        "fast_state_updated": bool(torch.count_nonzero(state[0][0]) > 0),
        "masked_timestep_inert": torch.equal(masked_token, token) and _state_equal(masked_state, state) and torch.equal(masked_present, present),
        "padding_inert": torch.equal(masked_token, token),
        "all_mask_absent": not bool(all_mask_present.any()) and torch.count_nonzero(all_mask_token) == 0 and all(torch.count_nonzero(value) == 0 for value in all_mask_state),
        "all_mask_continuation": torch.equal(continued_token, token) and _state_equal(continued_state, state) and torch.equal(continued_present, present),
        "batch_permutation_isolation": torch.equal(perm_token[inverse], token) and _state_equal(tuple(value[inverse] for value in perm_state), state) and torch.equal(perm_present[inverse], present),
        "cross_sample_isolation": torch.equal(isolated_token[0], token[0]) and all(torch.equal(value[0], reference[0]) for value, reference in zip(isolated_state, state, strict=True)),
        "partial_reset": all(torch.equal(value[0], reference[0]) for value, reference in zip(partial_state, state, strict=True)) and all(torch.count_nonzero(value[1]) == 0 for value in partial_state),
        "full_reset": all(torch.count_nonzero(value) == 0 for value in full_state),
        "boundary_isolation": not bool(boundary_present.any()) and torch.count_nonzero(boundary_token) == 0,
        "boundary_state_zero_or_reinitialized": all(torch.count_nonzero(value) == 0 for value in boundary_state),
        "segment_present_equal": torch.equal(present, split_present),
        "detach_value_exact": torch.equal(token, torch.einsum("bde,be->bd", state[0], state[2])[:, None] * state[3][:, None, None]),
        "graph_detached": not token.requires_grad and not any(value.requires_grad for value in state),
        "named_parameters_excluded": not list(backend.named_parameters()),
        "optimizer_excluded": not list(backend.parameters()),
        "checkpoint_excluded": not backend.state_dict(),
        "tail_update_counts": tail_pass,
        "provenance_pass": provenance_pass,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    payload = {
        "schema_version": "r09_b0_ttt_contract_v3",
        "status": "PASS",
        "root_revision": root_revision,
        "submodule_revision": submodule_revision,
        "gitlink_revision": gitlink_revision,
        "root_clean": root_clean,
        "submodule_clean": submodule_clean,
        "gitlink_matches_submodule": gitlink_revision == submodule_revision,
        "candidate": {"fast_weight_parametrization": "per_sample_W_bfloat16_[32,256]", "update_rule": "SGD_lr_0.1", "inner_objective": "MSE(W@e,stopgrad(e[:32]))", "inner_steps": 1, "segment_steps": 4, "fast_state_dtype": "bfloat16", "fast_state_bytes_limit": BYTES_LIMIT, "slow_learned_parameters": 0},
        "state": {"members": members, "logical_bytes_per_sample": logical, "fast_state_parameter_count": len(list(backend.named_parameters())), "bytes_limit": BYTES_LIMIT, "bytes_limit_pass": logical == BYTES_LIMIT},
        "tail_cases": tail_cases,
        "checks": checks,
        "segment": {"state_max_abs_diff": segment_state_max_abs, "token_max_abs_diff": segment_token_max_abs, "present_equal": torch.equal(present, split_present), "tolerance": 0.0, "pass": segment_state_max_abs == 0.0 and segment_token_max_abs == 0.0 and torch.equal(present, split_present)},
        "command": {"argv": sys.argv, "cwd": str(Path.cwd()), "python": sys.executable, "output": str(args.output), "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    required = [payload["state"]["bytes_limit_pass"], payload["segment"]["pass"], *checks.values()]
    payload["status"] = "PASS" if all(required) else "FAIL"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    if payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
