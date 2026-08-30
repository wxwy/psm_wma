"""Emit the CPU-only B0 TTT contract artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch

from cosmos_framework.model.generator.mot.local_evidence import TTTLocalMemoryBackend


def _member(value: torch.Tensor, shape: list[int]) -> dict[str, object]:
    return {"shape_per_sample": shape, "dtype": str(value.dtype).removeprefix("torch."), "bytes_per_sample": value[0].numel() * value.element_size()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.manual_seed(11)
    backend = TTTLocalMemoryBackend()
    evidence = torch.randn(2, 7, 256)
    mask = torch.tensor([[True] * 7, [False] * 7])
    token, state, present = backend.replay(evidence, mask)
    members = {"W": _member(state[0], [32, 256]), "pending_evidence": _member(state[1], [4, 256]), "last_evidence": _member(state[2], [256]), "initialized": _member(state[3], []), "segment_progress": _member(state[4], [])}
    logical = sum(item["bytes_per_sample"] for item in members.values())
    _, split, split_present = backend.replay(evidence[:, :2], mask[:, :2])
    split_token, split, split_present = backend.replay(evidence[:, 2:], mask[:, 2:], split)
    max_diff = max(float((left - right).abs().max()) if left.dtype.is_floating_point else float((left != right).any()) for left, right in zip(state, split, strict=True))
    payload = {"schema_version": "r09_b0_ttt_contract_v2", "status": "PASS", "state": {"members": members, "logical_bytes_per_sample": logical, "fast_state_parameter_count": len(list(backend.named_parameters())), "bytes_limit": 18953, "bytes_limit_pass": logical == 18953}, "checks": {"finite": bool(torch.isfinite(token).all()), "fast_state_updated": bool(torch.count_nonzero(state[0][0]) > 0), "segment_present_equal": bool(torch.equal(present, split_present)), "graph_detached": not token.requires_grad, "named_parameters_excluded": not list(backend.named_parameters()), "two_segment_max_abs_diff": max_diff, "two_segment_pass": max_diff == 0.0}, "command": {"tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
    payload["status"] = "PASS" if all((payload["state"]["bytes_limit_pass"], *[value for key, value in payload["checks"].items() if isinstance(value, bool)])) else "FAIL"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    if payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
