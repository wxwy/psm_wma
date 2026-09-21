#!/usr/bin/env bash
# Canonical PSM-WMA Local Memory + TTT A2 training entrypoint.
# Default topology: one 8-GPU node. Existing checkpoints auto-resume.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHILD="$ROOT/cosmos-framework"

[[ -x "$CHILD/.venv/bin/python" ]] || { echo "ERROR: missing cosmos-framework/.venv" >&2; exit 2; }

export NPROC_PER_NODE="${NPROC_PER_NODE:-8}"
export PSM_R09_B_TTT_B_STREAM="${PSM_R09_B_TTT_B_STREAM:-8}"
export PSM_R09_B_TTT_TBPTT_STEPS="${PSM_R09_B_TTT_TBPTT_STEPS:-16}"
export PSM_R09_B_TTT_GLOBAL_CONSUMERS="${PSM_R09_B_TTT_GLOBAL_CONSUMERS:-2048}"

for name in NPROC_PER_NODE PSM_R09_B_TTT_B_STREAM PSM_R09_B_TTT_TBPTT_STEPS PSM_R09_B_TTT_GLOBAL_CONSUMERS; do
  value="${!name}"
  [[ "$value" =~ ^[1-9][0-9]*$ ]] || { echo "ERROR: $name must be a positive integer, got $value" >&2; exit 2; }
done

denom=$((NPROC_PER_NODE * PSM_R09_B_TTT_B_STREAM * PSM_R09_B_TTT_TBPTT_STEPS))
if [[ -z "${PSM_R09_B_TTT_ACTIVE_GA:-}" ]]; then
  (( PSM_R09_B_TTT_GLOBAL_CONSUMERS % denom == 0 )) || {
    echo "ERROR: global consumers $PSM_R09_B_TTT_GLOBAL_CONSUMERS is not divisible by world*B*T=$denom" >&2
    exit 2
  }
  export PSM_R09_B_TTT_ACTIVE_GA=$((PSM_R09_B_TTT_GLOBAL_CONSUMERS / denom))
fi
[[ "$PSM_R09_B_TTT_ACTIVE_GA" =~ ^[1-9][0-9]*$ ]] || { echo "ERROR: PSM_R09_B_TTT_ACTIVE_GA must be positive" >&2; exit 2; }
actual_global=$((NPROC_PER_NODE * PSM_R09_B_TTT_B_STREAM * PSM_R09_B_TTT_TBPTT_STEPS * PSM_R09_B_TTT_ACTIVE_GA))
if (( actual_global != PSM_R09_B_TTT_GLOBAL_CONSUMERS )) && [[ "${PSM_ALLOW_GLOBAL_CONSUMER_CHANGE:-0}" != "1" ]]; then
  echo "ERROR: resolved global consumers/update=$actual_global, expected $PSM_R09_B_TTT_GLOBAL_CONSUMERS" >&2
  echo "Set PSM_ALLOW_GLOBAL_CONSUMER_CHANGE=1 only for an intentional batch-size experiment." >&2
  exit 2
fi

export PSM_HISTORY_MODE=ttt
export PSM_LOCAL_DUMMY_ENABLED=0
export PSM_R08_LOCAL_HISTORY_ENABLED=1
export PSM_E003_RECENT_HISTORY_CONTROL=0
export PSM_R09_A1_ENABLED=0
export PSM_R09_B1_TTT_ENABLED=0
export PSM_R09_B_TTT_ENABLED=1
export PSM_R09_B_TTT_ACTIVE=1
export PSM_R09_B_TTT_MEMBER_LAYOUT="${PSM_R09_B_TTT_MEMBER_LAYOUT:-a2}"
export PSM_ACTIVE_PREFETCH_DEPTH="${PSM_ACTIVE_PREFETCH_DEPTH:-4}"

# Capability preflight: checks the current source tree, not a frozen Git SHA.
VERIFY_OUTPUT="${VERIFY_OUTPUT:-/tmp/psm_wma_train_preflight.json}" bash "$ROOT/scripts/verify.sh" >/dev/null

if [[ "${DRY_RUN:-0}" != "1" ]]; then
  visible_gpus="$("$CHILD/.venv/bin/python" - <<'PY'
import torch
print(torch.cuda.device_count())
PY
)"
  (( visible_gpus >= NPROC_PER_NODE )) || {
    echo "ERROR: requested $NPROC_PER_NODE ranks but only $visible_gpus CUDA devices are visible" >&2
    exit 2
  }
fi

export LIBERO_ROOT="${LIBERO_ROOT:-/disk/rl/data/LIBERO_LeRobot_v3}"
export LIBERO_LATENT_CACHE_ROOT="${LIBERO_LATENT_CACHE_ROOT:-/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1}"
export EDGE_POLICY_CHECKPOINT="${EDGE_POLICY_CHECKPOINT:-/disk/rl/models/Cosmos3-Edge-Policy-DROID}"
export BASE_CHECKPOINT_PATH="${BASE_CHECKPOINT_PATH:-$CHILD/examples/checkpoints/Cosmos3-Edge-Policy-DROID-dcp}"
export WAN_VAE_PATH="${WAN_VAE_PATH:-$CHILD/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth}"
export OUTPUT_ROOT="${OUTPUT_ROOT:-$ROOT/outputs/train_local_memory_a2}"
export RUN_NAME="edge_libero_4in1_localmem_active"
RUN_DIR="$OUTPUT_ROOT/cosmos3_action_libero/action_sft/$RUN_NAME"
CHECKPOINT_ROOT="$RUN_DIR/checkpoints"

FRESH_START="${FRESH_START:-0}"
REQUIRE_RESUME="${REQUIRE_RESUME:-0}"
[[ "$FRESH_START" = 0 || "$FRESH_START" = 1 ]] || { echo "ERROR: FRESH_START must be 0 or 1" >&2; exit 2; }
[[ "$REQUIRE_RESUME" = 0 || "$REQUIRE_RESUME" = 1 ]] || { echo "ERROR: REQUIRE_RESUME must be 0 or 1" >&2; exit 2; }
[[ ! ( "$FRESH_START" = 1 && "$REQUIRE_RESUME" = 1 ) ]] || { echo "ERROR: FRESH_START and REQUIRE_RESUME are mutually exclusive" >&2; exit 2; }

LATEST_ITER=""
if [[ -d "$CHECKPOINT_ROOT" ]]; then
  LATEST_ITER="$(find "$CHECKPOINT_ROOT" -mindepth 1 -maxdepth 1 -type d -name 'iter_*' -printf '%f\n' 2>/dev/null | sort -V | tail -1)"
fi
if [[ "$FRESH_START" = 1 ]]; then
  if [[ -e "$RUN_DIR" ]] && [[ -n "$(find "$RUN_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
    echo "ERROR: FRESH_START=1 requires a new/empty run directory: $RUN_DIR" >&2
    exit 2
  fi
  export DISABLE_AUTO_RESUME=1
  MODE="fresh (explicit)"
elif [[ -n "$LATEST_ITER" ]]; then
  export DISABLE_AUTO_RESUME=0
  MODE="resume $LATEST_ITER"
elif [[ "$REQUIRE_RESUME" = 1 ]]; then
  echo "ERROR: REQUIRE_RESUME=1 but no iter_* checkpoint exists under $CHECKPOINT_ROOT" >&2
  exit 2
else
  export DISABLE_AUTO_RESUME=0
  MODE="fresh (no checkpoint found)"
fi

export LIBERO_MAX_EPISODES="${LIBERO_MAX_EPISODES:-100000}"
export LIBERO_LATENT_CACHE_VERIFY_RATIO="${LIBERO_LATENT_CACHE_VERIFY_RATIO:-0}"
export LIBERO_NUM_WORKERS="${LIBERO_NUM_WORKERS:-0}"
export LIBERO_PREFETCH_FACTOR="${LIBERO_PREFETCH_FACTOR:-1}"
export TOML_FILE=examples/toml/sft_config/action_policy_libero_edge_all_localmem_active.toml
export MAX_ITER="${MAX_ITER:-5000}"
export SAVE_ITER="${SAVE_ITER:-50}"
export EXTRA_TAIL_OVERRIDES="trainer.max_iter=$MAX_ITER checkpoint.save_iter=$SAVE_ITER trainer.logging_iter=1 ${EXTRA_TAIL_OVERRIDES:-}"

ROOT_GIT_SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
CHILD_GIT_SHA="$(git -C "$CHILD" rev-parse HEAD 2>/dev/null || echo unknown)"
echo ">>> PSM-WMA Local Memory + TTT A2 training"
echo ">>> source: root=$ROOT_GIT_SHA child=$CHILD_GIT_SHA"
echo ">>> mode: $MODE"
echo ">>> run: $RUN_DIR"
echo ">>> topology: ranks=$NPROC_PER_NODE B_stream/rank=$PSM_R09_B_TTT_B_STREAM T=$PSM_R09_B_TTT_TBPTT_STEPS GA/rank=$PSM_R09_B_TTT_ACTIVE_GA"
echo ">>> effective batch: $actual_global global consumers/update"
echo ">>> catalog: one global per-suite catalog -> deterministic rank shards -> rank-local stable slots"
echo ">>> max_iter=$MAX_ITER save_iter=$SAVE_ITER"
cd "$CHILD"
exec bash examples/launch_sft_action_policy_libero_edge_all.sh
