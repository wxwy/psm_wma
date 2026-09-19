#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHILD="$ROOT/cosmos-framework"
VERIFY_OUTPUT="${VERIFY_OUTPUT:-/tmp/psm_wma_resume_preflight.json}" bash "$ROOT/scripts/verify.sh" >/dev/null
export LIBERO_ROOT="${LIBERO_ROOT:-/disk/rl/data/LIBERO_LeRobot_v3}"
export LIBERO_LATENT_CACHE_ROOT="${LIBERO_LATENT_CACHE_ROOT:-/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1}"
export EDGE_POLICY_CHECKPOINT="${EDGE_POLICY_CHECKPOINT:-/disk/rl/models/Cosmos3-Edge-Policy-DROID}"
export BASE_CHECKPOINT_PATH="${BASE_CHECKPOINT_PATH:-$CHILD/examples/checkpoints/Cosmos3-Edge-Policy-DROID-dcp}"
export WAN_VAE_PATH="${WAN_VAE_PATH:-$CHILD/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth}"
export OUTPUT_ROOT="${OUTPUT_ROOT:-$ROOT/outputs/train_local_memory_a2}"
export RUN_NAME="edge_libero_4in1_localmem_active"
RUN_DIR="$OUTPUT_ROOT/cosmos3_action_libero/action_sft/$RUN_NAME"
[[ -d "$RUN_DIR/checkpoints" ]] || { echo "ERROR: no checkpoint directory: $RUN_DIR/checkpoints" >&2; exit 2; }

export PSM_R08_LOCAL_HISTORY_ENABLED=1
export PSM_R09_B_TTT_ENABLED=1
export PSM_R09_B_TTT_ACTIVE=1
export PSM_R09_B_TTT_MEMBER_LAYOUT="${PSM_R09_B_TTT_MEMBER_LAYOUT:-a2}"
export PSM_R09_B_TTT_B_STREAM="${PSM_R09_B_TTT_B_STREAM:-8}"
export PSM_R09_B_TTT_ACTIVE_GA="${PSM_R09_B_TTT_ACTIVE_GA:-16}"
export PSM_R09_B_TTT_TBPTT_STEPS="${PSM_R09_B_TTT_TBPTT_STEPS:-16}"
export PSM_ACTIVE_PREFETCH_DEPTH="${PSM_ACTIVE_PREFETCH_DEPTH:-4}"
export LIBERO_MAX_EPISODES="${LIBERO_MAX_EPISODES:-100000}"
export LIBERO_LATENT_CACHE_VERIFY_RATIO="${LIBERO_LATENT_CACHE_VERIFY_RATIO:-0}"
export LIBERO_NUM_WORKERS="${LIBERO_NUM_WORKERS:-0}"export LIBERO_PREFETCH_FACTOR="${LIBERO_PREFETCH_FACTOR:-1}"
export TOML_FILE=examples/toml/sft_config/action_policy_libero_edge_all_localmem_active.toml
export NPROC_PER_NODE=1
export MAX_ITER="${MAX_ITER:-5000}"
export SAVE_ITER="${SAVE_ITER:-50}"
export EXTRA_TAIL_OVERRIDES="trainer.max_iter=$MAX_ITER checkpoint.save_iter=$SAVE_ITER trainer.logging_iter=1 ${EXTRA_TAIL_OVERRIDES:-}"
export DISABLE_AUTO_RESUME=0

echo ">>> PSM-WMA resume A2 training"
echo ">>> run: $RUN_DIR"
echo ">>> launcher will select the largest iter_* checkpoint"
cd "$CHILD"
exec bash examples/launch_sft_action_policy_libero_edge_all.sh