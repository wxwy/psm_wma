"""Current-V3 async/lazy integration CPU gate; no real model/data/DCP/GPU."""

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
SOURCE = f"{CHILD}/cosmos_framework/trainer/no_ttt_worker_source_test.py::"
RECIPE = f"{CHILD}/cosmos_framework/trainer/no_ttt_async_recipe_test.py::"
ASYNC = ["tools/v3/no_ttt_async_port_test.py"] + [SOURCE + name for name in (
    "test_official_delta_caption_padding_and_source_windows_match",
    "test_build_does_not_call_eager_constructor_or_read_any_source_parquet",
    "test_lru_eviction_bounds_and_reload_preserve_exact_values",
    "test_bad_verified_metadata_and_mapping_fail_closed",
    "test_missing_changed_or_corrupt_source_never_becomes_valid_window",
)] + [RECIPE + name for name in (
    "test_real_transform_two_branches_preserve_values_and_original_rng_interleaving",
    "test_first_worker_recipe_build_never_calls_full_lerobot_constructor",
    "test_spawned_real_recipe_source_transform_cfg_and_cross_window_cleanup",
    "test_recipe_roundtrip_contains_only_small_metadata_and_reopens_private_readers",
    "test_worker_recipe_freezes_resolved_data_roots_before_alias_can_change",
)]
LOADER = f"{CHILD}/cosmos_framework/trainer/no_ttt_async_loader_test.py::"
TRAINER = f"{CHILD}/cosmos_framework/trainer/no_ttt_async_trainer_test.py::"
REGRESSION = [
    LOADER + "test_actual_source_transform_next_member_and_next_window_overlap",
    LOADER + "test_full_and_terminal_partial_three_windows_exact_data_and_interleaved_rng[8]",
    LOADER + "test_prepared_file_changed_after_worker_completion_is_rejected_before_rng[source]",
    LOADER + "test_persistence_option_and_speculative_checkpoint_are_rng_neutral[True]",
    TRAINER + "test_same_job_checkpoint_resume_worker_changes_preserve_entire_next_steps[0-8-0]",
    TRAINER + "test_same_job_checkpoint_resume_worker_changes_preserve_entire_next_steps[8-8-3]",
    TRAINER + "test_failed_active_window_keeps_checkpoint_frontier_and_reaps_speculation[native_error]",
    f"{CHILD}/cosmos_framework/trainer/no_ttt_cpu_loader_resume_test.py::test_worker_count_changes_resume_same_committed_state_without_changing_training[0-8]",
    f"{CHILD}/cosmos_framework/trainer/no_ttt_cpu_loader_resume_test.py::test_wrong_checkpoint_profile_never_starts_workers_or_native_model[format]",
    f"{CHILD}/examples/psm_wma_robocasa_matched_no_ttt_test.py::test_all_worker_counts_share_strict_training_and_config_identity",
]
STATIC = [
    f"{CHILD}/cosmos_framework/trainer/{name}.py"
    for name in (
        "no_ttt_async_recipe",
        "no_ttt_async_loader",
        "matched_no_ttt",
        "no_ttt_async_test_support",
        "no_ttt_worker_source",
        "no_ttt_worker_source_test",
        "no_ttt_async_recipe_test",
        "no_ttt_async_loader_test",
        "no_ttt_async_trainer_test",
        "no_ttt_cpu_loader_resume_test",
    )
] + [
    f"{CHILD}/cosmos_framework/utils/no_ttt_loader_profile.py",
    f"{CHILD}/cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py",
    f"{CHILD}/examples/psm_wma_robocasa_matched_no_ttt_test.py",
    "tools/v3/no_ttt_async_port_test.py",
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
        "gate": "CANONICAL_BASED_ASYNC_LAZY_PORT_TARGETED_SYNTHETIC_CPU",
        "steps": [],
        "real_gpu": False,
        "real_dcp_resume": False,
        "old_301_rerun": False,
        "old_58_full_rerun": False,
        "real_data": False,
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
        watched = sorted(set(name.split("::")[0] for name in STATIC + ASYNC + REGRESSION))

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
            "LD_LIBRARY_PATH": "",
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
                    "-o",
                    "markers=level: original local CPU test level",
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
