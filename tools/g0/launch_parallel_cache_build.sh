#!/usr/bin/env bash
# Parallel exact-window latent cache build: 4 suites x 5 shards = 20 processes.
set -euo pipefail

REPO_ROOT="/disk/rl/psm_wma"
COSMOS_ROOT="$REPO_ROOT/cosmos-framework"
VENV="$COSMOS_ROOT/.venv"
export LD_LIBRARY_PATH="$VENV/lib/python3.13/site-packages/nvidia/cu13/lib:$VENV/lib/python3.13/site-packages/nvidia/cudnn/lib:$VENV/lib/python3.13/site-packages/torch/lib"

OUTPUT_ROOT="/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1"
mkdir -p "$OUTPUT_ROOT"
mkdir -p "$REPO_ROOT/artifacts/g0"

pids=()
for suite in libero_spatial libero_object libero_goal libero_10; do
  for shard in 0 1 2 3 4; do
    log="$REPO_ROOT/artifacts/g0/cache_build_shared_vae_v1_${suite}_shard_${shard}.log"
    echo "[cache-build] $suite shard=$shard"
    (
      cd "$COSMOS_ROOT"
      "$VENV/bin/python" "$REPO_ROOT/tools/g0/build_cosmos_libero_latent_dataset.py" \
        --dataset-root "/disk/rl/data/LIBERO_LeRobot_v3/$suite" \
        --output-root "$OUTPUT_ROOT/$suite" \
        --vae-path "$COSMOS_ROOT/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth" \
        --image-size 256 \
        --device cuda \
        --windowed \
        --episode-shard "$shard" \
        --num-shards 5 \
        2>&1 | tee "$log"
    ) &
    pids+=($!)
  done
done

echo "started ${#pids[@]} processes"
for pid in "${pids[@]}"; do
  wait "$pid" || echo "process $pid failed"
done
echo "[cache-build] ALL SHARDS COMPLETE"
