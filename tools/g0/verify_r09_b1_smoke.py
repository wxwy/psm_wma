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
STATE_SCHEMA = {
    "W": {"shape_per_sample": [32, 256], "dtype": "bfloat16", "bytes_per_sample": 16384},
    "pending_evidence": {"shape_per_sample": [4, 256], "dtype": "bfloat16", "bytes_per_sample": 2048},
    "last_evidence": {"shape_per_sample": [256], "dtype": "bfloat16", "bytes_per_sample": 512},
    "initialized": {"shape_per_sample": [], "dtype": "bool", "bytes_per_sample": 1},
    "segment_progress": {"shape_per_sample": [], "dtype": "int64", "bytes_per_sample": 8},
}
SMOKE_PROFILES = {
    "gate_a_rebuild": {
        "name": "smoke_batch1_gate_a",
        "bounded_noncanonical": True,
        "dataloader_train.max_samples_per_batch": 1,
        "trainer.grad_accum_iter": 1,
    },
    "b1_smoke": {
        "name": "smoke_batch2_b1",
        "bounded_noncanonical": True,
        "dataloader_train.max_samples_per_batch": 2,
        "trainer.grad_accum_iter": 1,
    },
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


def _complete_dcp(path: Path) -> bool:
    return all((path / name / ".metadata").is_file() for name in ("model", "optim", "scheduler", "trainer"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _dcp_manifest(path: Path) -> dict[str, dict[str, object]]:
    return {
        str(item.relative_to(path)): {"size_bytes": item.stat().st_size, "sha256": _sha256(item)}
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def _sidecar_matches_command(sidecar: dict[str, object]) -> bool:
    command = sidecar.get("command")
    if not isinstance(command, str):
        return False
    if sidecar.get("command_sha256") != hashlib.sha256(command.encode()).hexdigest():
        return False
    argv = sidecar.get("command_argv")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv) or not argv or argv[0] != "env":
        return False
    unset = sidecar["unset_environment"]
    env = sidecar["environment"]
    if argv.count("-u") != len(unset) or any(argv.count(item) != 1 for item in unset):
        return False
    assignments = [item for item in argv if "=" in item]
    override_values = [
        item.removeprefix("EXTRA_TAIL_OVERRIDES=").split()
        for item in argv
        if item.startswith("EXTRA_TAIL_OVERRIDES=")
    ]
    profile = SMOKE_PROFILES.get(sidecar.get("phase"))
    if profile is None:
        return False
    overrides = (
        f"dataloader_train.max_samples_per_batch={profile['dataloader_train.max_samples_per_batch']}",
        f"trainer.grad_accum_iter={profile['trainer.grad_accum_iter']}",
    )
    return (
        all(assignments.count(f"{key}={value}") == 1 for key, value in env.items())
        and "DISABLE_AUTO_RESUME=1" in argv
        and len(override_values) == 1
        and all(override_values[0].count(item) == 1 for item in overrides)
    )


def _bounded_smoke_profile(sidecar: dict[str, object], expected_steps: int) -> bool:
    diagnostics = sidecar.get("launch_diagnostics")
    return (
        sidecar.get("smoke_profile") == SMOKE_PROFILES.get(sidecar.get("phase"))
        and sidecar.get("expected_steps") == expected_steps
        and isinstance(diagnostics, dict)
        and isinstance(diagnostics.get("started_unix"), float)
        and isinstance(diagnostics.get("dmesg_returncode"), int)
        and isinstance(diagnostics.get("dmesg_tail"), list)
    )


def _b1_first_batch_history(sidecar: dict[str, object]) -> bool:
    evidence = sidecar.get("b1_first_batch_history")
    if not isinstance(evidence, dict) or evidence.get("status") != "PASS":
        return False
    path = Path(str(evidence.get("path", "")))
    return (
        path.is_file()
        and evidence.get("sha256") == _sha256(path)
        and isinstance(evidence.get("effective_local_history_sample_count"), int)
        and evidence["effective_local_history_sample_count"] >= 1
    )


def _cache_only_no_fallback(log: Path, sidecar: dict[str, object]) -> bool:
    environment = sidecar["environment"]
    text = log.read_text(errors="replace").lower()
    forbidden = ("online vae fallback", "latent_cache_mismatch", "fallback to online")
    return environment["LIBERO_LATENT_CACHE_VERIFY_RATIO"] == "0" and bool(environment["LIBERO_LATENT_CACHE_ROOT"]) and not any(item in text for item in forbidden)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--initial-checkpoint", type=Path, required=True)
    parser.add_argument("--final-checkpoint", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--gate-a-log", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--gate-a-sidecar", type=Path, required=True)
    parser.add_argument("--training-sidecar", type=Path, required=True)
    parser.add_argument("--expected-root-revision", required=True)
    parser.add_argument("--expected-submodule-revision", required=True)
    parser.add_argument("--expected-gitlink-revision", required=True)
    parser.add_argument("--expected-steps", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    initial, final = _load(args.initial_checkpoint), _load(args.final_checkpoint)
    probe = json.loads(args.probe.read_text())
    gate_a_sidecar = json.loads(args.gate_a_sidecar.read_text())
    sidecar = json.loads(args.training_sidecar.read_text())
    added, removed = set(final) - set(initial), set(initial) - set(final)
    frozen = [name for name in set(initial) & set(final) if not _selected(name)]
    step = probe["representative_step"]
    groups = step["gradient_groups"]
    state = probe["state_contract"]
    total_finite, action_finite = _finite_loss(args.log, args.expected_steps)
    gate_a_total_finite, gate_a_action_finite = _finite_loss(args.gate_a_log, 2)
    expected_source = {
        "root_revision": args.expected_root_revision,
        "submodule_revision": args.expected_submodule_revision,
        "gitlink_revision": args.expected_gitlink_revision,
    }
    gate_a_output = gate_a_sidecar["output"]
    b1_output = sidecar["output"]
    gate_a_manifest = _dcp_manifest(args.initial_checkpoint)
    source_chain = all(
        item["source"] == expected_source and item["source"]["gitlink_revision"] == item["source"]["submodule_revision"]
        for item in (gate_a_sidecar, sidecar)
    )
    gpu_chain = all(item["gpu"]["index"] == 0 and "A100" in item["gpu"]["name"] and item["gpu"]["total_memory_mib"] >= 80000 and item["environment"].get("CUDA_VISIBLE_DEVICES") == "0" for item in (gate_a_sidecar, sidecar))
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
        "ttt_state_schema": state["members"] == STATE_SCHEMA and state["bytes_per_sample"] == 18953,
        "ttt_state_fresh_segment_reset_detached": state["segment_token_max_abs_diff"] == 0.0 and state["segment_present_equal"] and all(state["segment_members_exact"]) and state["fresh_token_exact"] and state["fresh_present_equal"] and all(state["fresh_members_exact"]) and state["token_detached"] and all(state["members_detached"]) and all(state["reset_selected_members_zero"]) and state["reset_selected_initialized_false"] and state["reset_selected_progress_zero"] and all(state["reset_unselected_members_exact"]) and state["reset_all_mask_selected_absent"] and state["reset_all_mask_selected_token_zero"] and all(state["reset_all_mask_members_detached"]),
        "cuda_peak_recorded": probe["full_run_cuda_peak"]["allocated_bytes"] > 0 and probe["full_run_cuda_peak"]["reserved_bytes"] > 0 and probe["full_run_cuda_peak"]["device"] is not None,
        "approved_single_a100_80gb_bound_and_recorded": gpu_chain and "A100" in probe["full_run_cuda_peak"]["device"],
        "gate_a_rebuilt_warm_start_complete": gate_a_sidecar["phase"] == "gate_a_rebuild" and gate_a_sidecar["expected_steps"] == 2 and gate_a_total_finite and gate_a_action_finite and gate_a_output["checkpoint"] == str(args.initial_checkpoint) and gate_a_output["log"] == str(args.gate_a_log) and _complete_dcp(args.initial_checkpoint) and bool(gate_a_manifest),
        "bounded_noncanonical_smoke_profile": _bounded_smoke_profile(gate_a_sidecar, 2) and _bounded_smoke_profile(sidecar, args.expected_steps),
        "b1_first_packed_batch_has_effective_local_history": _b1_first_batch_history(sidecar),
        "two_phase_d005_provenance_chain": source_chain and _sidecar_matches_command(gate_a_sidecar) and _sidecar_matches_command(sidecar) and sidecar["phase"] == "b1_smoke" and sidecar["expected_steps"] == args.expected_steps and sidecar["input"]["checkpoint"] == str(args.initial_checkpoint) and b1_output["checkpoint"] == str(args.final_checkpoint) and b1_output["log"] == str(args.log) and b1_output["probe"] == str(args.probe) and gate_a_sidecar["input"]["libero_root"] == sidecar["input"]["libero_root"] and gate_a_sidecar["input"]["cache_root"] == sidecar["input"]["cache_root"],
        "cache_only_no_online_vae_fallback_both_phases": _cache_only_no_fallback(args.gate_a_log, gate_a_sidecar) and _cache_only_no_fallback(args.log, sidecar),
        "b1_model_only_loads_exact_rebuilt_checkpoint": bool(re.search(re.escape(f"Loaded checkpoint from {args.initial_checkpoint}") + r"(?: \\([^)]*\\))? in iteration 0(?:\\n|$)", args.log.read_text(errors="replace"))) and "checkpoint.load_training_state=False" in sidecar["command"],
        "d005_binds_cache_only_training": sidecar["phase"] == "b1_smoke" and sidecar["network"] is False and sidecar["world_size"] == 1 and sidecar["environment"]["NPROC_PER_NODE"] == "1" and sidecar["environment"]["PSM_R09_B1_TTT_ENABLED"] == "1" and sidecar["environment"]["PSM_R08_HISTORY_MODE"] == "normal" and sidecar["environment"]["LIBERO_LATENT_CACHE_VERIFY_RATIO"] == "0" and sidecar["environment"]["LIBERO_LATENT_CACHE_ROOT"] and sidecar["input"]["checkpoint"] == str(args.initial_checkpoint) and sidecar["output"]["probe"] == str(args.probe),
        "verifier_root_clean": _clean(args.root),
        "verifier_submodule_clean": _clean(args.root / "cosmos-framework"),
    }
    result = {
        "schema_version": "r09_b1_smoke_v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "warnings": [
            "PASS 仅表示 bounded smoke profile 的 runtime/checkpoint 合同；不是 canonical Gate-A、正式规模训练、吞吐、收敛或 SR 证据。"
        ],
        "smoke_profiles": SMOKE_PROFILES,
        "allowlist": list(ALLOWLIST),
        "checkpoint": {"initial": str(args.initial_checkpoint), "final": str(args.final_checkpoint), "added": sorted(added), "removed": sorted(removed), "frozen_common_count": len(frozen), "gate_a_manifest": gate_a_manifest},
        "runtime_probe": probe,
        "gate_a_sidecar": {"path": str(args.gate_a_sidecar), "sha256": hashlib.sha256(args.gate_a_sidecar.read_bytes()).hexdigest(), "source": gate_a_sidecar["source"]},
        "training_sidecar": {"path": str(args.training_sidecar), "sha256": hashlib.sha256(args.training_sidecar.read_bytes()).hexdigest(), "source": sidecar["source"]},
        "command": {"argv": __import__("sys").argv, "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
