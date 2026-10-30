#!/usr/bin/env bash
set -uo pipefail
cd /workspace/work/psm-wma-inflight-snapshot-formal
task_evidence=/workspace/work/inflight-snapshot-evidence/author-full-after-code-review
test ! -e "$task_evidence" || exit 99
export CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTEST_ADDOPTS=''
export PYTHONPATH="$PWD:$PWD/cosmos-framework:$PWD/scripts"
/workspace/.venvs/psm-wma-cpu/bin/python \
  tools/v3/run_eval_v2_batch_b2_cpu_gate.py \
  --root-worktree /workspace/work/psm-wma-inflight-snapshot-formal \
  --expected-root a139b5a35877a79e0a56c2208f3002f731972b11 \
  --expected-child 0ae313e329d290fc6b8a50fda1112820fb7ac485 \
  --evidence-dir "$task_evidence" \
  2>&1 | tee "$task_evidence.console.log"
task_exit=${PIPESTATUS[0]}
printf '%s\n' "$task_exit" > "$task_evidence.shell-exit.txt"
exit "$task_exit"
