#!/usr/bin/env bash
# All PSM-WMA/Cosmos executable code comes from this Git checkout.
set -euo pipefail
if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 r1|r2 fresh|resume|benchmark [job-tag]" >&2
  exit 2
fi
PROFILE=$1; PHASE=$2; TAG=${3:-}
case "$PROFILE:$PHASE" in
  r1:fresh|r2:fresh|r1:resume|r2:resume|r1:benchmark|r2:benchmark) ;;
  *) echo "Invalid profile or phase" >&2; exit 2 ;;
esac
if [[ $# -eq 3 && ! "$TAG" =~ ^[a-z0-9][a-z0-9_-]{0,47}$ ]]; then
  echo "Invalid job tag" >&2; exit 2
fi
LOADER=${G2_DATA_LOADER:-sync}
RAW_WORKERS=0
LOADER_ARGS=()
case "$LOADER" in
  sync) ;;
  raw1|raw2|raw4|raw8) RAW_WORKERS=${LOADER#raw} ;;
  spawn1|spawn2|spawn4|spawn8) LOADER_ARGS+=(--g2-spawn-workers "${LOADER#spawn}") ;;
  *) echo "Expected sync, raw1/2/4/8 or spawn1/2/4/8" >&2; exit 2 ;;
esac
export PSM_V3_COMPACT_CACHED_VIDEO=${PSM_V3_COMPACT_CACHED_VIDEO:-0}
export PSM_G2_EPISODE_CACHE_SIZE=${PSM_G2_EPISODE_CACHE_SIZE:-4}
export PSM_G2_CAP2_TOKEN_CACHE=${PSM_G2_CAP2_TOKEN_CACHE:-0}
case "$PSM_G2_CAP2_TOKEN_CACHE" in
  0|1) ;;
  *) echo "Invalid CAP2 token cache setting" >&2; exit 2 ;;
esac
case "$PSM_V3_COMPACT_CACHED_VIDEO:$PSM_G2_EPISODE_CACHE_SIZE" in
  0:4|0:16|1:4|1:16) ;;
  *) echo "Invalid compact video or episode cache setting" >&2; exit 2 ;;
esac
BENCH_ARGS=()
if [[ "$PHASE" == benchmark ]]; then
  if [[ -z "$TAG" ]]; then echo "Benchmark requires a new job tag" >&2; exit 2; fi
  STEPS=${G2_BENCHMARK_STEPS:-10}
  case "$STEPS" in 2|10) ;; *) echo "Benchmark steps must be 2 or 10" >&2; exit 2 ;; esac
  BENCH_ARGS=(--g2-benchmark-steps "$STEPS")
  case "${G2_PROFILE_TRACE:-0}" in
    0) ;;
    1) BENCH_ARGS+=(--g2-profile-trace) ;;
    *) echo "G2_PROFILE_TRACE must be 0 or 1" >&2; exit 2 ;;
  esac
  JOB_NAME="${PROFILE}_g2_bench_$TAG"
  EXEC_PHASE=fresh
else
  if [[ "${G2_PROFILE_TRACE:-0}" != 0 ]]; then echo "Trace requires benchmark" >&2; exit 2; fi
  if [[ -z "$TAG" && "$LOADER:$PSM_V3_COMPACT_CACHED_VIDEO:$PSM_G2_EPISODE_CACHE_SIZE:$PSM_G2_CAP2_TOKEN_CACHE" != sync:0:4:0 ]]; then
    echo "Opt-in loader settings require a distinct formal job tag" >&2; exit 2
  fi
  JOB_NAME="${PROFILE}_g2_formal_30000_${TAG:-20261119}"
  EXEC_PHASE=$PHASE
fi
REPO_ROOT=$(cd -- "$(dirname -- "$0")/../.." && pwd -P)
export REPO_ROOT
source "$REPO_ROOT/configs/g2/robocasa365_target_atomic.assets.env"
if [[ "$PHASE" == benchmark && "$G2_GPUS" != 4,5,6,7 ]]; then
  echo "Issue #90 diagnostics use GPU 4,5,6,7" >&2; exit 2
fi
if [[ ! -x "$G2_PYTHON" ]]; then echo "Missing Python env: $G2_PYTHON" >&2; exit 3; fi
if [[ ! -f "$REPO_ROOT/cosmos-framework/examples/psm_wma_robocasa_corrected_phase5.py" ]]; then
  echo "Missing Cosmos submodule: clone --recurse-submodules" >&2; exit 3
fi
ROOT_SHA=$(git -C "$REPO_ROOT" rev-parse HEAD)
CHILD_SHA=$(git -C "$REPO_ROOT" ls-tree HEAD cosmos-framework | awk '{print $3}')
if [[ $(git -C "$REPO_ROOT/cosmos-framework" rev-parse HEAD) != "$CHILD_SHA" ]]; then
  echo "Root Gitlink / Child mismatch" >&2; exit 3
fi
# Nested under repository, ignored by Git. Never execute external scratch code.
SRC="$REPO_ROOT/.g2_run_source_${ROOT_SHA}_$PROFILE"
if [[ ! -d "$SRC" ]]; then git -C "$REPO_ROOT" worktree add --detach "$SRC" "$ROOT_SHA"; fi
if [[ ! -e "$SRC/cosmos-framework/.git" ]]; then
  if [[ -n $(ls -A "$SRC/cosmos-framework" 2>/dev/null) ]]; then
    echo "Nonempty uninitialized Cosmos child" >&2; exit 3
  fi
  git clone -q --no-checkout "$REPO_ROOT/cosmos-framework" "$SRC/cosmos-framework"
  git -C "$SRC/cosmos-framework" checkout -q --detach "$CHILD_SHA"
fi
if [[ $(git -C "$SRC" rev-parse HEAD) != "$ROOT_SHA" ||
      $(git -C "$SRC/cosmos-framework" rev-parse HEAD) != "$CHILD_SHA" ||
      -n $(git -C "$SRC" status --porcelain) ||
      -n $(git -C "$SRC/cosmos-framework" status --porcelain) ]]; then
  echo "Runtime repository source dirty or mismatched" >&2; exit 4
fi
RECIPE="$G2_OUTPUT_ROOT/recipes/$PROFILE"_g2_formal_30000.json
JOB="$G2_OUTPUT_ROOT/psm_wma_v3/corrected_phase5/$JOB_NAME"
mkdir -p "$G2_OUTPUT_ROOT/logs"
LOG="$G2_OUTPUT_ROOT/logs/${JOB_NAME}_${PHASE}.log"
if [[ -z "$TAG" ]]; then LOG="$G2_OUTPUT_ROOT/logs/${PROFILE}_${PHASE}.log"; fi
if [[ "$EXEC_PHASE" == fresh && ( -e "$JOB" || -L "$JOB" ) ]]; then echo "Fresh Job already exists: $JOB" >&2; exit 4; fi
if [[ "$PHASE" == resume && ! -f "$JOB/checkpoints/latest_checkpoint.txt" ]]; then
  echo "Resume requires latest same-job checkpoint" >&2; exit 4
fi
export PYTHONPATH="$SRC:$SRC/cosmos-framework"
export COSMOS_TRAINING=1 PYTHONNOUSERSITE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
"$G2_PYTHON" "$SRC/scripts/g2/materialize_formal_recipe.py" --profile "$PROFILE" --root "$SRC" --output "$RECIPE"
cd "$SRC/cosmos-framework"
"$G2_PYTHON" -m examples.psm_wma_robocasa_g2_recipe --check "$RECIPE"
export CUDA_VISIBLE_DEVICES="$G2_GPUS"
echo "G2 start $PROFILE $PHASE (source Root $ROOT_SHA Child $CHILD_SHA, GPU $G2_GPUS)"
printf 'job=%s loader=%s compact=%s episode_cache=%s cap2_cache=%s trace=%s\n' \
  "$JOB_NAME" "$LOADER" "$PSM_V3_COMPACT_CACHED_VIDEO" "$PSM_G2_EPISODE_CACHE_SIZE" "$PSM_G2_CAP2_TOKEN_CACHE" "${G2_PROFILE_TRACE:-0}" >>"$LOG"
# No GPU mutex, GPU-idle check or checkpoint retention/pruning.
"$G2_PYTHON" -m torch.distributed.run --standalone --nproc_per_node=4 --max_restarts=0 \
  examples/psm_wma_robocasa_corrected_phase5.py --phase "$EXEC_PHASE" \
  --g2-recipe "$RECIPE" --job-name "$JOB_NAME" "${BENCH_ARGS[@]}" "${LOADER_ARGS[@]}" \
  --root-worktree "$SRC" --output-root "$G2_OUTPUT_ROOT" \
  --source-root "$G2_RAW_ROOT" --cache-root "$G2_CACHE_ROOT" \
  --dataset-index-root "$G2_INDEX_ROOT" --edge "$G2_EDGE_MODEL" \
  --vae "$G2_WAN_VAE" --base-checkpoint "$G2_G1_JOB_ROOT/checkpoints/iter_000027700" \
  --expected-root "$ROOT_SHA" --expected-child "$CHILD_SHA" \
  --num-workers "$RAW_WORKERS" --world-size 4 >>"$LOG" 2>&1
