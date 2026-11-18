#!/usr/bin/env bash
set -euo pipefail
G2_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
G2_CPU_PYTHON="${G2_CPU_PYTHON:-/workspace/.venvs/psm-wma-cpu/bin/python}"
cd "${G2_REPO_ROOT}/cosmos-framework"
export CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1
G2_TEST_FILES=(
 cosmos_framework/model/generator/mot/g2_contracts_test.py
 cosmos_framework/model/generator/mot/g2_core_test.py
 cosmos_framework/model/generator/mot/g2_integration_test.py
 cosmos_framework/model/generator/mot/global_memory_test.py
 cosmos_framework/model/generator/mot/global_spatial_test.py
 cosmos_framework/model/generator/mot/memory_prefix_test.py
 cosmos_framework/model/generator/mot/inference_text_kv_memory_test.py
 cosmos_framework/model/generator/mot/local_memory_fsdp_scan_test.py
 cosmos_framework/model/generator/mot/parallelize_unified_mot_test.py
 cosmos_framework/data/generator/sequence_packing/runtime_test.py
 cosmos_framework/data/generator/sequence_packing/packers_test.py
 cosmos_framework/data/generator/action/utils/static_task_text_test.py
 cosmos_framework/data/generator/action/datasets/g2_training_adapter_test.py
 cosmos_framework/inference/g2_session_cache_test.py
 cosmos_framework/inference/g2_policy_conditions_test.py
 cosmos_framework/inference/g2_model_hooks_test.py
 cosmos_framework/inference/g2_text_kv_cache_test.py
 cosmos_framework/scripts/g2_policy_server_test.py
 cosmos_framework/inference/robocasa_session_transactions_test.py
 cosmos_framework/inference/robocasa_batch_transactions_test.py
 cosmos_framework/inference/local_memory_online_test.py
 cosmos_framework/data/generator/action/utils/transforms_test.py
 cosmos_framework/checkpoint/g2_warm_start_test.py
 cosmos_framework/trainer/g2_training_test.py
 cosmos_framework/trainer/g2_grouped_integration_test.py
 cosmos_framework/trainer/local_memory_grouped_test.py
 cosmos_framework/trainer/local_memory_grouped_resume_test.py
 examples/psm_wma_robocasa_g2_recipe_test.py
 examples/psm_wma_robocasa_corrected_phase5_test.py
 examples/psm_wma_robocasa_matched_no_ttt_test.py
)
"${G2_CPU_PYTHON}" -m pytest --noconftest -o addopts='' "${G2_TEST_FILES[@]}" -q \
 --junitxml="${G2_REPO_ROOT}/artifacts/g2_model_integration_final/junit.xml"
