#!/usr/bin/env python3
"""Emit read-only PASS/FAIL evidence for the bounded R09-B1 TTT smoke."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import torch
import torch.distributed.checkpoint as dcp
from torch.distributed.checkpoint import FileSystemReader
from torch.distributed.checkpoint.metadata import TensorStorageMetadata


ALLOWLIST = ("local_history_runtime.encoder", "local_memory2llm", "local_memory_modality_embed")
REMOVED_GRU = {
    "net.local_history_runtime.recurrent_backend.cell.weight_ih",
    "net.local_history_runtime.recurrent_backend.cell.weight_hh",
    "net.local_history_runtime.recurrent_backend.cell.bias_ih",
    "net.local_history_runtime.recurrent_backend.cell.bias_hh",
}


def _load(path: Path) -> dict[str, torch.Tensor]:
    metadata = FileSystemReader(path / "model").read_metadata()
    tensors = {
        name: torch.empty(tuple(record.size), dtype=record.properties.dtype)
        for name, record in metadata.state_dict_metadata.items()
        if isinstance(record, TensorStorageMetadata)
    }
    dcp.load(tensors, storage_reader=FileSystemReader(path / "model"), no_dist=True)
    return tensors


def _clean(path: Path) -> bool:
    return not subprocess.check_output(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"], text=True).strip()


def _selected(name: str) -> bool:
    return any(key in name for key in ALLOWLIST)


def _finite_loss(log: Path, expected_steps: int) -> tuple[bool, bool]:
    text = log.read_text(errors="replace")
    losses = [float(value) for value in re.findall(r"train/loss=([0-9.eE+-]+)", text)]
    actions = [float(value) for value in re.findall(r"flow_matching_loss_action=([0-9.eE+-]+)", text)]
    return (
        "Done with training." in text and len(losses) >= expected_steps and bool(losses) and bool(torch.isfinite(torch.tensor(losses)).all()),
        len(actions) >= expected_steps and bool(torch.isfinite(torch.tensor(actions)).all()),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--initial-checkpoint", type=Path, required=True)
    parser.add_argument("--final-checkpoint", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--expected-steps", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    initial, final = _load(args.initial_checkpoint), _load(args.final_checkpoint)
    probe = json.loads(args.probe.read_text())
    added, removed = set(final) - set(initial), set(initial) - set(final)
    frozen = [name for name in set(initial) & set(final) if not _selected(name)]
    step = probe["representative_step"]
    groups = step["gradient_groups"]
    state = probe["state_contract"]
    total_finite, action_finite = _finite_loss(args.log, args.expected_steps)
    checks = {
        "training_losses_finite": total_finite and action_finite,
        "checkpoint_schema_only_removes_gru": not added and removed == REMOVED_GRU,
        "frozen_common_tensors_bitwise_unchanged": all(torch.equal(initial[name], final[name]) for name in frozen),
        "optimizer_exact_three_key_membership": step["optimizer_matches_targets"] and not step["missing_optimizer_names"] and not step["unexpected_optimizer_names"],
        "encoder_ttt_gradient_absent_or_zero": all(not item["present"] or item["max_abs"] == 0.0 for item in groups["encoder"]),
        "adapter_gradients_present_finite_nonzero": all(
            item["present"] and item["finite"] and item["max_abs"] > 0
            for name in ("local_memory2llm", "local_memory_modality_embed")
            for item in groups[name]
        ),
        "ttt_state_schema": [member["name"] for member in state["members"]] == ["W", "pending", "last", "initialized", "progress"] and state["bytes_per_sample"] == 18953,
        "ttt_state_fresh_segment_reset_detached": state["segment_token_max_abs_diff"] == 0.0 and all(state["segment_members_exact"]) and state["fresh_token_exact"] and all(state["fresh_members_exact"]) and all(state["members_detached"]) and all(state["reset_selected_members_zero"]) and state["reset_selected_initialized_false"] and state["reset_selected_progress_zero"] and all(state["reset_unselected_members_exact"]) and state["reset_all_mask_selected_absent"] and state["reset_all_mask_selected_token_zero"],
        "cuda_peak_recorded": probe["full_run_cuda_peak"]["allocated_bytes"] > 0 and probe["full_run_cuda_peak"]["reserved_bytes"] > 0 and probe["full_run_cuda_peak"]["device"] is not None,
        "verifier_root_clean": _clean(args.root),
        "verifier_submodule_clean": _clean(args.root / "cosmos-framework"),
    }
    result = {
        "schema_version": "r09_b1_smoke_v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "allowlist": list(ALLOWLIST),
        "checkpoint": {"initial": str(args.initial_checkpoint), "final": str(args.final_checkpoint), "added": sorted(added), "removed": sorted(removed), "frozen_common_count": len(frozen)},
        "runtime_probe": probe,
        "command": {"argv": __import__("sys").argv, "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
