#!/usr/bin/env bash
# Canonical corrected Phase5 formal profile. Execution still requires Owner authorization.
set -euo pipefail
if [[ $# -lt 2 || $# -gt 3 || ( $1 != fresh && $1 != resume ) ]]; then
    echo "Usage: $0 {fresh|resume} EXECUTION_UNTIL [--owner-authorized-g1-cross-pair-resume]" >&2
    exit 2
fi
phase=$1
execution_until=$2
owner_args=()
if [[ $# == 3 ]]; then
    if [[ $phase != resume || $3 != --owner-authorized-g1-cross-pair-resume || ${JOB_NAME:-} != packed128_droid_fresh_g1_20261019 ]]; then
        echo "Owner cross-pair flag is only valid for the named G1 Resume" >&2
        exit 2
    fi
    owner_args=("$3")
fi
root_worktree=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
# The named G1 job must resume from its latest committed DCP even after a
# GitHub bookkeeping or implementation HEAD change. These SHAs are recorded
# as current runtime provenance, not compared against historical G1 HEAD.
# All non-source config/digest and per-rank Local state checks remain strict.
if [[ "$phase" == resume && "${JOB_NAME:-}" == packed128_droid_fresh_g1_20261019 ]]; then
    EXPECTED_ROOT="$(git -C "$root_worktree" rev-parse HEAD)"
    EXPECTED_CHILD="$(git -C "$root_worktree/cosmos-framework" rev-parse HEAD)"
    export EXPECTED_ROOT EXPECTED_CHILD
    echo "G1 Resume: current Root/Child recorded as provenance; no historical HEAD pin"
fi
for required in OUTPUT_ROOT SOURCE_ROOT CACHE_ROOT DATASET_INDEX_ROOT EDGE_POLICY_CHECKPOINT \
    WAN_VAE_PATH BASE_CHECKPOINT_PATH JOB_NAME EXPECTED_ROOT EXPECTED_CHILD; do
    if [[ -z ${!required:-} ]]; then
        echo "Missing required environment variable: $required" >&2
        exit 2
    fi
done
export HF_HUB_OFFLINE=1
export PYTHONPATH="$root_worktree/cosmos-framework${PYTHONPATH:+:$PYTHONPATH}"
cd -- "$root_worktree/cosmos-framework"
exec "${PYTHON:-python}" -m torch.distributed.run --standalone --nproc_per_node=8 \
    examples/psm_wma_robocasa_corrected_phase5.py \
    --phase "$phase" --formal-execution-until "$execution_until" \
    --root-worktree "$root_worktree" --expected-root "$EXPECTED_ROOT" --expected-child "$EXPECTED_CHILD" \
    --output-root "$OUTPUT_ROOT" --job-name "$JOB_NAME" \
    --source-root "$SOURCE_ROOT" --cache-root "$CACHE_ROOT" --dataset-index-root "$DATASET_INDEX_ROOT" \
    --edge "$EDGE_POLICY_CHECKPOINT" --vae "$WAN_VAE_PATH" --base-checkpoint "$BASE_CHECKPOINT_PATH" \
    --num-workers 0 --world-size 8 --t 16 --b 8 --ga 2 --k 4 \
    --max-iter 30000 --warmup 500 --save-iter 100 "${owner_args[@]}"
