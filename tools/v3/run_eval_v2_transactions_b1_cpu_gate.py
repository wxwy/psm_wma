"""Read-only exact-pair CPU replay for Phase B's first transaction/B1 increment."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

CHILD = "cosmos-framework"
PRODUCTION = [
    "inference/local_memory_state.py",
    "inference/local_memory_online.py",
    "inference/robocasa_local_memory_policy.py",
    "inference/robocasa_session_transactions.py",
    "inference/robocasa_transaction_client.py",
    "inference/robocasa_session_transactions_test.py",
    "scripts/action_policy_server_robocasa.py",
    "scripts/robocasa_transactions_b1_test.py",
]
INFERENCE_TESTS = [
    "inference/local_memory_online_test.py",
    "inference/robocasa_local_memory_policy_test.py",
    "inference/robocasa_session_transactions_test.py",
    "scripts/action_policy_server_robocasa_phase6_test.py",
    "scripts/robocasa_transactions_b1_test.py",
]
PHASE_A_TESTS = [
    "tools/v3/eval_v2_production_tests",
    *[
        f"{CHILD}/cosmos_framework/simulation/robocasa/{name}.py"
        for name in (
            "closed_loop_eval_contract_test",
            "closed_loop_eval_lifecycle_test",
            "closed_loop_eval_manual_test",
            "closed_loop_eval_phase6_test",
            "eval_utils_test",
            "local_memory_client_test",
        )
    ],
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-worktree", required=True, type=Path)
    parser.add_argument("--expected-root", required=True)
    parser.add_argument("--expected-child", required=True)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    args = parser.parse_args()
    root, out = args.root_worktree.resolve(), args.evidence_dir.resolve()
    if out.is_relative_to(root) or out.exists():
        parser.error("evidence must be a NEW directory outside the source worktree")
    out.mkdir(parents=True)
    state = {
        "gate": "TRANSACTION_B1_AUTHOR_OR_DS_CPU_ONLY",
        "status": "BLOCKED",
        "steps": [],
    }

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

    def git(directory, *arguments):
        return subprocess.check_output(
            ["git", "-C", str(directory), *arguments], text=True
        ).strip()

    def versions():
        return {
            "python": sys.version,
            "platform": platform.platform(),
            "packages": {
                name: importlib.metadata.version(name)
                for name in ("torch", "pytest", "ruff")
            },
        }

    try:
        for sha in (args.expected_root, args.expected_child):
            if re.fullmatch("[0-9a-f]{40}", sha) is None:
                raise ValueError("complete exact SHA required")
        child = root / CHILD
        identities = {
            "root": git(root, "rev-parse", "HEAD"),
            "child": git(child, "rev-parse", "HEAD"),
            "gitlink": git(root, "rev-parse", f"HEAD:{CHILD}"),
        }
        if identities != {
            "root": args.expected_root,
            "child": args.expected_child,
            "gitlink": args.expected_child,
        }:
            raise ValueError(f"exact-pair mismatch: {identities}")
        if git(root, "status", "--porcelain=v1") or git(
            child, "status", "--porcelain=v1"
        ):
            raise ValueError("clean isolated exact-pair worktrees required")
        if importlib.metadata.version("ruff") != "0.12.7":
            raise ValueError("Ruff0.12.7 required")
        state["identities"] = identities
        save("environment.json", versions())
        static = [f"{CHILD}/cosmos_framework/{name}" for name in PRODUCTION]
        static += ["tools/v3/run_eval_v2_transactions_b1_cpu_gate.py"]
        tests = {
            "inference": [
                f"{CHILD}/cosmos_framework/{name}" for name in INFERENCE_TESTS
            ],
            "phase_a_regression": PHASE_A_TESTS,
        }
        watched = set(static)
        for group in tests.values():
            for name in group:
                p = root / name
                if p.is_dir():
                    watched.update(
                        str(item.relative_to(root)) for item in p.rglob("*.py")
                    )
                else:
                    watched.add(name)

        def fingerprint():
            return {
                name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                for name in sorted(watched)
            }

        before = fingerprint()
        save("source_sha256.json", before)
        env = os.environ.copy()
        overrides = dict(
            CUDA_VISIBLE_DEVICES="",
            COSMOS_DEVICE="cpu",
            HF_HUB_OFFLINE="1",
            TRANSFORMERS_OFFLINE="1",
            PYTHONDONTWRITEBYTECODE="1",
            OMP_NUM_THREADS="1",
            MKL_NUM_THREADS="1",
            OPENBLAS_NUM_THREADS="1",
            HF_HOME=str(out / "cache/hf"),
            MPLCONFIGDIR=str(out / "cache/mpl"),
            XDG_CACHE_HOME=str(out / "cache/xdg"),
            RUFF_CACHE_DIR=str(out / "cache/ruff"),
            TRITON_CACHE_DIR=str(out / "cache/triton"),
            PYTEST_ADDOPTS="",
            PYTHONPATH=os.pathsep.join(map(str, (root, child, root / "scripts"))),
        )
        env.update(overrides)
        save("environment_overrides.json", overrides)

        def run(name, argv, timeout=1200):
            state["status"] = "RUNNING"
            step = {"name": name, "argv": argv, "cwd": str(root), "timeout_s": timeout}
            state["steps"].append(step)
            save("gate.json", state)
            print(f"CPU Gate: {name}", flush=True)
            start = time.monotonic()
            with (out / f"{name}.log").open("w") as log:
                result = subprocess.run(
                    argv,
                    cwd=root,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                )
            step.update(exit_code=result.returncode, seconds=time.monotonic() - start)
            save("gate.json", state)
            if result.returncode:
                raise RuntimeError(f"{name} failed; see {out / (name + '.log')}")

        run(
            "import_origin",
            [
                sys.executable,
                "-c",
                "import cosmos_framework,pathlib; "
                f"assert pathlib.Path(cosmos_framework.__file__).resolve().is_relative_to(pathlib.Path({str(child)!r})); "
                "print(cosmos_framework.__file__)",
            ],
            60,
        )
        run("ruff_check", [sys.executable, "-m", "ruff", "check", *static], 60)
        run(
            "ruff_format",
            [sys.executable, "-m", "ruff", "format", "--check", *static],
            60,
        )
        for name in static:
            ast.parse((root / name).read_text(), filename=name)
        state["syntax_files"] = len(static)
        combined = ET.Element("testsuites")
        totals = dict(tests=0, failures=0, errors=0, skipped=0)
        for group, names in tests.items():
            run(
                group,
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--noconftest",
                    "-c",
                    "/dev/null",
                    f"--rootdir={root}",
                    "-p",
                    "no:cacheprovider",
                    "-q",
                    "-s",
                    "-x",
                    *names,
                    f"--basetemp={out / (group + '_tmp')}",
                    f"--junitxml={out / (group + '.xml')}",
                ],
            )
            suites = list(ET.parse(out / f"{group}.xml").getroot().iter("testsuite"))
            counts = {
                key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in totals
            }
            if counts["tests"] == 0 or any(
                counts[key] for key in ("failures", "errors", "skipped")
            ):
                raise RuntimeError(
                    f"{group}: zero skips/failures/errors required: {counts}"
                )
            state[group] = counts
            for key in totals:
                totals[key] += counts[key]
            combined.extend(suites)
        ET.ElementTree(combined).write(
            out / "junit.xml", encoding="utf-8", xml_declaration=True
        )
        if (
            before != fingerprint()
            or git(root, "status", "--porcelain=v1")
            or git(child, "status", "--porcelain=v1")
        ):
            raise RuntimeError("source changed during CPU Gate")
        state.update(
            status="PASS",
            junit=totals,
            source_unchanged=True,
            gpu_native_model_simulation_dcp_training="NOT_RUN",
            independent_ds="caller_role_not_inferred",
        )
    except Exception as error:
        state.update(
            status="FAIL" if state["steps"] else "BLOCKED",
            error=f"{type(error).__name__}: {error}",
        )
    save("gate.json", state)
    print(json.dumps(state, indent=2), flush=True)
    return 0 if state["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
