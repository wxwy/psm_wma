"""Scoped author CPU checks; --formal requires a clean, exact Root/Child pair."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

p = argparse.ArgumentParser()
p.add_argument("output")
p.add_argument("--format", action="store_true")
p.add_argument("--formal", action="store_true")
a = p.parse_args()
root = Path("/workspace/psm-wma-eval-render-media")
child = root / "cosmos-framework"
out = Path(a.output)
out.mkdir(exist_ok=False)
root_files = ["scripts/robocasa_eval_v2/config.py", "scripts/robocasa_eval_v2/runtime.py",
              "scripts/robocasa_eval_v2/resources.py", "scripts/robocasa_eval_v2/cli.py",
              "scripts/robocasa_eval_v2/identity.py", "scripts/robocasa_eval_v2_processes.py",
              "tools/v3/eval_v2_batch_tests/render_mapping_test.py", "tools/v3/eval_v2_batch_tests/render_devices_test.py",
              "tools/v3/eval_v2_batch_tests/media_cleanup_test.py", "tools/v3/eval_v2_batch_tests/media_process_cleanup_test.py",
              "tools/v3/eval_v2_production_tests/worker_test.py"]
child_files = ["cosmos_framework/evaluation/robocasa_v2/contract.py", "cosmos_framework/evaluation/robocasa_v2/media.py",
               "cosmos_framework/simulation/robocasa/render_devices.py", "cosmos_framework/simulation/robocasa/eval_v2_adapter.py",
               "cosmos_framework/simulation/robocasa/eval_v2_worker.py", "cosmos_framework/simulation/robocasa/eval_v2_slot.py"]
test_nodes = ["tools/v3/eval_v2_batch_tests/render_mapping_test.py", "tools/v3/eval_v2_batch_tests/render_devices_test.py",
              "tools/v3/eval_v2_batch_tests/media_cleanup_test.py", "tools/v3/eval_v2_batch_tests/media_process_cleanup_test.py",
              "tools/v3/eval_v2_production_tests/worker_test.py", "tools/v3/eval_v2_production_tests/slot_test.py",
              "tools/v3/eval_v2_production_tests/process_test.py", "tools/v3/eval_v2_batch_tests/rollout_policy_test.py",
              "tools/v3/eval_v2_batch_tests/config_test.py", "tools/v3/eval_v2_production_tests/native_test.py",
              "tools/v3/eval_v2_production_tests/media_test.py::test_stalled_encoder_is_bounded_and_requests_owned_task_cleanup",
              "tools/v3/eval_v2_production_tests/media_test.py::test_optional_generated_video_bounds_do_not_throw_into_policy"]
env_fields = dict(CUDA_VISIBLE_DEVICES="", COSMOS_DEVICE="cpu", MUJOCO_GL="osmesa", PYOPENGL_PLATFORM="osmesa",
                  HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1", LD_LIBRARY_PATH="",
                  PYTHONPATH=os.pathsep.join(map(str, [root, root / "scripts", child])),
                  HF_HOME=str(out / "cache/hf"), MPLCONFIGDIR=str(out / "cache/mpl"), XDG_CACHE_HOME=str(out / "cache/xdg"),
                  RUFF_CACHE_DIR=str(out / "cache/ruff"), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
env = dict(os.environ, **env_fields)
commands = []


def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def version():
    return dict(root=git(root, "rev-parse", "HEAD"), child=git(child, "rev-parse", "HEAD"),
                gitlink=git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2],
                root_status=git(root, "status", "--porcelain"), child_status=git(child, "status", "--porcelain"))


before_version = version()
if a.formal:
    assert not a.format
    assert before_version["child"] == before_version["gitlink"]
    assert before_version["root_status"] == before_version["child_status"] == ""
(out / "invocation.json").write_text(json.dumps(dict(command=[sys.executable, *sys.argv], cwd=str(root), environment=env_fields,
    python=sys.version, formal=a.formal, versions=before_version, inputs="synthetic observations/frames, CPU subprocesses, fake EGL/NVML/HTTP model; no model/data/checkpoint", expected="all scoped tests/static pass; exact source unchanged"), indent=2) + "\n")


def run(name, args, cwd=root):
    started = time.monotonic()
    r = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=240)
    (out / (name + ".log")).write_bytes(r.stdout)
    commands.append(dict(name=name, command=args, cwd=str(cwd), exit_code=r.returncode, elapsed_s=time.monotonic()-started))
    (out / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    print(name, r.returncode, flush=True)
    if r.returncode:
        print(r.stdout.decode(errors="replace")[-9000:], flush=True)
        raise SystemExit(r.returncode)


ruff = ["/workspace/.venvs/psm-wma-cpu/bin/python", "-m", "ruff"]
run("ruff_version", ruff + ["--version"])
if a.format:
    run("root_format_write", ruff + ["format", *root_files])
    run("child_format_write", ruff + ["format", *child_files], child)
run("root_ruff", ruff + ["check", *root_files])
run("child_ruff", ruff + ["check", *child_files], child)
run("root_format", ruff + ["format", "--check", *root_files])
run("child_format", ruff + ["format", "--check", *child_files], child)
run("root_diff_check", ["git", "diff", "--check"])
run("child_diff_check", ["git", "diff", "--check"], child)
sources = [*(root / path for path in root_files), *(child / path for path in child_files)]
sources.extend(root / node.split("::")[0] for node in test_nodes)
sources = sorted(set(sources))
hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
(out / "source_sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
for source in sources:
    ast.parse(source.read_text(), filename=str(source))
(out / "syntax.log").write_text(f"PASS: {len(sources)} files parsed with Python {sys.version}\n")
run("pytest", [sys.executable, "-m", "pytest", "--noconftest", "-c", "/dev/null", "-q", "-s", "-x", "-p", "no:cacheprovider",
               f"--rootdir={root}", *test_nodes, f"--basetemp={out / 'pytest_tmp'}", f"--junitxml={out / 'junit.xml'}"])
assert hashes == {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
assert before_version == version()
x = ET.parse(out / "junit.xml").getroot()
counts = {name: len(list(x.iter(tag))) for name, tag in [("tests", "testcase"), ("failures", "failure"), ("errors", "error"), ("skipped", "skipped")]}
assert counts["failures"] == counts["errors"] == counts["skipped"] == 0
gate = dict(status="AUTHOR_SCOPED_CPU_PASS" if a.formal else "DEVELOPMENT_CPU_PASS", **counts, **before_version,
            source_unchanged=True, python=sys.version, ruff="0.12.7", real_gpu=False, real_egl=False,
            real_simulator=False, real_model=False, real_ffmpeg=False, independent_ds=False,
            scope="split renderer and Media lifecycle, relevant existing config/slot/native/process/video-policy regressions")
(out / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
print(json.dumps(gate), flush=True)
