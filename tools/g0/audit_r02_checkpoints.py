#!/usr/bin/env python3
"""Audit Cosmos3-Edge-Policy-DROID metadata needed by G0-R02."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from safetensors import safe_open


def git_commit(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    script_path = Path(__file__).resolve()
    checkpoint = args.checkpoint.resolve()
    index_path = checkpoint / "model.safetensors.index.json"
    config_path = checkpoint / "config.json"
    checkpoint_path = checkpoint / "checkpoint.json"

    index = json.loads(index_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    policy = json.loads(checkpoint_path.read_text(encoding="utf-8"))["policy"]
    root_weight_map = index["weight_map"]
    transformer_index_path = checkpoint / "transformer" / "diffusion_pytorch_model.safetensors.index.json"
    transformer_weight_map = json.loads(transformer_index_path.read_text(encoding="utf-8"))["weight_map"]

    # Match cosmos_framework.inference.model._diffusers_weight_map: old Edge
    # exports leaked stale K-Norm aliases into the root index. The supported
    # loader drops them and merges the canonical transformer component index.
    weight_map = {
        key: value for key, value in root_weight_map.items() if ".k_norm_und_for_gen." not in key
    }
    for key, relative_path in transformer_weight_map.items():
        weight_map.setdefault(key, f"transformer/{relative_path}")

    files: dict[str, dict[str, object]] = {}
    missing_indexed_keys: dict[str, list[str]] = {}
    for relative_path in sorted(set(weight_map.values())):
        shard_path = checkpoint / relative_path
        indexed_keys = {key for key, value in weight_map.items() if value == relative_path}
        with safe_open(str(shard_path), framework="pt", device="cpu") as shard:
            header_keys = set(shard.keys())
        missing = sorted(indexed_keys - header_keys)
        extra = sorted(header_keys - indexed_keys)
        files[relative_path] = {
            "indexed_key_count": len(indexed_keys),
            "header_key_count": len(header_keys),
            "missing_indexed_key_count": len(missing),
            "extra_header_key_count": len(extra),
            "extra_header_keys": extra,
        }
        if missing:
            missing_indexed_keys[relative_path] = missing

    raw_root_k_norm_keys = sorted(
        key for key in root_weight_map if ".k_norm_und_for_gen." in key
    )
    stale_root_k_norm_keys = sorted(key for key in raw_root_k_norm_keys if key.startswith("layers.layers."))
    overlay_path = "transformer/cosmos_framework_model.safetensors"
    overlay_k_norm_keys = sorted(
        key for key, value in root_weight_map.items() if value == overlay_path and "k_norm_und_for_gen" in key
    )
    effective_k_norm_keys = sorted(key for key in weight_map if "k_norm_und_for_gen" in key)
    model_config = config["model"]["config"]
    status = "PASS" if not missing_indexed_keys else "BLOCKED"
    result = {
        "schema_version": "1.0",
        "gate": "G0-R02",
        "status": status,
        "provenance": {
            "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "repo_commit": git_commit(root),
            "cosmos_commit": git_commit(root / "cosmos-framework"),
            "script_path": str(script_path.relative_to(root)),
            "script_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
            "command": [sys.executable, *sys.argv],
            "run_config": {
                "checkpoint": str(checkpoint),
                "output": str(args.output),
            },
        },
        "checkpoint": str(checkpoint),
        "audit_scope": "metadata/config/index-only; no full tensor value diff",
        "facts": {
            "raw_root_index_key_count": len(root_weight_map),
            "raw_root_k_norm_key_count": len(raw_root_k_norm_keys),
            "raw_root_stale_k_norm_key_count": len(stale_root_k_norm_keys),
            "raw_root_stale_k_norm_key_sample": stale_root_k_norm_keys[:3],
            "raw_root_overlay_k_norm_key_count": len(overlay_k_norm_keys),
            "raw_root_overlay_k_norm_key_sample": overlay_k_norm_keys[:3],
            "effective_index_key_count": len(weight_map),
            "effective_k_norm_key_count": len(effective_k_norm_keys),
            "effective_files": files,
            "effective_missing_indexed_key_count": sum(len(keys) for keys in missing_indexed_keys.values()),
            "model": {
                "action_gen": model_config["action_gen"],
                "max_action_dim": model_config["max_action_dim"],
                "num_embodiment_domains": model_config["num_embodiment_domains"],
                "use_und_k_norm_for_gen": model_config["vlm_config"]["model_instance"]["config"][
                    "use_und_k_norm_for_gen"
                ],
            },
            "droid_policy": policy,
        },
        "warm_start_decision": {
            "base_model_config": "EDGE_MODEL_CONFIG",
            "inherit": [
                "moe_gen",
                "time_embedder",
                "vae2llm",
                "llm2vae",
                "action2llm",
                "llm2action",
                "action_modality_embed",
                "language_model.*.k_norm_und_for_gen",
            ],
            "do_not_reuse_as_libero_contract": [
                "policy.action_chunk_size=32",
                "policy.conditioning_fps=15",
                "policy.domain_name=droid_lerobot",
            ],
            "libero_contract": {
                "fps": {"value": 20, "evidence": "action_policy_libero_nano.py:202"},
                "action_chunk_size": {"value": 16, "evidence": "action_policy_libero_nano.py:203"},
                "action_space": {
                    "value": "frame_wise_relative",
                    "evidence": "action_policy_libero_nano.py:207",
                },
                "rotation_representation": {"value": "6d", "evidence": "action_policy_libero_nano.py:208"},
                "action_normalization": {
                    "value": "quantile_rot",
                    "evidence": "action_policy_libero_nano.py:210",
                },
                "views": {"value": "agentview+wrist concat_view", "evidence": "action_policy_libero_nano.py:204-206"},
            },
        },
        "blockers": (
            [
                {
                    "id": "R02-INDEX-001",
                    "summary": "项目有效索引仍包含 shard header 中不存在的键",
                    "impact": "checkpoint 无法通过严格 Diffusers storage reader 加载",
                    "resolution": "修复索引合并逻辑后重新审计",
                }
            ]
            if missing_indexed_keys
            else []
        ),
        "limitations": [
            "cosmos_framework.inference.model 已兼容旧导出的陈旧 K-Norm 根索引；inference2/_model_io.py 尚未同步，当前不得作为该 checkpoint 的加载入口",
            "本 Gate 不重复全量张量数值 diff；既有数值变化结论仍按分层抽样证据处理",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "output": str(args.output)}, ensure_ascii=False))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
