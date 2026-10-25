#!/usr/bin/env bash
# Matched data/outer objective, independent model and job state. CPU review is not GPU authorization.
set -euo pipefail
if [[ $# -ne 2 || ( $1 != fresh && $1 != resume ) ]]; then
    echo "Usage: $0 {fresh|resume} EXECUTION_UNTIL" >&2
    exit 2
fi
phase=$1
execution_until=$2
for required in OUTPUT_ROOT SOURCE_ROOT CACHE_ROOT DATASET_INDEX_ROOT EDGE_POLICY_CHECKPOINT \
    WAN_VAE_PATH BASE_CHECKPOINT_PATH EXPECTED_ROOT EXPECTED_CHILD; do
    if [[ -z ${!required:-} ]]; then
        echo "Missing required environment variable: $required" >&2
        exit 2
    fi
done
export JOB_NAME=${JOB_NAME:-no_ttt_packed128_droid_fresh_30k}
if [[ $JOB_NAME != no_ttt_* ]]; then
    echo "Matched baseline requires a separate JOB_NAME beginning no_ttt_; never use G1" >&2
    exit 2
fi
root_worktree=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONPATH="$root_worktree/cosmos-framework${PYTHONPATH:+:$PYTHONPATH}"
cd -- "$root_worktree/cosmos-framework"
exec "${PYTHON:-python}" -m torch.distributed.run --standalone --nproc_per_node=8 \
    examples/psm_wma_robocasa_corrected_phase5.py --no-ttt \
    --phase "$phase" --formal-execution-until "$execution_until" \
    --root-worktree "$root_worktree" --expected-root "$EXPECTED_ROOT" --expected-child "$EXPECTED_CHILD" \
    --output-root "$OUTPUT_ROOT" --job-name "$JOB_NAME" \
    --source-root "$SOURCE_ROOT" --cache-root "$CACHE_ROOT" --dataset-index-root "$DATASET_INDEX_ROOT" \
    --edge "$EDGE_POLICY_CHECKPOINT" --vae "$WAN_VAE_PATH" --base-checkpoint "$BASE_CHECKPOINT_PATH" \
    --num-workers 0 --world-size 8 --t 16 --b 8 --ga 2 --k 4 \
    --max-iter 30000 --warmup 500 --save-iter 100
