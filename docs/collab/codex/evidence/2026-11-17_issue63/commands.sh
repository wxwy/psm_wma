#!/usr/bin/env bash
# Existing CPU interpreter only. Every replay needs a fresh evidence directory.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
G2_CHECK_PYTHON=${ISSUE63_PYTHON:-/workspace/.venvs/g2-view-vae-52/bin/python}
G2_CHECK_OUT=${ISSUE63_OUT:-docs/collab/codex/evidence/2026-11-17_issue63/final}
if [ -e "$G2_CHECK_OUT" ]; then
  echo 'Select fresh ISSUE63_OUT; never overwrite tracked/prior evidence' >&2
  exit 2
fi
mkdir -p "$G2_CHECK_OUT"
export ISSUE63_AUDIT_OUT="$G2_CHECK_OUT"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
"$G2_CHECK_PYTHON" docs/collab/codex/evidence/2026-11-17_issue63/cpu_audit.py before
"$G2_CHECK_PYTHON" -m pytest -q -p no:cacheprovider --tb=short g2/tests/test_view_vae_*.py \
 g2/tests/test_scene_view_event_index.py g2/tests/test_scene_view_index_package.py g2/tests/test_scene_graph_compact_v3.py \
 --junitxml="$G2_CHECK_OUT/pr53.xml" >"$G2_CHECK_OUT/pr53.log" 2>&1
"$G2_CHECK_PYTHON" -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_stage_a_*.py \
 --junitxml="$G2_CHECK_OUT/stage_a.xml" >"$G2_CHECK_OUT/stage_a.log" 2>&1
"$G2_CHECK_PYTHON" -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_atomic_6views_run.py \
 g2/tests/test_robot_pose_marker.py g2/tests/test_viewer_install.py \
 --junitxml="$G2_CHECK_OUT/related.xml" >"$G2_CHECK_OUT/related.log" 2>&1
"$G2_CHECK_PYTHON" -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_one_shot_*.py \
 --junitxml="$G2_CHECK_OUT/one_shot.xml" >"$G2_CHECK_OUT/one_shot.log" 2>&1
"$G2_CHECK_PYTHON" -m pytest -q -p no:cacheprovider --tb=short -rs \
 g2/tests/test_source_capsule*.py g2/tests/test_source_retirement*.py \
 --junitxml="$G2_CHECK_OUT/capsule.xml" >"$G2_CHECK_OUT/capsule.log" 2>&1
G2_CHECK_FILES=(g2/latent_cache/{final_source,source_locks,retirement_policy,source_retirement,storage,builder,sealed_source,production,ledger_archive,streaming}.py
 g2/offline/{stage_a,full_production,source_capacity,work_lifecycle}.py
 tools/g2/{consume_spatial_view_vae_events,audit_spatial_capacity,verify_spatial_source_index,resume_spatial_source_retirement}.py
 g2/tests/test_source_capsule*.py g2/tests/test_source_retirement*.py)
"$G2_CHECK_PYTHON" -m ruff check --select E4,E7,E9,F,I "${G2_CHECK_FILES[@]}" >"$G2_CHECK_OUT/ruff.log" 2>&1
"$G2_CHECK_PYTHON" -m ruff format --check "${G2_CHECK_FILES[@]}" >"$G2_CHECK_OUT/format.log" 2>&1
for G2_TOOL in verify_spatial_source_index audit_spatial_capacity resume_spatial_source_retirement; do
  "$G2_CHECK_PYTHON" -m "tools.g2.$G2_TOOL" --help >"$G2_CHECK_OUT/$G2_TOOL.help.log" 2>&1
done
"$G2_CHECK_PYTHON" docs/collab/codex/evidence/2026-11-17_issue63/protocol_probe.py \
 --summary "$G2_CHECK_OUT/synthetic_protocol.json" >"$G2_CHECK_OUT/synthetic_protocol.log" 2>&1
"$G2_CHECK_PYTHON" docs/collab/codex/evidence/2026-11-17_issue63/cpu_audit.py after
