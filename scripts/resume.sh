#!/usr/bin/env bash
# Compatibility alias: require an existing Local Memory + TTT checkpoint.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REQUIRE_RESUME=1
echo ">>> NOTE: scripts/resume.sh is a strict-resume alias." >&2
echo ">>> Canonical entrypoint: scripts/train_local_memory_ttt.sh" >&2
exec bash "$ROOT/scripts/train_local_memory_ttt.sh" "$@"