#!/usr/bin/env bash
set -euo pipefail
task_base=/workspace/work/ready-startup-evidence/synthetic900-diagnostic-once
task_run="$task_base/run"
task_python=/workspace/.venvs/psm-wma-cpu/bin/python
cd /workspace/work/psm-wma-ready-startup-formal
test ! -e "$task_run" || exit 99
export CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTEST_ADDOPTS=''
export HF_HOME="$task_run/cache/hf" MPLCONFIGDIR="$task_run/cache/mpl" XDG_CACHE_HOME="$task_run/cache/xdg"
export RUFF_CACHE_DIR="$task_run/cache/ruff" TRITON_CACHE_DIR="$task_run/cache/triton"
export PYTHONPATH="$PWD:$PWD/cosmos-framework:$PWD/scripts:$task_base"
export SYNTHETIC900_DIAGNOSTIC_DIR="$task_run"
"$task_python" "$task_base/source_snapshot.py" before
ps -eo pid,ppid,pgid,stat,comm > "$task_run/os_before.txt"
cp "$task_base/run_once.sh" "$task_run/launch.sh"
set +e
"$task_python" -m pytest \
  -p capture_runtime_traceback -vv -s --tb=long \
  --basetemp="$task_run/tmp" \
  --junitxml="$task_run/diagnostic.xml" \
  -o cache_dir="$task_run/cache/pytest" \
  tools/v3/eval_v2_production_tests/scheduler_test.py::test_900_exact_episode_major_dispatch_real_store_path_and_index_no_model_per_episode \
  2>&1 | tee "$task_run/console.log"
task_exit=${PIPESTATUS[0]}
set -e
printf '%s\n' "$task_exit" > "$task_run/shell-exit.txt"
ps -eo pid,ppid,pgid,stat,comm > "$task_run/os_after.txt"
"$task_python" "$task_base/source_snapshot.py" after
exit "$task_exit"
