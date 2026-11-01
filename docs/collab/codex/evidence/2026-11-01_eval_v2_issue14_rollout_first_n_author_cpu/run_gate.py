"""Frozen author CPU Gate for Issue14; never launches a model or simulator."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser()
p.add_argument("--root-worktree", type=Path, required=True)
p.add_argument("--expected-root", required=True)
p.add_argument("--expected-child", required=True)
p.add_argument("--evidence-dir", type=Path, required=True)
a = p.parse_args()
root = a.root_worktree.resolve()
child = root / "cosmos-framework"
out = a.evidence_dir.resolve()
out.mkdir(parents=True, exist_ok=False)
assert not out.is_relative_to(root)


def save(name, value):
    (out / name).write_text(json.dumps(value, indent=2) + "\n")


def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd)


root_files = [
    "scripts/robocasa_eval_v2/config.py",
    "scripts/robocasa_eval_v2/runtime.py",
    "tools/v3/eval_v2_batch_tests/rollout_policy_test.py",
]
adapter = "cosmos_framework/simulation/robocasa/eval_v2_adapter.py"
bindings = []
for directory, ref, files in [
    (root, a.expected_root, root_files + [
        "scripts/robocasa_eval_v2/cli.py",
        "tools/v3/eval_v2_batch_tests/config_test.py",
        "tools/v3/eval_v2_production_tests/native_test.py",
    ]),
    (child, a.expected_child, [adapter,
        "cosmos_framework/evaluation/robocasa_v2/media.py",
        "cosmos_framework/evaluation/robocasa_v2/store.py",
        "cosmos_framework/evaluation/robocasa_v2/contract.py",
        "cosmos_framework/evaluation/robocasa_v2/scheduler.py",
    ]),
]:
    for path in files:
        content = git(directory, "show", f"{ref}:{path}")
        assert (directory / path).read_bytes() == content
        bindings.append({
            "repository": "root" if directory == root else "child",
            "ref": ref, "path": path,
            "blob": git(directory, "rev-parse", f"{ref}:{path}").decode().strip(),
            "sha256": hashlib.sha256(content).hexdigest(),
        })
save("formal_source_bindings.json", bindings)

overrides = {
    "PYTHONPATH": os.pathsep.join(map(str, [root, root / "scripts", child])),
    "PYTHONDONTWRITEBYTECODE": "1", "CUDA_VISIBLE_DEVICES": "", "COSMOS_DEVICE": "cpu",
    "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "LD_LIBRARY_PATH": "",
    "HF_HOME": str(out / "cache/hf"), "MPLCONFIGDIR": str(out / "cache/mpl"),
    "XDG_CACHE_HOME": str(out / "cache/xdg"), "RUFF_CACHE_DIR": str(out / "cache/ruff"),
    "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
}
env = {**os.environ, **overrides}
save("environment.json", {
    "python": sys.version, "platform": platform.platform(), "overrides": overrides,
    "ruff": subprocess.check_output([sys.executable, "-m", "ruff", "--version"], env=env).decode().strip(),
    "pytest": subprocess.check_output([sys.executable, "-m", "pytest", "--version"], env=env).decode().strip(),
    "resources": "CPU-only; loopback HTTP model double; no real model/data/DCP, GPU, simulator, encoder or FFmpeg",
})
gate = {
    "gate": "AUTHOR_ISSUE14_ROLLOUT_FIRST_N_CPU", "status": "RUNNING",
    "identities": {"root": a.expected_root, "child": a.expected_child, "gitlink": a.expected_child},
    "steps": [], "real_GPU_model_data_DCP_server_simulator_FFmpeg": False,
    "active_runtime_or_shared_directory_access": False,
}


def verify_pair():
    assert git(root, "rev-parse", "HEAD").decode().strip() == a.expected_root
    assert git(child, "rev-parse", "HEAD").decode().strip() == a.expected_child
    assert git(root, "rev-parse", "HEAD:cosmos-framework").decode().strip() == a.expected_child
    assert not git(root, "status", "--porcelain")
    assert not git(child, "status", "--porcelain")
    for b in bindings:
        directory = root if b["repository"] == "root" else child
        assert hashlib.sha256((directory / b["path"]).read_bytes()).hexdigest() == b["sha256"]


def step(name, command, cwd=root, timeout=120):
    start = time.monotonic()
    result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    (out / f"{name}.log").write_bytes(result.stdout)
    gate["steps"].append({"name": name, "argv": list(map(str, command)), "cwd": str(cwd),
                          "exit_code": result.returncode, "timeout_s": timeout,
                          "seconds": time.monotonic() - start})
    save("gate.json", gate)
    if result.returncode:
        raise RuntimeError(f"{name} failed: {result.returncode}; see {out / (name + '.log')}")


try:
    verify_pair()
    allowed_root = {
        *root_files, "SESSION.md", "TODO.md", "cosmos-framework",
        "docs/build/PSM-WMA_V3_EvalV2_Rollout_First_N_Issue14_2026-11-01.md",
    }
    changed_root = set(git(root, "diff", "--name-only", "9ba1dd110a4e3e99e717937c2f8d044fa077cdbf", a.expected_root).decode().splitlines())
    changed_child = set(git(child, "diff", "--name-only", "6c83596d6a259e89c4cd3e79424024983426ac3d", a.expected_child).decode().splitlines())
    assert changed_root == allowed_root, sorted(changed_root)
    assert changed_child == {adapter}, sorted(changed_child)
    save("scope_audit.json", {"status": "PASS", "root_changes": sorted(changed_root),
                               "child_changes": sorted(changed_child), "production_files": 3,
                               "all_other_source_unchanged": True})
    (out / "root_implementation.diff").write_bytes(git(root, "diff", "9ba1dd110a4e3e99e717937c2f8d044fa077cdbf", a.expected_root))
    (out / "child_implementation.diff").write_bytes(git(child, "diff", "6c83596d6a259e89c4cd3e79424024983426ac3d", a.expected_child))
    step("root_ruff_check", [sys.executable, "-m", "ruff", "check", *root_files])
    step("root_ruff_format", [sys.executable, "-m", "ruff", "format", "--check", *root_files])
    step("child_ruff_check", [sys.executable, "-m", "ruff", "check", adapter], cwd=child)
    step("child_ruff_format", [sys.executable, "-m", "ruff", "format", "--check", adapter], cwd=child)
    for file in [*(root / path for path in root_files), child / adapter]:
        ast.parse(file.read_text(), filename=str(file))
    gate["syntax_files"] = 4
    step("pytest", [sys.executable, "-m", "pytest", "--noconftest", "-c", "/dev/null", "-q", "-s", "-x", "-p", "no:cacheprovider",
                    f"--rootdir={root}", root_files[2], "tools/v3/eval_v2_batch_tests/config_test.py",
                    "tools/v3/eval_v2_production_tests/native_test.py::test_broken_media_never_changes_environment_success_or_Core_commit",
                    "tools/v3/eval_v2_production_tests/native_test.py::test_horizon_failure_with_high_reward_is_valid_and_never_retried",
                    f"--basetemp={out / 'pytest_tmp'}", f"--junitxml={out / 'junit.xml'}"], timeout=180)
    xml = ET.parse(out / "junit.xml").getroot()
    totals = {"tests": len(list(xml.iter("testcase"))), "failures": len(list(xml.iter("failure"))),
              "errors": len(list(xml.iter("error"))), "skipped": len(list(xml.iter("skipped")))}
    assert totals == {"tests": 69, "failures": 0, "errors": 0, "skipped": 0}, totals
    gate["totals"] = totals
    verify_pair()
    gate.update(status="PASS", source_unchanged=True)
except BaseException as error:
    gate.update(status="FAIL", error=repr(error))
    (out / "gate_failure_traceback.log").write_text(traceback.format_exc())
    raise
finally:
    save("gate.json", gate)
    print(json.dumps(gate, indent=2), flush=True)
