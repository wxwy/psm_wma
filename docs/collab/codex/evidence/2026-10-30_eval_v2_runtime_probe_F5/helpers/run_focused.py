"""Run the bounded F5 persistence checks with immutable external raw evidence."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
label, directory = sys.argv[1:3]
root = Path(directory).resolve()
out = BASE / label
out.mkdir()
test_file = "tools/v3/eval_v2_production_tests/runtime_evidence_test.py"
tests = sys.argv[3:] or [test_file,
    "tools/v3/eval_v2_production_tests/entry_test.py",
    "tools/v3/eval_v2_production_tests/store_test.py"]
watched = ["scripts/robocasa_eval_v2/cli.py", "scripts/robocasa_eval_v2/identity.py",
           "scripts/robocasa_eval_v2/runtime.py", "scripts/robocasa_eval_v2/resources.py",
           "scripts/robocasa_vendor.py", "scripts/robocasa_episode_resume/model_identity.py",
           "tools/v3/eval_v2_production_tests/entry_test.py",
           "tools/v3/eval_v2_production_tests/store_test.py", test_file,
           "cosmos-framework/cosmos_framework/evaluation/robocasa_v2/store.py"]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def snapshot():
    return {"root": git(root, "rev-parse", "HEAD"),
            "child": git(root / "cosmos-framework", "rev-parse", "HEAD"),
            "gitlink": git(root, "rev-parse", "HEAD:cosmos-framework"),
            "root_status": git(root, "status", "--porcelain=v1"),
            "child_status": git(root / "cosmos-framework", "status", "--porcelain=v1"),
            "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                              for name in watched}}


overrides = {"CUDA_VISIBLE_DEVICES": "", "COSMOS_DEVICE": "cpu", "HF_HUB_OFFLINE": "1",
             "TRANSFORMERS_OFFLINE": "1", "LD_LIBRARY_PATH": "", "PYTHONDONTWRITEBYTECODE": "1",
             "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "",
             "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
             "HF_HOME": str(out / "cache/hf"), "XDG_CACHE_HOME": str(out / "cache/xdg"),
             "MPLCONFIGDIR": str(out / "cache/mpl"),
             "PYTHONPATH": f"{root}:{root}/cosmos-framework:{root}/scripts"}
args = ["/workspace/.venvs/psm-wma-cpu/bin/python", "-m", "pytest", "--noconftest",
        "-c", "/dev/null", f"--rootdir={root}", "-p", "no:cacheprovider", "-q", "-s", "--tb=long",
        f"--basetemp={out}/tmp", f"--junitxml={out}/junit.xml", *tests]
before = snapshot()
if label.startswith("final"):
    assert before["root_status"] == before["child_status"] == ""
    assert before["gitlink"] == before["child"]
metadata = {"label": label, "cwd": str(root), "argv": args, "environment_overrides": overrides,
            "source_before": before}
(out / "before.json").write_text(json.dumps(metadata, indent=2) + "\n")
started = time.monotonic()
with (out / "console.log").open("w") as stream:
    result = subprocess.run(args, cwd=root, env=dict(os.environ, **overrides),
                            stdout=stream, stderr=subprocess.STDOUT)
(out / "shell-exit.txt").write_text(f"{result.returncode}\n")
after = snapshot()
assert before == after, "Source changed during focused test execution"
metadata.update({"source_after": after, "source_unchanged": True,
                 "duration_s": time.monotonic() - started, "shell_exit": result.returncode})
(out / "execution.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(json.dumps({"label": label, "shell_exit": result.returncode,
                  "duration_s": metadata["duration_s"], "source_unchanged": True}))
sys.exit(result.returncode)
