#!/usr/bin/env python3
"""Generate the G0-R03 LIBERO action-contract audit artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch
from safetensors import safe_open

from cosmos_framework.data.generator.action.action_normalization import normalize_action
from cosmos_framework.data.generator.action.datasets.action_sft_dataset import get_action_libero_sft_dataset
from cosmos_framework.data.generator.action.domain_utils import get_domain_id
from cosmos_framework.inference.model import _diffusers_to_net_key, _diffusers_weight_map
from cosmos_framework.model.generator.mot.domain_aware_linear import DomainAwareLinear


SELECTORS = (
    "moe_gen",
    "time_embedder",
    "vae2llm",
    "llm2vae",
    "action2llm",
    "llm2action",
    "action_modality_embed",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def git_commit(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def checkpoint_parameter_counts(checkpoint: Path) -> tuple[int, int, dict[str, int]]:
    weight_map = _diffusers_weight_map(checkpoint)
    by_file: dict[str, list[str]] = {}
    for key, relative_path in weight_map.items():
        by_file.setdefault(relative_path, []).append(key)

    total = 0
    selected = 0
    selected_groups = {key: 0 for key in SELECTORS}
    for relative_path, keys in sorted(by_file.items()):
        with safe_open(str(checkpoint / relative_path), framework="pt", device="cpu") as shard:
            for source_key in keys:
                net_key = _diffusers_to_net_key(source_key, relative_path)
                if net_key is None:
                    continue
                count = 1
                for size in shard.get_slice(source_key).get_shape():
                    count *= size
                total += count
                matches = [selector for selector in SELECTORS if selector in net_key]
                if matches:
                    selected += count
                    for selector in matches:
                        selected_groups[selector] += count
    return total, selected, selected_groups


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    script_path = Path(__file__).resolve()
    dataset_path = args.dataset.resolve()
    checkpoint = args.checkpoint.resolve()

    dataset = get_action_libero_sft_dataset(
        root=str(dataset_path),
        fps=20,
        chunk_length=16,
        image_size=256,
        mode="wam",
        camera_mode="concat_view",
        action_space="frame_wise_relative",
        rotation_space="6d",
        pose_coordinate_frame="native",
        action_normalization="quantile_rot",
        split="full",
        resolution=None,
        max_action_dim=64,
        tokenizer_config=None,
        cfg_dropout_rate=0.0,
        append_viewpoint_info=False,
        append_duration_fps_timestamps=False,
        append_resolution_info=False,
        append_idle_frames=False,
        format_prompt_as_json=False,
    )
    sample = dataset[0]
    inner = dataset._dataset
    raw_7d = torch.from_numpy(inner._row_action[:16].copy()).float()
    converted_10d = inner._build_frame_wise_action(inner._row_action[:16])
    normalized_10d = normalize_action(converted_10d, "quantile", inner._load_norm_stats())

    transformer_config = json.loads((checkpoint / "transformer" / "config.json").read_text(encoding="utf-8"))
    hidden_size = int(transformer_config["hidden_size"])
    max_action_dim = int(transformer_config["action_dim"])
    num_domains = int(transformer_config["num_embodiment_domains"])
    libero_domain_id = get_domain_id("libero")
    droid_domain_id = get_domain_id("droid_lerobot")

    encoder = DomainAwareLinear(max_action_dim, hidden_size, num_domains)
    decoder = DomainAwareLinear(hidden_size, max_action_dim, num_domains)
    domain_ids = torch.full((sample["action"].shape[0],), libero_domain_id, dtype=torch.long)
    with torch.no_grad():
        encoded = encoder(sample["action"], domain_ids)
        decoded = decoder(encoded, domain_ids)

    total_params, selected_params, selected_groups = checkpoint_parameter_counts(checkpoint)
    failures: list[str] = []
    if list(sample["action"].shape) != [16, 64] or int(sample["raw_action_dim"]) != 10:
        failures.append("FAIL_ACTION_SHAPE")
    if int(sample["domain_id"]) != libero_domain_id or libero_domain_id == droid_domain_id:
        failures.append("FAIL_DOMAIN")
    if not torch.isfinite(sample["action"]).all() or not torch.isfinite(decoded).all():
        failures.append("FAIL_NONFINITE")
    if not torch.allclose(sample["action_raw"], normalized_10d):
        failures.append("FAIL_NORMALIZATION_TRACE")
    status = "FAIL" if failures else "PASS"

    result = {
        "schema_version": "1.0",
        "gate": "G0-R03",
        "status": status,
        "provenance": {
            "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "repo_commit": git_commit(root),
            "cosmos_commit": git_commit(root / "cosmos-framework"),
            "script_path": str(script_path.relative_to(root)),
            "script_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
            "command": [sys.executable, *sys.argv],
            "run_config": {"dataset": str(dataset_path), "checkpoint": str(checkpoint)},
        },
        "runtime_contract": {
            "dataset_length": len(dataset),
            "raw_parquet_action_shape": list(raw_7d.shape),
            "converted_action_shape": list(converted_10d.shape),
            "normalized_action_shape": list(normalized_10d.shape),
            "model_action_shape": list(sample["action"].shape),
            "video_shape": list(sample["video"].shape),
            "video_dtype": str(sample["video"].dtype),
            "raw_action_dim": int(sample["raw_action_dim"]),
            "domain_name": "libero",
            "domain_id": int(sample["domain_id"]),
            "droid_domain_id": droid_domain_id,
            "conditioning_fps": int(sample["conditioning_fps"]),
            "viewpoint": sample["viewpoint"],
            "mode": sample["mode"],
            "sequence_plan_type": type(sample["sequence_plan"]).__name__,
            "finite": bool(torch.isfinite(sample["action"]).all()),
            "normalization_trace": "parquet 7D -> rot6d 10D -> quantile_rot 10D -> zero-pad 64D",
            "action_raw_semantics": "当前字段实际保存已 quantile_rot 归一化、未 padding 的 10D；并非 parquet 原始 7D",
        },
        "projection_smoke": {
            "input_shape": list(sample["action"].shape),
            "encoded_shape": list(encoded.shape),
            "decoded_shape": list(decoded.shape),
            "hidden_size": hidden_size,
            "max_action_dim": max_action_dim,
            "num_embodiment_domains": num_domains,
            "finite": bool(torch.isfinite(decoded).all()),
        },
        "trainable_scope": {
            "selectors": list(SELECTORS),
            "effective_transformer_parameter_count": total_params,
            "selected_parameter_count": selected_params,
            "selected_fraction": selected_params / total_params,
            "selected_groups": selected_groups,
            "evidence": "action_policy_libero_nano.py:83-97; optimizer uses substring selection",
        },
        "warm_start_decision": {
            "inherit": ["shared Generator/moe_gen", "time_embedder", "vae2llm", "llm2vae", "action_modality_embed"],
            "domain_projection": "保留全部 DROID 权重，但 LIBERO 使用独立 domain_id=5；仅重初始化并更新 action2llm/llm2action 的 domain 5 行",
            "optimizer_constraint": "R04 必须验证行级更新保护；仅靠 domain_id 的零梯度不足以阻止 AdamW weight decay 改写其他 domain 行",
            "do_not_reuse": "DROID domain_id=8、15Hz、chunk32、joint/gripper contract",
        },
        "simulation_contract": {
            "image_transform": "closed_loop_eval.py:382-400：可选 rotate_180 后再 flipud",
            "gripper_mapping": "closed_loop_eval.py:507-533：zero_one/pm_one/pm_one_flip 显式映射",
            "framewise_to_env": "closed_loop_eval.py:580-602：rot6d 解码为 rotvec，输出 7D simulator delta",
        },
        "failures": failures,
        "limitations": [
            "DomainAwareLinear smoke 使用真实 Edge 维度但随机权重；checkpoint 数值 forward 属 G0-R04",
            "action_raw 字段命名与 LIBERO 当前实际语义不一致；训练输入未重复归一化，R04 前需决定是否修正文档或数据接口",
            "官方 substring selector 选择整个 action embedding；domain 5 之外的行需在 R04 验证 optimizer step 前后不变",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "output": str(args.output)}, ensure_ascii=False))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
