#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKPOINT_PATH="${1:-}"
[[ -n "$CHECKPOINT_PATH" ]] || { echo "usage: scripts/eval_recent_history.sh /absolute/path/to/iter_XXXXXXXXX" >&2; exit 2; }

export PSM_R08_LOCAL_HISTORY_ENABLED=1
export PSM_E003_RECENT_HISTORY_CONTROL=1
export PSM_R08_LOCAL_HISTORY_HORIZON="${PSM_R08_LOCAL_HISTORY_HORIZON:-64}"
export PSM_R08_HISTORY_MODE=normal
export PSM_LOCAL_DUMMY_ENABLED=0
export PSM_R09_A1_ENABLED=0
export PSM_R09_B1_TTT_ENABLED=0
export PSM_R09_B_TTT_ENABLED=0
export PSM_R09_B_TTT_ACTIVE=0
export LOCAL_MEMORY_MODE="${LOCAL_MEMORY_MODE:-required}"

CKPT_NAME="$(basename "$CHECKPOINT_PATH")"
export OUTPUT_DIR="${OUTPUT_DIR:-$ROOT/results/libero_recent_history/$CKPT_NAME/$LOCAL_MEMORY_MODE}"

exec "$ROOT/scripts/eval.sh" "$CHECKPOINT_PATH"
