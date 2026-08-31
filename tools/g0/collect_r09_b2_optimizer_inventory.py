#!/usr/bin/env python3
"""Collect the read-only R09-B2 P3 optimizer inventory, or a truthful BLOCKED result."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def summarize_failure(stderr: str, stdout: str) -> str:
    """保留最相关的异常行，避免长的上游诊断掩盖根因。"""
    details = stderr or stdout
    for line in reversed(details.splitlines()):
        if any(marker in line for marker in ("Error:", "Exception:", "ImportError:")):
            return line.strip()
    return details[-2000:]


def asset_records(paths: dict[str, Path]) -> dict[str, dict[str, object]]:
    return {
        name: {"path": str(path), "exists": path.exists(), "is_dir": path.is_dir()}
        for name, path in paths.items()
    }


def write_result(path: Path, result: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def worker(root: Path, toml: Path, ttt_enabled: bool, wan_vae_path: str, edge_checkpoint_path: str, base_checkpoint_path: str, libero_root: str) -> dict[str, object]:
    """Run only in the isolated no-CUDA worker process."""
    import torch

    if torch.cuda.is_initialized():
        raise RuntimeError("P3 worker started with CUDA already initialized")
    from cosmos_framework.configs.toml_config.sft_config import load_experiment_from_toml
    from cosmos_framework.utils.lazy_config import instantiate
    from cosmos_framework.utils.generator.optimizer import OptimizersContainer

    env = os.environ | {
        "PSM_R08_LOCAL_HISTORY_ENABLED": "1",
        "PSM_LOCAL_DUMMY_ENABLED": "0",
        "PSM_R09_B1_TTT_ENABLED": "1" if ttt_enabled else "0",
        "WAN_VAE_PATH": wan_vae_path,
        "EDGE_POLICY_CHECKPOINT": edge_checkpoint_path,
        "BASE_CHECKPOINT_PATH": base_checkpoint_path,
        "LIBERO_ROOT": libero_root,
    }
    os.environ.update(env)
    config = load_experiment_from_toml(toml)
    with torch.device("meta"):
        model = instantiate(config.model)
    if torch.cuda.is_initialized():
        raise RuntimeError("P3 model construction initialized CUDA")
    all_parameters = dict(model.net.named_parameters())
    keys_to_select = list(config.optimizer.keys_to_select)
    selector_matches = {
        name: parameter.requires_grad and (not keys_to_select or any(key in name for key in keys_to_select))
        for name, parameter in all_parameters.items()
    }
    try:
        optimizer = OptimizersContainer(model=model, **dict(config.optimizer))
    except Exception as error:
        return {
            "status": "BLOCKED",
            "reason": f"{type(error).__name__}: {error}",
            "inventory": {
                "selector": {"backend": config.model.config.local_history_backend, "keys_to_select": keys_to_select},
                "model_parameters": [
                    {"name": name, "trainable": parameter.requires_grad, "numel": parameter.numel(), "dtype": str(parameter.dtype).removeprefix("torch."), "selected_by_resolved_selector": selector_matches[name], "selected_by_optimizer": False}
                    for name, parameter in sorted(all_parameters.items())
                ],
                "optimizer_param_groups": [],
                "optimizer_state": {"not_materialized": True, "reason": "optimizer construction did not complete", "entries": []},
                "dcp_state": {"inspected": False, "reason": "optimizer construction did not complete; P3 does not invoke DCP save/load APIs"},
            },
        }
    if torch.cuda.is_initialized():
        raise RuntimeError("P3 optimizer construction initialized CUDA")
    parameter_names = {id(parameter): name for name, parameter in all_parameters.items()}
    groups = []
    optimizer_parameters = set()
    for optimizer_index, item in enumerate(optimizer.optimizers):
        for group_index, group in enumerate(item.param_groups):
            names = []
            for parameter in group["params"]:
                name = parameter_names.get(id(parameter))
                if name is None:
                    raise RuntimeError("optimizer parameter is absent from model.net.named_parameters")
                names.append(name)
                optimizer_parameters.add(id(parameter))
            groups.append({"optimizer_index": optimizer_index, "group_index": group_index, "parameter_names": sorted(names), "lr": group["lr"], "weight_decay": group.get("weight_decay")})
    selected = set(name for name, parameter in all_parameters.items() if id(parameter) in optimizer_parameters)
    model_rows = [{"name": name, "trainable": parameter.requires_grad, "numel": parameter.numel(), "dtype": str(parameter.dtype).removeprefix("torch."), "selected_by_resolved_selector": selector_matches[name], "selected_by_optimizer": name in selected} for name, parameter in sorted(all_parameters.items())]
    buffers = [{"name": name, "numel": value.numel(), "dtype": str(value.dtype).removeprefix("torch.")} for name, value in model.net.named_buffers()]
    ttt_keys = {"W", "pending_evidence", "last_evidence", "initialized", "segment_progress"}
    forbidden = [row["name"] for row in model_rows + buffers if row["name"].split(".")[-1] in ttt_keys]
    if forbidden:
        raise RuntimeError(f"TTT dynamic state unexpectedly registered persistently: {forbidden}")
    return {"status": "BLOCKED", "reason": "DCP schema membership is not inspected by the approved no-save/no-load P3 path", "inventory": {"model_parameters": model_rows, "named_buffers": buffers, "optimizer_param_groups": groups, "optimizer_state": {"not_materialized": True, "index_semantics": "in_process_parameter_object_identity; persisted_by_stable_parameter_name", "entries": []}, "dcp_state": {"inspected": False, "reason": "P3 does not invoke DCP save/load APIs"}, "selector": {"backend": config.model.config.local_history_backend, "keys_to_select": keys_to_select}}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--toml", type=Path, required=True)
    parser.add_argument("--wan-vae-path", type=Path, required=True)
    parser.add_argument("--edge-checkpoint-path", type=Path, required=True)
    parser.add_argument("--base-checkpoint-path", type=Path, required=True)
    parser.add_argument("--libero-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, toml = args.root.resolve(), args.toml.resolve()
    framework = root / "cosmos-framework"
    source = {"root_revision": git(root, "rev-parse", "HEAD"), "submodule_revision": git(framework, "rev-parse", "HEAD"), "gitlink_revision": git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2], "recipe_sha256": sha256(toml), "collector_sha256": sha256(Path(__file__).resolve()), "verifier_sha256": sha256(Path(__file__).with_name("verify_r09_b2_optimizer_inventory.py")), "optimizer_source_sha256": sha256(framework / "cosmos_framework/utils/generator/optimizer.py"), "sft_config_source_sha256": sha256(framework / "cosmos_framework/configs/toml_config/sft_config.py"), "model_source_sha256": sha256(framework / "cosmos_framework/model/generator/omni_mot_model.py")}
    assets = asset_records({"wan_vae": args.wan_vae_path, "edge_checkpoint": args.edge_checkpoint_path, "base_checkpoint": args.base_checkpoint_path, "libero_root": args.libero_root})
    result: dict[str, object] = {"schema_version": "r09_b2_optimizer_inventory_v1", "source": source, "input": {"assets": assets}, "execution": {"device": "meta", "weights_loaded": False, "checkpoint_loaded": False, "forward_executed": False, "backward_executed": False, "optimizer_step_executed": False, "scheduler_step_executed": False, "cuda_visible_devices": ""}}
    missing = [name for name, record in assets.items() if not record["exists"]]
    if missing:
        result.update({"status": "BLOCKED", "reason": f"missing required assets: {', '.join(missing)}"})
        for name in ("recurrent", "ttt_fast_weight"):
            result[name] = {"status": "BLOCKED", "reason": result["reason"]}
        write_result(args.output, result)
        print(json.dumps({"status": result["status"]}))
        return
    env = os.environ | {"PYTHONPATH": str(framework), "CUDA_VISIBLE_DEVICES": ""}
    for name, enabled in (("recurrent", False), ("ttt_fast_weight", True)):
        code = "from pathlib import Path; import json,sys; from tools.g0.collect_r09_b2_optimizer_inventory import worker; print(json.dumps(worker(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] == '1', sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]), sort_keys=True))"
        completed = subprocess.run([sys.executable, "-c", code, str(root), str(toml), "1" if enabled else "0", str(args.wan_vae_path), str(args.edge_checkpoint_path), str(args.base_checkpoint_path), str(args.libero_root)], env=env, cwd=root, text=True, capture_output=True)
        if completed.returncode:
            result[name] = {"status": "BLOCKED", "reason": summarize_failure(completed.stderr, completed.stdout)}
        else:
            result[name] = json.loads(completed.stdout.splitlines()[-1])
    result["status"] = "PASS" if all(result[name]["status"] == "PASS" for name in ("recurrent", "ttt_fast_weight")) else "BLOCKED"
    write_result(args.output, result)
    print(json.dumps({"status": result["status"]}))


if __name__ == "__main__":
    main()
