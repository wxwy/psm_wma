#!/usr/bin/env bash
# Existing-environment independent regression replay; no installs or GPU.
# Run from the exact 8e11f27b Root / d5c1ffc7 Child checkout (or a docs-only descendant).
# Choose a NEW evidence directory. Original review evidence must not be overwritten.
set -euo pipefail
PY=${REVIEW_PYTHON:-/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python}
OUT=${REVIEW_OUT:?Set REVIEW_OUT to a new independent evidence directory}
if [ -e "$OUT" ]; then echo 'Refusing to overwrite evidence' >&2; exit 2; fi
mkdir -p "$OUT"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
export COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0
"$PY" -m pytest -q -p no:cacheprovider g2/tests/test_view_vae_*.py \
  g2/tests/test_scene_view_event_index.py g2/tests/test_scene_view_index_package.py \
  g2/tests/test_scene_graph_compact_v3.py \
  --junitxml="$OUT/pr53.xml" >"$OUT/pr53.log" 2>&1
"$PY" -m pytest -q -rs -p no:cacheprovider g2/tests/test_stage_a_*.py \
  --junitxml="$OUT/stage_a.xml" >"$OUT/stage_a.log" 2>&1
"$PY" -m pytest -q -rs -p no:cacheprovider \
  g2/tests/test_atomic_6views_run.py g2/tests/test_robot_pose_marker.py \
  g2/tests/test_viewer_install.py \
  --junitxml="$OUT/related.xml" >"$OUT/related.log" 2>&1
"$PY" -m pytest -q -p no:cacheprovider \
  docs/collab/chatgpt/evidence/2026-11-17_issue54_27ccadb0/test_review_source_contracts.py \
  --junitxml="$OUT/original_probes.xml" >"$OUT/original_probes.log" 2>&1
# Server-only real-source scripts and results are retained at the canonical
# evidence path documented in the report. Do not upload private source outputs.
