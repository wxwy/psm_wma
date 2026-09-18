#!/usr/bin/env bash
# Full bounded validation; explicitly no multi-day training or automatic merge.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:?usage: run_a2_delivery_validation.sh NEW_OUTPUT_ROOT}"
[[ "$OUT" = /* ]] || OUT="$ROOT/$OUT"
[[ ! -e "$OUT" ]] || { echo "Refusing to overwrite $OUT" >&2; exit 2; }
USED="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1 | tr -d ' ')"
(( USED < 512 )) || { echo "BLOCKED_RESOURCE: GPU has $USED MiB allocated" >&2; exit 75; }
cd "$ROOT"
CHILD_SHA="$(git -C cosmos-framework rev-parse HEAD)"
bash tools/g0/run_a2_cpu_validation.sh "$OUT/cpu"
PSM_A2_NATIVE_VALIDATION=1 bash tools/g0/launch_local_memory_a2.sh "$OUT/control" 3 2 fresh
# New-process restore from the control's completed iter_2 checkpoint. This proves
# checkpoint recovery, not an abrupt-kill witness; do not label it save/kill/resume.
CP=cosmos3_action_libero/action_sft/edge_libero_4in1_localmem_active/checkpoints
mkdir -p "$OUT/resume/$CP"
cp -a --reflink=auto "$OUT/control/$CP/iter_000000002" "$OUT/resume/$CP/"
printf 'iter_000000002\n' > "$OUT/resume/$CP/latest_checkpoint.txt"
PSM_A2_NATIVE_VALIDATION=0 bash tools/g0/launch_local_memory_a2.sh "$OUT/resume" 3 2 resume
# High cap means all existing training episodes, rather than the 10-episode smoke subset.
LIBERO_MAX_EPISODES=100000 PSM_A2_NATIVE_VALIDATION=0 \
  bash tools/g0/launch_local_memory_a2.sh "$OUT/budget" 20 10 fresh
cosmos-framework/.venv/bin/python tools/g0/verify_active_local_memory_pretrain_gate.py \
  --cpu "$OUT/cpu" --control "$OUT/control" --resume "$OUT/resume" \
  --budget "$OUT/budget" --require-budget --expected-child "$CHILD_SHA" \
  --output "$OUT/delivery_status.json"
