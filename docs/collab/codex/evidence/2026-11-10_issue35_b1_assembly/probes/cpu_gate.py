"""Issue35 B1 assembly: existing scoped CPU gate plus strict two-file static checks."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback


def save(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-root", required=True)
    parser.add_argument("--expected-child", required=True)
    parser.add_argument("--expected-tests", type=int, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    child = root / "cosmos-framework"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = dict(
        os.environ,
        CUDA_VISIBLE_DEVICES="",
        LD_LIBRARY_PATH="",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        PYTHONDONTWRITEBYTECODE="1",
        RUFF_CACHE_DIR=str(out / "ruff"),
    )
    files = [
        child / "cosmos_framework/model/generator/mot" / name
        for name in ("memory_prefix.py", "memory_prefix_test.py")
    ]

    def identity():
        return dict(
            root=git(root, "rev-parse", "HEAD"),
            child=git(child, "rev-parse", "HEAD"),
            gitlink=git(root, "rev-parse", "HEAD:cosmos-framework"),
            root_status=git(root, "status", "--porcelain"),
            child_status=git(child, "status", "--porcelain"),
        )

    def hashes():
        return {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        }

    def run(name, command):
        with (out / (name + ".log")).open("x") as log:
            result = subprocess.run(
                command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT
            )
        save(
            out / (name + ".command.json"),
            dict(argv=command, cwd=str(root), exit_code=result.returncode),
        )
        assert result.returncode == 0, name + " failed; original log retained"

    state = dict(
        status="RUNNING",
        independent_approval="NOT_CLAIMED",
        real_H100="PENDING_INDEPENDENT_GPT",
    )
    try:
        before = identity()
        assert before == dict(
            root=args.expected_root,
            child=args.expected_child,
            gitlink=args.expected_child,
            root_status="",
            child_status="",
        )
        initial_hashes = hashes()
        save(out / "identity.json", before)
        save(out / "new_source_before.json", initial_hashes)
        save(
            out / "environment.json",
            {
                name: env[name]
                for name in (
                    "CUDA_VISIBLE_DEVICES",
                    "LD_LIBRARY_PATH",
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "HF_HUB_OFFLINE",
                    "TRANSFORMERS_OFFLINE",
                    "PYTHONDONTWRITEBYTECODE",
                )
            },
        )
        ruff = [sys.executable, "-m", "ruff"]
        run(
            "new_static_lint",
            [*ruff, "check", "--config", str(child / ".ruff.toml"), *map(str, files)],
        )
        run(
            "new_static_format",
            [
                *ruff,
                "format",
                "--check",
                "--config",
                str(child / ".ruff.toml"),
                *map(str, files),
            ],
        )
        for path in files:
            ast.parse(path.read_text(), str(path))
        helper = (
            root
            / "docs/collab/codex/evidence/2026-11-09_issue31_prefix_pack/cpu/cpu_gate.py"
        )
        run(
            "existing_scoped_gate",
            [
                sys.executable,
                str(helper),
                "--root",
                str(root),
                "--run",
                str(out / "scoped"),
                "--expected-root",
                args.expected_root,
                "--expected-child",
                args.expected_child,
            ],
        )
        gate = json.loads((out / "scoped/gate.json").read_text())
        assert gate["status"] == "PASS" and gate["source_unchanged"]
        assert gate["junit"] == dict(
            tests=args.expected_tests, failures=0, errors=0, skipped=0
        )
        final_hashes = hashes()
        save(out / "new_source_after.json", final_hashes)
        assert initial_hashes == final_hashes and identity() == before
        state.update(
            status="PASS",
            identity=before,
            junit=gate["junit"],
            source_unchanged=True,
            source_files=gate["source_files"],
            static_files=gate["static_files"] + len(files),
            new_static_files=len(files),
            inherited_import_order_exceptions=gate["inherited_import_order_exceptions"],
            excluded_preexisting_failure=gate["excluded_preexisting_failure"],
            existing_gate_sha256=hashlib.sha256(helper.read_bytes()).hexdigest(),
        )
    except BaseException as error:
        state.update(status="FAIL", error=repr(error))
        with (out / "traceback.txt").open("x") as stream:
            traceback.print_exc(file=stream)
    save(out / "gate.json", state)
    print(json.dumps(state, indent=2), flush=True)
    return 0 if state["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
