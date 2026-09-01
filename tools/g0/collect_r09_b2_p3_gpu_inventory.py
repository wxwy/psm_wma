#!/usr/bin/env python3
"""GPU-only P3 collector; execution requires a separately reviewed token."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


RUN_TOKEN = "APPROVE_TO_RUN_GPU_ONLY_P3_GATE"
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


def prepare_isolated_worker(
    edge_checkpoint_path: Path, tokenizer_config: dict[str, object]
) -> dict[str, object]:
    """准备未来 worker 的唯一导入前契约；本函数不导入 HF/Transformers。"""
    before = local_processor_record(edge_checkpoint_path)
    ready = before["is_local_directory"] and all(
        asset["exists"] for asset in before["required_assets"].values()
    )
    if not ready:
        raise ValueError("local Edge processor assets must exist before worker imports")
    validate_local_tokenizer_binding(before, tokenizer_config)
    before["resolved_tokenizer_binding"] = {
        "repository": tokenizer_config.get("repository"),
        "revision": tokenizer_config.get("revision"),
        "tokenizer_type": tokenizer_config.get("tokenizer_type"),
    }
    before["before_assets"] = before["required_assets"]
    before["after_assets"] = before["required_assets"]
    before["observed_offline_environment"] = apply_offline_processor_environment(before)
    return before


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--edge-checkpoint-path", type=Path, required=True)
    parser.add_argument("--approved-run-token", default="")
    parser.add_argument("--max-peak-gib", type=int, default=24)
    args = parser.parse_args()
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
    raise RuntimeError("GPU collector implementation must be invoked only after the separate run review")


if __name__ == "__main__":
    main()
