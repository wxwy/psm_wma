#!/usr/bin/env python3
"""Collect G0-R05 tiny-overfit evidence into a machine-readable Gate JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


LOSS_KEYS = ("total_loss", "action_flow_loss", "action_x0_reconstruction_mae", "vision_flow_loss")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--held-out", type=Path, required=True)
    parser.add_argument("--reload-held-out", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--trend-window", type=int, default=10)
    parser.add_argument("--max-train-loss-ratio", type=float, default=0.80)
    parser.add_argument("--max-vision-loss-ratio", type=float, default=1.10)
    parser.add_argument("--reload-rtol", type=float, default=1e-5)
    parser.add_argument("--reload-atol", type=float, default=1e-6)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def median(values: list[float]) -> float:
    return float(statistics.median(values))


def git_commit(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    script_path = Path(__file__).resolve()
    stats = json.loads(args.stats.read_text(encoding="utf-8"))
    metrics = read_jsonl(args.metrics)
    held_out_rows = read_jsonl(args.held_out)
    reload_rows = read_jsonl(args.reload_held_out)
    failures: list[str] = []

    if stats.get("status") != "PASS":
        failures.append("FAIL_ACTION_STATS_SANITY")
    if len(metrics) != args.steps or [row.get("iteration") for row in metrics] != list(range(1, args.steps + 1)):
        failures.append("FAIL_STEP_SEQUENCE")

    finite_fields = (
        "total_loss_finite",
        "action_flow_loss_finite",
        "action_x0_reconstruction_mae_finite",
        "vision_flow_loss_finite",
        "grad_finite",
    )
    if not metrics or not all(all(row.get(field) is True for field in finite_fields) for row in metrics):
        failures.append("FAIL_NONFINITE_TRAIN_METRIC")

    trends: dict[str, dict[str, float]] = {}
    if len(metrics) >= args.trend_window * 2:
        for key in LOSS_KEYS:
            first = median([float(row[key]) for row in metrics[: args.trend_window]])
            last = median([float(row[key]) for row in metrics[-args.trend_window :]])
            ratio = last / max(abs(first), 1e-12)
            trends[key] = {"first_median": first, "last_median": last, "ratio": ratio}
        for key in ("total_loss", "action_flow_loss", "action_x0_reconstruction_mae"):
            if trends[key]["ratio"] > args.max_train_loss_ratio:
                failures.append(f"FAIL_{key.upper()}_TREND")
        if trends["vision_flow_loss"]["ratio"] > args.max_vision_loss_ratio:
            failures.append("FAIL_VISION_LOSS_UNSTABLE")
    else:
        failures.append("FAIL_INSUFFICIENT_TREND_WINDOW")

    held_out = held_out_rows[-1] if held_out_rows else None
    reloaded = reload_rows[-1] if reload_rows else None
    if held_out is None or reloaded is None:
        failures.append("FAIL_MISSING_HELD_OUT")
        reload_comparison = {}
    else:
        held_out_finite_fields = tuple(field for field in finite_fields if field != "grad_finite")
        if not all(held_out.get(field) is True and reloaded.get(field) is True for field in held_out_finite_fields):
            failures.append("FAIL_NONFINITE_HELD_OUT")
        reload_comparison = {}
        for key in LOSS_KEYS:
            lhs = float(held_out[key])
            rhs = float(reloaded[key])
            matches = math.isclose(lhs, rhs, rel_tol=args.reload_rtol, abs_tol=args.reload_atol)
            reload_comparison[key] = {"in_memory": lhs, "reloaded": rhs, "matches": matches}
            if not matches:
                failures.append(f"FAIL_RELOAD_{key.upper()}_MISMATCH")

    checkpoint_parts = {name: (args.checkpoint / name).is_dir() for name in ("model", "optim", "scheduler", "trainer")}
    if not all(checkpoint_parts.values()):
        failures.append("FAIL_CHECKPOINT_INCOMPLETE")

    result = {
        "schema_version": "1.0",
        "gate": "G0-R05",
        "status": "FAIL" if failures else "PASS",
        "failures": failures,
        "provenance": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "repo_commit": git_commit(root),
            "cosmos_commit": git_commit(root / "cosmos-framework"),
            "script_path": str(script_path.relative_to(root)),
            "script_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
            "command": [sys.executable, *sys.argv],
        },
        "run": {
            "steps_expected": args.steps,
            "steps_observed": len(metrics),
            "optimizer_type": metrics[-1].get("optimizer_type") if metrics else None,
            "fused": metrics[-1].get("fused") if metrics else None,
            "all_finite": "FAIL_NONFINITE_TRAIN_METRIC" not in failures,
            "gpu_step_peak_mib_max": max((float(row["gpu_step_peak_mib"]) for row in metrics), default=None),
            "rss_kb_max": max((int(row["rss_kb"]) for row in metrics), default=None),
        },
        "trends": trends,
        "held_out": held_out,
        "reload_held_out": reloaded,
        "reload_comparison": reload_comparison,
        "checkpoint": {"path": str(args.checkpoint), "parts": checkpoint_parts},
        "stats_sanity": {
            "path": str(args.stats),
            "status": stats.get("status"),
            "max_outside_normalized_unit_rate": stats.get("distribution", {}).get(
                "max_outside_normalized_unit_rate"
            ),
        },
        "thresholds": {
            "trend_window": args.trend_window,
            "max_train_loss_ratio": args.max_train_loss_ratio,
            "max_vision_loss_ratio": args.max_vision_loss_ratio,
            "reload_rtol": args.reload_rtol,
            "reload_atol": args.reload_atol,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
