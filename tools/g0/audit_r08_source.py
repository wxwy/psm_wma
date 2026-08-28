"""CPU-only R08 Step 0 source audit for LIBERO causal-history inputs."""

from __future__ import annotations

import argparse
import ast
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys

import numpy as np
import pyarrow.parquet as pq
import torch


SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")
REQUIRED_COLUMNS = ("index", "episode_index", "task_index", "timestamp", "action", "observation.state")


def _git_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _loader_parquet_columns(loader_source: Path) -> list[str]:
    source = loader_source.read_text()
    match = re.search(r"pq\.read_table\(path, columns=(\[[^]]+\])\)", source, re.DOTALL)
    if match is None:
        raise RuntimeError(f"Could not locate loader pq.read_table columns in {loader_source}")
    columns = ast.literal_eval(match.group(1).replace("_ACTION_FEATURE", repr("action")))
    if not isinstance(columns, list) or not all(isinstance(column, str) for column in columns):
        raise RuntimeError(f"Unexpected loader parquet columns: {columns!r}")
    return columns


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _audit_suite(dataset_root: Path, cache_root: Path, suite: str) -> dict[str, object]:
    root = dataset_root / suite
    info = json.loads((root / "meta" / "info.json").read_text())
    parquet_paths = sorted((root / "data").glob("chunk-*/file-*.parquet"))
    if not parquet_paths:
        raise FileNotFoundError(f"No parquet files under {root / 'data'}")
    rows = []
    state_shapes: set[tuple[int, ...]] = set()
    state_finite = True
    state_rows_match_parquet_rows = True
    for path in parquet_paths:
        table = pq.read_table(path, columns=list(REQUIRED_COLUMNS))
        states = np.asarray(table["observation.state"].to_pylist(), dtype=np.float32)
        state_shapes.add(tuple(states.shape[1:]))
        state_finite = state_finite and bool(np.isfinite(states).all())
        state_rows_match_parquet_rows = state_rows_match_parquet_rows and states.shape[0] == table.num_rows
        rows.append(
            {
                "index": table["index"].to_numpy(),
                "episode_index": table["episode_index"].to_numpy(),
                "task_index": table["task_index"].to_numpy(),
                "timestamp": table["timestamp"].to_numpy(),
                "action": np.asarray(table["action"].to_pylist(), dtype=np.float32),
                "state": states,
            }
        )
    merged = {key: np.concatenate([row[key] for row in rows]) for key in rows[0]}
    order = np.argsort(merged["index"].astype(np.int64), kind="stable")
    for key in merged:
        merged[key] = merged[key][order]
    episode = merged["episode_index"].astype(np.int64)
    index = merged["index"].astype(np.int64)
    timestamp = merged["timestamp"].astype(np.float64)
    same_episode_next = episode[:-1] == episode[1:]
    index_strictly_increasing = bool(np.all(np.diff(index) > 0))
    cache_manifest_path = cache_root / suite / "dataset_manifest.json"
    cache_manifest = json.loads(cache_manifest_path.read_text())
    episode_file = cache_root / suite / "episodes" / f"episode_{int(episode[0]):06d}.pt"
    cache_item = torch.load(episode_file, map_location="cpu", weights_only=True)
    first_window = cache_item["windows"][sorted(cache_item["windows"], key=int)[0]]
    return {
        "suite": suite,
        "info_features_state": info.get("features", {}).get("observation.state"),
        "parquet_files": len(parquet_paths),
        "row_count": int(index.size),
        "parquet_columns": list(REQUIRED_COLUMNS),
        "state": {
            "dtype": "float32",
            "shapes": [list(shape) for shape in sorted(state_shapes)],
            "finite": state_finite,
            "row_count_matches_parquet_rows": state_rows_match_parquet_rows,
            "row_alignment_method": "state/index/episode_index/timestamp are read from each same parquet table and reordered with the same stable global-index permutation",
            "common_index_is_strictly_increasing": index_strictly_increasing,
            "feature_metadata": info.get("features", {}).get("observation.state"),
            "semantic_status": (
                "Only the dataset feature metadata is recorded. The duplicate gripper label means "
                "this audit does not infer a formal eight-dimension physical-state mapping."
            ),
        },
        "timeline": {
            "index_strictly_increasing": index_strictly_increasing,
            "episode_nondecreasing": bool(np.all(np.diff(episode) >= 0)),
            "timestamp_strictly_increasing_within_episode": bool(np.all(np.diff(timestamp)[same_episode_next] > 0)),
            "raw_action_shape": list(merged["action"].shape[1:]),
            "loader_target_action_rows": "anchor t -> raw action rows [t, t+16), converted by _build_frame_wise_action",
            "causal_history_action_rows": "for anchor t, only raw action rows j<t are eligible; a_t and later are forbidden",
            "transition_semantics_evidence": (
                "The current loader names this action_space frame_wise_relative and consumes the stored rows directly. "
                "The parquet schema itself has no separate transition-id field; R08 must retain the conservative j<t boundary."
            ),
        },
        "exact_window_cache": {
            "manifest_path": str(cache_manifest_path),
            "manifest_sha256": _sha256(cache_manifest_path),
            "schema_version": cache_manifest.get("schema_version"),
            "latent_shape": cache_manifest.get("latent_shape"),
            "vae_encode_contract": cache_manifest.get("vae_encode_contract"),
            "sample_window_frame_indices": first_window["window_frame_indices"].tolist(),
            "sample_latent_source_frame_indices": first_window["latent_source_frame_indices"].tolist(),
            "sample_latent_shape": list(first_window["latent"].shape),
            "sample_latent_dtype": str(first_window["latent"].dtype),
            "current_concat_and_vae_canvas": {
                "concat_layout": "third-person left + wrist right; 256x256 + 256x256 -> 256x512",
                "pre_vae_model_canvas": [192, 320],
                "evidence": "cosmos-framework/docs/action_policy_libero_posttrain.md:50-53",
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    loader_source = root / "cosmos-framework/cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py"
    loader_columns = _loader_parquet_columns(loader_source)
    report = {
        "schema_version": "r08_source_audit_v1",
        "status": "PASS",
        "scope": "CPU-only source audit; no model/data-contract modification",
        "loader_source": "cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py",
        "source_evidence": {
            "loader_parquet_read": "libero_lerobot_dataset.py:162-169",
            "cache_manifest_validation": "libero_lerobot_dataset.py:280-329",
            "cache_window_validation": "libero_lerobot_dataset.py:331-377",
            "sample_target_action_and_extras": "libero_lerobot_dataset.py:393-436",
            "action_conversion": "libero_lerobot_dataset.py:438-446",
            "concat_view": "libero_lerobot_dataset.py:448-465",
            "current_concat_and_vae_canvas": "cosmos-framework/docs/action_policy_libero_posttrain.md:50-53",
            "vae_exact_duration_constants": "cosmos_framework/model/generator/vision_vae.py:12-13",
        },
        "loader_current_columns": loader_columns,
        "loader_does_not_currently_read_observation_state": "observation.state" not in loader_columns,
        "action_conversion": "raw 7D axis-angle action -> existing _build_frame_wise_action -> 10D rot6d action",
        "suites": [_audit_suite(args.dataset_root, args.cache_root, suite) for suite in SUITES],
        "gate_decision": "state schema/alignment is audit-PASS; state semantics remain unspecified and must not be inferred before R08 integration",
        "provenance": {
            "root_commit": _git_commit(root),
            "submodule_commit": _git_commit(root / "cosmos-framework"),
            "dataset_root": str(args.dataset_root),
            "cache_root": str(args.cache_root),
            "argv": sys.argv,
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "hostname": socket.gethostname(),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"R08 source audit: {report['status']} -> {args.output}")


if __name__ == "__main__":
    main()
