#!/usr/bin/env python3
"""Prove the first bounded B1 packed batch contains effective Local history."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import torch


def _per_sample_masks(value: Any) -> list[torch.Tensor]:
    if isinstance(value, torch.Tensor):
        return [item.reshape(-1).bool() for item in value]
    if isinstance(value, list):
        masks: list[torch.Tensor] = []
        for item in value:
            if isinstance(item, list):
                masks.extend(_per_sample_masks(item))
            elif isinstance(item, torch.Tensor):
                masks.extend(_per_sample_masks(item))
            else:
                raise TypeError(f"history_mask contains unsupported {type(item).__name__}.")
        return masks
    raise TypeError(f"history_mask must be tensor/list, got {type(value).__name__}.")


def _scalar_values(value: Any, count: int) -> list[int | None]:
    if isinstance(value, torch.Tensor):
        flat = value.detach().cpu().reshape(-1).tolist()
        return [int(item) for item in flat[:count]]
    if isinstance(value, list):
        result: list[int] = []
        for item in value:
            result.extend(item.detach().cpu().reshape(-1).tolist() if isinstance(item, torch.Tensor) else [])
        return [int(item) for item in result[:count]]
    return [None] * count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--overrides", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    framework = root / "cosmos-framework"
    sys.path.insert(0, str(framework))
    os.chdir(framework)

    from cosmos_framework.configs.toml_config.sft_config import load_experiment_from_toml
    from cosmos_framework.utils.lazy_config import instantiate

    overrides = args.overrides.split()
    config = load_experiment_from_toml(
        "examples/toml/sft_config/action_policy_libero_edge_all.toml", extra_overrides=overrides
    )
    expected_count = 2
    actual_limit = config.dataloader_train.max_samples_per_batch
    if actual_limit != expected_count:
        raise ValueError(f"B1 first-batch evidence requires max_samples_per_batch={expected_count}, got {actual_limit}.")
    batch = next(iter(instantiate(config.dataloader_train)))
    masks = _per_sample_masks(batch["history_mask"])
    if len(masks) != expected_count:
        raise ValueError(f"Expected {expected_count} packed samples, got {len(masks)} history masks.")
    present = [bool(mask.any()) for mask in masks]
    episodes = _scalar_values(batch.get("episode_index"), expected_count)
    starts = _scalar_values(batch.get("start_frame"), expected_count)
    result = {
        "schema_version": "r09_b1_first_batch_history_v1",
        "status": "PASS" if any(present) else "FAIL",
        "profile": {"dataloader_train.max_samples_per_batch": expected_count, "trainer.grad_accum_iter": 1},
        "effective_local_history_sample_count": sum(present),
        "samples": [
            {
                "sample_index": index,
                "history_present": item_present,
                "history_valid_steps": int(mask.sum().item()),
                "episode_index": episodes[index],
                "start_frame": starts[index],
            }
            for index, (mask, item_present) in enumerate(zip(masks, present, strict=True))
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit("First B1 packed batch has no effective Local history.")


if __name__ == "__main__":
    main()
