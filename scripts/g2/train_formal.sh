#!/usr/bin/env bash
# All PSM-WMA/Cosmos executable code comes from this Git checkout.
set -euo pipefail
if [[ $# != 2 ]]; then echo "Usage: $0 r1|r2 fresh|resume" >&2; exit 2; fi
PROFILE=$1; PHASE=$2
case "$PROFILE:$PHASE" in r1:fresh|r2:fresh|r1:resume|r2:resume) ;; *) echo "Invalid profile/phase" >&2; exit 2;; esac
REPO_ROOT=$(cd -- "$(dirname -- "$0")/../.." && pwd -P)
export REPO_ROOT
source "$REPO_ROOT/configs/g2/robocasa365_target_atomic.assets.env"
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
SRC="$REPO_ROOT/.g2_run_source"
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
JOB_NAME="$PROFILE"_g2_formal_30000_20261119
RECIPE="$G2_OUTPUT_ROOT/recipes/$PROFILE"_g2_formal_30000.json
JOB="$G2_OUTPUT_ROOT/psm_wma_v3/corrected_phase5/$JOB_NAME"
mkdir -p "$G2_OUTPUT_ROOT/logs"
LOG="$G2_OUTPUT_ROOT/logs/$PROFILE"_"$PHASE".log
if [[ "$PHASE" == fresh && -e "$JOB" ]]; then echo "Fresh Job already exists: $JOB" >&2; exit 4; fi
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
echo "G2 start $PROFILE $PHASE (source Root $ROOT_SHA Child $CHILD_SHA; GPU $G2_GPUS)"
# No GPU mutex, GPU-idle check or checkpoint retention/pruning.
"$G2_PYTHON" -m torch.distributed.run --standalone --nproc_per_node=4 --max_restarts=0 \
  examples/psm_wma_robocasa_corrected_phase5.py --phase "$PHASE" \
  --g2-recipe "$RECIPE" --job-name "$JOB_NAME" \
  --root-worktree "$SRC" --output-root "$G2_OUTPUT_ROOT" \
  --source-root "$G2_RAW_ROOT" --cache-root "$G2_CACHE_ROOT" \
  --dataset-index-root "$G2_INDEX_ROOT" --edge "$G2_EDGE_MODEL" \
  --vae "$G2_WAN_VAE" --base-checkpoint "$G2_G1_JOB_ROOT/checkpoints/iter_000027700" \
  --expected-root "$ROOT_SHA" --expected-child "$CHILD_SHA" \
  --num-workers 0 --world-size 4 >>"$LOG" 2>&1
