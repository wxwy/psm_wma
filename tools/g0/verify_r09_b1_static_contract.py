#!/usr/bin/env python3
"""Emit the CPU-only static contract for R09-B1 TTT training wiring."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import torch
from torch import nn


EXACT_OPTIMIZER_KEYS = [
    "local_history_runtime.encoder",
    "local_memory2llm",
    "local_memory_modality_embed",
]


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _recipe_snapshot(root: Path, *, b1: bool, a1: bool = False, probe: bool = False) -> dict[str, object]:
    code = """import json
from cosmos_framework.configs.base.experiment.action.posttrain_config import action_policy_libero_edge_all as recipe
print(json.dumps({'backend': recipe.action_policy_libero_edge_all['model']['config']['local_history_backend'], 'optimizer_keys': list(recipe.action_policy_libero_edge_all['optimizer']['keys_to_select'])}))
"""
    env = os.environ | {
        "PYTHONPATH": str(root / "cosmos-framework"),
        "PSM_R08_LOCAL_HISTORY_ENABLED": "1",
        "PSM_LOCAL_DUMMY_ENABLED": "0",
        "PSM_R09_B1_TTT_ENABLED": "1" if b1 else "0",
        "PSM_R09_A1_ENABLED": "1" if a1 else "0",
    }
    if probe:
        env["PSM_R09_A1_PROBE_OUTPUT"] = "/tmp/r09_a1_probe.json"
    else:
        env.pop("PSM_R09_A1_PROBE_OUTPUT", None)
    completed = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True, check=False)
    if completed.returncode:
        return {"failed": True, "stderr": completed.stderr}
    return json.loads(completed.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / "cosmos-framework"))
    from cosmos_framework.configs.base.defaults.model_config import OmniMoTModelConfig
    from cosmos_framework.model.generator.mot.local_evidence import (
        LocalEvidenceEncoder,
        LocalHistoryRuntime,
        StatelessLocalReplayReadout,
        TTTLocalMemoryBackend,
    )
    from cosmos_framework.utils.generator.optimizer import _build_params_with_metadata

    root_clean = not _git(root, "status", "--porcelain", "--untracked-files=no")
    submodule = root / "cosmos-framework"
    submodule_clean = not _git(submodule, "status", "--porcelain", "--untracked-files=no")
    gitlink = _git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2]
    submodule_revision = _git(submodule, "rev-parse", "HEAD")
    backend = TTTLocalMemoryBackend(evidence_dim=256, local_dim=32, segment_steps=4)
    torch.manual_seed(17)
    evidence = torch.randn(2, 5, 256)
    mask = torch.ones(2, 5, dtype=torch.bool)
    token, state, _ = backend.replay(evidence, mask)
    repeat_token, repeat_state, _ = backend.replay(evidence, mask)
    state_reference = tuple(value.clone() for value in state)
    no_grad_fail_fast = False
    inference_mode_fail_fast = False
    for context, key in ((torch.no_grad(), "no_grad"), (torch.inference_mode(), "inference")):
        try:
            with context:
                backend.replay(evidence, mask, state)
        except RuntimeError as error:
            assert "training grad-mode" in str(error)
            if key == "no_grad":
                no_grad_fail_fast = True
            else:
                inference_mode_fail_fast = True
    state_unchanged = all(torch.equal(value, expected) for value, expected in zip(state, state_reference, strict=True))
    default_snapshot = _recipe_snapshot(root, b1=False)
    ttt_snapshot = _recipe_snapshot(root, b1=True)
    a1_excluded = bool(_recipe_snapshot(root, b1=True, a1=True).get("failed")) and bool(
        _recipe_snapshot(root, b1=True, probe=True).get("failed")
    )
    model = nn.Module()
    model.net = nn.Module()
    model.net.local_history_runtime = LocalHistoryRuntime(
        LocalEvidenceEncoder(evidence_dim=256, visual_dim=96),
        StatelessLocalReplayReadout(evidence_dim=256, local_dim=32),
        TTTLocalMemoryBackend(evidence_dim=256, local_dim=32),
    )
    model.net.local_memory2llm = nn.Linear(32, 8).to(dtype=torch.bfloat16)
    model.net.local_memory_modality_embed = nn.Parameter(torch.zeros(8, dtype=torch.bfloat16))
    selected = _build_params_with_metadata(model, EXACT_OPTIMIZER_KEYS, {}, 1.0, False)
    selected_ids = {id(parameter) for parameter, _ in selected}
    selected_names = {name: parameter for name, parameter in model.net.named_parameters() if id(parameter) in selected_ids}
    optimizer = torch.optim.SGD([parameter for parameter, _ in selected], lr=0.1)
    token_for_grad, _, _ = model.net.local_history_runtime.recurrent_backend.replay(evidence, mask)
    (model.net.local_memory2llm(token_for_grad).sum() + model.net.local_memory_modality_embed.sum()).backward()
    prefix_matches = {key: sorted(name for name in selected_names if key in name) for key in EXACT_OPTIMIZER_KEYS}
    gradient_facts = {
        key: {
            "present": any(selected_names[name].grad is not None for name in names),
            "finite": all(selected_names[name].grad is None or bool(torch.isfinite(selected_names[name].grad).all()) for name in names),
            "nonzero": any(selected_names[name].grad is not None and bool(torch.count_nonzero(selected_names[name].grad)) for name in names),
        }
        for key, names in prefix_matches.items()
    }
    backend_names = [name for name in selected_names if "local_history_runtime.recurrent_backend" in name]
    backend_parameter_ids = {id(parameter) for parameter in model.net.local_history_runtime.recurrent_backend.parameters()}
    backend_specific_state_empty = not any(id(parameter) in backend_parameter_ids for parameter in optimizer.state)
    command = {"argv": sys.argv, "cwd": str(Path.cwd()), "python": sys.executable, "output": str(args.output)}
    command_hash = hashlib.sha256(json.dumps(command, sort_keys=True).encode()).hexdigest()
    checks = {
        "root_clean": root_clean,
        "submodule_clean": submodule_clean,
        "gitlink_matches_submodule": gitlink == submodule_revision,
        "selector_default_recurrent": OmniMoTModelConfig().local_history_backend == "recurrent" and default_snapshot.get("backend") == "recurrent",
        "selector_ttt_opt_in": ttt_snapshot.get("backend") == "ttt_fast_weight",
        "a1_mutual_exclusion": a1_excluded,
        "b0_dimensions": (backend.evidence_dim, backend.local_dim, backend.segment_steps) == (256, 32, 4),
        "backend_zero_parameters": not list(backend.named_parameters()),
        "backend_empty_state_dict": not backend.state_dict(),
        "fresh_state_per_forward": torch.equal(token, repeat_token) and all(torch.equal(a, b) for a, b in zip(state, repeat_state, strict=True)),
        "normal_grad_pass": not token.requires_grad and bool(torch.isfinite(token).all()),
        "no_grad_fail_fast": no_grad_fail_fast and state_unchanged,
        "inference_mode_fail_fast": inference_mode_fail_fast and state_unchanged,
        "outer_graph_detached": not token.requires_grad and all(not value.requires_grad for value in state),
        "exact_optimizer_keys": ttt_snapshot.get("optimizer_keys") == EXACT_OPTIMIZER_KEYS,
        "backend_matches_empty": not backend_names,
        "selected_parameter_names_present": bool(selected_names),
        "backend_specific_state_empty": backend_specific_state_empty,
    }
    status = all(checks.values()) and (not args.require_clean or (root_clean and submodule_clean and gitlink == submodule_revision))
    result = {
        "schema_version": "r09_b1_static_contract_v1",
        "status": "PASS" if status else "FAIL",
        "source": {"root_revision": _git(root, "rev-parse", "HEAD"), "submodule_revision": submodule_revision, "gitlink_revision": gitlink, "root_clean": root_clean, "submodule_clean": submodule_clean},
        "selector": {"field": "local_history_backend", "legal_values": ["recurrent", "ttt_fast_weight"], "default": "recurrent", "opt_in_env": "PSM_R09_B1_TTT_ENABLED"},
        "backend": {"parameter_count": 0, "state_dict_empty": True, "fresh_state_per_forward": checks["fresh_state_per_forward"], "no_grad_fail_fast": checks["no_grad_fail_fast"], "inference_mode_fail_fast": checks["inference_mode_fail_fast"], "normal_grad_pass": checks["normal_grad_pass"], "outer_graph_detached": checks["outer_graph_detached"]},
        "optimizer": {"exact_keys": EXACT_OPTIMIZER_KEYS, "matched_parameter_names": prefix_matches, "selected_parameter_names": sorted(selected_names), "backend_matched_names": backend_names, "backend_specific_state_empty": backend_specific_state_empty, "gradient_facts": gradient_facts | {"encoder_ttt_path_nonzero_grad_required": False}},
        "recipe_snapshots": {"default": default_snapshot, "ttt": ttt_snapshot},
        "checks": checks,
        "command": {**command, "canonical_command_hash": command_hash, "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
