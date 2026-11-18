#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
BATCH_PYTHON=${BATCH_PYTHON:-/workspace/.venvs/g2-view-vae-52/bin/python}
BATCH_GATE_OUT=${BATCH_GATE_OUT:-docs/collab/codex/evidence/2026-11-18_issue68/full}
test ! -e "$BATCH_GATE_OUT"
mkdir -p "$BATCH_GATE_OUT"
export BATCH_GATE_OUT CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0
export PYTHONPATH="$PWD:$PWD/cosmos-framework"
"$BATCH_PYTHON" docs/collab/codex/evidence/2026-11-18_issue68/cpu_gate.py before
"$BATCH_PYTHON" -m pytest -q -p no:cacheprovider --tb=short -rs \
 g2/tests/test_view_vae_*.py g2/tests/test_scene_view_event_index.py \
 g2/tests/test_scene_view_index_package.py g2/tests/test_scene_graph_compact_v3.py \
 g2/tests/test_stage_a_*.py g2/tests/test_atomic_6views_run.py \
 g2/tests/test_robot_pose_marker.py g2/tests/test_viewer_install.py \
 g2/tests/test_one_shot_*.py g2/tests/test_source_capsule*.py \
 g2/tests/test_source_retirement*.py g2/tests/test_view_only_source.py \
 g2/tests/test_working_source_access.py g2/tests/test_view_first_*.py \
 g2/tests/test_batch_encoding.py g2/tests/test_batch_queue.py g2/tests/test_batch_engine.py \
 --junitxml="$BATCH_GATE_OUT/pytest.xml" >"$BATCH_GATE_OUT/pytest.log" 2>&1
BATCH_FILES=(g2/latent_cache/{batch_*,contract,builder,production,streaming,storage}.py
 g2/offline/full_production.py tools/g2/{run_spatial_vae_engine,verify_spatial_vae_batches,build_spatial_view_vae_cache}.py
 g2/tests/{batch_helpers,test_batch_encoding,test_batch_queue,test_batch_engine}.py)
"$BATCH_PYTHON" -m ruff check --select E4,E7,E9,F,I "${BATCH_FILES[@]}" >"$BATCH_GATE_OUT/ruff.log" 2>&1
"$BATCH_PYTHON" -m ruff format --check "${BATCH_FILES[@]}" >"$BATCH_GATE_OUT/format.log" 2>&1
"$BATCH_PYTHON" -m tools.g2.run_spatial_vae_engine --help >"$BATCH_GATE_OUT/engine.help.log"
"$BATCH_PYTHON" -m tools.g2.verify_spatial_vae_batches --help >"$BATCH_GATE_OUT/replay.help.log"
"$BATCH_PYTHON" docs/collab/codex/evidence/2026-11-18_issue68/cpu_gate.py after
