"""Verify synchronized-A2 long-run readiness from immutable implementation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "cosmos-framework"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def target_pair(expected_root: str, expected_child: str) -> dict:
    current_root = git("rev-parse", "HEAD")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", expected_root, current_root],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tree = git("ls-tree", expected_root, "cosmos-framework").split()
    require(len(tree) >= 3 and tree[2] == expected_child, "implementation root does not bind expected child")
    live_child = git("rev-parse", "HEAD", cwd=CHILD)
    require(live_child == expected_child, "live child differs from expected implementation child")
    require(not git("status", "--short", "--untracked-files=no", cwd=CHILD), "child tracked source is dirty")
    return {
        "implementation_root": expected_root,
        "implementation_child": expected_child,
        "verifier_root": current_root,
    }


def delivery_check(path: Path, expected_root: str, expected_child: str) -> dict:
    report = json.loads(path.read_text())
    require(report.get("result") == "PASS", "A2 delivery verifier is not PASS")
    checks = {item["check"]: item for item in report.get("checks", [])}
    require(checks and all(item.get("status") == "PASS" for item in checks.values()), "A2 delivery has non-PASS checks")
    committed = checks["committed_target"]["detail"]
    require(
        committed.get("root") == expected_root and committed.get("child") == expected_child,
        "A2 delivery verifier targets another implementation pair",
    )
    exact = checks["exact_pair_evidence_binding"]["detail"]
    require(exact.get("expected") == [expected_root, expected_child], "delivery exact-pair binding differs")
    budget = checks["twenty_step_budget"]["detail"]
    require(budget.get("steps_recorded", 0) >= 20, "A2 full-catalog budget has fewer than 20 steps")
    require(budget.get("member_layout") == "a2", "budget is not A2 layout")
    require(budget.get("native_forwards_per_update") == 16, "budget native forward count differs")
    require(budget.get("consumers_per_update") == 2048, "budget consumer count differs")
    require(str(budget.get("data_max_episodes_per_suite")) == "100000", "budget is not full-catalog scope")
    peak = float(budget["cuda_peak_allocated_GiB"])
    wall = float(budget["step_wall_mean_s"])
    require(math.isfinite(peak) and peak < 60.0, "A2 memory budget exceeds 60 GiB")
    require(math.isfinite(wall) and wall > 0, "A2 step-wall evidence is invalid")
    return {
        "path": str(path),
        "sha256": sha(path),
        "steps": int(budget["steps_recorded"]),
        "step_wall_mean_s": wall,
        "cuda_peak_allocated_GiB": peak,
        "projected_5000_days_base": wall * 5000.0 / 86400.0,
        "scope": "A2 full-catalog 20-step direct measurement; excludes eval/checkpoint overhead",
    }


def probe_receipt_check(path: Path, expected_root: str, expected_child: str, probe_script: Path) -> dict:
    receipt = json.loads(path.read_text())
    require(receipt.get("implementation_root") == expected_root, "probe receipt implementation root differs")
    require(receipt.get("implementation_child") == expected_child, "probe receipt implementation child differs")
    require(receipt.get("child_at_launch") == expected_child, "probe launched from another child")
    require(not receipt.get("tracked_root_dirty"), "probe launched from dirty tracked root")
    require(not receipt.get("tracked_child_dirty"), "probe launched from dirty tracked child")
    require(receipt.get("target_windows") == 5000, "probe receipt target is not 5000 windows")
    require(receipt.get("b_stream") == 8 and receipt.get("ga") == 16, "probe receipt geometry differs")
    require(receipt.get("ttt_tbptt_steps") == 16, "probe receipt T differs")
    current_hash = sha(probe_script)
    require(current_hash == receipt.get("probe_script_sha256"), "probe script bytes changed after run")
    # Once the tool is committed, the committed blob must match the launched bytes.
    blob = subprocess.check_output(["git", "show", f"HEAD:{probe_script.relative_to(ROOT)}"], cwd=ROOT)
    require(hashlib.sha256(blob).hexdigest() == current_hash, "committed probe blob differs from launched bytes")
    return {
        "path": str(path),
        "sha256": sha(path),
        "root_at_launch": receipt["root_at_launch"],
        "child_at_launch": receipt["child_at_launch"],
        "probe_script_sha256": current_hash,
    }


def probe_check(combined_path: Path, capacity_path: Path, reuse_path: Path, expected_child: str) -> dict:
    combined = json.loads(combined_path.read_text())
    capacity = json.loads(capacity_path.read_text())
    reuse = json.loads(reuse_path.read_text())
    require(combined.get("result") == "PASS", "combined A2 long-run probe is not PASS")
    require(capacity.get("result") == "PASS", "A2 capacity probe is not PASS")
    require(reuse.get("result") == "PASS", "A2 epoch-reuse probe is not PASS")
    require(combined.get("implementation_child") == expected_child, "probe used another child")
    require(combined.get("capacity") == capacity, "capacity artifact differs from combined report")
    require(combined.get("epoch_reuse") == reuse, "reuse artifact differs from combined report")

    require(capacity.get("target_windows") == 5000, "capacity target is not 5000")
    require(capacity.get("windows_completed") == 5000, "capacity did not complete 5000 windows")
    require(capacity.get("driver_window_index") == 5000, "driver window index differs")
    require(capacity.get("b_stream") == 8 and capacity.get("ga") == 16, "capacity geometry differs")
    require(capacity.get("native_forwards_per_update") == 16, "capacity forward count differs")
    require(capacity.get("consumers_per_update") == 2048, "capacity consumer count differs")
    require(capacity.get("consumers_total") == 5000 * 2048, "capacity total consumers differs")
    require(not capacity.get("group_shape_errors"), "capacity has group-shape errors")
    require(not capacity.get("chronology_errors"), "capacity has chronology errors")
    require(capacity.get("error") is None, "capacity raised an error")

    slot_epoch = {int(k): int(v) for k, v in reuse.get("slot_epoch", {}).items()}
    events = {int(k): int(v) for k, v in reuse.get("slot_epoch_events", {}).items()}
    rebinds = {int(k): int(v) for k, v in reuse.get("per_slot_rebinds", {}).items()}
    require(set(slot_epoch) == set(range(8)), "reuse does not cover all stable slots")
    require(all(slot_epoch[s] > 0 for s in range(8)), "a stable slot never crossed a reuse epoch")
    require(all(events[s] == slot_epoch[s] for s in range(8)), "slot epoch events disagree with final epoch")
    require(all(rebinds[s] > 0 for s in range(8)), "a stable slot never rebound")
    require(not reuse.get("queue_replay_mismatches"), "queue replay mismatch detected")
    require(reuse.get("error") is None, "reuse probe raised an error")

    return {
        "combined_path": str(combined_path),
        "combined_sha256": sha(combined_path),
        "capacity_path": str(capacity_path),
        "capacity_sha256": sha(capacity_path),
        "reuse_path": str(reuse_path),
        "reuse_sha256": sha(reuse_path),
        "slot_epoch": {str(k): slot_epoch[k] for k in sorted(slot_epoch)},
        "per_slot_rebinds": {str(k): rebinds[k] for k in sorted(rebinds)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delivery", type=Path, required=True)
    parser.add_argument("--combined", type=Path, required=True)
    parser.add_argument("--capacity", type=Path, required=True)
    parser.add_argument("--reuse", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--expected-root", required=True)
    parser.add_argument("--expected-child", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    checks = []
    result = "PASS"
    try:
        pair = target_pair(args.expected_root, args.expected_child)
        checks.append({"check": "implementation_pair", "status": "PASS", "detail": pair})
        delivery = delivery_check(args.delivery, args.expected_root, args.expected_child)
        checks.append({"check": "delivery_engineering", "status": "PASS", "detail": delivery})
        probe_script = ROOT / "tools/g0/probe_a2_stable_slot_long_run.py"
        receipt = probe_receipt_check(args.receipt, args.expected_root, args.expected_child, probe_script)
        checks.append({"check": "probe_source_binding", "status": "PASS", "detail": receipt})
        probe = probe_check(args.combined, args.capacity, args.reuse, args.expected_child)
        checks.append({"check": "capacity_and_epoch_reuse", "status": "PASS", "detail": probe})
    except Exception as exc:  # noqa: BLE001
        result = "FAIL"
        checks.append({"check": "failure", "status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
        delivery = None

    report = {
        "schema": "a2_long_run_readiness_v1",
        "result": result,
        "verdict": "READY_FOR_LONG_RUN" if result == "PASS" else "BLOCKED",
        "implementation_pair": [args.expected_root, args.expected_child],
        "checks": checks,
        "owner_decision": {
            "decision": "D028",
            "mm_required": False,
            "full_catalog_b1_required": False,
            "matched_b1_speedup_scope": "10-episode/suite control only; not a full-catalog speedup claim",
        },
        "long_run_authorization": result == "PASS",
        "long_run_started": False,
        "policy_success_rate_claim": False,
        "estimate": (
            {
                "step_wall_mean_s": delivery["step_wall_mean_s"],
                "projected_5000_days_base": delivery["projected_5000_days_base"],
                "includes_eval_checkpoint_overhead": False,
            }
            if result == "PASS" and delivery is not None
            else None
        ),
        "verifier_sha256": sha(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result": result, "verdict": report["verdict"], "checks": [(x["check"], x["status"]) for x in checks]}, indent=2))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
