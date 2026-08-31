#!/usr/bin/env python3
"""Collect read-only R09-B2 P0 asset/config/resource evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")
TTT_KEYS = (
    "local_history_runtime.encoder",
    "local_memory2llm",
    "local_memory_modality_embed",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def resolved_config(
    root: Path,
    toml: Path,
    ttt_enabled: bool,
    base_checkpoint: Path,
    libero_root: Path,
    cache_root: Path,
    wan_vae_path: Path,
    edge_policy_checkpoint: Path,
) -> dict[str, object]:
    code = (
        "import json,sys; "
        "from cosmos_framework.configs.toml_config.sft_config import load_experiment_from_toml; "
        "c=load_experiment_from_toml(sys.argv[1]); m=c.model.config; "
        "print(json.dumps({'local_history_backend':m.local_history_backend,"
        "'local_history_horizon':m.local_history_horizon,'local_memory_dim':m.local_memory_dim,"
        "'keys_to_select':list(c.optimizer.keys_to_select),'precision':m.precision,"
        "'max_iter':c.trainer.max_iter,'grad_accum_iter':c.trainer.grad_accum_iter,"
        "'max_samples_per_batch':c.dataloader_train.max_samples_per_batch,'joint_seed':c.dataloader_train.seed,"
        "'trainer_seed':c.trainer.seed,'compile_enabled':m.compile.enabled,'ema_enabled':m.ema.enabled}, sort_keys=True, default=str))"
    )
    env = os.environ | {
        "PSM_R08_LOCAL_HISTORY_ENABLED": "1",
        "PSM_R09_A1_ENABLED": "0",
        "PSM_R09_A1_PROBE_OUTPUT": "",
        "PSM_R09_B1_TTT_ENABLED": "1" if ttt_enabled else "0",
        "PSM_R09_B1_PROBE_OUTPUT": "",
        "PSM_R08_HISTORY_MODE": "normal",
        "PSM_LOCAL_DUMMY_ENABLED": "0",
        "BASE_CHECKPOINT_PATH": str(base_checkpoint),
        "LIBERO_ROOT": str(libero_root),
        "LIBERO_LATENT_CACHE_ROOT": str(cache_root),
        "WAN_VAE_PATH": str(wan_vae_path),
        "EDGE_POLICY_CHECKPOINT": str(edge_policy_checkpoint),
    }
    try:
        result = subprocess.run(
            [sys.executable, "-c", code, str(toml)],
            cwd=root / "cosmos-framework",
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "无法解析 B2 预检配置：\n"
            f"stdout:\n{error.stdout}\n"
            f"stderr:\n{error.stderr}"
        ) from error
    return json.loads(result.stdout.splitlines()[-1])


def selected(config: dict[str, object]) -> dict[str, object]:
    return config


def gpu_snapshot() -> dict[str, object]:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used", "--format=csv,noheader,nounits"],
        text=True,
        capture_output=True,
        check=False,
    )
    return {"returncode": result.returncode, "csv": result.stdout.splitlines()}


def memory_snapshot() -> dict[str, str]:
    fields = {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", maxsplit=1)
        if key in fields:
            values[key] = value.strip()
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--toml", type=Path, required=True)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--libero-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--wan-vae-path", type=Path, required=True)
    parser.add_argument("--edge-policy-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, toml = args.root.resolve(), args.toml.resolve()
    args.base_checkpoint = args.base_checkpoint.resolve()
    args.libero_root = args.libero_root.resolve()
    args.cache_root = args.cache_root.resolve()
    args.wan_vae_path = args.wan_vae_path.resolve()
    args.edge_policy_checkpoint = args.edge_policy_checkpoint.resolve()
    recurrent = selected(resolved_config(root, toml, False, args.base_checkpoint, args.libero_root, args.cache_root, args.wan_vae_path, args.edge_policy_checkpoint))
    ttt = selected(resolved_config(root, toml, True, args.base_checkpoint, args.libero_root, args.cache_root, args.wan_vae_path, args.edge_policy_checkpoint))
    differences = {key: {"recurrent": recurrent[key], "ttt_fast_weight": ttt[key]} for key in recurrent if recurrent[key] != ttt[key]}
    resolved_config_contract = {
        "selected_fields": sorted(recurrent),
        "complete_resolved_config_diff_present": False,
        "selected_field_diff_allowed_only": set(differences) <= {"local_history_backend", "keys_to_select"},
    }
    source = {
        "root_revision": git(root, "rev-parse", "HEAD"),
        "submodule_revision": git(root / "cosmos-framework", "rev-parse", "HEAD"),
        "gitlink_revision": git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2],
    }
    stream_contract = {
        "required_fields": ["ordinal", "suite", "task_id", "episode_index", "start_frame"],
        "manifest_path": None,
        "sha256": None,
        "enforceable_by_current_dataset": False,
    }
    capture_contract = {
        "mode": None,
        "before_after_hashes_required": ["model", "optimizer", "rng", "dataloader_cursor", "local_runtime_state"],
        "non_mutating_implementation_present": False,
    }
    optimizer_contract = {
        "actual_parameter_membership_present": False,
        "required_fields": ["name", "trainable", "numel", "optimizer_state_membership"],
    }
    launch_contract = {
        "exact_argv_present": False,
        "sanitized_environment_present": False,
        "world_size": None,
        "optimizer_updates_required": 100,
        "derived_samples_per_optimizer_update": None,
    }
    manifests = {suite: sha256(args.cache_root / suite / "dataset_manifest.json") for suite in SUITES}
    checks = {
        "gitlink_matches_submodule": source["gitlink_revision"] == source["submodule_revision"],
        "base_checkpoint_exists": args.base_checkpoint.is_dir(),
        "libero_root_exists": args.libero_root.is_dir(),
        "selected_field_diff_allowed_only": resolved_config_contract["selected_field_diff_allowed_only"],
        "complete_resolved_config_diff_present": resolved_config_contract["complete_resolved_config_diff_present"],
        "backend_selectors_exact": recurrent["local_history_backend"] == "recurrent" and ttt["local_history_backend"] == "ttt_fast_weight",
        "ttt_optimizer_keys_exact": tuple(ttt["keys_to_select"]) == TTT_KEYS,
        "same_step_budget": recurrent["max_iter"] == ttt["max_iter"],
        "same_microbatch_and_accumulation": recurrent["max_samples_per_batch"] == ttt["max_samples_per_batch"] and recurrent["grad_accum_iter"] == ttt["grad_accum_iter"],
        "stream_manifest_enforceable": stream_contract["enforceable_by_current_dataset"],
        "capture_non_mutating_implementation_present": capture_contract["non_mutating_implementation_present"],
        "optimizer_membership_explicit": optimizer_contract["actual_parameter_membership_present"],
        "exact_launch_budget_frozen": launch_contract["exact_argv_present"] and launch_contract["sanitized_environment_present"],
    }
    payload = {
        "schema_version": "r09_b2_matched_training_preflight_p0_v1",
        "status": "PASS" if all(checks.values()) else "BLOCKED",
        "source": source,
        "assets": {
            "toml": {"path": str(toml), "sha256": sha256(toml)},
            "base_checkpoint": str(args.base_checkpoint),
            "libero_root": str(args.libero_root),
            "cache_root": str(args.cache_root),
            "cache_manifest_sha256": manifests,
        },
        "recurrent": recurrent,
        "ttt_fast_weight": ttt,
        "resolved_differences": differences,
        "resolved_config_contract": resolved_config_contract,
        "stream_contract": stream_contract,
        "capture_contract": capture_contract,
        "optimizer_contract": optimizer_contract,
        "launch_contract": launch_contract,
        "resource": {"gpu": gpu_snapshot(), "cpu_count": os.cpu_count(), "memory": memory_snapshot()},
        "checks": checks,
        "blockers": [
            "当前 dataset 没有可强制消费的 window-ID manifest。",
            "当前没有 non-mutating Normal/Zero/Shuffle capture 实现。",
            "当前没有实际 parameter/optimizer-state membership 清单。",
            "当前没有冻结 exact argv、sanitized environment、world size 和 100 optimizer-update 预算的 D005。",
            "当前仅比较关键 selected config 字段，尚无完整 resolved-config machine diff。",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": payload["status"], "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
