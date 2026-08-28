#!/usr/bin/env python3
"""汇总 R08 Gate A 单卡受控训练的机器可读证据。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


R08_PREFIX = "local_history_runtime."


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--root-revision", required=True)
    parser.add_argument("--submodule-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    probe = json.loads(args.probe.read_text(encoding="utf-8"))
    log = args.log.read_text(encoding="utf-8")
    steps = probe.get("steps", [])
    target = next((step for step in steps if step.get("iteration") == 2), None)
    if target is None:
        raise ValueError("缺少第 2 个 optimizer step 的 probe 记录。")

    membership = target["optimizer_membership"]
    gradients = target["gradients"]
    updates = target["updates"]
    targets = [name for name in membership if name.startswith(R08_PREFIX)]
    all_optimizer_membership = bool(targets) and all(membership[name] for name in membership)
    r08_grad_finite = all(gradients[name]["present"] and gradients[name]["finite"] for name in targets)
    r08_grad_max_abs = max(gradients[name]["max_abs"] for name in targets)
    r08_update_finite = all(updates[name]["present"] and updates[name]["finite"] for name in targets)
    r08_update_max_abs = max(updates[name]["max_abs"] for name in targets)
    losses = [step["loss"] for step in steps]
    loss_finite = all(isinstance(value, float) and value == value and abs(value) != float("inf") for value in losses)
    peak_matches = re.findall(r"peak_gpu_mem_gb\s+([0-9.]+)", log)
    reserved_matches = re.findall(r"peak_gpu_mem_reserved_gb\s+([0-9.]+)", log)
    runtime_matches = re.findall(r"perf/step_wall_s=([0-9.]+)", log)
    checkpoint_files = sorted(
        {str(path.relative_to(args.checkpoint)): path.stat().st_size for path in args.checkpoint.rglob("*") if path.is_file()}.items()
    )
    checkpoint_complete = "Saved checkpoint to" in log
    result = {
        "schema_version": "r08_gate_a_single_gpu_v1",
        "status": "PASS" if all_optimizer_membership and loss_finite and r08_grad_finite and r08_grad_max_abs > 0 and r08_update_finite and r08_update_max_abs > 0 else "FAIL",
        "training_completed": "Done with training." in log,
        "checkpoint_save": {
            "complete": checkpoint_complete,
            "status": "COMPLETE" if checkpoint_complete else "INCOMPLETE_DISK_SPACE",
            "path": str(args.checkpoint),
            "files": checkpoint_files,
        },
        "steps": [{"iteration": step["iteration"], "loss": step["loss"]} for step in steps],
        "all_optimizer_membership": all_optimizer_membership,
        "r08_grad_finite": r08_grad_finite,
        "r08_grad_max_abs": r08_grad_max_abs,
        "r08_update_finite": r08_update_finite,
        "r08_update_max_abs": r08_update_max_abs,
        "loss_finite": loss_finite,
        "peak_gpu_mem_gb": [float(value) for value in peak_matches],
        "peak_gpu_mem_reserved_gb": [float(value) for value in reserved_matches],
        "step_wall_seconds": [float(value) for value in runtime_matches],
        "provenance": {
            "root_revision": args.root_revision,
            "submodule_revision": args.submodule_revision,
            "probe": {"path": str(args.probe), "sha256": sha256(args.probe)},
            "log": {"path": str(args.log), "sha256": sha256(args.log)},
            "config": {"path": str(args.config), "sha256": sha256(args.config)},
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"R08 Gate A: {result['status']}")


if __name__ == "__main__":
    main()
