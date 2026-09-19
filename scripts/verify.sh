#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHILD="$ROOT/cosmos-framework"
PY="$CHILD/.venv/bin/python"
[[ -x "$PY" ]] || { echo "ERROR: missing cosmos-framework/.venv" >&2; exit 2; }

NPROC="${NPROC_PER_NODE:-8}"
B_STREAM="${PSM_R09_B_TTT_B_STREAM:-8}"
T_STEPS="${PSM_R09_B_TTT_TBPTT_STEPS:-16}"
TARGET="${PSM_R09_B_TTT_GLOBAL_CONSUMERS:-2048}"
GA="${PSM_R09_B_TTT_ACTIVE_GA:-}"
if [[ -z "$GA" ]]; then
  denom=$((NPROC * B_STREAM * T_STEPS))
  (( TARGET % denom == 0 )) || { echo "ERROR: cannot derive integral GA from target=$TARGET and denom=$denom" >&2; exit 2; }
  GA=$((TARGET / denom))
fi
ACTUAL=$((NPROC * B_STREAM * T_STEPS * GA))

ROOT_GIT_SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
CHILD_GIT_SHA="$(git -C "$CHILD" rev-parse HEAD 2>/dev/null || echo unknown)"

"$PY" - <<'PY'
import inspect
from cosmos_framework.model.generator.mot.active_local_memory_launch import (
    ActiveLocalMemoryLaunchCallback, canonical_segment_streams,
)
from cosmos_framework.model.generator.mot.parallelize_vfm_network import (
    _local_memory_fsdp_ignored_parameters,
)
from cosmos_framework.trainer import _sync_active_local_replicated_gradients

signature = inspect.signature(canonical_segment_streams)
assert "rank" in signature.parameters and "world_size" in signature.parameters
assert "single-rank training only" not in inspect.getsource(ActiveLocalMemoryLaunchCallback.on_train_start)
assert callable(_local_memory_fsdp_ignored_parameters)
assert callable(_sync_active_local_replicated_gradients)
PY

if (( ACTUAL != TARGET )) && [[ "${PSM_ALLOW_GLOBAL_CONSUMER_CHANGE:-0}" != "1" ]]; then
  echo "ERROR: effective global consumers/update=$ACTUAL, expected $TARGET" >&2
  exit 2
fi

echo "PASS: current-source Local Memory + TTT multi-rank capability preflight"
echo "  root=$ROOT_GIT_SHA"
echo "  child=$CHILD_GIT_SHA"
echo "  ranks=$NPROC B_stream/rank=$B_STREAM T=$T_STEPS GA/rank=$GA global_consumers/update=$ACTUAL"

if [[ -n "${VERIFY_OUTPUT:-}" ]]; then
  ROOT_GIT_SHA="$ROOT_GIT_SHA" CHILD_GIT_SHA="$CHILD_GIT_SHA" NPROC="$NPROC" B_STREAM="$B_STREAM" T_STEPS="$T_STEPS" GA="$GA" ACTUAL="$ACTUAL" "$PY" - <<'PY'
import json, os
payload = {
    "result": "PASS",
    "kind": "current_source_multirank_capability_preflight",
    "root_git_sha": os.environ["ROOT_GIT_SHA"],
    "child_git_sha": os.environ["CHILD_GIT_SHA"],
    "world_size": int(os.environ["NPROC"]),
    "b_stream_per_rank": int(os.environ["B_STREAM"]),
    "ttt_steps": int(os.environ["T_STEPS"]),
    "ga_per_rank": int(os.environ["GA"]),
    "global_consumers_per_update": int(os.environ["ACTUAL"]),
}
with open(os.environ["VERIFY_OUTPUT"], "w") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY
fi
