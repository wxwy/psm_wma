#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHILD="$ROOT/cosmos-framework"
CHECKPOINT_PATH="${1:-}"
[[ -n "$CHECKPOINT_PATH" ]] || { echo "usage: scripts/eval.sh /absolute/path/to/iter_XXXXXXXXX" >&2; exit 2; }
[[ "$CHECKPOINT_PATH" = /* ]] || CHECKPOINT_PATH="$PWD/$CHECKPOINT_PATH"
[[ -d "$CHECKPOINT_PATH" ]] || { echo "ERROR: checkpoint not found: $CHECKPOINT_PATH" >&2; exit 2; }

export LIBERO_ROOT="${LIBERO_ROOT:-/disk/rl/data/LIBERO_LeRobot_v3}"
export EDGE_POLICY_CHECKPOINT="${EDGE_POLICY_CHECKPOINT:-/disk/rl/models/Cosmos3-Edge-Policy-DROID}"
export WAN_VAE_PATH="${WAN_VAE_PATH:-$CHILD/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth}"
export PSM_R08_LOCAL_HISTORY_ENABLED="${PSM_R08_LOCAL_HISTORY_ENABLED:-1}"
export PSM_E003_RECENT_HISTORY_CONTROL="${PSM_E003_RECENT_HISTORY_CONTROL:-0}"
export PSM_R09_A1_ENABLED="${PSM_R09_A1_ENABLED:-0}"
export PSM_R09_B1_TTT_ENABLED="${PSM_R09_B1_TTT_ENABLED:-0}"
export PSM_R09_B_TTT_ENABLED="${PSM_R09_B_TTT_ENABLED:-1}"
export PSM_R09_B_TTT_ACTIVE="${PSM_R09_B_TTT_ACTIVE:-1}"
export PSM_R09_B_TTT_MEMBER_LAYOUT="${PSM_R09_B_TTT_MEMBER_LAYOUT:-a2}"
export PSM_R09_B_TTT_B_STREAM="${PSM_R09_B_TTT_B_STREAM:-8}"
export PSM_R09_B_TTT_ACTIVE_GA="${PSM_R09_B_TTT_ACTIVE_GA:-16}"
export PSM_R09_B_TTT_TBPTT_STEPS="${PSM_R09_B_TTT_TBPTT_STEPS:-16}"

LOCAL_MEMORY_MODE="${LOCAL_MEMORY_MODE:-required}"
NUM_STEPS="${NUM_STEPS:-30}"
NUM_TRIALS="${NUM_TRIALS:-10}"
MAX_STEPS="${MAX_STEPS:-700}"
SERVER_PORT="${SERVER_PORT:-8000}"
TASK_IDS="${TASK_IDS:-0,1,2,3,4,5,6,7,8,9}"
TASK_SUITES="${TASK_SUITES:-libero_spatial libero_object libero_goal libero_10}"
PROFILE_INFERENCE="${PROFILE_INFERENCE:-0}"
[[ "$PROFILE_INFERENCE" = 0 || "$PROFILE_INFERENCE" = 1 ]] || { echo "ERROR: PROFILE_INFERENCE must be 0 or 1" >&2; exit 2; }
if [[ "$PROFILE_INFERENCE" = 1 ]]; then
  [[ "$NUM_TRIALS" = 1 ]] || { echo "ERROR: PROFILE_INFERENCE=1 requires NUM_TRIALS=1" >&2; exit 2; }
  [[ "$TASK_IDS" != *,* ]] || { echo "ERROR: PROFILE_INFERENCE=1 requires exactly one TASK_ID" >&2; exit 2; }
  [[ "$(wc -w <<<"$TASK_SUITES")" = 1 ]] || { echo "ERROR: PROFILE_INFERENCE=1 requires exactly one TASK_SUITE" >&2; exit 2; }
fi
CKPT_NAME="$(basename "$CHECKPOINT_PATH")"
RESULT_ROOT="${OUTPUT_DIR:-$ROOT/results/libero_local_memory/$CKPT_NAME/$LOCAL_MEMORY_MODE}"
mkdir -p "$RESULT_ROOT"
cd "$CHILD"
export LD_LIBRARY_PATH="$CHILD/.venv/lib/python3.13/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="$CHILD/examples/_server_shim${PYTHONPATH:+:$PYTHONPATH}"

SERVER_LOG="$RESULT_ROOT/action_server.log"
.venv/bin/python -m cosmos_framework.scripts.action_policy_server_libero \
  --experiment action_policy_libero_edge_all \
  --experiment-overrides "model.config.tokenizer.vae_path=$WAN_VAE_PATH" \
  --experiment-overrides "model.config.vlm_config.tokenizer.tokenizer_type=$EDGE_POLICY_CHECKPOINT" \
  --checkpoint-path "$CHECKPOINT_PATH" \
  --no-use-ema-weights \
  --action-normalization quantile_rot \
  --action-stats-path cosmos_framework/data/generator/action/normalizer_stats/libero_native_frame_wise_relative_rot6d.json \
  --raw-action-dim 10 --fps 20 --port "$SERVER_PORT" --num-steps "$NUM_STEPS" \
  --guidance "${GUIDANCE:-1.0}" --local-memory-mode "$LOCAL_MEMORY_MODE" \
  >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!
cleanup() { kill "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

ready=0
for _ in $(seq 1 120); do
  if curl -sf "http://localhost:$SERVER_PORT/" >/dev/null 2>&1; then ready=1; break; fi
  kill -0 "$SERVER_PID" 2>/dev/null || break
  sleep 5
done
[[ "$ready" == 1 ]] || { echo "ERROR: action server did not become ready; see $SERVER_LOG" >&2; exit 1; }
echo ">>> checkpoint: $CHECKPOINT_PATH"
echo ">>> local_memory_mode: $LOCAL_MEMORY_MODE"
echo ">>> results: $RESULT_ROOT"

for suite in $TASK_SUITES; do
  suite_out="$RESULT_ROOT/$suite"
  mkdir -p "$suite_out"
  echo ">>> evaluating $suite"
  PROFILE_ARGS=()
  if [[ "$PROFILE_INFERENCE" = 1 ]]; then
    PROFILE_ARGS+=(--profile_inference --num_envs 1 --video_samples_per_task 0)
  fi
  SERVER_URL="http://localhost:$SERVER_PORT" \
  TASK_SUITE="$suite" TASK_IDS="$TASK_IDS" NUM_TRIALS="$NUM_TRIALS" \
  OUTPUT_DIR="$suite_out" \
  bash examples/launch_closed_loop_eval_libero_task0.sh --max_steps "$MAX_STEPS" "${PROFILE_ARGS[@]}"
done

echo ">>> evaluation complete: $RESULT_ROOT"