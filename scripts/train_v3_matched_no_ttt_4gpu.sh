#!/usr/bin/env bash
# Isolated world4/GA4 No-TTT profile: same nominal effective batch as G1
# (4 ranks * B8 * T16 * GA4 = 2048), but a different rank/episode partition.
# Real DROID/Cache/S0/GPU acceptance is separate; never touch a G1 job.
set -euo pipefail
if [[ $# -ne 2 || ( $1 != fresh && $1 != resume ) ]]; then
    echo "Usage: $0 {fresh|resume} EXECUTION_UNTIL" >&2
    exit 2
fi
phase=$1
execution_until=$2
for required in OUTPUT_ROOT SOURCE_ROOT CACHE_ROOT DATASET_INDEX_ROOT EDGE_POLICY_CHECKPOINT \
    WAN_VAE_PATH BASE_CHECKPOINT_PATH; do
    if [[ -z ${!required:-} ]]; then
        echo "Missing required environment variable: $required" >&2
        exit 2
    fi
done
export JOB_NAME=${JOB_NAME:-no_ttt_packed128_droid_fresh_30k_world4_ga4}
if [[ $JOB_NAME != no_ttt_*_world4_ga4 ]]; then
    echo "4GPU profile requires a distinct no_ttt_*_world4_ga4 job, never G1/8GPU" >&2
    exit 2
fi
if [[ -n ${CUDA_VISIBLE_DEVICES:-} && ${CUDA_VISIBLE_DEVICES} != "4,5,6,7" ]]; then
    echo "4GPU profile requires CUDA_VISIBLE_DEVICES=4,5,6,7; refusing other devices" >&2
    exit 2
fi
export CUDA_VISIBLE_DEVICES=4,5,6,7
root_worktree=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
child_worktree="$root_worktree/cosmos-framework"
# Capture the observed source SHA pair. No manually maintained EXPECTED_* vars;
# same-job Resume still checks the immutable saved source/config identity.
actual_root=$(git -C "$root_worktree" rev-parse HEAD)
actual_child=$(git -C "$child_worktree" rev-parse HEAD)
gitlink=$(git -C "$root_worktree" ls-tree HEAD cosmos-framework | awk '{print $3}')
if [[ "$actual_child" != "$gitlink" || ${#actual_root} -ne 40 || ${#actual_child} -ne 40 ]]; then
    echo "Root Gitlink and Child checkout are inconsistent; refusing 4GPU launch" >&2
    exit 2
fi
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONPATH="$child_worktree${PYTHONPATH:+:$PYTHONPATH}"
cd -- "$child_worktree"
exec "${PYTHON:-python}" -m torch.distributed.run --standalone --nproc_per_node=4 \
    examples/psm_wma_robocasa_corrected_phase5.py --no-ttt \
    --phase "$phase" --formal-execution-until "$execution_until" \
    --root-worktree "$root_worktree" --expected-root "$actual_root" --expected-child "$actual_child" \
    --output-root "$OUTPUT_ROOT" --job-name "$JOB_NAME" \
    --source-root "$SOURCE_ROOT" --cache-root "$CACHE_ROOT" --dataset-index-root "$DATASET_INDEX_ROOT" \
    --edge "$EDGE_POLICY_CHECKPOINT" --vae "$WAN_VAE_PATH" --base-checkpoint "$BASE_CHECKPOINT_PATH" \
    --num-workers 0 --world-size 4 --t 16 --b 8 --ga 4 --k 4 \
    --max-iter 30000 --warmup 500 --save-iter 100
