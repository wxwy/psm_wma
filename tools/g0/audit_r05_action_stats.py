#!/usr/bin/env python3
"""Audit bundled LIBERO action statistics against the local dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch

from cosmos_framework.data.generator.action.libero_pose_utils import libero_rotation_format
from cosmos_framework.data.generator.action.pose_utils import convert_rotation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tail-rate", type=float, default=0.10)
    return parser.parse_args()


def git_commit(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def load_local_actions(dataset: Path) -> tuple[np.ndarray, list[str]]:
    paths = sorted((dataset / "data").glob("chunk-*/file-*.parquet"))
    if not paths:
        paths = sorted((dataset / "data").glob("chunk-*/episode_*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No action parquet files found under {dataset / 'data'}")

    parts = []
    for path in paths:
        action = pq.read_table(path, columns=["action"])["action"]
        parts.append(np.asarray(action.to_pylist(), dtype=np.float32))
    raw = torch.from_numpy(np.concatenate(parts, axis=0))
    if raw.ndim != 2 or raw.shape[1] != 7:
        raise ValueError(f"Expected local raw action [N,7], got {tuple(raw.shape)}")

    rotation_matrix = convert_rotation(raw[:, 3:6], input_format="axisangle", output_format="matrix")
    rotation = convert_rotation(rotation_matrix, input_format="matrix", output_format=libero_rotation_format("6d"))
    converted = torch.cat([raw[:, :3], rotation, raw[:, 6:7]], dim=-1)
    return converted.numpy(), [str(path) for path in paths]


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    dataset = args.dataset.resolve()
    stats_path = args.stats.resolve()
    output = args.output.resolve()
    script_path = Path(__file__).resolve()

    local, parquet_paths = load_local_actions(dataset)
    stats_document = json.loads(stats_path.read_text(encoding="utf-8"))
    bundled = stats_document["global_raw"]
    bundled_q01 = np.asarray(bundled["q01"], dtype=np.float64)
    bundled_q99 = np.asarray(bundled["q99"], dtype=np.float64)
    local_q01 = np.quantile(local, 0.01, axis=0)
    local_q99 = np.quantile(local, 0.99, axis=0)

    if local.shape[1] != bundled_q01.size or bundled_q01.shape != bundled_q99.shape:
        raise ValueError(
            f"Action/stats dimension mismatch: local={local.shape[1]}, "
            f"q01={bundled_q01.shape}, q99={bundled_q99.shape}"
        )

    span = bundled_q99 - bundled_q01
    finite = bool(np.isfinite(local).all() and np.isfinite(span).all())
    positive_span = bool(np.all(span > 0.0))
    normalized = 2.0 * (local - bundled_q01) / np.maximum(span, 1e-8) - 1.0
    below_rate = np.mean(local < bundled_q01, axis=0)
    above_rate = np.mean(local > bundled_q99, axis=0)
    outside_rate = np.mean(np.abs(normalized) > 1.0, axis=0)
    intervals_overlap = (local_q99 >= bundled_q01) & (local_q01 <= bundled_q99)

    failures = []
    if not finite:
        failures.append("FAIL_NONFINITE")
    if not positive_span:
        failures.append("FAIL_NONPOSITIVE_STATS_SPAN")
    if not bool(np.all(intervals_overlap)):
        failures.append("FAIL_DISJOINT_QUANTILE_INTERVAL")
    if float(np.max(outside_rate)) > args.max_tail_rate:
        failures.append("FAIL_EXCESSIVE_NORMALIZED_TAIL")

    result = {
        "schema_version": "1.0",
        "gate": "G0-R05-STATS",
        "status": "FAIL" if failures else "PASS",
        "failures": failures,
        "provenance": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "repo_commit": git_commit(root),
            "cosmos_commit": git_commit(root / "cosmos-framework"),
            "script_path": str(script_path.relative_to(root)),
            "script_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
            "command": [sys.executable, *sys.argv],
            "dataset": str(dataset),
            "stats_path": str(stats_path),
            "stats_sha256": hashlib.sha256(stats_path.read_bytes()).hexdigest(),
        },
        "input": {
            "num_frames": int(local.shape[0]),
            "action_dim": int(local.shape[1]),
            "parquet_file_count": len(parquet_paths),
            "conversion": "parquet 7D axis-angle -> Cosmos rot6d 10D",
            "stats_block": "global_raw",
        },
        "thresholds": {"max_tail_rate": args.max_tail_rate, "intervals_must_overlap": True},
        "distribution": {
            "local_q01": local_q01.tolist(),
            "local_q99": local_q99.tolist(),
            "bundled_q01": bundled_q01.tolist(),
            "bundled_q99": bundled_q99.tolist(),
            "q01_abs_delta": np.abs(local_q01 - bundled_q01).tolist(),
            "q99_abs_delta": np.abs(local_q99 - bundled_q99).tolist(),
            "below_bundled_q01_rate": below_rate.tolist(),
            "above_bundled_q99_rate": above_rate.tolist(),
            "outside_normalized_unit_rate": outside_rate.tolist(),
            "max_outside_normalized_unit_rate": float(np.max(outside_rate)),
            "intervals_overlap": intervals_overlap.tolist(),
            "finite": finite,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
