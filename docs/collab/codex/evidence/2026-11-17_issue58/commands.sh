#!/usr/bin/env bash
# Existing CPU interpreter only; no installation, GPU, private data or network.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
G2_CHECK_PYTHON=${ISSUE58_PYTHON:-/workspace/.venvs/g2-view-vae-52/bin/python}
G2_CHECK_OUT=${ISSUE58_OUT:-docs/collab/codex/evidence/2026-11-17_issue58/final}
if [ -e "$G2_CHECK_OUT" ]; then
  echo 'Select a fresh ISSUE58_OUT; earlier evidence is immutable' >&2
  exit 2
fi
mkdir -p "$G2_CHECK_OUT"
export ISSUE58_AUDIT_OUT="$G2_CHECK_OUT"
export ISSUE58_TEST_TEMP
ISSUE58_TEST_TEMP=$(mktemp -d -t issue58-cpu-XXXXXXXX)
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
"$G2_CHECK_PYTHON" docs/collab/codex/evidence/2026-11-17_issue58/cpu_audit.py before
"$G2_CHECK_PYTHON" -m pytest -q -p no:cacheprovider --tb=short g2/tests/test_view_vae_*.py \
 g2/tests/test_scene_view_event_index.py g2/tests/test_scene_view_index_package.py \
 g2/tests/test_scene_graph_compact_v3.py --junitxml="$G2_CHECK_OUT/pr53.xml" >"$G2_CHECK_OUT/pr53.log" 2>&1
"$G2_CHECK_PYTHON" -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_stage_a_*.py \
 --junitxml="$G2_CHECK_OUT/stage_a.xml" >"$G2_CHECK_OUT/stage_a.log" 2>&1
"$G2_CHECK_PYTHON" -m pytest -q -p no:cacheprovider --tb=short -rs \
 g2/tests/test_atomic_6views_run.py g2/tests/test_robot_pose_marker.py g2/tests/test_viewer_install.py \
 --junitxml="$G2_CHECK_OUT/related.xml" >"$G2_CHECK_OUT/related.log" 2>&1
"$G2_CHECK_PYTHON" -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_one_shot_*.py \
 --basetemp="$ISSUE58_TEST_TEMP/cases" --junitxml="$G2_CHECK_OUT/one_shot.xml" >"$G2_CHECK_OUT/one_shot.log" 2>&1
G2_CHECK_FILES=(g2/latent_cache/streaming.py g2/latent_cache/ledger_archive.py
 g2/offline/full_production.py g2/offline/work_lifecycle.py g2/offline/process_control.py
 g2/tests/test_stage_a_streaming.py g2/tests/test_one_shot_ledger.py
 g2/tests/test_one_shot_work.py g2/tests/test_one_shot_supervisor.py
 tools/g2/consume_spatial_view_vae_events.py tools/g2/run_stage_a_production.py)
"$G2_CHECK_PYTHON" -m ruff check --select E4,E7,E9,F,I "${G2_CHECK_FILES[@]}" >"$G2_CHECK_OUT/ruff.log" 2>&1
"$G2_CHECK_PYTHON" -m ruff format --check "${G2_CHECK_FILES[@]}" >"$G2_CHECK_OUT/format.log" 2>&1
"$G2_CHECK_PYTHON" -m ruff check --select E9,F g2/offline/atomic_6views_run.py >"$G2_CHECK_OUT/original_producer_ruff.log" 2>&1
bash -n scripts/g2/run_stage_a_full.sh >"$G2_CHECK_OUT/bash.log" 2>&1
"$G2_CHECK_PYTHON" -m tools.g2.run_stage_a_production --help >"$G2_CHECK_OUT/production_help.log" 2>&1
"$G2_CHECK_PYTHON" -m tools.g2.consume_spatial_view_vae_events --help >"$G2_CHECK_OUT/consumer_help.log" 2>&1
"$G2_CHECK_PYTHON" docs/collab/codex/evidence/2026-11-17_issue58/cpu_audit.py after
