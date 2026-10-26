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
loader_workers=${NOTTT_LOADER_WORKERS:-0}
loader_args=()
# Same Job identity for all worker counts; the loader is transport, not training state.
default_job=no_ttt_packed128_droid_fresh_30k_world4_ga4
case "$loader_workers" in
    0)
        if [[ -n ${NOTTT_PREFETCH_FACTOR:-} || -n ${NOTTT_PERSISTENT_WORKERS:-} || -n ${NOTTT_LOADER_TIMEOUT_S:-} ]]; then
            echo "workers=0 disables prefetch/persistent/timeout options" >&2
            exit 2
        fi
        ;;
    1|2|4|8)
        loader_args=(--no-ttt-loader-workers "$loader_workers" --no-ttt-prefetch-factor "${NOTTT_PREFETCH_FACTOR:-1}"
            --no-ttt-loader-timeout-s "${NOTTT_LOADER_TIMEOUT_S:-120}")
        case "${NOTTT_PERSISTENT_WORKERS:-1}" in
            1) loader_args+=(--no-ttt-persistent-workers) ;;
            0) loader_args+=(--no-ttt-nonpersistent-workers) ;;
            *) echo "NOTTT_PERSISTENT_WORKERS must be 0/1" >&2; exit 2 ;;
        esac
        ;;
    *) echo "NOTTT_LOADER_WORKERS must be 0/1/2/4/8" >&2; exit 2 ;;
esac
export JOB_NAME=${JOB_NAME:-$default_job}
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
if [[ ! -f "$child_worktree/examples/psm_wma_robocasa_corrected_phase5.py" ]]; then
    echo "Missing expected V3 training source under $child_worktree" >&2
    exit 2
fi
# Owner-authorized 4GPU No-TTT: do NOT check or require Root/Child HEAD,
# Root Gitlink, Root dirty/untracked files or EXPECTED_ROOT/EXPECTED_CHILD.
# Only the named no_ttt_*_world4_ga4 profile gets this exception in Python.
# Use the project's training venv by default, not base conda torch.
if [[ -z ${PYTHON:-} && -x "$child_worktree/.venv/bin/python" ]]; then
    PYTHON="$child_worktree/.venv/bin/python"
fi
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONPATH="$child_worktree${PYTHONPATH:+:$PYTHONPATH}"
cd -- "$child_worktree"
exec "${PYTHON:-python}" -m torch.distributed.run --standalone --nproc_per_node=4 \
    examples/psm_wma_robocasa_corrected_phase5.py --no-ttt \
    --phase "$phase" --formal-execution-until "$execution_until" \
    --root-worktree "$root_worktree" \
    --output-root "$OUTPUT_ROOT" --job-name "$JOB_NAME" \
    --source-root "$SOURCE_ROOT" --cache-root "$CACHE_ROOT" --dataset-index-root "$DATASET_INDEX_ROOT" \
    --edge "$EDGE_POLICY_CHECKPOINT" --vae "$WAN_VAE_PATH" --base-checkpoint "$BASE_CHECKPOINT_PATH" \
    --num-workers 0 --world-size 4 --t 16 --b 8 --ga 4 --k 4 \
    --max-iter 30000 --warmup 500 --save-iter 100 "${loader_args[@]}"
