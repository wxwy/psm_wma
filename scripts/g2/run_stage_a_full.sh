#!/usr/bin/env bash
# One explicit Owner invocation; no deletion, environment installation or merge.
set -euo pipefail
if [ "$#" -lt 3 ]; then
  echo "usage: $0 /absolute/existing/python /absolute/config.json preflight|run|resume|progress|stop [--manual-start]" >&2
  exit 2
fi
G2_PYTHON="$1"
G2_CONFIG="$2"
G2_ACTION="$3"
shift 3
case "$G2_PYTHON:$G2_CONFIG" in /*:/*) ;; *) echo 'absolute interpreter/config paths required' >&2; exit 2;; esac
G2_REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$G2_REPO_ROOT"
export PYTHONPATH="$G2_REPO_ROOT:$G2_REPO_ROOT/cosmos-framework"
export PYTHONDONTWRITEBYTECODE=1 COSMOS_TRAINING=0 COSMOS_INTERNAL=0
exec "$G2_PYTHON" -m tools.g2.run_stage_a_production "$G2_ACTION" --config "$G2_CONFIG" "$@"
