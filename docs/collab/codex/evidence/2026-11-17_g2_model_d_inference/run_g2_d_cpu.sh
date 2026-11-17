#!/usr/bin/env bash
set -uo pipefail
PSM_G2_D_EVIDENCE_DIR="${1:?evidence directory required (run from Child root)}"
mkdir -p "$PSM_G2_D_EVIDENCE_DIR"
export PYTHONPATH=.
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
PSM_G2_D_PYTHON="${PSM_G2_D_PYTHON:-/workspace/.venvs/psm-wma-cpu/bin/python}"
"$PSM_G2_D_PYTHON" -m pytest -q -c /dev/null --rootdir=. --noconftest -p no:cacheprovider \
  cosmos_framework/inference/g2_session_cache_test.py \
  cosmos_framework/inference/g2_policy_conditions_test.py \
  cosmos_framework/inference/g2_text_kv_cache_test.py \
  cosmos_framework/inference/g2_model_hooks_test.py \
  cosmos_framework/scripts/g2_policy_server_test.py \
  cosmos_framework/inference/robocasa_session_transactions_test.py \
  cosmos_framework/inference/robocasa_batch_transactions_test.py \
  cosmos_framework/inference/local_memory_online_test.py \
  cosmos_framework/scripts/action_policy_server_robocasa_phase6_test.py \
  cosmos_framework/scripts/robocasa_transactions_b1_test.py \
  cosmos_framework/model/generator/mot/inference_text_kv_memory_test.py \
  cosmos_framework/model/generator/mot/prefix_text_kv_memory_test.py \
  cosmos_framework/data/generator/action/utils/static_task_text_test.py \
  cosmos_framework/model/generator/mot/g2_contracts_test.py \
  cosmos_framework/model/generator/mot/g2_core_test.py \
  cosmos_framework/model/generator/mot/global_memory_test.py \
  cosmos_framework/model/generator/mot/global_spatial_test.py \
  --junitxml="$PSM_G2_D_EVIDENCE_DIR/junit.xml" \
  > "$PSM_G2_D_EVIDENCE_DIR/pytest.log" 2>&1
PSM_G2_D_STATUS=$?
printf '%s\n' "$PSM_G2_D_STATUS" > "$PSM_G2_D_EVIDENCE_DIR/exit-status.txt"
exit "$PSM_G2_D_STATUS"
