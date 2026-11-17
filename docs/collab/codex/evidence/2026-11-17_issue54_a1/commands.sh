#!/usr/bin/env bash
# Author CPU/static only. Use a new ISSUE54_EVIDENCE_OUT when replaying.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
PY=${ISSUE54_PYTHON:-/workspace/.venvs/g2-view-vae-52/bin/python}
RUFF=${ISSUE54_RUFF:-/workspace/.venvs/g2-view-vae-52/bin/ruff}
OUT=${ISSUE54_EVIDENCE_OUT:-docs/collab/codex/evidence/2026-11-17_issue54_a1}
mkdir -p "$OUT"
if [ -e "$OUT/final_pr53_regression.log" ]; then
  echo 'Refusing to overwrite prior evidence; choose a fresh ISSUE54_EVIDENCE_OUT' >&2
  exit 2
fi
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
export ISSUE54_AUDIT_OUT="$OUT"
"$PY" - <<'PY'
import hashlib, importlib.metadata as md, json, os, platform, subprocess, sys
from pathlib import Path
out=Path(os.environ['ISSUE54_AUDIT_OUT'])
paths=sorted(p for root in ('g2','tools/g2') for p in Path(root).rglob('*')
    if p.is_file() and p.suffix in ('.py','.js','.html','.css','.json') and '__pycache__' not in p.parts)
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(out/'source_before.json').write_text(json.dumps(hashes,sort_keys=True,indent=2)+'\n')
packages={}
for name in ('numpy','Pillow','pytest','torch','ruff','pyarrow','mujoco'):
    try: packages[name]=md.version(name)
    except md.PackageNotFoundError: packages[name]=None
environment=dict(executable=sys.executable,python=sys.version,platform=platform.platform(),packages=packages,
    source_head_before_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    source_kind='WORKTREE_CANDIDATE_HASHES_FROZEN_BEFORE_TEST_NOT_A_COMMIT_CLAIM',
    GPU_used=False,network_during_tests=False,new_environment_created=False)
(out/'environment.json').write_text(json.dumps(environment,sort_keys=True,indent=2)+'\n')
PY
"$PY" -m pytest g2/tests/test_view_vae_*.py g2/tests/test_scene_view_event_index.py \
  g2/tests/test_scene_view_index_package.py g2/tests/test_scene_graph_compact_v3.py \
  -q --tb=short --junitxml="$OUT/final_pr53_regression.xml" >"$OUT/final_pr53_regression.log" 2>&1
"$PY" -m pytest g2/tests/test_stage_a_*.py -q --tb=short \
  --junitxml="$OUT/final_stage_a_cpu.xml" >"$OUT/final_stage_a_cpu.log" 2>&1
"$PY" -m pytest g2/tests/test_atomic_6views_run.py g2/tests/test_robot_pose_marker.py \
  g2/tests/test_viewer_install.py -q --tb=short -rs \
  --junitxml="$OUT/final_producer_viewer.xml" >"$OUT/final_producer_viewer.log" 2>&1
NEW=(g2/offline/output_profile.py g2/offline/task_entities.py g2/offline/spatial_metadata.py
  g2/offline/language_context.py g2/offline/stage_a.py g2/latent_cache/streaming.py
  tools/g2/verify_spatial_profile.py tools/g2/inspect_stage_a_example.py g2/tests/test_stage_a_*.py)
"$RUFF" check --select E4,E7,E9,F,I "${NEW[@]}" >"$OUT/final_ruff_new.log" 2>&1
"$RUFF" format --check "${NEW[@]}" >"$OUT/final_format_new.log" 2>&1
# Existing producer modules retain their historical formatting. No broad reformat.
"$RUFF" check --select F,E9 g2/offline/atomic_6views_run.py g2/offline/atomic_6views_plan.py \
  g2/offline/atomic_6views_snapshots.py g2/offline/episode.py g2/offline/scene_view_event_index.py \
  g2/views/render_connections.py g2/views/robot_pose_marker.py >"$OUT/final_ruff_existing.log" 2>&1
node --check g2/viewer/viewer.js >"$OUT/final_js_syntax.log" 2>&1
node g2/tests/viewer_stage_a_variants_smoke.js >"$OUT/final_viewer_variants.log" 2>&1
"$PY" -m tools.g2.verify_spatial_profile --help >"$OUT/final_verify_help.log" 2>&1
"$PY" -m g2.offline.atomic_6views_run --help >"$OUT/final_producer_help.log" 2>&1
"$PY" -m tools.g2.inspect_stage_a_example --output "$OUT/synthetic_run" >"$OUT/final_protocol_example.log" 2>&1
"$PY" -m tools.g2.verify_spatial_profile --episode-root "$OUT/synthetic_run/example_episode" \
  >"$OUT/final_protocol_verify.log" 2>&1
cp "$OUT/synthetic_run/protocol_example.json" "$OUT/protocol_example.json"
# Only the synthetic tree just created and successfully verified above.
rm -r "$OUT/synthetic_run"
git diff --check >"$OUT/final_diff_check.log" 2>&1
"$PY" - <<'PY'
import hashlib, json, os, subprocess, xml.etree.ElementTree as ET
from pathlib import Path
out=Path(os.environ['ISSUE54_AUDIT_OUT'])
before=json.loads((out/'source_before.json').read_text())
after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
(out/'source_after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n')
assert before==after, 'source changed during final checks'
def cases(path):
    return {(c.attrib['classname'],c.attrib['name']) for c in ET.parse(path).iter('testcase')}
old=cases('docs/collab/chatgpt/evidence/2026-11-16_issue52_778d1ed8/pytest.xml')
current=cases(out/'final_pr53_regression.xml')
assert len(old)==283 and old==current, 'old approved test identities changed'
summaries={}
for name,file in [('pr53','final_pr53_regression.xml'),('stage_a','final_stage_a_cpu.xml'),('producer_viewer','final_producer_viewer.xml')]:
    root=ET.parse(out/file)
    suites=list(root.iter('testsuite'))
    summaries[name]={k:sum(int(s.attrib[k]) for s in suites) for k in ('tests','failures','errors','skipped')}
    summaries[name]['skipped_cases']=[dict(test=c.attrib['classname']+'::'+c.attrib['name'],reason=c.find('skipped').attrib.get('message'))
        for c in root.iter('testcase') if c.find('skipped') is not None]
    assert summaries[name]['failures']==0 and summaries[name]['errors']==0
assert summaries['pr53']['skipped']==0 and summaries['stage_a']['skipped']==0
protected=['g2/latent_cache/'+p+'.py' for p in ('__init__','contract','encoding','source','storage','builder')]
protected += ['tools/g2/build_spatial_view_vae_cache.py','tools/g2/verify_spatial_view_vae_cache.py']
protected += sorted(str(p) for p in Path('g2/tests').glob('test_view_vae_*.py'))
protected += ['g2/tests/test_scene_view_event_index.py','g2/tests/test_scene_view_index_package.py','g2/tests/test_scene_graph_compact_v3.py']
subprocess.run(['git','diff','--exit-code','778d1ed8a031429fd857c980fc872d4c85123cd1','--',*protected],check=True,capture_output=True)
child=subprocess.check_output(['git','-C','cosmos-framework','rev-parse','HEAD'],text=True).strip()
assert child=='d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2'
assert not subprocess.check_output(['git','-C','cosmos-framework','status','--porcelain'],text=True)
gate=dict(schema='g2_issue54_a1_author_cpu_gate_v1',scope='AUTHOR_CODE_CPU_NOT_GPT_SERVER_ACCEPTANCE',
    results=summaries,missing_approved_test_identities=[],approved_baseline_cases=len(old),
    protected_pr53_core_and_tests_unchanged=protected,source_fingerprints_stable=True,source_file_count=len(before),
    source_manifest_sha256=hashlib.sha256((out/'source_before.json').read_bytes()).hexdigest(),
    child_gitlink=child,nav_remote_observed='70eb7b447e65d793b0ebe18b258291ce46f057c1',
    nav_scope='REMOTE_REF_ONLY_NO_NATIVE_RUNTIME_IN_THIS_WORKSPACE',training_ready=False,
    static=dict(new_rules='E4,E7,E9,F,I',existing_rules='F,E9',new_format='PASS',JS_syntax='PASS'),
    A2='IMMUTABLE_EVENTS_AND_SOURCE_SEAL_INTERFACE_ONLY_NO_WORKER_OR_ACK',
    not_run=['real PyArrow caption read','real RoboCasa/native/F27 samples','Wan/weights/GPU','A2 queue/consumer/ACK/recovery',
        'new-source post-hoc VAE adapter','stream/post-hoc numerical parity','full production','state15','joint alignment','training','merge'])
(out/'gate.json').write_text(json.dumps(gate,sort_keys=True,indent=2)+'\n')
print(json.dumps({'gate':'PASS','results':summaries,'preserved_pr53':len(old)},sort_keys=True))
PY
