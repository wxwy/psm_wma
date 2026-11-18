#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
VF_PYTHON=${VF_PYTHON:-/workspace/.venvs/g2-view-vae-52/bin/python}
VF_GATE_OUT=${VF_GATE_OUT:-docs/collab/codex/evidence/2026-11-18_view_first_retirement/final}
test ! -e "$VF_GATE_OUT"
mkdir -p "$VF_GATE_OUT"
export VF_GATE_OUT
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0
export PYTHONPATH="$PWD:$PWD/cosmos-framework"
"$VF_PYTHON" docs/collab/codex/evidence/2026-11-18_view_first_retirement/cpu_gate.py before
"$VF_PYTHON" -m pytest -q -p no:cacheprovider --tb=short -rs \
 g2/tests/test_view_vae_*.py g2/tests/test_scene_view_event_index.py \
 g2/tests/test_scene_view_index_package.py g2/tests/test_scene_graph_compact_v3.py \
 g2/tests/test_stage_a_*.py g2/tests/test_atomic_6views_run.py \
 g2/tests/test_robot_pose_marker.py g2/tests/test_viewer_install.py \
 g2/tests/test_one_shot_*.py g2/tests/test_source_capsule*.py \
 g2/tests/test_source_retirement*.py g2/tests/test_view_only_source.py \
 g2/tests/test_working_source_access.py g2/tests/test_view_first_*.py \
 --junitxml="$VF_GATE_OUT/pytest.xml" >"$VF_GATE_OUT/pytest.log" 2>&1
VF_FILES=(g2/offline/{view_only_source,stage_a,source_capacity}.py
 g2/latent_cache/{final_source,source_retirement,retirement_policy,streaming,production,sealed_source,builder,storage,ledger_archive,posthoc}.py
 tools/g2/{build_spatial_view_vae_cache,retire_view_first_sources}.py
 g2/tests/test_working_source_access.py g2/tests/test_view_first_*.py)
"$VF_PYTHON" -m ruff check --select E4,E7,E9,F,I "${VF_FILES[@]}" >"$VF_GATE_OUT/ruff.log" 2>&1
"$VF_PYTHON" -m ruff format --check "${VF_FILES[@]}" >"$VF_GATE_OUT/format.log" 2>&1
"$VF_PYTHON" -m tools.g2.retire_view_first_sources --help >"$VF_GATE_OUT/retire.help.log" 2>&1
"$VF_PYTHON" -m tools.g2.build_spatial_view_vae_cache --help >"$VF_GATE_OUT/build.help.log" 2>&1
"$VF_PYTHON" docs/collab/codex/evidence/2026-11-18_view_first_retirement/protocol_probe.py --output "$VF_GATE_OUT/synthetic_protocol.json" >"$VF_GATE_OUT/protocol.log" 2>&1
"$VF_PYTHON" docs/collab/codex/evidence/2026-11-18_view_first_retirement/cpu_gate.py after
