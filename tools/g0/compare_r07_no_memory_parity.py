#!/usr/bin/env python3
"""Compare old/new R07 Local-disabled parity capture artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


INPUT_SUMMARY_KEYS = (
    "x0_vision",
    "xt_vision",
    "sigma_vision_schedule",
    "sigma_vision_effective",
    "x0_action",
    "xt_action",
    "sigma_action_effective",
    "text_ids",
)
STRUCTURE_SUMMARY_KEYS = (
    "text_indexes",
    "vision_indexes",
    "action_indexes",
    "position_ids",
)
FUNCTIONAL_SUMMARY_KEYS = (
    "preds_vision",
    "preds_action",
)
STRUCTURE_KEYS = ("split_lens", "attn_modes")
LOSS_KEYS = ("loss", "flow_matching_loss_vision", "flow_matching_loss_action")


def load_document(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--loss-tolerance", type=float, default=1e-4)
    args = parser.parse_args()

    old = load_document(args.old)
    new = load_document(args.new)
    exact: dict[str, bool] = {}
    for key in INPUT_SUMMARY_KEYS + STRUCTURE_SUMMARY_KEYS + FUNCTIONAL_SUMMARY_KEYS + STRUCTURE_KEYS:
        exact[key] = old.get(key) == new.get(key)
    loss_diffs = {key: abs(float(old[key]) - float(new[key])) for key in LOSS_KEYS}
    losses_pass = all(value <= args.loss_tolerance for value in loss_diffs.values())
    status = "PASS" if all(exact.values()) and losses_pass else "FAIL"
    layers = {
        "input": {key: exact[key] for key in INPUT_SUMMARY_KEYS},
        "structure": {
            key: exact[key] for key in STRUCTURE_SUMMARY_KEYS + STRUCTURE_KEYS
        },
        "functional": {
            "summaries": {key: exact[key] for key in FUNCTIONAL_SUMMARY_KEYS},
            "losses_pass": losses_pass,
        },
    }
    result = {
        "schema_version": "r07_no_memory_parity_comparison_v1",
        "status": status,
        "old_path": str(args.old),
        "new_path": str(args.new),
        "layers": layers,
        "exact_fields": exact,
        "loss_diffs": loss_diffs,
        "loss_tolerance": args.loss_tolerance,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"R07 no-memory parity: {status}")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
