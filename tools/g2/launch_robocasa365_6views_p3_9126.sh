#!/usr/bin/env bash
# RoboCasa365 target-atomic: 9,126 episode G2 Full Map + sixview + P3 indexed SG.
# Run manually from the V3 checkout: bash tools/g2/launch_robocasa365_6views_p3_9126.sh
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
BACKUP="$(dirname -- "$ROOT")"
NAV="$BACKUP/nav_sg"
FLAT="/mnt/data1/data_v2_0617/robocasa365_v3_flat"
PLAN="$FLAT/.g2_atomic_9126_plan_20261113"
OUT="$FLAT/robocasa365-target-atomic-6views"
WORK="$BACKUP/.g2_atomic_6views_v3_9126_work_20261114"
PY="$ROOT/cosmos-framework/.venv/bin/python"
NAV_SETUP="$NAV/.g2_catkin_ws/devel/setup.bash"
NATIVE_BIN="$NAV/.g2_catkin_ws/devel/lib/mapping/gt_direct_color_episode"
EXPECTED_V3_BASE="057d71255e2cbd2b11ba76aad258ff101d682b3b"
EXPECTED_NAV_HEAD="70eb7b447e65d793b0ebe18b258291ce46f057c1"
EXPECTED_PLAN_SHA="f1dfcc5243a466a1c1a885e407fade7ef860eb72079494f3cc7dc90334283643"

# Fail closed before starting workers. This is the approved simulation-only
# P3 recipe; never weaken the native nav_sg collision-mesh checker.
[[ "$(git -C "$ROOT" branch --show-current)" == "V3" ]] || { echo "Expected V3 branch" >&2; exit 2; }
git -C "$ROOT" merge-base --is-ancestor "$EXPECTED_V3_BASE" HEAD || { echo "Unapproved V3 code ancestry" >&2; exit 2; }
git -C "$ROOT" diff --quiet HEAD -- g2/offline/atomic_6views_run.py g2/offline/atomic_6views_snapshots.py g2/offline/scene_graph_compact_v3.py || { echo "G2 production source is modified" >&2; exit 2; }
[[ "$(git -C "$NAV" rev-parse HEAD)" == "$EXPECTED_NAV_HEAD" ]] || { echo "nav_sg G2 HEAD mismatch" >&2; exit 2; }
[[ -f "$PLAN/index.json" && "$(sha256sum "$PLAN/index.json" | awk '{print $1}')" == "$EXPECTED_PLAN_SHA" ]] || { echo "Immutable 9,126 plan mismatch" >&2; exit 2; }
[[ -x "$PY" && -f "$NAV_SETUP" && -x "$NATIVE_BIN" ]] || { echo "Missing Python, ROS setup, or native binary" >&2; exit 2; }
[[ ! -e "$OUT" || ( -d "$OUT" && ! -L "$OUT" ) ]] || { echo "Invalid output root" >&2; exit 2; }
[[ ! -e "$WORK" || ( -d "$WORK" && ! -L "$WORK" ) ]] || { echo "Invalid work root" >&2; exit 2; }

set +u
source /mnt/data/shenzhen/anaconda3/etc/profile.d/conda.sh
conda activate "$BACKUP/.nav_sg_g2_noetic"
set -u

cd "$ROOT"
export PYTHONPATH="$ROOT/.g2_runtime_deps_py313:$ROOT"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

mkdir -p "$OUT" "$WORK" "$ROOT/.g2_atomic_6views_prod/logs"
LOG="$ROOT/.g2_atomic_6views_prod/logs/g2_p3_9126_$(date -u +'%Y%m%dT%H%M%SZ').log"
exec > >(tee -a "$LOG") 2>&1
echo "G2_P3_PRODUCTION_BEGIN_UTC=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "G2_P3_LAUNCHER=$ROOT/tools/g2/launch_robocasa365_6views_p3_9126.sh"
echo "G2_V3_HEAD=$(git -C "$ROOT" rev-parse HEAD)"
echo "G2_NAV_HEAD=$(git -C "$NAV" rev-parse HEAD)"
echo "G2_PLAN_SHA=$EXPECTED_PLAN_SHA"
echo "G2_PREEXISTING_COMPLETED=$(find "$OUT" -type f -name COMPLETE.json | wc -l)"
echo "G2_WORK_ROOT=$WORK"
echo "G2_OUTPUT_ROOT=$OUT"
echo "G2_LOG=$LOG"
echo "G2_CARDS=4,5,6,7 G2_WORKERS_PER_GPU=8 G2_MAX_ATTEMPTS=2 G2_EXPECTED_TOTAL=9126"
df -h /mnt/data /mnt/data1

set +e
nice -n 15 ionice -c3 "$PY" -u -m g2.offline.atomic_6views_run run \
  --plan-root "$PLAN" \
  --output-root "$OUT" \
  --work-root "$WORK" \
  --expected 9126 --batch-size 100 --resume \
  --gpus 4,5,6,7 --workers-per-gpu 8 \
  --ros-port-base 21500 --max-attempts 2 \
  --nav-repo "$NAV" \
  --nav-setup "$NAV_SETUP" \
  --native-binary "$NATIVE_BIN" \
  --sim-direct-geometry-only --sim-color-only \
  --scene-event-index --sg-event-index --lazy-texel-decode --sim-direct-material \
  --robot-pose-marker --robot-pose-marker-style game_arrow \
  --robot-pose-marker-outline --robot-pose-marker-outline-width 1.0 \
  --robot-pose-marker-outline-color '#E1E5EA' \
  --robot-pose-marker-fill-color '#454B53' \
  --robot-pose-marker-length-px 26.6 --robot-pose-marker-relief raised \
  --manual-start --allow-experimental
RC=$?
set -e
echo "G2_P3_PRODUCTION_EXIT_CODE=$RC"
echo "G2_P3_PRODUCTION_END_UTC=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
exit "$RC"
