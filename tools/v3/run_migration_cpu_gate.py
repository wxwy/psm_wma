#!/usr/bin/env python3
"""Read-only CPU Gate for V3 migration completion. Never starts training or fetches Git.

Run after DS has safely synchronized the existing Root/Child worktree. Evidence
must be a NEW directory outside that worktree. A failed stage stops the sequence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import py_compile
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ACCEPTED_CHILD = "71e03c8501c94a2ad5fed60955af657d3f945b85"
FROZEN_CONFIG_DIGEST = "70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37"
TEST_FILES = (
    "../tools/v3/remaining_optimizations_test.py",
    "cosmos_framework/model/generator/omni_mot_cached_vision_test.py",
    "cosmos_framework/simulation/robocasa/local_memory_client_test.py",
    "cosmos_framework/utils/ordered_prefetch_test.py",
    "cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch_test.py",
    "cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py",
    "cosmos_framework/model/generator/mot/local_memory_grouped_window_test.py",
    "cosmos_framework/trainer/local_memory_grouped_test.py",
    "cosmos_framework/trainer/local_memory_grouped_resume_test.py",
    "cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py",
    "cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py",
    "examples/psm_wma_robocasa_formal_monitor_test.py",
    "examples/psm_wma_robocasa_formal_monitor_safety_test.py",
    "examples/psm_wma_robocasa_corrected_telemetry_test.py",
    "examples/psm_wma_robocasa_corrected_phase5_test.py",
)


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def allowed_root_records(porcelain: str) -> list[str]:
    allowed = []
    for record in porcelain.split("\0"):
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            raise ValueError("invalid Root status record")
        status, name = record[:2], record[3:]
        note = name in {"SESSION.md", "TODO.md"} and "D" not in status and "R" not in status
        evidence = (
            status == "??"
            and name.startswith(("artifacts/", "docs/collab/chatgpt/DS_PRO_"))
            and Path(name).suffix in {".json", ".jsonl", ".log", ".txt", ".md", ".png", ".csv", ".xml"}
        )
        if not note and not evidence:
            raise ValueError(f"unapproved Root change: {record}")
        allowed.append(record)
    return allowed


def verify_pair(root: Path, expected_root: str, expected_child: str) -> dict:
    if any(re.fullmatch(r"[0-9a-f]{40}", sha) is None for sha in (expected_root, expected_child)):
        raise ValueError("expected SHA must be a full lowercase 40-character commit")
    child = root / "cosmos-framework"
    observed_root, observed_child = git(root, "rev-parse", "HEAD"), git(child, "rev-parse", "HEAD")
    link = git(root, "ls-tree", "HEAD", "cosmos-framework").split()
    if (
        observed_root != expected_root
        or observed_child != expected_child
        or len(link) != 4
        or link[:2] != ["160000", "commit"]
        or link[2] != expected_child
    ):
        raise ValueError("Root/Child/Gitlink lock mismatch")
    child_status = git(child, "status", "--porcelain=v1", "--untracked-files=all")
    if child_status:
        raise ValueError(f"Child must be clean: {child_status}")
    # Do not strip the leading status-column space from NUL-delimited records.
    root_status = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1", "-z", "--untracked-files=all"], text=True
    )
    return {
        "root": observed_root,
        "child": observed_child,
        "gitlink": link[2],
        "preserved_root_notes": allowed_root_records(root_status),
    }


def cpu_environment(child: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        CUDA_VISIBLE_DEVICES="",
        COSMOS_DEVICE="cpu",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        PYTHONDONTWRITEBYTECODE="1",
        OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        PYTHONPATH=os.pathsep.join((str(child), str(child.parent / "scripts"))),
    )
    # Prevent stale torchrun context from making CPU tests join a training process group.
    for name in ("RANK", "LOCAL_RANK", "WORLD_SIZE", "LOCAL_WORLD_SIZE", "MASTER_ADDR", "MASTER_PORT"):
        env.pop(name, None)
    return env


def source_hashes(child: Path, paths: list[str]) -> dict[str, str]:
    return {name: hashlib.sha256((child / name).read_bytes()).hexdigest() for name in paths}


def run_command(command: list[str], *, cwd: Path, env: dict, output: Path, timeout: float) -> int:
    print("[CPU Gate] " + shlex.join(command), flush=True)
    with output.open("x", encoding="utf-8") as handle:
        handle.write("$ " + shlex.join(command) + "\n")
        handle.flush()
        completed = subprocess.run(
            command, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=timeout, check=False
        )
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-worktree", type=Path, required=True)
    parser.add_argument("--expected-root", required=True)
    parser.add_argument("--expected-child", required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=1800)
    args = parser.parse_args(argv)
    root, evidence = args.root_worktree.resolve(), args.evidence_dir.resolve()
    if evidence.is_relative_to(root):
        parser.error("evidence-dir must be outside the source worktree")
    if not 0 < args.timeout_seconds < float("inf"):
        parser.error("timeout-seconds must be finite and positive")
    evidence.mkdir(parents=True, exist_ok=False)
    report = {
        "gate": "V3-MIGRATION-COMPLETION-CPU",
        "scope": "cpu_static_only_no_real_DCP_no_GPU_no_resume",
        "status": "BLOCKED",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_config_digest_expected": FROZEN_CONFIG_DIGEST,
        "config_digest_measured": None,
        "stages": [],
    }
    try:
        report["pair"] = verify_pair(root, args.expected_root, args.expected_child)
        child = root / "cosmos-framework"
        env = cpu_environment(child)
        git(child, "merge-base", "--is-ancestor", ACCEPTED_CHILD, args.expected_child)
        names = git(child, "diff", "--name-only", ACCEPTED_CHILD, args.expected_child).splitlines()
        changed_python = sorted(name for name in names if name.endswith(".py"))
        if not changed_python or any(not (child / name).is_file() for name in (*changed_python, *TEST_FILES)):
            raise ValueError("expected changed Python source/test file is missing")
        measured = sorted(set(changed_python).union(TEST_FILES))
        report["source_sha256"] = source_hashes(child, measured)
        root_python = [
            "tools/v3/run_migration_cpu_gate.py",
            "tools/v3/run_migration_cpu_gate_test.py",
            "tools/v3/remaining_optimizations_test.py",
            "scripts/v3_evaluation_identity.py",
            "scripts/eval_robocasa_18task_queue.py",
        ]
        report["root_source_sha256"] = source_hashes(root, root_python)
        syntax_dir = evidence / "py_compile"
        for name in root_python:
            target = syntax_dir / "root" / (name + "c")
            target.parent.mkdir(parents=True, exist_ok=True)
            py_compile.compile(str(root / name), cfile=str(target), doraise=True)
        for name in measured:
            target = syntax_dir / (name + "c")
            target.parent.mkdir(parents=True, exist_ok=True)
            py_compile.compile(str(child / name), cfile=str(target), doraise=True)
        report["stages"].append({"stage": "py_compile", "status": "PASS", "files": len(measured) + len(root_python)})
        ruff = shutil.which("ruff")
        if ruff is None:
            raise RuntimeError("Ruff 0.12.7 is not installed in the existing environment; no auto-install")
        version = subprocess.check_output([ruff, "--version"], cwd=child, env=env, text=True).strip()
        report["ruff_version"] = version
        if version != "ruff 0.12.7":
            raise RuntimeError(f"require ruff 0.12.7, observed {version}")
        lint_files = [*changed_python, *(str(root / name) for name in root_python)]
        commands = (
            ("ruff_check", [ruff, "check", "--config", str(child / ".ruff.toml"), *lint_files]),
            ("ruff_format", [ruff, "format", "--check", "--config", str(child / ".ruff.toml"), *lint_files]),
            (
                "runner_pytest",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--noconftest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    "-o",
                    "addopts=",
                    f"--junitxml={evidence / 'runner_pytest.xml'}",
                    str(root / root_python[1]),
                ],
            ),
            (
                "pytest",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    "-o",
                    "addopts=",
                    "--tb=short",
                    f"--junitxml={evidence / 'pytest.xml'}",
                    *TEST_FILES,
                ],
            ),
        )
        commands = (
            *commands,
            *(
                (f"bash_{index}", ["bash", "-n", str(root / name)])
                for index, name in enumerate(
                    ("scripts/eval_robocasa.sh", "scripts/eval.sh", "scripts/train_local_memory_ttt.sh")
                )
            ),
        )
        for stage, command in commands:
            code = run_command(
                command, cwd=child, env=env, output=evidence / f"{stage}.log", timeout=args.timeout_seconds
            )
            report["stages"].append({"stage": stage, "returncode": code, "status": "PASS" if code == 0 else "FAIL"})
            if code:
                report["status"] = "FAIL"
                return 1
        report["pair_after"] = verify_pair(root, args.expected_root, args.expected_child)
        if source_hashes(child, measured) != report["source_sha256"]:
            raise ValueError("source changed while running the CPU gate")
        if source_hashes(root, root_python) != report["root_source_sha256"]:
            raise ValueError("Root gate source changed while running")
        report["status"] = "PASS"
        return 0
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        return 2
    finally:
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (evidence / "gate.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "evidence": str(evidence)}, sort_keys=True), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
