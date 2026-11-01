"""Development-only Python3.13 CPU fault tests, with isolated output/caches."""
import os
from pathlib import Path
import subprocess
import sys

root = Path("/workspace/psm-wma-eval-render-media")
child = root / "cosmos-framework"
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/psm-eval-render-media-20261101/media_development_1")
out.mkdir(exist_ok=False)
env = dict(os.environ, CUDA_VISIBLE_DEVICES="", COSMOS_DEVICE="cpu", MUJOCO_GL="osmesa", PYOPENGL_PLATFORM="osmesa",
           HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1", LD_LIBRARY_PATH="",
           PYTHONPATH=os.pathsep.join(map(str, [root, root / "scripts", child])),
           HF_HOME=str(out / "cache/hf"), MPLCONFIGDIR=str(out / "cache/mpl"), XDG_CACHE_HOME=str(out / "cache/xdg"),
           RUFF_CACHE_DIR=str(out / "cache/ruff"), OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


def run(name, args, cwd=root):
    r = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    (out / (name + ".log")).write_bytes(r.stdout)
    print(name, r.returncode, flush=True)
    if r.returncode:
        print(r.stdout.decode(errors="replace")[-10000:], flush=True)
        raise SystemExit(r.returncode)


ruff = ["/workspace/.venvs/psm-wma-cpu/bin/python", "-m", "ruff"]
root_files = ["scripts/robocasa_eval_v2_processes.py", "scripts/robocasa_eval_v2/runtime.py",
              "tools/v3/eval_v2_batch_tests/media_cleanup_test.py", "tools/v3/eval_v2_batch_tests/media_process_cleanup_test.py"]
child_files = ["cosmos_framework/evaluation/robocasa_v2/media.py", "cosmos_framework/simulation/robocasa/eval_v2_adapter.py"]
run("root_format", ruff + ["format", *root_files])
run("child_format", ruff + ["format", *child_files], child)
run("root_ruff", ruff + ["check", *root_files])
run("child_ruff", ruff + ["check", *child_files], child)
run("python_version", [sys.executable, "--version"])
run("pytest", [sys.executable, "-m", "pytest", "--noconftest", "-c", "/dev/null", "-q", "-s", "-x", "-p", "no:cacheprovider",
               f"--rootdir={root}", "tools/v3/eval_v2_batch_tests/media_cleanup_test.py", "tools/v3/eval_v2_batch_tests/media_process_cleanup_test.py",
               f"--basetemp={out / 'pytest_tmp'}", f"--junitxml={out / 'junit.xml'}"])
