#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/cosmos-framework/.venv/bin/python}"
BUILDER="$SCRIPT_DIR/build_cosmos_robocasa_latent_dataset.py"
MERGER="$SCRIPT_DIR/merge_robocasa_latent_shards.py"

if [[ $# -eq 0 ]]; then
  echo "usage: CUDA_VISIBLE_DEVICES=0,1,... $0 <builder args>" >&2
  echo "example: $0 --source-root ... --output-root ... --vae-path ... --suite robocasa365_target_atomic --episode-limit 10" >&2
  exit 2
fi

OUTPUT_ROOT=""
ARGS=("$@")
for ((i=0; i<${#ARGS[@]}; i++)); do
  case "${ARGS[$i]}" in
    --output-root)
      if (( i + 1 >= ${#ARGS[@]} )); then
        echo "[error] --output-root requires a value" >&2
        exit 2
      fi
      OUTPUT_ROOT="${ARGS[$((i+1))]}"
      ;;
    --output-root=*)
      OUTPUT_ROOT="${ARGS[$i]#--output-root=}"
      ;;
    --task-shard|--num-task-shards|--task-shard=*|--num-task-shards=*)
      echo "[error] shard arguments are owned by this launcher; do not pass ${ARGS[$i]}" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$OUTPUT_ROOT" ]]; then
  echo "[error] --output-root is required" >&2
  exit 2
fi

GPU_SPEC="${ROBOCASA_GPUS:-${CUDA_VISIBLE_DEVICES:-}}"
if [[ -z "$GPU_SPEC" ]]; then
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "[error] set CUDA_VISIBLE_DEVICES or ROBOCASA_GPUS" >&2
    exit 2
  fi
  GPU_SPEC="$(nvidia-smi --query-gpu=index --format=csv,noheader | paste -sd, -)"
fi

IFS=',' read -r -a GPUS <<< "$GPU_SPEC"
NUM_GPUS="${#GPUS[@]}"
if (( NUM_GPUS <= 0 )); then
  echo "[error] no GPUs resolved from: $GPU_SPEC" >&2
  exit 2
fi

mkdir -p "$OUTPUT_ROOT/logs"
export PYTHONPATH="$REPO_ROOT/cosmos-framework:${PYTHONPATH:-}"

echo "[parallel] GPUs=$GPU_SPEC processes=$NUM_GPUS"
echo "[parallel] output_root=$OUTPUT_ROOT"

PIDS=()
for ((rank=0; rank<NUM_GPUS; rank++)); do
  gpu="${GPUS[$rank]}"
  log="$OUTPUT_ROOT/logs/robocasa_cache_shard_$(printf '%04d' "$rank")_of_$(printf '%04d' "$NUM_GPUS").log"
  echo "[launch] shard=$rank/$NUM_GPUS gpu=$gpu log=$log"
  (
    CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON_BIN" "$BUILDER"       "${ARGS[@]}"       --device cuda:0       --task-shard "$rank"       --num-task-shards "$NUM_GPUS"
  ) >"$log" 2>&1 &
  PIDS+=("$!")
done

failed=0
for ((rank=0; rank<NUM_GPUS; rank++)); do
  if wait "${PIDS[$rank]}"; then
    echo "[done] shard=$rank/$NUM_GPUS"
  else
    status=$?
    echo "[fail] shard=$rank/$NUM_GPUS exit=$status" >&2
    failed=1
  fi
done

if (( failed != 0 )); then
  echo "[error] one or more RoboCasa cache shards failed; global manifest not merged" >&2
  exit 1
fi

"$PYTHON_BIN" "$MERGER"   --output-root "$OUTPUT_ROOT"   --num-task-shards "$NUM_GPUS"

echo "[done] parallel RoboCasa cache build complete: $OUTPUT_ROOT"
