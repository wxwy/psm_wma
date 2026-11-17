#!/usr/bin/env bash
# CPU author checks, existing interpreter only. Use a fresh output on replay.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
PY=${ISSUE54_PYTHON:-/workspace/.venvs/g2-view-vae-52/bin/python}
RUFF=${ISSUE54_RUFF:-/workspace/.venvs/g2-view-vae-52/bin/ruff}
OUT=${ISSUE54_A2_OUT:-docs/collab/codex/evidence/2026-11-17_issue54_a2/final}
mkdir -p "$OUT"
if [ -e "$OUT/pr53.log" ]; then
  echo 'Refusing to overwrite prior evidence; select a fresh ISSUE54_A2_OUT' >&2
  exit 2
fi
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
export ISSUE54_A2_AUDIT_OUT="$OUT"
"$PY" - <<'PY'
import hashlib,importlib.metadata as md,json,os,platform,subprocess,sys
from pathlib import Path
out=Path(os.environ['ISSUE54_A2_AUDIT_OUT'])
paths=sorted(p for root in ('g2','tools/g2') for p in Path(root).rglob('*')
    if p.is_file() and p.suffix in ('.py','.js','.html','.css','.json') and '__pycache__' not in p.parts)
source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(out/'source_before.json').write_text(json.dumps(source,sort_keys=True,indent=2)+'\n')
packages={}
for name in ('numpy','Pillow','pytest','torch','ruff','pyarrow','pandas','mujoco'):
    try: packages[name]=md.version(name)
    except md.PackageNotFoundError: packages[name]=None
env=dict(executable=sys.executable,python=sys.version,platform=platform.platform(),packages=packages,
    parent_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    source_kind='WORKTREE_CANDIDATE_HASHES_NOT_A_COMMIT_CLAIM',GPU_used=False,
    new_environment=False,packages_installed=False,dependency_overlay=False,network_during_tests=False)
(out/'environment.json').write_text(json.dumps(env,sort_keys=True,indent=2)+'\n')
PY
"$PY" -m pytest -q -p no:cacheprovider --tb=short g2/tests/test_view_vae_*.py \
 g2/tests/test_scene_view_event_index.py g2/tests/test_scene_view_index_package.py \
 g2/tests/test_scene_graph_compact_v3.py --junitxml="$OUT/pr53.xml" >"$OUT/pr53.log" 2>&1
"$PY" -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_stage_a_*.py \
 --junitxml="$OUT/stage_a.xml" >"$OUT/stage_a.log" 2>&1
"$PY" -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_atomic_6views_run.py \
 g2/tests/test_robot_pose_marker.py g2/tests/test_viewer_install.py \
 --junitxml="$OUT/related.xml" >"$OUT/related.log" 2>&1
FILES=(g2/latent_cache/builder.py g2/latent_cache/storage.py g2/latent_cache/streaming.py
 g2/latent_cache/sealed_source.py g2/latent_cache/production.py g2/offline/stage_a.py
 tools/g2/build_spatial_view_vae_cache.py tools/g2/consume_spatial_view_vae_events.py
 g2/tests/test_stage_a_streaming.py g2/tests/test_stage_a_consumer_cli.py)
"$RUFF" check --select E4,E7,E9,F,I "${FILES[@]}" >"$OUT/ruff.log" 2>&1
"$RUFF" format --check "${FILES[@]}" >"$OUT/format.log" 2>&1
"$RUFF" check --select E9,F g2/offline/atomic_6views_run.py g2/offline/episode.py >"$OUT/legacy_format_scope_ruff.log" 2>&1
"$PY" -m tools.g2.consume_spatial_view_vae_events --help >"$OUT/consumer_help.log" 2>&1
"$PY" -m tools.g2.build_spatial_view_vae_cache --help >"$OUT/build_help.log" 2>&1
"$PY" -m tools.g2.verify_spatial_view_vae_cache --help >"$OUT/verify_help.log" 2>&1
"$PY" docs/collab/codex/evidence/2026-11-17_issue54_a2/protocol_probe.py --summary "$OUT/protocol_example.json" >"$OUT/protocol_example.log" 2>&1
"$PY" - <<'PY'
import hashlib,json,os,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
out=Path(os.environ['ISSUE54_A2_AUDIT_OUT'])
before=json.loads((out/'source_before.json').read_text())
after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
(out/'source_after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n')
assert before==after
baseroot=Path('docs/collab/codex/evidence/2026-11-17_issue54_f1_f2')
def cases(path):
    return {(c.attrib['classname'],c.attrib['name']) for c in ET.parse(path).iter('testcase')}
results={}
for name in ('pr53','stage_a','related'):
    root=ET.parse(out/(name+'.xml'))
    old=cases(baseroot/('final_'+name+'.xml'))
    current=cases(out/(name+'.xml'))
    assert not old-current,(name,sorted(old-current))
    results[name]={k:sum(int(s.attrib[k]) for s in root.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    results[name].update(baseline_identities=len(old),missing_baseline_identities=[],new_identities=len(current-old),
        skipped_cases=[dict(id=c.attrib['classname']+'::'+c.attrib['name'],reason=c.find('skipped').attrib.get('message'))
            for c in root.iter('testcase') if c.find('skipped') is not None])
    assert results[name]['failures']==results[name]['errors']==0
assert results['pr53']['tests']==283 and results['pr53']['skipped']==0
child=subprocess.check_output(['git','-C','cosmos-framework','rev-parse','HEAD'],text=True).strip()
assert child=='d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2'
assert not subprocess.check_output(['git','-C','cosmos-framework','status','--porcelain'],text=True)
protected=['g2/latent_cache/encoding.py','g2/latent_cache/source.py',
 'g2/offline/language_context.py','g2/offline/task_entities.py','cosmos-framework']
subprocess.run(['git','diff','--exit-code','8e11f27bb8e6e8d29c353a56acd0e15da1ddb2a8','--',*protected],check=True,capture_output=True)
probe=Path('docs/collab/chatgpt/evidence/2026-11-17_issue54_27ccadb0/test_review_source_contracts.py')
assert hashlib.sha256(probe.read_bytes()).hexdigest()=='860424fa81b6447cb361d7272ff0a365dfef6ef6087b0a3f51ab97f63fd306e0'
gate=dict(schema='g2_issue54_a2_author_cpu_gate_v1',results=results,source_count=len(before),source_hashes_stable=True,
    preserved_approved_baseline=431,child_gitlink=child,training_ready=False,
    scope='AUTHOR_CPU_FAKE_ENCODER_NOT_GPT_REAL_VAE_OR_NATIVE_ACCEPTANCE',
    not_run=['real producer/native F27 pixels','real VAE/weights/GPU','streaming real numeric/performance parity',
        'full production','state15','joint alignment','training','merge',
        'original three reviewer probes: native PyArrow missing locally; prior GPT approval preserved'])
(out/'gate.json').write_text(json.dumps(gate,sort_keys=True,indent=2)+'\n')
print(json.dumps(gate,sort_keys=True))
PY
