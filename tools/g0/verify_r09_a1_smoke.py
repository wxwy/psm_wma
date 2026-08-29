#!/usr/bin/env python3
"""Emit read-only evidence for the completed R09-A1 single-GPU smoke."""

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


ALLOWLIST = (
    "local_history_runtime.encoder",
    "local_history_runtime.recurrent_backend",
    "local_history_runtime.readout",
    "local_memory2llm",
    "local_memory_modality_embed",
)


def _revision(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def _clean(path: Path) -> bool:
    return not subprocess.check_output(
        ["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"], text=True
    ).strip()


def _load_model(checkpoint: Path) -> tuple[dict[str, torch.Tensor], dict[str, TensorStorageMetadata]]:
    reader = FileSystemReader(checkpoint / "model")
    metadata = reader.read_metadata()
    tensors = {
        name: torch.empty(tuple(record.size), dtype=record.properties.dtype)
        for name, record in metadata.state_dict_metadata.items()
        if isinstance(record, TensorStorageMetadata)
    }
    dcp.load(tensors, storage_reader=reader, no_dist=True)
    return tensors, {
        name: record
        for name, record in metadata.state_dict_metadata.items()
        if isinstance(record, TensorStorageMetadata)
    }


def _selected(name: str) -> bool:
    return any(prefix in name for prefix in ALLOWLIST)


def _digest(value: torch.Tensor) -> str:
    return hashlib.sha256(value.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()


def _training_summary(log_path: Path) -> dict[str, object]:
    text = log_path.read_text(errors="replace")
    iterations = [int(value) for value in re.findall(r"iteration=(\d+) \| train/loss=", text)]
    losses = [float(value) for value in re.findall(r"train/loss=([0-9.eE+-]+)", text)]
    action_losses = [float(value) for value in re.findall(r"flow_matching_loss_action=([0-9.eE+-]+)", text)]
    latency = [float(value) for value in re.findall(r"perf/step_wall_s=([0-9.eE+-]+)", text)]
    return {
        "completed": "Done with training." in text,
        "iterations_logged": len(iterations),
        "last_iteration": iterations[-1] if iterations else None,
        "finite_loss": bool(losses) and all(torch.isfinite(torch.tensor(losses)).tolist()),
        "finite_action_loss": bool(action_losses) and all(torch.isfinite(torch.tensor(action_losses)).tolist()),
        "last_loss": losses[-1] if losses else None,
        "last_action_loss": action_losses[-1] if action_losses else None,
        "step_wall_seconds": {
            "count": len(latency),
            "min": min(latency) if latency else None,
            "max": max(latency) if latency else None,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--initial-checkpoint", type=Path, required=True)
    parser.add_argument("--final-checkpoint", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    initial, initial_meta = _load_model(args.initial_checkpoint)
    final, final_meta = _load_model(args.final_checkpoint)
    initial_names, final_names = set(initial), set(final)
    common = sorted(initial_names & final_names)
    added = sorted(final_names - initial_names)
    removed = sorted(initial_names - final_names)
    selected_names = sorted(name for name in final_names if _selected(name))
    frozen = [name for name in common if not _selected(name)]
    changed_selected = [name for name in selected_names if name in initial and not torch.equal(initial[name], final[name])]
    unchanged_frozen = all(torch.equal(initial[name], final[name]) for name in frozen)
    selected_elements = sum(final[name].numel() for name in selected_names)
    expected_added = {
        "net.local_history_runtime.recurrent_backend.cell.weight_ih",
        "net.local_history_runtime.recurrent_backend.cell.weight_hh",
        "net.local_history_runtime.recurrent_backend.cell.bias_ih",
        "net.local_history_runtime.recurrent_backend.cell.bias_hh",
    }
    training = _training_summary(args.log)
    checks = {
        "checkpoint_schema_matches_except_recurrent_backend": not removed and set(added) == expected_added,
        "exact_allowlist_yields_20_tensors": len(selected_names) == 20,
        "exact_allowlist_yields_282336_elements": selected_elements == 282336,
        "all_frozen_common_tensors_bitwise_unchanged": unchanged_frozen,
        "at_least_one_preexisting_selected_tensor_changed": bool(changed_selected),
        "training_completed_100_steps": training["completed"] and training["last_iteration"] == 100,
        "all_logged_losses_finite": bool(training["finite_loss"] and training["finite_action_loss"]),
    }
    result = {
        "schema_version": "r09_a1_smoke_v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "root_revision": _revision(args.root),
        "submodule_revision": _revision(args.root / "cosmos-framework"),
        "tracked_clean": {"root": _clean(args.root), "submodule": _clean(args.root / "cosmos-framework")},
        "allowlist": list(ALLOWLIST),
        "selected": {
            "names": selected_names,
            "tensor_count": len(selected_names),
            "element_count": selected_elements,
            "changed_preexisting_names": changed_selected,
        },
        "checkpoint": {
            "initial": str(args.initial_checkpoint),
            "final": str(args.final_checkpoint),
            "initial_tensor_count": len(initial_meta),
            "final_tensor_count": len(final_meta),
            "added_names": added,
            "removed_names": removed,
            "frozen_common_tensor_count": len(frozen),
            "frozen_common_digest": hashlib.sha256(
                "".join(f"{name}:{_digest(final[name])}" for name in frozen).encode()
            ).hexdigest(),
        },
        "training": training,
        "checks": checks,
        "command": {
            "argv": [str(value) for value in __import__("sys").argv],
            "cwd": str(Path.cwd()),
            "python": __import__("sys").executable,
        },
    }
    result["command_hash"] = hashlib.sha256(json.dumps(result["command"], sort_keys=True).encode()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
