"""Focused Owner GPU resource-policy CPU checks; no real GPU/driver probes."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

mode, output = sys.argv[1:]
assert mode in ("development", "formal")
root = Path("/workspace/psm-wma-eval-render-media")
child = root / "cosmos-framework"
out = Path(output)
out.mkdir(exist_ok=False)
source_files = ["scripts/robocasa_eval_v2/resources.py", "tools/v3/eval_v2_batch_tests/render_mapping_test.py",
                "tools/v3/eval_v2_production_tests/entry_test.py", "tools/v3/eval_v2_batch_tests/owner_gpu_resource_policy_test.py"]
test_nodes = ["tools/v3/eval_v2_batch_tests/owner_gpu_resource_policy_test.py",
              "tools/v3/eval_v2_batch_tests/render_mapping_test.py", "tools/v3/eval_v2_batch_tests/render_devices_test.py",
              "tools/v3/eval_v2_production_tests/entry_test.py::test_config_and_resource_gates_no_protected_writes",
              "tools/v3/eval_v2_production_tests/entry_test.py::test_shared_gpu_has_no_occupancy_admission_but_retains_missing_device_safety"]
files = sorted(set([*(root / p for p in source_files), *(root / p.split("::")[0] for p in test_nodes),
                    child / "cosmos_framework/simulation/robocasa/render_devices.py"]))
overrides = dict(CUDA_VISIBLE_DEVICES="", COSMOS_DEVICE="cpu", MUJOCO_GL="osmesa", PYOPENGL_PLATFORM="osmesa",
    HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1", LD_LIBRARY_PATH="",
    HF_HOME=str(out / "cache/hf"), MPLCONFIGDIR=str(out / "cache/mpl"), XDG_CACHE_HOME=str(out / "cache/xdg"),
    RUFF_CACHE_DIR=str(out / "cache/ruff"), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
    PYTHONPATH=os.pathsep.join(map(str, [root, root / "scripts", child])))
env = dict(os.environ, **overrides)
commands = []


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, timeout=30).decode().strip()


def versions():
    return dict(root=git(root, "rev-parse", "HEAD"), child=git(child, "rev-parse", "HEAD"),
        gitlink=git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2],
        root_status=git(root, "status", "--porcelain"), child_status=git(child, "status", "--porcelain"))


def run(name, args, cwd=root):
    started = time.monotonic()
    r = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    (out / f"{name}.log").write_bytes(r.stdout)
    commands.append(dict(name=name, command=args, cwd=str(cwd), exit_code=r.returncode, elapsed_s=time.monotonic()-started))
    (out / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    print(name, r.returncode, flush=True)
    if r.returncode:
        print(r.stdout.decode(errors="replace")[-6500:], flush=True)
        raise SystemExit(r.returncode)


ruff = ["/workspace/.venvs/psm-wma-cpu/bin/python", "-m", "ruff"]
run("ruff_version", ruff + ["--version"])
if mode == "development":
    run("format_write", ruff + ["format", *source_files])
run("ruff", ruff + ["check", *source_files])
run("format", ruff + ["format", "--check", *source_files])
before = versions()
assert before["child"] == before["gitlink"] == "9a8cd6183424bfce245fbca393ca25ed59919ea6"
assert before["child_status"] == ""
if mode == "formal":
    assert before["root_status"] == ""
hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(out / "source_sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
(out / "invocation.json").write_text(json.dumps(dict(mode=mode, command=[sys.executable, *sys.argv], cwd=str(root), environment=overrides,
    python=sys.version, versions=before, inputs="synthetic nvidia-smi/own-RSS/EGL/HTTP/metadata doubles; no real model/data/DCP",
    expected="all focused tests/static pass, unchanged source and Child, no driver/GPU/process-list access"), indent=2) + "\n")
for p in files:
    ast.parse(p.read_text(), filename=str(p))
(out / "syntax.log").write_text(f"PASS: {len(files)} files parsed with {sys.version}\n")
run("pytest", [sys.executable, "-m", "pytest", "--noconftest", "-c", "/dev/null", "-q", "-s", "-x", "-p", "no:cacheprovider",
               f"--rootdir={root}", *test_nodes, f"--basetemp={out / 'pytest_tmp'}", f"--junitxml={out / 'junit.xml'}"])
assert hashes == {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
assert before == versions()
x = ET.parse(out / "junit.xml").getroot()
counts = {name: len(list(x.iter(tag))) for name, tag in [("tests", "testcase"), ("failures", "failure"), ("errors", "error"), ("skipped", "skipped")]}
assert counts == dict(tests=70, failures=0, errors=0, skipped=0), counts
gate = dict(status="AUTHOR_FOCUSED_CPU_PASS", **counts, **before, mode=mode, source_unchanged=True,
    python=sys.version, ruff="0.12.7", real_gpu=False, real_nvml=False, real_egl=False, real_ffmpeg=False,
    real_simulator=False, independent_ds=False, child_unchanged=True, historical_suites_rerun=False)
(out / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
print(json.dumps(gate), flush=True)
