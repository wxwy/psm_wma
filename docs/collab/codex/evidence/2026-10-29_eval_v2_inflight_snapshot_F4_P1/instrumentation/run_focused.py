"""Freeze a bounded RED/GREEN command and raw evidence outside source trees."""

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
phase, source = sys.argv[1:3]
assert phase in {"red", "green"}
root = Path(source).resolve()
out = BASE / (sys.argv[3] if len(sys.argv) == 4 else phase)
out.mkdir()
python = "/workspace/.venvs/psm-wma-cpu/bin/python"
tests = ["tools/v3/eval_v2_production_tests/runtime_progress_test.py"]
if phase == "green":
    tests += [
        "tools/v3/eval_v2_production_tests/runtime_test.py::test_real_runtime_rounds_native_Core_then_resume_no_model_or_env_work",
        "tools/v3/eval_v2_production_tests/scheduler_test.py::test_three_asynchronous_workers_same_round_parallel_with_strict_barrier",
    ]
overrides = {
    "CUDA_VISIBLE_DEVICES": "", "COSMOS_DEVICE": "cpu", "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1", "LD_LIBRARY_PATH": "", "PYTHONDONTWRITEBYTECODE": "1",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "",
    "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
    "HF_HOME": str(out / "cache/hf"), "MPLCONFIGDIR": str(out / "cache/mpl"),
    "XDG_CACHE_HOME": str(out / "cache/xdg"),
    "PYTHONPATH": f"{root}:{root}/cosmos-framework:{root}/scripts",
}
env = dict(os.environ, **overrides)
args = [python, "-m", "pytest", "-q", "-s", "--tb=long",
        f"--basetemp={out}/tmp", f"--junitxml={out}/junit.xml",
        "-o", f"cache_dir={out}/cache/pytest", *tests]
watched = json.loads(Path("/workspace/work/ready-startup-evidence/author-full-after-review/source_sha256.json").read_text())
watched[tests[0]] = None


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def snapshot():
    return {
        "root": git(root, "rev-parse", "HEAD"),
        "child": git(root / "cosmos-framework", "rev-parse", "HEAD"),
        "gitlink": git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2],
        "root_status": git(root, "status", "--porcelain=v1", "--untracked-files=all"),
        "child_status": git(root / "cosmos-framework", "status", "--porcelain=v1", "--untracked-files=all"),
        "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in watched},
    }


before = snapshot()
assert before["child"] == before["gitlink"] == "0ae313e329d290fc6b8a50fda1112820fb7ac485"
if phase == "green":
    assert before["root_status"] == before["child_status"] == ""
metadata = {"phase": phase, "utc_start": datetime.now(timezone.utc).isoformat(),
            "cwd": str(root), "argv": args, "environment_overrides": overrides,
            "python_version": sys.version, "source_before": before}
(out / "execution_before.json").write_text(json.dumps(metadata, indent=2) + "\n")
started = time.monotonic()
with (out / "console.log").open("w") as stream:
    result = subprocess.run(args, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
(out / "shell-exit.txt").write_text(f"{result.returncode}\n")
after = snapshot()
assert before == after
metadata.update({"utc_end": datetime.now(timezone.utc).isoformat(),
                 "duration_s": time.monotonic() - started,
                 "shell_exit": result.returncode, "source_after": after,
                 "source_unchanged": True})
(out / "execution.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(json.dumps({"phase": phase, "root": before["root"], "shell_exit": result.returncode,
                  "duration_s": metadata["duration_s"], "source_unchanged": True}))
sys.exit(result.returncode)
