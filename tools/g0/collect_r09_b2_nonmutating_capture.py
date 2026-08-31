#!/usr/bin/env python3
"""Generate CPU-only concrete P2 isolation mutation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from cosmos_framework.callbacks.r09_b2_capture import require_unchanged, take_isolation_snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    values = {"parameters": {"weight": torch.tensor([1.0])}, "buffers": {"buffer": torch.tensor([1.0])}, "optimizer": {"state": torch.tensor([1.0])}, "scheduler": {"step": 1}, "batch_metadata": {"ordinal": 0, "epoch": 0, "microbatch": 0}, "recurrent_state": {"hidden": torch.tensor([1.0])}, "ttt_state": {key: torch.tensor([1.0]) for key in ("fast_weight", "lr", "segment", "reset", "detach")}}
    checks = {}
    for name, value in values.items():
        before = take_isolation_snapshot(**values)
        key = next(iter(value))
        value[key] = value[key] + 1
        after = take_isolation_snapshot(**values)
        try:
            require_unchanged(before, after)
        except RuntimeError:
            checks[name] = {"before": getattr(before, name), "after": getattr(after, name), "rejected": True}
        else:
            checks[name] = {"before": getattr(before, name), "after": getattr(after, name), "rejected": False}
        value[key] = value[key] - 1
    result = {"schema_version": "r09_b2_nonmutating_capture_cpu_v2", "status": "PASS" if all(item["rejected"] and item["before"] != item["after"] for item in checks.values()) else "FAIL", "mutation_checks": checks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "count": len(checks)}))


if __name__ == "__main__":
    main()
