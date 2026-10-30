"""Author-only targeted dual-mode checks with external raw evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

label, directory = sys.argv[1:3]
root = Path(directory).resolve()
out = Path(__file__).parent / label
out.mkdir()
new = ["cosmos-framework/cosmos_framework/inference/robocasa_dual_mode_test.py",
       "tools/v3/eval_v2_batch_tests/dual_mode_test.py"]
old = ["cosmos-framework/cosmos_framework/" + name for name in (
    "inference/robocasa_session_transactions_test.py", "inference/robocasa_batch_transactions_test.py",
    "scripts/robocasa_transactions_b1_test.py", "simulation/robocasa/eval_v2_transactions_test.py")]
tests = sys.argv[3:] or new
if label.startswith("final"):
    tests = new + old + ["tools/v3/eval_v2_batch_tests/runtime_test.py", "tools/v3/eval_v2_batch_tests/config_test.py",
                        "tools/v3/eval_v2_production_tests/contract_test.py", "tools/v3/eval_v2_production_tests/entry_test.py",
                        "tools/v3/eval_v2_production_tests/slot_test.py", "tools/v3/eval_v2_production_tests/worker_test.py",
                        "tools/v3/eval_v2_production_tests/slot_transport_test.py", "tools/v3/eval_v2_production_tests/native_test.py", "tools/v3/eval_v2_production_tests/store_test.py", "tools/v3/eval_v2_production_tests/runtime_progress_test.py"]
def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
def snapshot():
    watched = {root / name for name in ['cosmos-framework/cosmos_framework/inference/robocasa_session_transactions.py', 'cosmos-framework/cosmos_framework/inference/robocasa_batch_transactions.py', 'cosmos-framework/cosmos_framework/inference/robocasa_transaction_client.py', 'cosmos-framework/cosmos_framework/inference/robocasa_transaction_mode.py', 'cosmos-framework/cosmos_framework/scripts/action_policy_server_robocasa.py', 'scripts/eval_robocasa_18task_queue.py', 'cosmos-framework/cosmos_framework/simulation/robocasa/eval_v2_adapter.py', 'cosmos-framework/cosmos_framework/simulation/robocasa/eval_v2_transactions.py', 'cosmos-framework/cosmos_framework/simulation/robocasa/eval_v2_worker.py']}
    for base in ("scripts/robocasa_eval_v2", "tools/v3/eval_v2_batch_tests",
                 "cosmos-framework/cosmos_framework/evaluation/robocasa_v2"):
        watched.update(root.glob(base + "/**/*.py"))
    for repo, prefix in ((root, ""), (root / "cosmos-framework", "cosmos-framework/")):
        for name in git(repo, "diff", "--name-only", "HEAD").splitlines():
            path = root / (prefix + name)
            if path.is_file() and path.suffix == ".py": watched.add(path)
        for name in git(repo, "ls-files", "--others", "--exclude-standard").splitlines():
            path = root / (prefix + name)
            if path.is_file() and path.suffix == ".py": watched.add(path)
    watched.update(root / name.split("::", 1)[0] for name in tests)
    return {"root": git(root, "rev-parse", "HEAD"), "child": git(root / "cosmos-framework", "rev-parse", "HEAD"),
            "gitlink": git(root, "rev-parse", "HEAD:cosmos-framework"),
            "root_status": git(root, "status", "--porcelain=v1"),
            "child_status": git(root / "cosmos-framework", "status", "--porcelain=v1"),
            "sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(watched)}}
overrides = {"CUDA_VISIBLE_DEVICES": "", "COSMOS_DEVICE": "cpu", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
             "LD_LIBRARY_PATH": "", "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "",
             "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
             "HF_HOME": str(out / "cache/hf"), "XDG_CACHE_HOME": str(out / "cache/xdg"), "MPLCONFIGDIR": str(out / "cache/mpl"),
             "PYTHONPATH": f"{root}:{root}/cosmos-framework:{root}/scripts"}
args = [sys.executable, "-m", "pytest", "--noconftest", "-c", "/dev/null", f"--rootdir={root}", "-p", "no:cacheprovider",
        "-q", "-s", "--tb=long", f"--basetemp={out}/tmp", f"--junitxml={out}/junit.xml", *tests]
before = snapshot()
if label.startswith("final"):
    assert before["root_status"] == before["child_status"] == "" and before["gitlink"] == before["child"]
meta = {"cwd": str(root), "argv": args, "environment_overrides": overrides, "source_before": before}
(out / "before.json").write_text(json.dumps(meta, indent=2) + "\n")
start = time.monotonic()
with (out / "console.log").open("w") as f:
    result = subprocess.run(args, cwd=root, env=dict(os.environ, **overrides), stdout=f, stderr=subprocess.STDOUT)
(out / "shell-exit.txt").write_text(str(result.returncode) + "\n")
after = snapshot()
meta.update(shell_exit=result.returncode, duration_s=time.monotonic()-start,
            source_after=after, source_unchanged=before == after)
if (out / "junit.xml").exists():
    cases = list(ET.parse(out / "junit.xml").getroot().iter("testcase"))
    meta["counts"] = {"collected": len(cases), "failures": sum(c.find("failure") is not None for c in cases),
                      "errors": sum(c.find("error") is not None for c in cases), "skipped": sum(c.find("skipped") is not None for c in cases)}
(out / "execution.json").write_text(json.dumps(meta, indent=2) + "\n")
print(json.dumps({k: meta[k] for k in ("shell_exit", "duration_s", "source_unchanged", "counts") if k in meta}))
assert before == after
sys.exit(result.returncode)
