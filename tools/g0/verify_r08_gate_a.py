#!/usr/bin/env python3
"""汇总 R08 Gate A 单卡受控训练的机器可读证据。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


R08_PREFIX = "local_history_runtime."


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--reload-log", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    probe = json.loads(args.probe.read_text(encoding="utf-8"))
    log = args.log.read_text(encoding="utf-8")
    reload_log = args.reload_log.read_text(encoding="utf-8")
    root = Path(__file__).resolve().parents[2]
    submodule = root / "cosmos-framework"
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
    required_checkpoint_files = {
        f"{component}/.metadata" for component in ("model", "optim", "scheduler", "trainer")
    }
    checkpoint_complete = "Saved checkpoint to" in log and required_checkpoint_files.issubset(dict(checkpoint_files))
    reload_keys_match = re.search(
        r"Resuming ckpt .* with keys: \['model', 'optim', 'scheduler', 'trainer'\]", reload_log
    ) is not None
    reload_iteration_match = re.search(r"Loaded checkpoint .* in iteration 2", reload_log) is not None
    reload_completed = "Done with training." in reload_log
    reload_pass = reload_keys_match and reload_iteration_match and reload_completed
    root_revision = git(root, "rev-parse", "HEAD")
    submodule_revision = git(submodule, "rev-parse", "HEAD")
    gitlink_revision = git(root, "rev-parse", "HEAD:cosmos-framework")
    root_clean = not git(root, "status", "--porcelain", "--untracked-files=no")
    submodule_clean = not git(submodule, "status", "--porcelain", "--untracked-files=no")
    provenance_valid = root_revision == gitlink_revision == submodule_revision and root_clean and submodule_clean
    hard_pass = (
        "Done with training." in log
        and loss_finite
        and all_optimizer_membership
        and r08_grad_finite
        and r08_grad_max_abs > 0
        and r08_update_finite
        and r08_update_max_abs > 0
        and checkpoint_complete
        and reload_pass
        and provenance_valid
    )
    result = {
        "schema_version": "r08_gate_a_single_gpu_v2",
        "status": "PASS" if hard_pass else "FAIL",
        "training_completed": "Done with training." in log,
        "checkpoint_save": {
            "complete": checkpoint_complete,
            "status": "COMPLETE" if checkpoint_complete else "INCOMPLETE_DISK_SPACE",
            "path": str(args.checkpoint),
            "files": checkpoint_files,
        },
        "checkpoint_reload": {
            "pass": reload_pass,
            "source_checkpoint": str(args.checkpoint),
            "completed_steps": 2,
            "model_restored": reload_keys_match,
            "optimizer_restored": reload_keys_match,
            "scheduler_trainer_state_restored": reload_keys_match,
            "fresh_process_completed": reload_completed,
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
            "root_revision": root_revision,
            "submodule_revision": submodule_revision,
            "gitlink_revision": gitlink_revision,
            "root_clean_tracked": root_clean,
            "submodule_clean_tracked": submodule_clean,
            "valid": provenance_valid,
            "verifier": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
            "probe": {"path": str(args.probe), "sha256": sha256(args.probe)},
            "log": {"path": str(args.log), "sha256": sha256(args.log)},
            "reload_log": {"path": str(args.reload_log), "sha256": sha256(args.reload_log)},
            "config": {"path": str(args.config), "sha256": sha256(args.config)},
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"R08 Gate A: {result['status']}")


if __name__ == "__main__":
    main()
