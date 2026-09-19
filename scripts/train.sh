#!/usr/bin/env bash
# Compatibility alias. Canonical Local Memory + TTT A2 training entrypoint:
#   scripts/train_local_memory_ttt.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo ">>> NOTE: scripts/train.sh is an alias for Local Memory + TTT A2 training." >&2
echo ">>> Canonical entrypoint: scripts/train_local_memory_ttt.sh" >&2
exec bash "$ROOT/scripts/train_local_memory_ttt.sh" "$@"
