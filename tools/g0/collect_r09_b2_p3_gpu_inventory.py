#!/usr/bin/env python3
"""GPU-only P3 collector; execution requires a separately reviewed token."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


RUN_TOKEN = "APPROVE_TO_RUN_GPU_ONLY_P3_GATE"
INVENTORY_MODEL_OVERRIDES = {"load_vision_tokenizer": False}
FROZEN_SOURCE_PATHS = {
    "recipe_sha256": "cosmos-framework/examples/toml/sft_config/action_policy_libero_edge_all.toml",
    "production_recipe_source_sha256": "cosmos-framework/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py",
    "edge_model_config_source_sha256": "cosmos-framework/cosmos_framework/configs/base/experiment/sft/models/edge_model_config.py",
    "inherited_recipe_source_sha256": "cosmos-framework/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_all_nano.py",
    "collector_sha256": "tools/g0/collect_r09_b2_p3_gpu_inventory.py",
    "verifier_sha256": "tools/g0/verify_r09_b2_p3_gpu_inventory.py",
    "model_source_sha256": "cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py",
    "optimizer_source_sha256": "cosmos-framework/cosmos_framework/utils/generator/optimizer.py",
    "dcp_source_sha256": "cosmos-framework/cosmos_framework/checkpoint/dcp.py",
}
REQUIRED_PROCESSOR_ASSETS = (
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.jinja",
    "special_tokens_map.json",
    "preprocessor_config.json",
    "video_preprocessor_config.json",
)


def local_processor_record(path: Path) -> dict[str, object]:
    """只读审计；不导入 transformers 或触发任何下载。"""
    canonical = path.expanduser().resolve()
    assets = {}
    for name in REQUIRED_PROCESSOR_ASSETS:
        asset = canonical / name
        digest = hashlib.sha256(asset.read_bytes()).hexdigest() if asset.is_file() else None
        assets[name] = {
            "path": str(asset),
            "exists": asset.is_file(),
            "size_bytes": asset.stat().st_size if asset.is_file() else None,
            "sha256": digest,
        }
    return {
        "canonical_path": str(canonical),
        "is_local_directory": canonical.is_dir(),
        "required_assets": assets,
        "offline_environment": {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HUGGINGFACE_HUB_CACHE": str(canonical),
        },
    }


def apply_offline_processor_environment(record: dict[str, object]) -> dict[str, str]:
    """在未来隔离 worker 的任何 HF/Transformers 导入前调用。"""
    expected = record["offline_environment"]
    os.environ.update(expected)
    return {key: os.environ.get(key, "") for key in expected}


def compare_processor_records(before: dict[str, object], after: dict[str, object]) -> bool:
    """严格比较已批准 processor 配置文件的只读快照。"""
    return before == after


def validate_local_tokenizer_binding(
    processor: dict[str, object], tokenizer_config: dict[str, object]
) -> None:
    """future worker 的导入前 hard-gate：只能使用 recipe 解析后的本地路径。"""
    canonical = processor["canonical_path"]
    if tokenizer_config.get("repository") is not None or tokenizer_config.get("revision") is not None:
        raise ValueError("resolved tokenizer must not retain a remote repository or revision")
    if tokenizer_config.get("tokenizer_type") != canonical:
        raise ValueError("resolved tokenizer_type must equal the canonical local Edge checkpoint")


def resolved_tokenizer_binding(vlm_config: object) -> dict[str, object]:
    """Canonicalize the exact tokenizer node consumed by the production helper."""
    tokenizer = vlm_config.get("tokenizer") if isinstance(vlm_config, dict) else getattr(vlm_config, "tokenizer")
    getter = tokenizer.get if hasattr(tokenizer, "get") else lambda key: getattr(tokenizer, key, None)
    return {key: getter(key) for key in ("repository", "revision", "tokenizer_type")}


def prepare_isolated_worker(
    edge_checkpoint_path: Path, vlm_config: object
) -> dict[str, object]:
    """准备未来 worker 的唯一导入前契约；本函数不导入 HF/Transformers。"""
    before = local_processor_record(edge_checkpoint_path)
    ready = before["is_local_directory"] and all(
        asset["exists"] for asset in before["required_assets"].values()
    )
    if not ready:
        raise ValueError("local Edge processor assets must exist before worker imports")
    binding = resolved_tokenizer_binding(vlm_config)
    validate_local_tokenizer_binding(before, binding)
    before["resolved_tokenizer_binding"] = binding
    before["before_assets"] = before["required_assets"]
    before["observed_offline_environment"] = apply_offline_processor_environment(before)
    return before


def run_production_processor_construction(
    record: dict[str, object], vlm_config: object
) -> dict[str, object]:
    """future worker 的固定生产构造路径；仅在独立 run 审批后调用。"""
    actual_binding = resolved_tokenizer_binding(vlm_config)
    if actual_binding != record["resolved_tokenizer_binding"]:
        raise ValueError("actual production tokenizer binding differs from validated binding")

    from cosmos_framework.model.generator.omni_mot_model import build_vlm_processor

    processor = build_vlm_processor(vlm_config)
    if processor is None:
        raise RuntimeError("production processor construction returned None")
    after = local_processor_record(Path(record["canonical_path"]))
    record["after_assets"] = after["required_assets"]
    binding = json.dumps(actual_binding, sort_keys=True)
    record["phase_trace"] = [
        "offline_env_applied", "binding_validated", "processor_constructed", "post_snapshot_taken"
    ]
    record["construction_witness"] = {
        "constructor_identity": "cosmos_framework.model.generator.omni_mot_model.build_vlm_processor",
        "binding_sha256": hashlib.sha256(binding.encode()).hexdigest(),
        "processor_type": f"{type(processor).__module__}.{type(processor).__qualname__}",
    }
    return record


def _tensor_metadata(value: object) -> dict[str, object]:
    return {
        "shape": list(value.shape),
        "dtype": str(value.dtype).removeprefix("torch."),
        "numel": value.numel(),
    }


def _state_leaf_metadata(value: object, path: str = "") -> list[dict[str, object]]:
    """只遍历 state_dict schema；不复制或序列化 tensor 内容。"""
    if hasattr(value, "shape") and hasattr(value, "dtype") and hasattr(value, "numel"):
        return [{"path": path, "kind": "tensor", **_tensor_metadata(value)}]
    if isinstance(value, dict):
        rows = []
        for key in sorted(value, key=str):
            child = f"{path}.{key}" if path else str(key)
            rows.extend(_state_leaf_metadata(value[key], child))
        return rows
    if isinstance(value, (list, tuple)):
        rows = []
        for index, item in enumerate(value):
            rows.extend(_state_leaf_metadata(item, f"{path}[{index}]"))
        return rows
    scalar = value if value is None or isinstance(value, (bool, int, float, str)) else repr(value)
    return [{"path": path, "kind": type(value).__name__, "value": scalar}]


def _stable_parameter_references(value: object, stable_names: set[str]) -> set[str]:
    """从 production optimizer state_dict 中反查稳定参数名。"""
    references: set[str] = set()
    if isinstance(value, str):
        candidate = value.removeprefix("net.")
        if candidate in stable_names:
            references.add(candidate)
    elif isinstance(value, dict):
        for key, item in value.items():
            references.update(_stable_parameter_references(key, stable_names))
            references.update(_stable_parameter_references(item, stable_names))
    elif isinstance(value, (list, tuple)):
        for item in value:
            references.update(_stable_parameter_references(item, stable_names))
    return references


def _worker_inventory(
    root: Path,
    toml: Path,
    edge_checkpoint_path: Path,
    backend: str,
    path_environment: dict[str, str],
    max_peak_gib: int,
) -> dict[str, object]:
    """仅由 run-token 分支在隔离单卡进程调用。"""
    pre_import_processor = local_processor_record(edge_checkpoint_path)
    apply_offline_processor_environment(pre_import_processor)
    os.environ.update(path_environment)
    os.environ.update({
        "PSM_R08_LOCAL_HISTORY_ENABLED": "1",
        "PSM_LOCAL_DUMMY_ENABLED": "0",
        "PSM_R09_A1_ENABLED": "0",
        "PSM_R09_B1_TTT_ENABLED": "1" if backend == "ttt_fast_weight" else "0",
    })
    import torch

    if torch.distributed.is_initialized():
        raise RuntimeError("P3 worker must not initialize distributed")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("P3 worker requires exactly one visible CUDA device")

    from cosmos_framework.checkpoint.dcp import ModelWrapper
    from cosmos_framework.configs.toml_config.sft_config import load_experiment_from_toml
    from cosmos_framework.utils.lazy_config import instantiate

    def enforce_peak_limit(phase: str) -> None:
        peak = max(torch.cuda.max_memory_allocated(), torch.cuda.max_memory_reserved())
        if peak > max_peak_gib * 1024**3:
            raise RuntimeError(f"P3 exceeded {max_peak_gib} GiB after {phase}: {peak} bytes")

    config = load_experiment_from_toml(toml)
    vlm_config = config.model.config.vlm_config
    processor = prepare_isolated_worker(edge_checkpoint_path, vlm_config)
    processor = run_production_processor_construction(processor, vlm_config)

    observed_overrides = {}
    for key, value in INVENTORY_MODEL_OVERRIDES.items():
        observed_overrides[key] = {"before": getattr(config.model.config, key), "after": value}
        setattr(config.model.config, key, value)
    model = instantiate(config.model)
    enforce_peak_limit("model construction")
    optimizer = instantiate(config.optimizer, model=model)
    enforce_peak_limit("optimizer construction")

    parameters = dict(model.net.named_parameters())
    buffers = dict(model.net.named_buffers())
    keys_to_select = list(config.optimizer.keys_to_select)
    selector = {
        name: not keys_to_select or any(key in name for key in keys_to_select)
        for name in parameters
    }
    reverse = {id(parameter): name for name, parameter in parameters.items()}
    grouped_names: list[str] = []
    groups = []
    for optimizer_index, inner in enumerate(optimizer.optimizers):
        for group_index, group in enumerate(inner.param_groups):
            entries = []
            for parameter in group["params"]:
                name = reverse.get(id(parameter))
                if name is None:
                    raise RuntimeError("optimizer parameter is absent from model.net.named_parameters")
                grouped_names.append(name)
                entries.append({"name": name, **_tensor_metadata(parameter)})
            groups.append({
                "optimizer_index": optimizer_index,
                "group_index": group_index,
                "parameters": sorted(entries, key=lambda row: row["name"]),
                "lr": group["lr"],
                "weight_decay": group.get("weight_decay"),
            })
    if len(grouped_names) != len(set(grouped_names)):
        raise RuntimeError("optimizer contains a duplicate model parameter")
    selected = set(grouped_names)

    optimizer_state_entries = []
    for inner in optimizer.optimizers:
        for parameter, state in inner.state.items():
            name = reverse.get(id(parameter))
            if name is None:
                raise RuntimeError("optimizer state key is absent from model.net.named_parameters")
            optimizer_state_entries.append({
                "parameter_name": name,
                "state_keys": sorted(str(key) for key in state),
                "state": _state_leaf_metadata(state),
            })

    model_dcp = ModelWrapper(model).state_dict()
    enforce_peak_limit("ModelWrapper.state_dict")
    optimizer_dcp = optimizer.state_dict()
    enforce_peak_limit("OptimizersContainer.state_dict")
    model_dcp_keys = sorted(model_dcp)
    expected_model_keys = {name: f"net.{name}" for name in parameters}
    selected_model_keys = {
        name: expected_model_keys[name]
        for name in selected
        if expected_model_keys[name] in model_dcp
    }
    optimizer_references = _stable_parameter_references(optimizer_dcp, set(parameters))
    if set(selected_model_keys) != selected:
        raise RuntimeError("selected optimizer parameters are missing from production ModelWrapper.state_dict")
    if optimizer_references != selected:
        raise RuntimeError("production OptimizersContainer.state_dict membership differs from optimizer groups")

    ttt_names = {"W", "pending_evidence", "last_evidence", "initialized", "segment_progress"}
    persistent_keys = model_dcp_keys + [row["path"] for row in _state_leaf_metadata(optimizer_dcp, "optimizer")]
    forbidden = [key for key in persistent_keys if key.split(".")[-1].split("[")[0] in ttt_names]
    if forbidden:
        raise RuntimeError(f"TTT runtime state became persistent: {forbidden}")
    final_processor = local_processor_record(edge_checkpoint_path)
    processor["worker_final_assets"] = final_processor["required_assets"]
    if processor["worker_final_assets"] != processor["before_assets"]:
        raise RuntimeError("local processor assets changed during full worker construction")
    if torch.distributed.is_initialized():
        raise RuntimeError("P3 worker initialized distributed unexpectedly")

    return {
        "status": "PASS",
        "local_processor": processor,
        "inventory_model_overrides": observed_overrides,
        "inventory": {
            "selector": {"backend": backend, "keys_to_select": keys_to_select},
            "selector_optimizer_exclusions": [],
            "model_parameters": [
                {
                    "name": name,
                    "trainable": parameter.requires_grad,
                    **_tensor_metadata(parameter),
                    "selected_by_resolved_selector": selector[name],
                    "selected_by_optimizer": name in selected,
                }
                for name, parameter in sorted(parameters.items())
            ],
            "named_buffers": [
                {"name": name, **_tensor_metadata(value)} for name, value in sorted(buffers.items())
            ],
            "optimizer_param_groups": groups,
            "optimizer_state": {
                "eligible_parameter_names": sorted(selected),
                "not_materialized": not optimizer_state_entries,
                "index_semantics": "in_process_parameter_object_identity;persisted_by_stable_parameter_name",
                "entries": sorted(optimizer_state_entries, key=lambda row: row["parameter_name"]),
            },
            "dcp_state": {
                "inspected": True,
                "production_binding": {
                    "model_symbol": "cosmos_framework.checkpoint.dcp.ModelWrapper.state_dict",
                    "optimizer_symbol": "cosmos_framework.utils.generator.optimizer.OptimizersContainer.state_dict",
                    "model_invoked": True,
                    "optimizer_invoked": True,
                },
                "model_state_keys": model_dcp_keys,
                "selected_model_parameter_keys": selected_model_keys,
                "optimizer_parameter_references": sorted(optimizer_references),
                "optimizer_state_schema": _state_leaf_metadata(optimizer_dcp),
                "persistent_keys": persistent_keys,
            },
        },
        "execution": {
            "backend": backend,
            "device": str(torch.cuda.current_device()),
            "distributed_initialized": torch.distributed.is_initialized(),
            "observed_environment": {
                key: os.environ.get(key, "")
                for key in (
                    "CUDA_VISIBLE_DEVICES", "EDGE_POLICY_CHECKPOINT", "WAN_VAE_PATH",
                    "BASE_CHECKPOINT_PATH", "LIBERO_ROOT", "PSM_R08_LOCAL_HISTORY_ENABLED",
                    "PSM_LOCAL_DUMMY_ENABLED", "PSM_R09_A1_ENABLED", "PSM_R09_B1_TTT_ENABLED",
                    "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HUGGINGFACE_HUB_CACHE",
                )
            },
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
        },
    }


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matched_diff(backends: dict[str, dict[str, object]]) -> dict[str, object]:
    def selected(name: str, field: str) -> set[str]:
        rows = backends[name].get("inventory", {}).get("model_parameters", [])
        return {row["name"] for row in rows if row.get(field)}

    result = {"allowed_backend_specific_prefixes": ["local_history_runtime.recurrent_backend."]}
    for field, label in (
        ("selected_by_resolved_selector", "resolved_selector"),
        ("selected_by_optimizer", "optimizer"),
    ):
        recurrent = selected("recurrent", field)
        ttt = selected("ttt_fast_weight", field)
        result[f"recurrent_only_{label}"] = sorted(recurrent - ttt)
        result[f"ttt_only_{label}"] = sorted(ttt - recurrent)
    return result


def _gpu_uuid(visible_device: str) -> str:
    completed = subprocess.run(
        ["nvidia-smi", "-i", visible_device, "--query-gpu=uuid", "--format=csv,noheader"],
        text=True,
        capture_output=True,
        check=True,
    )
    values = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(values) != 1:
        raise RuntimeError(f"expected one visible GPU UUID, got {values}")
    return values[0]


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--toml", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--edge-checkpoint-path", type=Path, required=True)
    parser.add_argument("--wan-vae-path", type=Path)
    parser.add_argument("--base-checkpoint-path", type=Path)
    parser.add_argument("--libero-root", type=Path)
    parser.add_argument("--d005-record", type=Path)
    parser.add_argument("--approved-run-token", default="")
    parser.add_argument("--max-peak-gib", type=int, default=24)
    parser.add_argument("--worker-backend", choices=("recurrent", "ttt_fast_weight"))
    args = parser.parse_args()
    root = args.root.resolve()
    processor = local_processor_record(args.edge_checkpoint_path)
    processor_ready = processor["is_local_directory"] and all(
        asset["exists"] for asset in processor["required_assets"].values()
    )
    if args.approved_run_token != RUN_TOKEN or not processor_ready:
        result = {
            "schema_version": "r09_b2_p3_gpu_inventory_v1",
            "status": "BLOCKED",
            "reason": (
                "GPU execution requires separately reviewed APPROVE_TO_RUN_GPU_ONLY_P3_GATE token"
                if processor_ready
                else "local processor directory or required assets are missing"
            ),
            "local_processor": processor,
            "execution": {
                "world_size": 1,
                "distributed_initialized": False,
                "weights_loaded": False,
                "checkpoint_loaded": False,
                "forward_executed": False,
                "backward_executed": False,
                "optimizer_step_executed": False,
                "scheduler_step_executed": False,
                "checkpoint_saved": False,
                "peak_allocated_bytes": 0,
                "peak_reserved_bytes": 0,
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": "BLOCKED"}))
        return
    if args.max_peak_gib != 24 or args.toml is None or args.d005_record is None:
        raise ValueError("approved P3 run requires --toml, --d005-record, and --max-peak-gib=24")
    required_paths = {
        "WAN_VAE_PATH": args.wan_vae_path,
        "BASE_CHECKPOINT_PATH": args.base_checkpoint_path,
        "LIBERO_ROOT": args.libero_root,
    }
    if any(path is None for path in required_paths.values()):
        raise ValueError("approved P3 run requires --wan-vae-path, --base-checkpoint-path, and --libero-root")
    path_environment = {
        "EDGE_POLICY_CHECKPOINT": str(args.edge_checkpoint_path.resolve()),
        **{key: str(path.resolve()) for key, path in required_paths.items()},
    }
    if args.worker_backend:
        result = _worker_inventory(
            root, args.toml.resolve(), args.edge_checkpoint_path.resolve(), args.worker_backend,
            path_environment, args.max_peak_gib,
        )
        _write_json(args.output, result)
        return

    if os.environ.get("WORLD_SIZE", "1") != "1":
        raise RuntimeError("P3 requires WORLD_SIZE=1")
    environment = {
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        **path_environment,
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HUGGINGFACE_HUB_CACHE": str(args.edge_checkpoint_path.resolve()),
    }
    if not environment["CUDA_VISIBLE_DEVICES"] or "," in environment["CUDA_VISIBLE_DEVICES"]:
        raise RuntimeError("P3 requires one explicit CUDA_VISIBLE_DEVICES entry")
    gpu_uuid = _gpu_uuid(environment["CUDA_VISIBLE_DEVICES"])
    root_revision = _git(root, "rev-parse", "HEAD")
    framework = root / "cosmos-framework"
    submodule_revision = _git(framework, "rev-parse", "HEAD")
    gitlink_revision = _git(root, "ls-tree", root_revision, "cosmos-framework").split()[2]
    command_argv = [str(Path(sys.argv[0]).resolve()), *sys.argv[1:]]
    d005 = {
        "root_revision": root_revision,
        "submodule_revision": submodule_revision,
        "gitlink_revision": gitlink_revision,
        "command_argv": command_argv,
        "cwd": str(Path.cwd().resolve()),
        "environment": environment,
        "gpu_uuid": gpu_uuid,
        "world_size": 1,
        "max_peak_gib": args.max_peak_gib,
        "approved_run_token": args.approved_run_token,
    }
    d005_path = args.d005_record.resolve()
    try:
        d005_relative = d005_path.relative_to(root)
    except ValueError as error:
        raise ValueError("D005 record must be inside root") from error
    _write_json(d005_path, d005)

    backends = {}
    for backend in ("recurrent", "ttt_fast_weight"):
        backend_output = args.output.with_name(f"{args.output.stem}_{backend}.json").resolve()
        command = command_argv + ["--worker-backend", backend, "--output", str(backend_output)]
        child_environment = os.environ | environment
        completed = subprocess.run(command, cwd=root, env=child_environment, text=True, capture_output=True)
        if completed.returncode:
            backends[backend] = {
                "status": "BLOCKED",
                "reason": (completed.stderr or completed.stdout)[-4000:],
            }
        else:
            backends[backend] = json.loads(backend_output.read_text())

    peak_allocated = max(record.get("execution", {}).get("peak_allocated_bytes", 0) for record in backends.values())
    peak_reserved = max(record.get("execution", {}).get("peak_reserved_bytes", 0) for record in backends.values())
    pass_backends = all(record.get("status") == "PASS" for record in backends.values())
    within_limit = max(peak_allocated, peak_reserved) <= args.max_peak_gib * 1024**3
    provenance = {
        "root_revision": root_revision,
        "submodule_revision": submodule_revision,
        "gitlink_revision": gitlink_revision,
        "command_argv": command_argv,
        "cwd": str(Path.cwd().resolve()),
        "environment": environment,
        "gpu_uuid": gpu_uuid,
        "approved_run_token": args.approved_run_token,
        "d005_record": {"path": str(d005_relative), "sha256": _sha256(d005_path)},
    }
    provenance.update({field: _sha256(root / relative) for field, relative in FROZEN_SOURCE_PATHS.items()})
    result = {
        "schema_version": "r09_b2_p3_gpu_inventory_v1",
        "status": "PASS" if pass_backends and within_limit else "BLOCKED",
        "reason": None if pass_backends and within_limit else "backend construction blocked or 24 GiB cap exceeded",
        "local_processor": backends.get("recurrent", {}).get("local_processor", processor),
        "provenance": provenance,
        "execution": {
            "world_size": 1,
            "distributed_initialized": False,
            "weights_loaded": False,
            "checkpoint_loaded": False,
            "forward_executed": False,
            "backward_executed": False,
            "optimizer_step_executed": False,
            "scheduler_step_executed": False,
            "checkpoint_saved": False,
            "peak_allocated_bytes": peak_allocated,
            "peak_reserved_bytes": peak_reserved,
        },
        **backends,
        "matched_diff": _matched_diff(backends) if pass_backends else {
            "allowed_backend_specific_prefixes": ["local_history_runtime.recurrent_backend."],
        },
    }
    _write_json(args.output, result)
    print(json.dumps({"status": result["status"]}))


if __name__ == "__main__":
    main()
