#!/usr/bin/env bash
# Parallel exact-window latent cache build for libero_90 only.
#
# 仿照 launch_parallel_cache_build.sh 的 4in1 模式，只跑 libero_90 单 suite
# × 5 shard 并发。复用 build_cosmos_libero_latent_dataset.py。
# 默认串行等所有 shard 完成；可传 BACKGROUND=1 切后台 nohup。
#
# 与 launch_parallel_cache_build.sh 差异：
#   - 只 1 suite（libero_90），数据源 /disk/rl/data/LIBERO_LeRobot_v3/libero_90
#   - 输出到 /disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1/libero_90
#   - 日志落到 artifacts/g0/cache_build_shared_vae_v1_libero_90_shard_*.log
#   - 完成后打印 sentinel 与 merge 提示，由调用方决定是否 merge / 上传 HF
set -uo pipefail

REPO_ROOT="/disk/rl/psm_wma"
COSMOS_ROOT="$REPO_ROOT/cosmos-framework"
VENV="$COSMOS_ROOT/.venv"
export LD_LIBRARY_PATH="$VENV/lib/python3.13/site-packages/nvidia/cu13/lib:$VENV/lib/python3.13/site-packages/nvidia/cudnn/lib:$VENV/lib/python3.13/site-packages/torch/lib"

OUTPUT_ROOT="/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1"
SUITE="libero_90"
DATASET_ROOT="/disk/rl/data/LIBERO_LeRobot_v3/$SUITE"
NUM_SHARDS="${NUM_SHARDS:-5}"
BACKGROUND="${BACKGROUND:-0}"

mkdir -p "$OUTPUT_ROOT/$SUITE" "$REPO_ROOT/artifacts/g0"

echo "[cache-build-libero_90] $SUITE shards=$NUM_SHARDS background=$BACKGROUND"
pids=()
for shard in $(seq 0 $((NUM_SHARDS - 1))); do
  log="$REPO_ROOT/artifacts/g0/cache_build_shared_vae_v1_${SUITE}_shard_${shard}.log"
  echo "  start $SUITE shard=$shard -> $log"
  (
    cd "$COSMOS_ROOT"
    "$VENV/bin/python" "$REPO_ROOT/tools/g0/build_cosmos_libero_latent_dataset.py" \
      --dataset-root "$DATASET_ROOT" \
      --output-root "$OUTPUT_ROOT/$SUITE" \
      --vae-path "$COSMOS_ROOT/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth" \
      --image-size 256 \
      --device cuda \
      --windowed \
      --episode-shard "$shard" \
      --num-shards "$NUM_SHARDS" \
      2>&1 | tee "$log"
  ) &
  pids+=($!)
done

echo "started ${#pids[@]} processes"

if [[ "$BACKGROUND" == "1" ]]; then
  echo "[cache-build-libero_90] BACKGROUND=1，shard PID=${pids[*]}；主脚本立即退出，监控请看 artifacts/g0/cache_build_shared_vae_v1_${SUITE}_shard_*.log"
  disown -a 2>/dev/null || true
  exit 0
fi

status=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    echo "process $pid failed"
    status=1
  fi
done

if (( status == 0 )); then
  echo "[cache-build-libero_90] ALL $NUM_SHARDS SHARDS COMPLETE"
  echo "$NUM_SHARDS shards done at $(date -Iseconds)" > "$REPO_ROOT/artifacts/g0/.libero_90_cache_build_done"
  echo "下一步 merge:"
  echo "  python3 $REPO_ROOT/tools/g0/merge_latent_cache_shards.py --output-root $OUTPUT_ROOT/$SUITE"
else
  echo "[cache-build-libero_90] 存在失败 shard，请查看 artifacts/g0/cache_build_shared_vae_v1_${SUITE}_shard_*.log"
  exit 1
fi