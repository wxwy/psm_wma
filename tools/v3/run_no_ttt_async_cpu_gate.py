"""Read-only exact-pair No-TTT async CPU replay. No model, dataset or GPU input."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

CHILD = "cosmos-framework"
ASYNC = [
    f"{CHILD}/cosmos_framework/trainer/{name}.py"
    for name in (
        "no_ttt_async_recipe_test",
        "no_ttt_async_loader_test",
        "no_ttt_async_trainer_test",
    )
]
REGRESSION = [
    f"{CHILD}/cosmos_framework/trainer/{name}.py"
    for name in (
        "no_ttt_cpu_loader_test",
        "no_ttt_cpu_loader_resume_test",
        "matched_no_ttt_test",
    )
] + [
    f"{CHILD}/cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py",
    f"{CHILD}/cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py",
    f"{CHILD}/examples/psm_wma_robocasa_matched_no_ttt_test.py",
    "tools/v3/no_ttt_workers_entry_test.py",
    "tools/v3/matched_no_ttt_entry_test.py",
]
STATIC = [
    f"{CHILD}/cosmos_framework/trainer/{name}.py"
    for name in (
        "no_ttt_async_recipe",
        "no_ttt_async_loader",
        "no_ttt_async_test_support",
        "matched_no_ttt",
        "no_ttt_cpu_loader_resume_test",
        "no_ttt_async_recipe_test",
        "no_ttt_async_loader_test",
        "no_ttt_async_trainer_test",
    )
] + [
    f"{CHILD}/cosmos_framework/utils/no_ttt_loader_profile.py",
    f"{CHILD}/cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py",
    f"{CHILD}/examples/psm_wma_robocasa_matched_no_ttt_test.py",
    "tools/v3/run_no_ttt_async_cpu_gate.py",
    "tools/v3/no_ttt_workers_entry_test.py",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-worktree", required=True, type=Path)
    parser.add_argument("--expected-root", required=True)
    parser.add_argument("--expected-child", required=True)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    args = parser.parse_args()
    root, out = args.root_worktree.resolve(), args.evidence_dir.resolve()
    if out.exists() or out.is_relative_to(root):
        parser.error("NEW external evidence directory required")
    out.mkdir(parents=True)
    state = {
        "status": "BLOCKED",
        "gate": "NOTTT_ASYNC_AUTHOR_OR_DS_CPU_ONLY",
        "steps": [],
        "real_gpu": False,
        "real_dcp_resume": False,
        "excluded_real_data_nodes": [
            f"{CHILD}/cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py::test_optional_real_data_debug_smoke"
        ],
        "exclusion_reason": "Owner authorizes synthetic CPU only; real asset execution is forbidden, not a skipped CPU requirement",
    }

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2) + "\n")

    def git(directory, *words):
        return subprocess.check_output(
            ["git", "-C", str(directory), *words], text=True
        ).strip()

    try:
        child = root / CHILD
        observed = {
            "root": git(root, "rev-parse", "HEAD"),
            "child": git(child, "rev-parse", "HEAD"),
            "gitlink": git(root, "rev-parse", f"HEAD:{CHILD}"),
        }
        state["identities"] = observed
        if observed != {
            "root": args.expected_root,
            "child": args.expected_child,
            "gitlink": args.expected_child,
        }:
            raise ValueError("exact Root/Child/Gitlink mismatch")
        if any(
            git(directory, "status", "--porcelain=v1", "--untracked-files=all")
            for directory in (root, child)
        ):
            raise ValueError("clean worktrees required")
        if importlib.metadata.version("ruff") != "0.12.7":
            raise ValueError("Ruff0.12.7 required")
        watched = sorted(set(STATIC + ASYNC + REGRESSION))

        def hashes():
            return {
                name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                for name in watched
            }

        before = hashes()
        save("source_sha256.json", before)
        overrides = {
            "CUDA_VISIBLE_DEVICES": "",
            "COSMOS_DEVICE": "cpu",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_ADDOPTS": "",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "HF_HOME": str(out / "cache/hf"),
            "MPLCONFIGDIR": str(out / "cache/mpl"),
            "XDG_CACHE_HOME": str(out / "cache/xdg"),
            "RUFF_CACHE_DIR": str(out / "cache/ruff"),
            "PYTHONPATH": os.pathsep.join(map(str, (root, child, root / "scripts"))),
            "PSM_NOTTT_ASYNC_EVIDENCE": str(out / "timelines"),
        }
        env = {**os.environ, **overrides}
        for key in (
            "RANK",
            "WORLD_SIZE",
            "LOCAL_RANK",
            "LOCAL_WORLD_SIZE",
            "MASTER_ADDR",
            "MASTER_PORT",
            "PSM_PHASE4A_CACHE_ROOT",
            "PSM_PHASE4A_SOURCE_ROOT",
        ):
            env.pop(key, None)
        save(
            "environment.json",
            {
                "python": sys.version,
                "overrides": overrides,
                "versions": {
                    k: importlib.metadata.version(k)
                    for k in ("torch", "pytest", "ruff")
                },
            },
        )

        def run(name, argv, timeout=1800):
            step = {"name": name, "argv": argv, "cwd": str(root), "timeout_s": timeout}
            state["steps"].append(step)
            state["status"] = "RUNNING"
            save("gate.json", state)
            print(f"[NoTTT async CPU Gate] {name}", flush=True)
            started = time.monotonic()
            with (out / f"{name}.log").open("w") as stream:
                process = subprocess.Popen(
                    argv,
                    cwd=root,
                    env=env,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    code = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Only the new, owned test session is targeted. Never let
                    # an outer watchdog leave spawned CPU workers behind.
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
                    raise
            step.update(exit_code=code, seconds=time.monotonic() - started)
            if code:
                raise RuntimeError(f"{name} failed; see {name}.log")

        run(
            "import_origin",
            [
                sys.executable,
                "-c",
                "import pathlib,cosmos_framework; "
                f"assert pathlib.Path(cosmos_framework.__file__).resolve().is_relative_to(pathlib.Path({str(child)!r})); "
                "print(cosmos_framework.__file__)",
            ],
            60,
        )
        run("ruff_check", [sys.executable, "-m", "ruff", "check", *STATIC], 60)
        run(
            "ruff_format",
            [sys.executable, "-m", "ruff", "format", "--check", *STATIC],
            60,
        )
        for name in STATIC:
            ast.parse((root / name).read_text(), filename=name)
        state["syntax_files"] = len(STATIC)
        totals = dict(tests=0, failures=0, errors=0, skipped=0)
        combined = ET.Element("testsuites")
        for name, tests in (("async", ASYNC), ("regression", REGRESSION)):
            run(
                name,
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--noconftest",
                    "-c",
                    "/dev/null",
                    "-q",
                    "-s",
                    "-x",
                    f"--deselect={CHILD}/cosmos_framework/model/generator/mot/robocasa_exact_window_local_test.py::test_optional_real_data_debug_smoke",
                    "-p",
                    "no:cacheprovider",
                    f"--rootdir={root}",
                    *tests,
                    f"--basetemp={out / (name + '_tmp')}",
                    f"--junitxml={out / (name + '.xml')}",
                ],
            )
            suites = list(ET.parse(out / f"{name}.xml").getroot().iter("testsuite"))
            counts = {
                key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in totals
            }
            if not counts["tests"] or any(
                counts[k] for k in ("failures", "errors", "skipped")
            ):
                raise RuntimeError(
                    f"{name}: zero tests or failed/error/skipped testcase"
                )
            for suite in suites:
                combined.append(suite)
            for key in totals:
                totals[key] += counts[key]
        ET.ElementTree(combined).write(out / "junit.xml", encoding="unicode")
        state["totals"] = totals
        state["source_unchanged"] = hashes() == before
        if not state["source_unchanged"] or any(
            git(d, "status", "--porcelain=v1") for d in (root, child)
        ):
            raise ValueError("source/working tree changed during CPU replay")
        state["status"] = "PASS"
    except Exception as exc:
        state["error"] = f"{type(exc).__name__}: {exc}"
        if state["status"] == "RUNNING":
            state["status"] = "FAIL"
    save("gate.json", state)
    return 0 if state["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
