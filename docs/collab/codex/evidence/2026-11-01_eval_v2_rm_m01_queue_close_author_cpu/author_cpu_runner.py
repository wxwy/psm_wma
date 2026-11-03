"""RM-M01 focused CPU RED/GREEN; formal mode requires an exact clean Git pair."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

mode, output = sys.argv[1:]
assert mode in ("red", "green", "formal")
root = Path("/workspace/psm-wma-eval-render-media")
child = root / "cosmos-framework"
out = Path(output)
out.mkdir(exist_ok=False)
test_path = "tools/v3/eval_v2_batch_tests/media_queue_close_fault_test.py"
media_path = "cosmos_framework/evaluation/robocasa_v2/media.py"
files = [root / test_path, child / media_path,
         root / "tools/v3/eval_v2_batch_tests/media_cleanup_test.py",
         root / "tools/v3/eval_v2_production_tests/native_test.py",
         root / "tools/v3/eval_v2_production_tests/store_test.py",
         child / "cosmos_framework/simulation/robocasa/eval_v2_adapter.py"]
overrides = dict(CUDA_VISIBLE_DEVICES="", COSMOS_DEVICE="cpu", MUJOCO_GL="osmesa", PYOPENGL_PLATFORM="osmesa",
                 HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1", LD_LIBRARY_PATH="",
                 HF_HOME=str(out / "cache/hf"), MPLCONFIGDIR=str(out / "cache/mpl"), XDG_CACHE_HOME=str(out / "cache/xdg"),
                 RUFF_CACHE_DIR=str(out / "cache/ruff"), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                 PYTHONPATH=os.pathsep.join(map(str, [root, root / "scripts", child])))
env = dict(os.environ, **overrides)
commands = []


def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd, timeout=30).decode().strip()


def run(name, args, cwd=root, expected=0):
    start = time.monotonic()
    r = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    (out / f"{name}.log").write_bytes(r.stdout)
    commands.append(dict(name=name, command=args, cwd=str(cwd), exit_code=r.returncode, elapsed_s=time.monotonic()-start))
    (out / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    print(f"{name}: exit={r.returncode} expected={expected}", flush=True)
    if r.returncode != expected:
        print(r.stdout.decode(errors="replace")[-7000:], flush=True)
        raise SystemExit(r.returncode or 1)


def versions():
    return dict(root=git(root, "rev-parse", "HEAD"), child=git(child, "rev-parse", "HEAD"),
                gitlink=git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2],
                root_status=git(root, "status", "--porcelain"), child_status=git(child, "status", "--porcelain"))


ruff = ["/workspace/.venvs/psm-wma-cpu/bin/python", "-m", "ruff"]
run("ruff_version", ruff + ["--version"])
if mode == "red":
    run("test_format_write", ruff + ["format", test_path])
run("root_ruff", ruff + ["check", test_path])
run("child_ruff", ruff + ["check", media_path], child)
run("root_format", ruff + ["format", "--check", test_path])
run("child_format", ruff + ["format", "--check", media_path], child)
before = versions()
if mode == "formal":
    assert before["root_status"] == before["child_status"] == ""
    assert before["gitlink"] == before["child"]
if mode == "red":
    assert before["child"] == "d3b2a29b978ff4abef800b9e71fab4422b7a0d23" and before["child_status"] == ""
    shutil.copyfile(root / test_path, out / "frozen_test_before_red.py")
hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
(out / "source_before.json").write_text(json.dumps(hashes, indent=2) + "\n")
(out / "invocation.json").write_text(json.dumps(dict(command=[sys.executable, *sys.argv], cwd=str(root), mode=mode,
    environment=overrides, python=sys.version, versions=before, input="synthetic stopped Queue/process/fd and HTTP model/env doubles; no assets/checkpoint",
    expected="red10 failures+4passes on frozen old production; green/formal29passes, no error/skip", frozen_test_sha256=hashes[test_path]), indent=2) + "\n")
for path in files:
    ast.parse(path.read_text(), filename=str(path))
(out / "syntax.log").write_text(f"PASS: {len(files)} files parsed on {sys.version}\n")
nodes = [test_path]
if mode != "red":
    nodes += ["tools/v3/eval_v2_batch_tests/media_cleanup_test.py",
              "tools/v3/eval_v2_production_tests/native_test.py::test_broken_media_never_changes_environment_success_or_Core_commit",
              "tools/v3/eval_v2_production_tests/native_test.py::test_horizon_failure_with_high_reward_is_valid_and_never_retried"]
run("pytest", [sys.executable, "-m", "pytest", "--noconftest", "-c", "/dev/null", "-q", "-s", "-p", "no:cacheprovider",
               f"--rootdir={root}", *nodes, f"--basetemp={out / 'pytest_tmp'}", f"--junitxml={out / 'junit.xml'}"], expected=1 if mode == "red" else 0)
x = ET.parse(out / "junit.xml").getroot()
cases = list(x.iter("testcase"))
counts = dict(tests=len(cases), failures=len(list(x.iter("failure"))), errors=len(list(x.iter("error"))), skipped=len(list(x.iter("skipped"))))
assert counts == (dict(tests=14, failures=10, errors=0, skipped=0) if mode == "red" else dict(tests=29, failures=0, errors=0, skipped=0)), counts
if mode == "red":
    for case in cases:
        if case.find("failure") is not None:
            assert case.attrib["name"].startswith(("test_unknown_queue_error_", "test_native_adapter_reports_"))
            assert "assert False is True" in case.find("failure").attrib["message"]
assert hashes == {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
assert before == versions()
result = dict(status="EXPECTED_OLD_PRODUCTION_RED" if mode == "red" else "AUTHOR_TARGETED_CPU_PASS", mode=mode, **counts, **before,
              test_sha256=hashes[test_path], media_sha256=hashes["cosmos-framework/"+media_path], source_unchanged_during_test=True,
              python=sys.version, ruff="0.12.7", real_gpu=False, real_egl=False, real_ffmpeg=False, real_model=False,
              independent_ds=False, full192_rerun=False)
(out / "gate.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result), flush=True)
