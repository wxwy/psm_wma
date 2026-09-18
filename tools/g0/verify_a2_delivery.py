"""Verify actual A2 run artifacts, not manually entered PASS/READY labels.

Training-code equivalence is explicit: every source file hashed at launch must
still match, and its hash must match the named immutable child commit. A later
review/report-only commit does not invalidate otherwise identical source bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import io
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "cosmos-framework"
CHECKPOINT_SUFFIX = Path(
    "cosmos3_action_libero/action_sft/edge_libero_4in1_localmem_active/checkpoints"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str, cwd: Path = CHILD) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def source_receipt(receipt: dict) -> dict:
    if receipt.get("dirty"):
        raise ValueError("evidence was captured from dirty tracked source")
    commit = receipt["child"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("receipt child is not an exact commit")
    code = receipt["tracked_code_sha256"]
    if not isinstance(code, dict) or len(code) < 10:
        raise ValueError("receipt has no substantive source scope")
    changed, commit_mismatch = [], []
    names = list(code)
    query = "".join(f"{commit}:{name}\n" for name in names).encode()
    blob_stream = io.BytesIO(
        subprocess.check_output(["git", "cat-file", "--batch"], input=query, cwd=CHILD)
    )
    for name, digest in code.items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("invalid evidence source path")
        if not (CHILD / path).is_file() or sha(CHILD / path) != digest:
            changed.append(name)
        header = blob_stream.readline().decode().split()
        if len(header) != 3 or header[1] != "blob":
            raise ValueError(f"evidence path is absent in its claimed commit: {name}")
        raw = blob_stream.read(int(header[2]))
        if blob_stream.read(1) != b"\n":
            raise ValueError("invalid git object framing")
        if hashlib.sha256(raw).hexdigest() != digest:
            commit_mismatch.append(name)
    if changed or commit_mismatch:
        raise ValueError(
            f"evidence source mismatch: working={changed}, immutable={commit_mismatch}"
        )
    for name, digest in receipt.get("input_metadata_sha256", {}).items():
        if not Path(name).is_file() or sha(Path(name)) != digest:
            raise ValueError(f"input metadata changed: {name}")
    return {
        "child_at_capture": commit,
        "checked_source_files": len(code),
        "input_metadata_files": len(receipt.get("input_metadata_sha256", {})),
        "scope": "exact captured source bytes; not an authorization for uncaptured code",
    }


def inspect_run(directory: Path, *, min_steps: int = 1) -> dict:
    launches = sorted(directory.glob("launch_*.json"))
    if not launches:
        raise FileNotFoundError(f"no launch receipt: {directory}")
    receipt_file = launches[-1]
    receipt = json.loads(receipt_file.read_text())
    binding = source_receipt(receipt)
    suffix = receipt_file.stem.removeprefix("launch_")
    exit_file = directory / f"exit_{suffix}.txt"
    if not exit_file.is_file():
        raise FileNotFoundError(f"run not finished: {exit_file}")
    if exit_file.read_text().strip() != "0":
        raise ValueError(f"training process failed: {directory}")
    text = (directory / f"process_{suffix}.log").read_text(errors="replace")
    restored_iteration = None
    if receipt.get("mode") == "resume":
        matches = re.findall(r"Loaded checkpoint.*in iteration (\d+)", text)
        if not matches or int(matches[-1]) <= 0:
            raise ValueError(
                "resume process did not report loading a nonzero checkpoint"
            )
        restored_iteration = int(matches[-1])
    metrics_file = directory / "metrics.jsonl"
    rows = [
        json.loads(line)
        for line in metrics_file.read_text().splitlines()
        if line.strip()
    ]
    if restored_iteration is not None:
        rows = [r for r in rows if r["window_index"] > restored_iteration]
    if len(rows) < min_steps or len({r["window_index"] for r in rows}) != len(rows):
        raise ValueError("insufficient or repeated completed windows")
    env = receipt["environment"]
    slots = int(env["PSM_R09_B_TTT_B_STREAM"])
    ga = int(env["PSM_R09_B_TTT_ACTIVE_GA"])
    n = slots * 16 * ga
    expected_groups = {
        "moe_gen", "time_embedder", "vae2llm", "llm2vae", "action2llm", "llm2action",
        "action_modality_embed", "local_memory_runtime.evidence_encoder",
        "local_memory_runtime.ttt_core", "local_memory2llm", "local_memory_modality_embed",
    }
    for row in rows:
        if row["layout"] != "active_a2_v1" or row["native_forwards"] != ga:
            raise ValueError("actual native layout/call count differs from A2 configuration")
        if row["valid_consumers"] != n or row["group_counts"] != [slots * 16] * ga:
            raise ValueError("actual consumers/GA scale differs from configuration")
        losses = (row["loss_min"], row["loss_mean"], row["loss_max"])
        if not all(math.isfinite(v) for v in losses) or not losses[0] <= losses[1] <= losses[2]:
            raise ValueError("non-finite or inconsistent native losses")
        gradients = row["gradients"]
        if set(gradients) != expected_groups:
            raise ValueError(f"trainable gradient groups differ from D025: {sorted(gradients)}")
        if any(not g["finite"] or g["with_grad"] <= 0 or g["nonzero_grad"] <= 0 for g in gradients.values()):
            raise ValueError("missing, zero, or non-finite gradient in a D025 trainable group")
        if sum(row["optimizer_group_sizes"]) != sum(g["tensors"] for g in gradients.values()):
            raise ValueError("optimizer membership differs from requires-grad telemetry")
    cp = directory / CHECKPOINT_SUFFIX / f"iter_{rows[-1]['window_index']:09d}"
    for component in ("model", "optim", "scheduler", "trainer", "dataloader"):
        if not (cp / component).is_dir() or not any((cp / component).iterdir()):
            raise ValueError(f"final checkpoint component absent: {component}")
    text = (directory / f"process_{suffix}.log").read_text(errors="replace")
    walls = [float(v) for v in re.findall(r"perf/step_wall_s=([0-9.eE+-]+)", text)]
    if not walls:
        raise ValueError("actual trainer wall-time records absent")
    return {
        "directory": str(directory),
        "binding": binding,
        "launch_receipt": str(receipt_file),
        "launch_sha256": sha(receipt_file),
        "metrics_sha256": sha(metrics_file),
        "steps_recorded": len(rows),
        "first_window": rows[0]["window_index"],
        "last_window": rows[-1]["window_index"],
        "consumers_per_update": n,
        "native_forwards_per_update": ga,
        "last_checkpoint": str(cp),
        "step_wall_mean_s": sum(walls) / len(walls),
        "cuda_peak_allocated_GiB": max(r["peak_allocated_bytes"] for r in rows) / 2**30,
        "data_max_episodes_per_suite": env["LIBERO_MAX_EPISODES"],
        "rows": rows,
    }


def inspect_cpu(directory: Path) -> dict:
    receipt = json.loads((directory / "receipt.json").read_text())
    binding = source_receipt(receipt)
    if sha(Path(receipt["harness"])) != receipt["harness_sha256"]:
        raise ValueError("CPU validation harness changed after execution")
    if (directory / "exit_code.txt").read_text().strip() != "0":
        raise ValueError("CPU test command failed")
    junit = ET.parse(directory / "junit.xml").getroot()
    suites = list(junit.iter("testsuite"))
    count = sum(int(s.get("tests", 0)) for s in suites)
    errors = sum(int(s.get("errors", 0)) + int(s.get("failures", 0)) for s in suites)
    names = [case.get("classname", "") for case in junit.iter("testcase")]
    required = (
        "grouped_active_runtime_test",
        "grouped_active_model_test",
        "local_memory_online_test",
        "local_memory_policy_test",
        "local_memory_client_test",
        "closed_loop_local_memory_test",
        "local_evidence_test",
        "active_local_memory_launch_test",
        "production_active_wiring_test",
    )
    if (
        count < 100
        or errors
        or any(not any(module in name for name in names) for module in required)
    ):
        raise ValueError("required CPU behavior suites failed or were not executed")
    return {
        "tests": count,
        "errors_and_failures": errors,
        "binding": binding,
        "junit_sha256": sha(directory / "junit.xml"),
        "directory": str(directory),
    }


def compare_resume(control: dict, resumed: dict) -> dict:
    original = {r["window_index"]: r for r in control["rows"]}
    keys = (
        "actual_consumer_identity_sha256",
        "slot_epoch",
        "stream_index",
        "active_cursor",
        "exposure",
        "group_counts",
    )
    compared, mismatches = [], []
    for row in resumed["rows"]:
        index = row["window_index"]
        if index not in original:
            continue
        compared.append(index)
        mismatches.extend(
            f"window{index}:{key}" for key in keys if row[key] != original[index][key]
        )
    if not compared or mismatches:
        raise ValueError(
            f"resume identity/frontier mismatch: compared={compared}, mismatch={mismatches}"
        )
    first = resumed["rows"][0]
    previous = original.get(first["window_index"] - 1)
    if previous is None or previous.get("fast_state_records", 0) <= 0:
        raise ValueError("control has no preceding retained fast-state witness")
    if (
        first.get("fast_state_before_first_group_sha256")
        != previous["fast_state_sha256"]
    ):
        raise ValueError("resumed fast-state bytes differ from saved control state")
    return {
        "compared_windows": compared,
        "matched_fields": list(keys),
        "restored_fast_state_matches_saved_bytes": True,
        "gpu_post_update_bitwise_equivalence_claimed": False,
    }


def inspect_native(path: Path) -> dict:
    report = json.loads(path.read_text())
    parity, online = report["native_group_parity"], report["online_generation"]
    visual = report["rgb_visual96_parity"]
    if report.get("result") != "PASS" or visual.get("result") != "PASS":
        raise ValueError("native validation or raw-RGB visual96 parity failed")
    if not (
        parity["consumers"] == 128
        and parity["grouped_forwards"] == 1
        and parity["scalar_forwards"] == 8
        and parity["gradient_tensors"] >= 20
        and 0 <= parity["loss_relative_error"] <= 0.01
        and 0 <= parity["gradient_relative_l2"] <= 0.05
        and 0 <= parity["local_gradient_relative_l2"] <= 0.05
    ):
        raise ValueError(
            "native regrouping did not meet predeclared numerical tolerances"
        )
    if not (
        online["consumer_steps"] == [0, 1]
        and online["slow_weights_unchanged"]
        and online["no_slow_parameter_grads"]
        and online["actions_finite"]
        and math.isfinite(online["local_token_max_abs"])
        and online["local_token_max_abs"] > 0
        and math.isfinite(online["local_on_off_action_max_difference"])
        and online["local_on_off_action_max_difference"] > 1e-8
    ):
        raise ValueError("real Local-memory generation invariants failed")
    return {
        "path": str(path),
        "sha256": sha(path),
        "parity": parity,
        "online_generation": online,
        "rgb_visual96_parity": visual,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--resume", type=Path, required=True)
    parser.add_argument("--budget", type=Path)
    parser.add_argument("--require-budget", action="store_true")
    parser.add_argument("--expected-child", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checks, values = [], {}

    def check(name, operation):
        try:
            values[name] = operation()
            checks.append({"check": name, "status": "PASS", "detail": values[name]})
        except FileNotFoundError as error:
            checks.append({"check": name, "status": "BLOCKED", "error": str(error)})
        except Exception as error:
            checks.append(
                {
                    "check": name,
                    "status": "FAIL",
                    "error": f"{type(error).__name__}: {error}",
                }
            )

    def current_source():
        child = git("rev-parse", "HEAD")
        if child != args.expected_child or git(
            "status", "--short", "--untracked-files=no"
        ):
            raise ValueError(
                "current committed child differs from the requested clean target"
            )
        return {"root": git("rev-parse", "HEAD", cwd=ROOT), "child": child}

    check("committed_target", current_source)
    check("cpu_behavior", lambda: inspect_cpu(args.cpu))
    check("gpu_control", lambda: inspect_run(args.control, min_steps=3))
    check("gpu_resume", lambda: inspect_run(args.resume))
    if "gpu_control" in values and "gpu_resume" in values:
        check(
            "resume_frontier_and_fast_state",
            lambda: compare_resume(values["gpu_control"], values["gpu_resume"]),
        )
    else:
        checks.append(
            {
                "check": "resume_frontier_and_fast_state",
                "status": "BLOCKED",
                "error": "missing valid runs",
            }
        )
    check(
        "real_native_parity_and_inference",
        lambda: inspect_native(args.control / "native_validation.json"),
    )
    if args.budget:
        check("twenty_step_budget", lambda: inspect_run(args.budget, min_steps=20))
    elif args.require_budget:
        checks.append(
            {
                "check": "twenty_step_budget",
                "status": "BLOCKED",
                "error": "no new-layout budget run",
            }
        )
    for item in checks:
        if isinstance(item.get("detail"), dict):
            item["detail"].pop("rows", None)
    statuses = {c["status"] for c in checks}
    result = (
        "FAIL" if "FAIL" in statuses else "BLOCKED" if "BLOCKED" in statuses else "PASS"
    )
    report = {
        "schema": "a2_delivery_verification_v1",
        "result": result,
        "checks": checks,
        "scope": "engineering validation of the named A2 source; not policy success-rate evidence",
        "long_run_authorization": False,
        "independent_review_approval": False,
        "budget_required": args.require_budget,
        "verifier_sha256": sha(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "result": result,
                "checks": [
                    {k: v for k, v in c.items() if k != "detail"} for c in checks
                ],
            },
            indent=2,
        )
    )
    return 0 if result == "PASS" else 2 if result == "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
