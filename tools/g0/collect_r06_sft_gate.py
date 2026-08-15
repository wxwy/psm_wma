#!/usr/bin/env python3
"""Collect machine-readable evidence for the R06 task-0 SFT gate."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _json(path: Path) -> Any:
    return json.loads(path.read_text())


def _finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    return not isinstance(value, float) or math.isfinite(value)


def _metrics(path: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    losses = [float(r[key]) for r in rows for key in ("loss", "total_loss") if key in r]
    return {
        "steps": len(rows),
        "loss_first": losses[0] if losses else None,
        "loss_last": losses[-1] if losses else None,
        "all_finite": _finite(rows),
    }


def _episodes(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [episode for task in summary.get("task_results", []) for episode in task.get("episode_results", [])]


def _closed_loop_pass(summary: dict[str, Any]) -> bool:
    episodes = _episodes(summary)
    return bool(summary.get("overall_success_rate", 0) > 0 and episodes and all(
        episode.get("error") is None and int(episode.get("steps", 0)) == 520 for episode in episodes
    ))


def _action_files(path: Path) -> dict[str, bytes]:
    return {str(file.relative_to(path)): file.read_bytes() for file in sorted(path.rglob("*.json"))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--domain-guard", type=Path, required=True)
    parser.add_argument("--eval-summary", type=Path, required=True)
    parser.add_argument("--repeat-summary", type=Path, required=True)
    parser.add_argument("--eval-actions", type=Path, required=True)
    parser.add_argument("--repeat-actions", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/g0/r06/R06_sft_libero_closed_loop.json"))
    args = parser.parse_args()

    metrics = _metrics(args.metrics)
    domain = _json(args.domain_guard)
    evaluation = _json(args.eval_summary)
    repeat = _json(args.repeat_summary)
    checkpoint_parts = {name: (args.checkpoint / name).is_dir() for name in ("model", "optim", "scheduler", "trainer")}
    checkpoint_complete = all(checkpoint_parts.values())
    domain_pass = bool(domain.get("status", domain.get("pass", False)) in (True, "PASS", "pass"))
    eval_pass = _closed_loop_pass(evaluation)
    repeat_pass = _closed_loop_pass(repeat)
    action_files = _action_files(args.eval_actions)
    repeat_action_files = _action_files(args.repeat_actions)
    actions_equal = bool(action_files) and action_files == repeat_action_files
    result = {
        "gate": "G0-R06-SFT",
        "status": "PASS" if all((metrics["all_finite"], metrics["steps"] >= 500, checkpoint_complete, domain_pass, eval_pass, repeat_pass, actions_equal)) else "FAIL",
        "training": metrics,
        "checkpoint": {"path": str(args.checkpoint), "four_parts": checkpoint_parts},
        "domain_row_guard": domain,
        "closed_loop": evaluation,
        "same_seed_repeat": repeat,
        "action_repeat": {"evaluation_files": len(action_files), "repeat_files": len(repeat_action_files), "bitwise_equal": actions_equal},
        "criteria": {
            "training_finite": metrics["all_finite"],
            "500_steps": metrics["steps"] >= 500,
            "checkpoint_four_parts": checkpoint_complete,
            "domain_rows_0_4_6_31_unchanged": domain_pass,
            "closed_loop": eval_pass,
            "same_seed_repeat": repeat_pass and actions_equal,
            "closed_loop_success_rate_gt_zero": eval_pass,
            "closed_loop_episodes_520_no_error": eval_pass,
            "repeat_actions_bitwise_equal": actions_equal,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
