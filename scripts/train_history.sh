#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHILD="$ROOT/cosmos-framework"
MODE="${PSM_HISTORY_MODE:-}"
[[ -n "$MODE" ]] || {
    echo "ERROR: set PSM_HISTORY_MODE=none|window|gru|ttt" >&2
    exit 2
}

case "$MODE" in
  none)
    export PSM_LOCAL_DUMMY_ENABLED=0
    export PSM_R08_LOCAL_HISTORY_ENABLED=0
    export PSM_E003_RECENT_HISTORY_CONTROL=0
    export PSM_R09_A1_ENABLED=0
    export PSM_R09_B1_TTT_ENABLED=0
    export PSM_R09_B_TTT_ENABLED=0
    export PSM_R09_B_TTT_ACTIVE=0
    cd "$CHILD"
    exec bash examples/launch_sft_action_policy_libero_edge_all.sh
    ;;
  window)
    cd "$CHILD"
    exec bash examples/launch_sft_action_policy_libero_edge_all_window_history.sh
    ;;
  gru)
    cd "$CHILD"
    exec bash examples/launch_sft_action_policy_libero_edge_all_recent_history.sh
    ;;
  ttt)
    exec bash "$ROOT/scripts/train_local_memory_ttt.sh"
    ;;
  *)
    echo "ERROR: unsupported PSM_HISTORY_MODE=$MODE; expected none|window|gru|ttt" >&2
    exit 2
    ;;
esac
