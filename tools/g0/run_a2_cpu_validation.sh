#!/usr/bin/env bash
# Isolated CPU validation; does not install packages or access model/data files.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/artifacts/g0/chatgpt_a2_delivery/cpu}"
[[ "$OUT" = /* ]] || OUT="$ROOT/$OUT"
mkdir -p "$OUT"
cd "$ROOT/cosmos-framework"
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
.venv/bin/python -c 'import os, cosmos_framework; assert os.path.realpath(cosmos_framework.__file__).startswith(os.getcwd()+"/"), cosmos_framework.__file__; print(cosmos_framework.__file__)'
TESTS=(
  cosmos_framework/model/generator/mot/grouped_active_runtime_test.py
  cosmos_framework/model/generator/mot/grouped_active_model_test.py
  cosmos_framework/model/generator/mot/local_evidence_test.py
  cosmos_framework/model/generator/mot/ttt_lifecycle_test.py
  cosmos_framework/model/generator/mot/active_local_memory_driver_test.py
  cosmos_framework/model/generator/mot/active_local_memory_launch_test.py
  cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py
  cosmos_framework/model/generator/mot/canonical_segment_runtime_test.py
  cosmos_framework/model/generator/mot/local_memory_segment_test.py
  cosmos_framework/model/generator/mot/production_active_wiring_test.py
  cosmos_framework/model/generator/omni_mot_model_test.py
)
set +e
.venv/bin/python -m pytest -q "${TESTS[@]}" --junitxml="$OUT/junit.xml" > "$OUT/pytest.log" 2>&1
RC=$?
printf '%s\n' "$RC" > "$OUT/exit_code.txt"
tail -8 "$OUT/pytest.log"
exit "$RC"
