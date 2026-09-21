#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKPOINT_PATH="${1:-}"
[[ -n "$CHECKPOINT_PATH" ]] || {
  echo "usage: PSM_HISTORY_MODE=none|window|gru|ttt scripts/eval_history.sh /absolute/path/to/iter_XXXXXXXXX" >&2
  exit 2
}
MODE="${PSM_HISTORY_MODE:-}"
[[ -n "$MODE" ]] || { echo "ERROR: set PSM_HISTORY_MODE=none|window|gru|ttt" >&2; exit 2; }

export PSM_LOCAL_DUMMY_ENABLED=0
export PSM_R09_A1_ENABLED=0
export PSM_R09_B1_TTT_ENABLED=0
unset PSM_R09_A1_PROBE_OUTPUT PSM_R09_B1_PROBE_OUTPUT PSM_R09_B2_STREAM_MANIFEST_ROOT

case "$MODE" in
  none)
    export PSM_R08_LOCAL_HISTORY_ENABLED=0
    export PSM_E003_RECENT_HISTORY_CONTROL=0
    export PSM_R09_B_TTT_ENABLED=0
    export PSM_R09_B_TTT_ACTIVE=0
    export LOCAL_MEMORY_MODE="${LOCAL_MEMORY_MODE:-off}"
    ;;
  window)
    export PSM_RECENT_HISTORY_HORIZON="${PSM_RECENT_HISTORY_HORIZON:-16}"
    export PSM_R08_LOCAL_HISTORY_ENABLED=0
    export PSM_E003_RECENT_HISTORY_CONTROL=0
    export PSM_R09_B_TTT_ENABLED=0
    export PSM_R09_B_TTT_ACTIVE=0
    export LOCAL_MEMORY_MODE="${LOCAL_MEMORY_MODE:-required}"
    ;;
  gru)
    export PSM_RECENT_HISTORY_HORIZON="${PSM_RECENT_HISTORY_HORIZON:-16}"
    export PSM_R08_LOCAL_HISTORY_ENABLED=1
    export PSM_E003_RECENT_HISTORY_CONTROL=1
    export PSM_LOCAL_DUMMY_DIM=32
    export PSM_R09_B_TTT_ENABLED=0
    export PSM_R09_B_TTT_ACTIVE=0
    export LOCAL_MEMORY_MODE="${LOCAL_MEMORY_MODE:-required}"
    ;;
  ttt)
    export PSM_R08_LOCAL_HISTORY_ENABLED=1
    export PSM_E003_RECENT_HISTORY_CONTROL=0
    export PSM_LOCAL_DUMMY_DIM=32
    export PSM_R09_B_TTT_ENABLED=1
    export PSM_R09_B_TTT_ACTIVE=1
    export LOCAL_MEMORY_MODE="${LOCAL_MEMORY_MODE:-required}"
    ;;
  *)
    echo "ERROR: unsupported PSM_HISTORY_MODE=$MODE; expected none|window|gru|ttt" >&2
    exit 2
    ;;
esac

export OUTPUT_DIR="${OUTPUT_DIR:-$ROOT/results/libero_history/$MODE/$(basename "$CHECKPOINT_PATH")/$LOCAL_MEMORY_MODE}"
exec "$ROOT/scripts/eval.sh" "$CHECKPOINT_PATH"
