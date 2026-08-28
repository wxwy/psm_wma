#!/usr/bin/env python3
"""Verify the R08 Step 2 causal Local-history dataset contract on CPU."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import torch

from cosmos_framework.data.generator.action.action_normalization import normalize_action
from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
from cosmos_framework.data.generator.action.utils.transforms import ActionTransformPipeline


def _summary(value: torch.Tensor) -> dict[str, object]:
    value = value.detach().cpu().contiguous()
    return {
        "shape": list(value.shape),
        "dtype": str(value.dtype),
        "sha256": hashlib.sha256(value.numpy().tobytes()).hexdigest(),
    }


def _git_head(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--latent-cache-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    dataset = LIBEROLeRobotDataset(
        root=str(args.dataset_root),
        latent_cache_root=str(args.latent_cache_root),
        split="full",
        local_history_horizon=16,
    )
    start = dataset._build_item(0)
    partial = dataset._build_item(3)
    full = dataset._build_item(16)
    disabled = LIBEROLeRobotDataset(
        root=str(args.dataset_root), latent_cache_root=str(args.latent_cache_root), split="full"
    )._build_item(0)
    mask = full["history_mask"]
    source_rows = full["history_global_row_indices"][mask].numpy()
    anchor_row = int(source_rows[-1]) + 1
    current_target_rows = set(range(anchor_row, anchor_row + dataset._chunk_length))
    expected_raw = dataset._build_frame_wise_action(dataset._row_action[source_rows])
    expected_normalized = normalize_action(expected_raw, dataset.action_normalization, dataset._load_norm_stats())
    expected_visual = torch.stack(
        [
            torch.nn.functional.adaptive_avg_pool2d(
                dataset._load_cached_latent(int(dataset._ep_vals[0]), frame)[0].unsqueeze(0), output_size=(1, 2)
            ).flatten()
            for frame in full["history_frame_indices"].tolist()
        ]
    )
    transformed = ActionTransformPipeline(tokenizer_config=None, max_action_dim=64)(full.copy(), resolution="256")
    partial_padding = ~partial["history_mask"]
    padded_evidence_keys = (
        "history_visual_summary",
        "history_state_raw",
        "local_history_action_raw",
        "local_history_action",
        "history_age_steps",
        "history_dt_s",
    )

    checks = {
        "h0_all_padding": not bool(start["history_mask"].any()),
        "horizon_zero_has_no_history_fields": not any(
            key.startswith("local_history_") or key.startswith("history_") for key in disabled
        ),
        "h3_left_padded": partial["history_mask"].tolist() == [False] * 13 + [True] * 3,
        "h16_all_valid": bool(mask.all()),
        "strictly_prior_rows": int(full["history_global_row_indices"][-1]) + 1 == int(dataset._ep_starts[0]) + 16,
        "history_target_rows_disjoint": int(source_rows.max()) == anchor_row - 1
        and set(source_rows).isdisjoint(current_target_rows),
        "history_rows_same_episode": bool((dataset._row_episode[source_rows] == dataset._row_episode[anchor_row]).all()),
        "history_dt_exact": bool(
            torch.allclose(
                full["history_dt_s"].squeeze(-1),
                torch.from_numpy(dataset._row_timestamp[anchor_row] - dataset._row_timestamp[source_rows]).float(),
            )
        ),
        "raw_action_parity": bool(torch.allclose(full["local_history_action_raw"], expected_raw)),
        "normalized_action_parity": bool(torch.allclose(full["local_history_action"], expected_normalized)),
        "state_row_parity": bool(
            torch.allclose(full["history_state_raw"], torch.from_numpy(dataset._row_state[source_rows]).float())
        ),
        "z0_visual_summary_parity": bool(torch.allclose(full["history_visual_summary"], expected_visual)),
        "padding_inert": all(torch.count_nonzero(partial[key][partial_padding]) == 0 for key in padded_evidence_keys)
        and torch.equal(partial["history_frame_indices"][partial_padding], torch.full((13,), -1, dtype=torch.long))
        and torch.equal(
            partial["history_global_row_indices"][partial_padding], torch.full((13,), -1, dtype=torch.long)
        ),
        "native_action_unchanged": transformed["action_raw"].shape[0] == full["action"].shape[0]
        and bool(torch.allclose(transformed["action_raw"], full["action"])),
        "native_history_action_absent": "history_action" not in transformed,
        "local_evidence_survives_transform": "local_history_action" in transformed,
        "sequence_plan_has_no_action_prefix": transformed["sequence_plan"].condition_frame_indexes_action == [],
    }
    result = {
        "schema_version": 1,
        "gate": "G0-R08-STEP2-CAUSAL-HISTORY-CONTRACT",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "dataset_root": str(args.dataset_root),
        "latent_cache_root": str(args.latent_cache_root),
        "root_commit": _git_head(Path(__file__).resolve().parents[2]),
        "submodule_commit": _git_head(Path(__file__).resolve().parents[2] / "cosmos-framework"),
        "checks": checks,
        "h16": {
            "history_frame_indices": _summary(full["history_frame_indices"]),
            "history_mask": _summary(full["history_mask"]),
            "visual_summary": _summary(full["history_visual_summary"]),
            "state_raw": _summary(full["history_state_raw"]),
            "local_history_action": _summary(full["local_history_action"]),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if result["status"] != "PASS":
        raise SystemExit("R08 causal-history contract failed")


if __name__ == "__main__":
    main()
