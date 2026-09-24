#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHILD="$ROOT/cosmos-framework"
CHECKPOINT_PATH="${1:-}"
[[ -n "$CHECKPOINT_PATH" ]] || {
  echo "usage: scripts/eval_robocasa.sh /absolute/path/to/iter_XXXXXXXXX" >&2
  exit 2
}
[[ "$CHECKPOINT_PATH" = /* ]] || CHECKPOINT_PATH="$PWD/$CHECKPOINT_PATH"
[[ -d "$CHECKPOINT_PATH" ]] || {
  echo "ERROR: checkpoint not found: $CHECKPOINT_PATH" >&2
  exit 2
}

export EDGE_POLICY_CHECKPOINT="${EDGE_POLICY_CHECKPOINT:-/disk/rl/models/Cosmos3-Edge-Policy-DROID}"
export WAN_VAE_PATH="${WAN_VAE_PATH:-$CHILD/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth}"
export MUJOCO_GL="${MUJOCO_GL:-egl}"

SERVER_PORT="${SERVER_PORT:-8000}"
EVAL_GPU="${EVAL_GPU:-0}"
NUM_STEPS="${NUM_STEPS:-30}"
GUIDANCE="${GUIDANCE:-1.0}"
LOCAL_MEMORY_MODE="${LOCAL_MEMORY_MODE:-required}"
ROBOCASA_SPLIT="${ROBOCASA_SPLIT:-target}"
TASK_SETS="${TASK_SETS:-atomic_seen}"
TASK_INDICES="${TASK_INDICES:-}"
MAX_TASKS="${MAX_TASKS:-}"
NUM_TRIALS="${NUM_TRIALS:-10}"
REPLAN_STEPS="${REPLAN_STEPS:-5}"
BASE_DECODE_MODE="${BASE_DECODE_MODE:-velocity}"
SAVE_VIDEOS="${SAVE_VIDEOS:-1}"
CKPT_NAME="$(basename "$CHECKPOINT_PATH")"
RESULT_ROOT="${OUTPUT_DIR:-$ROOT/results/robocasa_local_ttt/$CKPT_NAME/$ROBOCASA_SPLIT/$LOCAL_MEMORY_MODE}"
mkdir -p "$RESULT_ROOT"

case "$LOCAL_MEMORY_MODE" in
  required|auto|zero|init)
    EVAL_MEMORY_ARG="--local-memory"
    ;;
  off)
    EVAL_MEMORY_ARG="--no-local-memory"
    ;;
  *)
    echo "ERROR: LOCAL_MEMORY_MODE must be required|auto|off|zero|init" >&2
    exit 2
    ;;
esac

case "$SAVE_VIDEOS" in
  1) VIDEO_ARG="--save-videos" ;;
  0) VIDEO_ARG="--no-save-videos" ;;
  *) echo "ERROR: SAVE_VIDEOS must be 0 or 1" >&2; exit 2 ;;
esac

cd "$CHILD"
export PYTHONPATH="$CHILD${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$CHILD/.venv/lib/python3.13/site-packages/nvidia/cu13/lib:${LD_LIBRARY_PATH:-}"

SERVER_LOG="$RESULT_ROOT/action_server.log"
CUDA_VISIBLE_DEVICES="$EVAL_GPU" .venv/bin/python -m cosmos_framework.scripts.action_policy_server_robolab   --checkpoint-path "$CHECKPOINT_PATH"   --allow-dcp-checkpoint   --no-use-ema-weights   --experiment action_policy_robocasa_edge_all   --domain-name robocasa   --action-space robocasa_ego   --action-dim 20   --action-chunk-size 16   --conditioning-fps 20   --resolution 256   --image-height 256   --image-width 512   --history-length 1   --format-prompt-as-json   --local-memory-mode "$LOCAL_MEMORY_MODE"   --port "$SERVER_PORT"   --num-steps "$NUM_STEPS"   --guidance "$GUIDANCE"   >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

ready=0
for _ in $(seq 1 120); do
  if curl -sf "http://127.0.0.1:$SERVER_PORT/healthz" >/dev/null 2>&1; then
    ready=1
    break
  fi
  kill -0 "$SERVER_PID" 2>/dev/null || break
  sleep 5
done
[[ "$ready" == 1 ]] || {
  echo "ERROR: RoboCasa action server did not become ready; see $SERVER_LOG" >&2
  exit 1
}

echo ">>> checkpoint: $CHECKPOINT_PATH"
echo ">>> split/task_sets: $ROBOCASA_SPLIT / $TASK_SETS"
echo ">>> Local-TTT mode: $LOCAL_MEMORY_MODE"
echo ">>> trials/replan: $NUM_TRIALS / $REPLAN_STEPS"
echo ">>> base decode: $BASE_DECODE_MODE"
echo ">>> results: $RESULT_ROOT"

ARGS=(
  --host 127.0.0.1
  --port "$SERVER_PORT"
  --split "$ROBOCASA_SPLIT"
  --task-sets
)
read -r -a TASK_SET_ARRAY <<< "$TASK_SETS"
ARGS+=("${TASK_SET_ARRAY[@]}")
ARGS+=(
  --num-trials "$NUM_TRIALS"
  --replan-steps "$REPLAN_STEPS"
  --output-dir "$RESULT_ROOT"
  --base-decode-mode "$BASE_DECODE_MODE"
  "$EVAL_MEMORY_ARG"
  "$VIDEO_ARG"
)

if [[ -n "$TASK_INDICES" ]]; then
  ARGS+=(--task-indices "$TASK_INDICES")
fi
if [[ -n "$MAX_TASKS" ]]; then
  ARGS+=(--max-tasks "$MAX_TASKS")
fi

.venv/bin/python -m cosmos_framework.simulation.robocasa.closed_loop_eval "${ARGS[@]}"

echo ">>> RoboCasa evaluation complete: $RESULT_ROOT"
