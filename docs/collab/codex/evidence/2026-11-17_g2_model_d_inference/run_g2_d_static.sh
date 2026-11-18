#!/usr/bin/env bash
set -euo pipefail
PSM_G2_D_EVIDENCE_DIR="${1:?evidence directory required (run from Child root)}"
PSM_G2_D_RUFF="${PSM_G2_D_RUFF:-/workspace/.venvs/psm-wma-cpu/bin/ruff}"
PSM_G2_D_PYTHON="${PSM_G2_D_PYTHON:-/workspace/.venvs/psm-wma-cpu/bin/python}"
files=(
  cosmos_framework/inference/g2_session_cache.py
  cosmos_framework/inference/g2_session_cache_test.py
  cosmos_framework/inference/g2_policy_conditions.py
  cosmos_framework/inference/g2_policy_conditions_test.py
  cosmos_framework/inference/g2_text_kv_cache_test.py
  cosmos_framework/inference/g2_model_hooks.py
  cosmos_framework/inference/g2_model_hooks_test.py
  cosmos_framework/scripts/g2_policy_server_test.py
  cosmos_framework/scripts/action_policy_server_robocasa.py
  cosmos_framework/inference/robocasa_session_transactions.py
  cosmos_framework/inference/robocasa_batch_transactions.py
)
"$PSM_G2_D_RUFF" check "${files[@]}" > "$PSM_G2_D_EVIDENCE_DIR/ruff.log" 2>&1
legacy=cosmos_framework/model/generator/mot/inference_text_kv_memory.py
"$PSM_G2_D_RUFF" check --ignore I001 "$legacy" > "$PSM_G2_D_EVIDENCE_DIR/ruff-legacy.log" 2>&1
"$PSM_G2_D_RUFF" format --check "${files[@]}" "$legacy" > "$PSM_G2_D_EVIDENCE_DIR/format.log" 2>&1
"$PSM_G2_D_PYTHON" -m compileall -q "${files[@]}" "$legacy" > "$PSM_G2_D_EVIDENCE_DIR/syntax.log" 2>&1
git diff --check > "$PSM_G2_D_EVIDENCE_DIR/diff-check.log" 2>&1
git ls-files -z -- '*.py' | xargs -0 sha256sum > "$PSM_G2_D_EVIDENCE_DIR/source-after.sha256"
cmp "$PSM_G2_D_EVIDENCE_DIR/source-before.sha256" "$PSM_G2_D_EVIDENCE_DIR/source-after.sha256"
sha256sum -c "$PSM_G2_D_EVIDENCE_DIR/source-before.sha256" > "$PSM_G2_D_EVIDENCE_DIR/source-verify.log"
"$PSM_G2_D_PYTHON" -c 'import json,platform,torch,pytest; print(json.dumps({"python":platform.python_version(),"torch":torch.__version__,"pytest":pytest.__version__,"cuda_used":False},sort_keys=True))' > "$PSM_G2_D_EVIDENCE_DIR/environment.json" 2> "$PSM_G2_D_EVIDENCE_DIR/environment.stderr"
