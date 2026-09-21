#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKPOINT_PATH="${1:-}"
[[ -n "$CHECKPOINT_PATH" ]] || {
  echo "usage: PSM_HISTORY_MODE=none|window|gru|ttt PROFILE_SUITE=libero_10 PROFILE_TASK_ID=0 scripts/profile_history.sh /absolute/path/to/checkpoint" >&2
  exit 2
}

MODE="${PSM_HISTORY_MODE:-}"
case "$MODE" in
  none|window|gru|ttt) ;;
  *) echo "ERROR: set PSM_HISTORY_MODE=none|window|gru|ttt" >&2; exit 2 ;;
esac

PROFILE_GPU="${PROFILE_GPU:-0}"
[[ "$PROFILE_GPU" =~ ^[0-9]+$ ]] || { echo "ERROR: PROFILE_GPU must be one GPU index" >&2; exit 2; }
export CUDA_VISIBLE_DEVICES="$PROFILE_GPU"

SUITE="${PROFILE_SUITE:-libero_10}"
TASK_ID="${PROFILE_TASK_ID:-0}"
[[ "$TASK_ID" =~ ^[0-9]+$ ]] || { echo "ERROR: PROFILE_TASK_ID must be one integer task id" >&2; exit 2; }

CKPT_NAME="$(basename "$CHECKPOINT_PATH")"
export PROFILE_INFERENCE=1
export NUM_TRIALS=1
export TASK_SUITES="$SUITE"
export TASK_IDS="$TASK_ID"
export VIDEO_SAMPLES_PER_TASK=0
export OUTPUT_DIR="${OUTPUT_DIR:-$ROOT/results/libero_profile/$MODE/$CKPT_NAME/${SUITE}_task${TASK_ID}}"

echo ">>> single-GPU single-process single-episode inference profile"
echo ">>> mode=$MODE checkpoint=$CHECKPOINT_PATH"
echo ">>> gpu=$PROFILE_GPU suite=$SUITE task=$TASK_ID"
echo ">>> action-only profiling; generated-video decode/PNG disabled"
echo ">>> output=$OUTPUT_DIR"

exec "$ROOT/scripts/eval_history.sh" "$CHECKPOINT_PATH"
