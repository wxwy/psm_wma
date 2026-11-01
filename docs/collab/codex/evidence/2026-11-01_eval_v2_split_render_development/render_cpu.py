"""Development CPU check; dirty source hashes retained, not a Formal Gate."""

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path("/workspace/psm-wma-eval-render-media")
child = root / "cosmos-framework"
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/psm-eval-render-media-20261101/render_development_1")
out.mkdir(exist_ok=False)
root_files = ["scripts/robocasa_eval_v2/config.py", "scripts/robocasa_eval_v2/runtime.py",
              "scripts/robocasa_eval_v2/resources.py", "scripts/robocasa_eval_v2/cli.py",
              "tools/v3/eval_v2_batch_tests/render_mapping_test.py", "tools/v3/eval_v2_batch_tests/render_devices_test.py",
              "tools/v3/eval_v2_production_tests/worker_test.py"]
child_files = ["cosmos_framework/simulation/robocasa/render_devices.py",
               "cosmos_framework/simulation/robocasa/eval_v2_worker.py", "cosmos_framework/simulation/robocasa/eval_v2_slot.py"]
env = {**os.environ, "PYTHONPATH": os.pathsep.join(map(str, [root, root / "scripts", child])),
       "CUDA_VISIBLE_DEVICES": "", "COSMOS_DEVICE": "cpu", "MUJOCO_GL": "osmesa", "PYOPENGL_PLATFORM": "osmesa",
       "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1", "LD_LIBRARY_PATH": "",
       "HF_HOME": str(out / "cache/hf"), "MPLCONFIGDIR": str(out / "cache/mpl"), "XDG_CACHE_HOME": str(out / "cache/xdg"),
       "RUFF_CACHE_DIR": str(out / "cache/ruff"), "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def run(name, args, cwd=root):
    result = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    (out / (name + ".log")).write_bytes(result.stdout)
    print(name, result.returncode, flush=True)
    if result.returncode:
        print(result.stdout.decode(errors="replace")[-12000:], flush=True)
        raise SystemExit(result.returncode)


run("root_format", [sys.executable, "-m", "ruff", "format", *root_files])
run("child_format", [sys.executable, "-m", "ruff", "format", *child_files], child)
files = [*(root / f for f in root_files), *(child / f for f in child_files)]
before = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
(out / "dirty_source_sha256.json").write_text(json.dumps(before, indent=2) + "\n")
(out / "root_development.diff").write_bytes(subprocess.check_output(["git", "diff"], cwd=root))
(out / "child_development.diff").write_bytes(subprocess.check_output(["git", "diff"], cwd=child))
run("root_check", [sys.executable, "-m", "ruff", "check", *root_files])
run("child_check", [sys.executable, "-m", "ruff", "check", *child_files], child)
for f in files:
    ast.parse(f.read_text())
run("pytest", [sys.executable, "-m", "pytest", "--noconftest", "-c", "/dev/null", "-q", "-s", "-x", "-p", "no:cacheprovider",
               f"--rootdir={root}", "tools/v3/eval_v2_batch_tests/render_mapping_test.py", "tools/v3/eval_v2_batch_tests/render_devices_test.py",
               "tools/v3/eval_v2_production_tests/worker_test.py", "tools/v3/eval_v2_batch_tests/rollout_policy_test.py",
               "tools/v3/eval_v2_batch_tests/config_test.py",
               "tools/v3/eval_v2_production_tests/native_test.py::test_broken_media_never_changes_environment_success_or_Core_commit",
               "tools/v3/eval_v2_production_tests/native_test.py::test_horizon_failure_with_high_reward_is_valid_and_never_retried",
               f"--basetemp={out / 'pytest_tmp'}", f"--junitxml={out / 'junit.xml'}"])
assert before == {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
x = ET.parse(out / "junit.xml").getroot()
print(json.dumps({"development_only": True, "tests": len(list(x.iter("testcase"))), "failures": len(list(x.iter("failure"))),
                  "errors": len(list(x.iter("error"))), "skipped": len(list(x.iter("skipped"))), "source_unchanged_after_format": True}), flush=True)
