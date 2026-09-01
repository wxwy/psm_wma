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
