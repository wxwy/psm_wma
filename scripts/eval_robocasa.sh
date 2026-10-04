#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHILD="$ROOT/cosmos-framework"
CHECKPOINT_PATH="${1:-}"
DATASET_DIR="${2:-}"

[[ -n "$CHECKPOINT_PATH" && -n "$DATASET_DIR" ]] || {
  echo "usage: scripts/eval_robocasa.sh /abs/path/to/iter_XXXXXXXXX /abs/path/to/task/date/lerobot" >&2
  exit 2
}
[[ "$CHECKPOINT_PATH" = /* ]] || CHECKPOINT_PATH="$PWD/$CHECKPOINT_PATH"
[[ "$DATASET_DIR" = /* ]] || DATASET_DIR="$PWD/$DATASET_DIR"
[[ -d "$CHECKPOINT_PATH/model" ]] || { echo "ERROR: DCP model/ missing: $CHECKPOINT_PATH" >&2; exit 2; }
[[ -f "$DATASET_DIR/extras/dataset_meta.json" ]] || {
  echo "ERROR: DATASET_DIR must contain extras/dataset_meta.json: $DATASET_DIR" >&2
  exit 2
}

JOB_DIR="$(cd "$CHECKPOINT_PATH/../.." && pwd)"
CONFIG_FILE="${CONFIG_FILE:-$JOB_DIR/config.yaml}"
[[ -f "$CONFIG_FILE" ]] || { echo "ERROR: CONFIG_FILE missing: $CONFIG_FILE" >&2; exit 2; }

SERVER_PYTHON="${SERVER_PYTHON:-$CHILD/.venv/bin/python}"
SIM_PYTHON="${SIM_PYTHON:?set SIM_PYTHON to the robosuite/robocasa Python executable}"
[[ -x "$SERVER_PYTHON" ]] || { echo "ERROR: SERVER_PYTHON not executable: $SERVER_PYTHON" >&2; exit 2; }
[[ -x "$SIM_PYTHON" ]] || { echo "ERROR: SIM_PYTHON not executable: $SIM_PYTHON" >&2; exit 2; }

LOCAL_MEMORY_MODE="${LOCAL_MEMORY_MODE:-required}"
[[ "$LOCAL_MEMORY_MODE" == "required" || "$LOCAL_MEMORY_MODE" == "off" ]] || {
  echo "ERROR: LOCAL_MEMORY_MODE must be required|off" >&2
  exit 2
}

SERVER_PORT="${SERVER_PORT:-8912}"
EVAL_GPU="${EVAL_GPU:-0}"
NUM_STEPS="${NUM_STEPS:-30}"
GUIDANCE="${GUIDANCE:-1.0}"
NUM_TRIALS="${NUM_TRIALS:-1}"
ACTION_HORIZON="${ACTION_HORIZON:-16}"
SEED="${SEED:-0}"
TIMEOUT="${TIMEOUT:-600}"
MUJOCO_GL="${MUJOCO_GL:-egl}"
export MUJOCO_GL

if [[ "$LOCAL_MEMORY_MODE" == "required" ]]; then
  if ! [[ "$ACTION_HORIZON" =~ ^[0-9]+$ ]] || (( ACTION_HORIZON < 1 || ACTION_HORIZON > 16 )); then
    echo "ERROR: required V3 Local-TTT requires 1 <= ACTION_HORIZON <= 16 (Local TBPTT T=16)" >&2
    exit 2
  fi
fi

TASK_NAME="$(basename "$(dirname "$(dirname "$DATASET_DIR")")")"
CKPT_NAME="$(basename "$CHECKPOINT_PATH")"
RESULT_ROOT="${OUTPUT_DIR:-$ROOT/results/robocasa_v3_local_ttt/$CKPT_NAME/$LOCAL_MEMORY_MODE/$TASK_NAME}"
mkdir -p "$RESULT_ROOT"

export PYTHONPATH="$CHILD${PYTHONPATH:+:$PYTHONPATH}"

SERVER_LOG="$RESULT_ROOT/action_server.log"
CUDA_VISIBLE_DEVICES="$EVAL_GPU" "$SERVER_PYTHON" -m cosmos_framework.scripts.action_policy_server_robocasa   --checkpoint-path "$CHECKPOINT_PATH"   --config-file "$CONFIG_FILE"   --port "$SERVER_PORT"   --raw-action-dim 15   --local-memory-mode "$LOCAL_MEMORY_MODE"   --local-memory-max-sessions 1   --num-steps "$NUM_STEPS"   --guidance "$GUIDANCE"   --fps 20   --http-400-on-error   >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

ready=0
for _ in $(seq 1 120); do
  if curl -sf "http://127.0.0.1:$SERVER_PORT/info" >"$RESULT_ROOT/server_info.json" 2>/dev/null; then
    ready=1
    break
  fi
  kill -0 "$SERVER_PID" 2>/dev/null || break
  sleep 5
done
[[ "$ready" == 1 ]] || {
  echo "ERROR: V3 RoboCasa action server did not become ready; see $SERVER_LOG" >&2
  exit 1
}

"$SERVER_PYTHON" - "$RESULT_ROOT/server_info.json" "$LOCAL_MEMORY_MODE" <<'PY'
import json, sys
info = json.load(open(sys.argv[1]))
mode = (info.get("local_memory") or {}).get("mode", "off")
if mode != sys.argv[2]:
    raise SystemExit(f"server Local-TTT mode mismatch: expected={sys.argv[2]} actual={mode}")
print(f"[server] checkpoint={info.get('checkpoint')} local_memory={info.get('local_memory')}")
PY

echo ">>> checkpoint: $CHECKPOINT_PATH"
echo ">>> config: $CONFIG_FILE"
echo ">>> dataset: $DATASET_DIR"
echo ">>> Local-TTT mode: $LOCAL_MEMORY_MODE"
echo ">>> trials/seed/action_horizon: $NUM_TRIALS / $SEED / $ACTION_HORIZON"
echo ">>> results: $RESULT_ROOT"

CUDA_VISIBLE_DEVICES="$EVAL_GPU" "$SIM_PYTHON" "$CHILD/cosmos_framework/simulation/robocasa/closed_loop_eval.py"   --server-url "http://127.0.0.1:$SERVER_PORT"   --dataset-dir "$DATASET_DIR"   --num-test-episodes "$NUM_TRIALS"   --action-horizon "$ACTION_HORIZON"   --image-size 256   --cam-size 256   --camera-set left_wrist   --use-state   --use-base-action   --base-encoding raw   --local-memory-mode "$LOCAL_MEMORY_MODE"   --success-latch 1   --seed "$SEED"   --timeout "$TIMEOUT"   --output-dir "$RESULT_ROOT"

echo ">>> RoboCasa V3 evaluation complete: $RESULT_ROOT"
