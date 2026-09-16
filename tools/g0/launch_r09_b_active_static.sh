#!/bin/bash
# D6: launch the active Local-Memory CPU/static smoke over the real libero4in1
# latent cache.  CPU-only, read-only, no checkpoint, no GPU, no trainer.
#
# Env (defaults match tools/g0/launch_r09_b1_smoke.sh):
#   LIBERO_ROOT               LIBERO_LeRobot_v3 PARENT dir (4 suite subdirs)
#   LIBERO_LATENT_CACHE_ROOT  exact-window shared-VAE latent cache root
#
# Usage:
#   bash tools/g0/launch_r09_b_active_static.sh \
#     --members 1 --output-json artifacts/g0/active_static_probe/probe.json
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRAMEWORK="$ROOT/cosmos-framework"
PYTHON="$FRAMEWORK/.venv/bin/python"
PROBE="$ROOT/tools/g0/probe_r09_b_active_static.py"

if [[ ! -x "$PYTHON" ]]; then
    echo "ERROR: interpreter not found: $PYTHON" >&2
    exit 1
fi

: "${LIBERO_ROOT:=/disk/rl/data/LIBERO_LeRobot_v3}"
: "${LIBERO_LATENT_CACHE_ROOT:=/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1}"

if [[ ! -d "$LIBERO_LATENT_CACHE_ROOT" ]]; then
    echo "ERROR: LIBERO_LATENT_CACHE_ROOT not found: $LIBERO_LATENT_CACHE_ROOT" >&2
    exit 1
fi
for _s in libero_spatial libero_object libero_goal libero_10; do
    if [[ ! -f "$LIBERO_ROOT/$_s/meta/info.json" ]]; then
        echo "ERROR: LIBERO_ROOT/$_s/meta/info.json missing (got LIBERO_ROOT=$LIBERO_ROOT)" >&2
        exit 1
    fi
done

# CPU-only by construction: the probe never builds the LLM and never moves to CUDA.
export CUDA_VISIBLE_DEVICES=""
export LIBERO_ROOT LIBERO_LATENT_CACHE_ROOT
export LIBERO_NUM_WORKERS=0
export LIBERO_LATENT_CACHE_VERIFY_RATIO=0
export PSM_R08_LOCAL_HISTORY_ENABLED=1
export PSM_R08_LOCAL_HISTORY_HORIZON=16
export PSM_R09_B_TTT_ENABLED=1
export PSM_R09_B_TTT_ACTIVE=0
export TOKENIZERS_PARALLELISM=false

echo "== D6 active Local-Memory CPU/static smoke =="
echo "interpreter : $PYTHON"
echo "LIBERO_ROOT : $LIBERO_ROOT"
echo "cache root  : $LIBERO_LATENT_CACHE_ROOT"
echo

exec "$PYTHON" "$PROBE" "$@"
