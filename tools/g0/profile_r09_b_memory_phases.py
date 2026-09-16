#!/usr/bin/env python3
"""R09-B 逐阶段显存 profile：baseline / local / active 三条选择集。

复现 P3 collector 的构造顺序，但在每个阶段边界记录 torch CUDA 显存，把 P3 Gate
只发布一个 `peak_allocated_bytes` 标量的结论展开成逐阶段分解；并补上 P3 从未跑过的
正式 active selector（`PSM_R09_B_TTT_ENABLED=1`，整体替换为 SELECTORS 四组）。

`load_vision_tokenizer` 在本工具里可切换：P3 inventory 固定为 False（只做 inventory），
而正式训练是 True（config dump 实测），两者相差一整份 Wan VAE，必须分开量。

无数据集、无 forward/backward/step、无外网、不写 checkpoint。只读地构造与测量。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import collect_r09_b2_p3_gpu_inventory as p3  # noqa: E402  复用其只读构造原语


# 三条选择集。baseline 是已训到 iter_2800 的正式路线（纯 Nano allowlist）；
# local 等于 P3 collector 的 recurrent backend；active 是正式 Local-Memory 路线。
BACKEND_ENVIRONMENTS = {
    "baseline": {
        "PSM_R08_LOCAL_HISTORY_ENABLED": "0",
        "PSM_LOCAL_DUMMY_ENABLED": "0",
        "PSM_R09_A1_ENABLED": "0",
        "PSM_R09_B1_TTT_ENABLED": "0",
        "PSM_R09_B_TTT_ENABLED": "0",
    },
    "local": {
        "PSM_R08_LOCAL_HISTORY_ENABLED": "1",
        "PSM_LOCAL_DUMMY_ENABLED": "0",
        "PSM_R09_A1_ENABLED": "0",
        "PSM_R09_B1_TTT_ENABLED": "0",
        "PSM_R09_B_TTT_ENABLED": "0",
    },
    "active": {
        "PSM_R08_LOCAL_HISTORY_ENABLED": "1",
        "PSM_LOCAL_DUMMY_ENABLED": "0",
        "PSM_R09_A1_ENABLED": "0",
        "PSM_R09_B1_TTT_ENABLED": "0",
        "PSM_R09_B_TTT_ENABLED": "1",
        "PSM_R09_B_TTT_ACTIVE": "1",
        "PSM_R09_B_TTT_ACTIVE_GA": "16",
    },
}


def _worker_profile(
    root: Path,
    toml: Path,
    edge_checkpoint_path: Path,
    backend: str,
    path_environment: dict[str, str],
    load_vision_tokenizer: bool,
) -> dict[str, object]:
    """仅在单卡隔离子进程内调用；不初始化 distributed、不执行任何 step。"""
    pre_import_processor = p3.local_processor_record(edge_checkpoint_path)
    p3.apply_offline_processor_environment(pre_import_processor)
    os.environ.update(path_environment)
    os.environ.update(BACKEND_ENVIRONMENTS[backend])

    import torch

    if torch.distributed.is_initialized():
        raise RuntimeError("memory-phase worker must not initialize distributed")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("memory-phase worker requires exactly one visible CUDA device")

    from cosmos_framework.checkpoint.dcp import ModelWrapper
    from cosmos_framework.configs.toml_config.sft_config import load_experiment_from_toml
    from cosmos_framework.utils.lazy_config import instantiate

    trace: list[dict[str, object]] = []
    previous_allocated = 0

    def record(stage: str) -> None:
        """记录一个阶段边界的瞬时占用与累计峰值；delta 即该阶段的净增量。"""
        nonlocal previous_allocated
        allocated = torch.cuda.memory_allocated()
        trace.append({
            "stage": stage,
            "allocated_bytes": allocated,
            "reserved_bytes": torch.cuda.memory_reserved(),
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
            "delta_allocated_bytes": allocated - previous_allocated,
        })
        previous_allocated = allocated

    p3._set_worker_production_cwd(root)
    torch.cuda.reset_peak_memory_stats()
    record("cuda_init")

    config = load_experiment_from_toml(toml)
    vlm_config = config.model.config.vlm_config
    processor = p3.prepare_isolated_worker(edge_checkpoint_path, vlm_config)
    processor = p3.run_production_processor_construction(processor, vlm_config)
    record("processor")

    observed_vision_tokenizer = {"before": getattr(config.model.config, "load_vision_tokenizer"), "after": load_vision_tokenizer}
    setattr(config.model.config, "load_vision_tokenizer", load_vision_tokenizer)
    model = instantiate(config.model)
    record("model_build")

    optimizer = instantiate(config.optimizer, model=model)
    record("optimizer_build")

    parameters = dict(model.net.named_parameters())
    keys_to_select = list(config.optimizer.keys_to_select)
    selected = [
        name for name in parameters
        if not keys_to_select or any(key in name for key in keys_to_select)
    ]
    selected_elements = sum(parameters[name].numel() for name in selected)
    dtype_bytes = {"torch.bfloat16": 2, "torch.float32": 4}
    selected_dtypes = sorted({str(parameters[name].dtype) for name in selected})

    model_dcp = ModelWrapper(model).state_dict()
    record("model_state_dict")
    optimizer_dcp = optimizer.state_dict()
    record("optimizer_state_dict")

    return {
        "schema_version": "r09_b_memory_phases_v1",
        "status": "PASS",
        "backend": backend,
        "load_vision_tokenizer": load_vision_tokenizer,
        "observed_load_vision_tokenizer": observed_vision_tokenizer,
        "keys_to_select": keys_to_select,
        "parameter_count": len(parameters),
        "selected_parameter_count": len(selected),
        "selected_element_count": selected_elements,
        "selected_dtypes": selected_dtypes,
        "selected_dtype_bytes": {dtype: dtype_bytes.get(dtype) for dtype in selected_dtypes},
        "selected_parameters": [
            {"name": name, "shape": list(parameters[name].shape), "numel": parameters[name].numel()}
            for name in selected
        ],
        "model_state_dict_key_count": len(model_dcp),
        "optimizer_state_dict_root_keys": sorted(optimizer_dcp),
        "stage_trace": trace,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
    }


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--toml", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--edge-checkpoint-path", type=Path, required=True)
    parser.add_argument("--base-checkpoint-path", type=Path, required=True)
    parser.add_argument("--wan-vae-path", type=Path, required=True)
    parser.add_argument("--libero-root", type=Path, required=True)
    parser.add_argument("--backends", default="baseline,local,active")
    parser.add_argument("--vision-tokenizer", default="0,1")
    parser.add_argument("--worker-backend", choices=tuple(BACKEND_ENVIRONMENTS))
    parser.add_argument("--worker-vision-tokenizer", choices=("0", "1"))
    args = parser.parse_args()

    root = args.root.resolve()
    path_environment = {
        "EDGE_POLICY_CHECKPOINT": str(args.edge_checkpoint_path.resolve()),
        "BASE_CHECKPOINT_PATH": str(args.base_checkpoint_path.resolve()),
        "WAN_VAE_PATH": str(args.wan_vae_path.resolve()),
        "LIBERO_ROOT": str(args.libero_root.resolve()),
    }

    if args.worker_backend:
        result = _worker_profile(
            root,
            args.toml.resolve(),
            args.edge_checkpoint_path.resolve(),
            args.worker_backend,
            path_environment,
            args.worker_vision_tokenizer == "1",
        )
        _write_json(args.output, result)
        return

    if os.environ.get("WORLD_SIZE", "1") != "1":
        raise RuntimeError("memory-phase profile requires WORLD_SIZE=1")
    child_environment = {
        **os.environ,
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", "0"),
        "WORLD_SIZE": "1",
        **path_environment,
    }

    combinations = [
        (backend, vision)
        for backend in args.backends.split(",")
        for vision in args.vision_tokenizer.split(",")
    ]
    results: dict[str, dict[str, object]] = {}
    for backend, vision in combinations:
        tag = f"{backend}_vision{vision}"
        unit_output = args.output.with_name(f"{args.output.stem}_{tag}.json").resolve()
        command = [
            sys.executable, str(Path(__file__).resolve()),
            "--root", str(root),
            "--toml", str(args.toml.resolve()),
            "--edge-checkpoint-path", str(args.edge_checkpoint_path.resolve()),
            "--base-checkpoint-path", str(args.base_checkpoint_path.resolve()),
            "--wan-vae-path", str(args.wan_vae_path.resolve()),
            "--libero-root", str(args.libero_root.resolve()),
            "--worker-backend", backend,
            "--worker-vision-tokenizer", vision,
            "--output", str(unit_output),
        ]
        completed = subprocess.run(command, cwd=root, env=child_environment, text=True, capture_output=True)
        if completed.returncode or not unit_output.is_file():
            results[tag] = {
                "status": "BLOCKED",
                "reason": f"worker exited {completed.returncode}",
                "stdout": completed.stdout[-4000:],
                "stderr": completed.stderr[-4000:],
            }
            break
        results[tag] = json.loads(unit_output.read_text())
        if results[tag].get("status") != "PASS":
            break

    aggregate = {
        "schema_version": "r09_b_memory_phases_v1",
        "status": "PASS" if all(r.get("status") == "PASS" for r in results.values()) and len(results) == len(combinations) else "BLOCKED",
        "combination_count": len(combinations),
        "completed_count": sum(1 for r in results.values() if r.get("status") == "PASS"),
        "results": results,
    }
    _write_json(args.output, aggregate)
    print(json.dumps({"status": aggregate["status"], "completed": aggregate["completed_count"], "of": aggregate["combination_count"]}))


if __name__ == "__main__":
    main()
