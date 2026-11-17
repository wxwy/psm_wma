#!/usr/bin/env bash
# Narrow F1/F2 author gate. Use existing interpreters only, fresh output on replay.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
PY=${ISSUE54_PYTHON:-/workspace/.venvs/g2-view-vae-52/bin/python}
RUFF=${ISSUE54_RUFF:-/workspace/.venvs/g2-view-vae-52/bin/ruff}
OUT=${ISSUE54_F1F2_OUT:-docs/collab/codex/evidence/2026-11-17_issue54_f1_f2}
mkdir -p "$OUT"
if [ -e "$OUT/final_pr53.log" ]; then
  echo 'Choose a fresh ISSUE54_F1F2_OUT; refusing to overwrite evidence' >&2
  exit 2
fi
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
export COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0
export ISSUE54_AUDIT_OUT="$OUT"
"$PY" - <<'PY'
import hashlib,importlib.metadata as md,importlib.util,json,os,platform,subprocess,sys
from pathlib import Path
out=Path(os.environ['ISSUE54_AUDIT_OUT'])
paths=sorted(p for root in ('g2','tools/g2') for p in Path(root).rglob('*')
    if p.is_file() and p.suffix in ('.py','.js','.html','.css','.json') and '__pycache__' not in p.parts)
source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
(out/'source_before.json').write_text(json.dumps(source,sort_keys=True,indent=2)+'\n')
packages={}
for name in ('numpy','Pillow','pytest','torch','ruff','pyarrow','pandas','mujoco'):
    try:packages[name]=md.version(name)
    except md.PackageNotFoundError:packages[name]=None
env=dict(executable=sys.executable,python=sys.version,platform=platform.platform(),packages=packages,
    parent_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    source_kind='WORKTREE_CANDIDATE_HASHES_NOT_A_COMMIT_CLAIM',
    pyarrow_available=importlib.util.find_spec('pyarrow') is not None,
    GPU_used=False,new_environment=False,packages_installed=False,dependency_overlay=False,network_during_tests=False)
(out/'environment.json').write_text(json.dumps(env,sort_keys=True,indent=2)+'\n')
PY
"$PY" -m pytest -q -p no:cacheprovider --tb=short g2/tests/test_view_vae_*.py \
  g2/tests/test_scene_view_event_index.py g2/tests/test_scene_view_index_package.py \
  g2/tests/test_scene_graph_compact_v3.py --junitxml="$OUT/final_pr53.xml" >"$OUT/final_pr53.log" 2>&1
"$PY" -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_stage_a_*.py \
  --junitxml="$OUT/final_stage_a.xml" >"$OUT/final_stage_a.log" 2>&1
"$PY" -m pytest -q -p no:cacheprovider --tb=short -rs g2/tests/test_atomic_6views_run.py \
  g2/tests/test_robot_pose_marker.py g2/tests/test_viewer_install.py \
  --junitxml="$OUT/final_related.xml" >"$OUT/final_related.log" 2>&1
# Run exactly the two original F2 bodies even when this interpreter lacks Arrow.
"$PY" -m pytest -q -p no:cacheprovider --tb=short \
  docs/collab/codex/evidence/2026-11-17_issue54_f1_f2/replay_role_assertions.py \
  --junitxml="$OUT/final_role_probes.xml" >"$OUT/final_role_probes.log" 2>&1
if "$PY" -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('pyarrow') else 1)"; then
  "$PY" -m pytest -q -p no:cacheprovider --tb=short \
    docs/collab/chatgpt/evidence/2026-11-17_issue54_27ccadb0/test_review_source_contracts.py \
    --junitxml="$OUT/final_original_three.xml" >"$OUT/final_original_three.log" 2>&1
else
  echo 'NOT_RUN: original F1 real-Parquet probe; existing interpreter has no PyArrow. No stubs/installs.' \
    >"$OUT/original_parquet_NOT_RUN.log"
fi
FILES=(g2/offline/language_context.py g2/offline/task_entities.py g2/offline/stage_a.py
  g2/tests/test_stage_a_contracts.py g2/tests/test_stage_a_caption_table.py
  g2/tests/test_stage_a_caption_parquet.py g2/tests/test_stage_a_task_semantics.py
  docs/collab/codex/evidence/2026-11-17_issue54_f1_f2/replay_role_assertions.py)
"$RUFF" check --select E4,E7,E9,F,I "${FILES[@]}" >"$OUT/final_ruff.log" 2>&1
"$RUFF" format --check "${FILES[@]}" >"$OUT/final_format.log" 2>&1
"$PY" -m tools.g2.verify_spatial_profile --help >"$OUT/final_verify_help.log" 2>&1
"$PY" -m tools.g2.inspect_stage_a_example --output "$OUT/synthetic_run" >"$OUT/final_example.log" 2>&1
"$PY" -m tools.g2.verify_spatial_profile --episode-root "$OUT/synthetic_run/example_episode" \
  >"$OUT/final_example_verify.log" 2>&1
cp "$OUT/synthetic_run/protocol_example.json" "$OUT/protocol_example.json"
rm -r "$OUT/synthetic_run" # only this command's successfully verified synthetic tree
git diff --check >"$OUT/final_diff_check.log" 2>&1
"$PY" - <<'PY'
import hashlib,json,os,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
out=Path(os.environ['ISSUE54_AUDIT_OUT'])
env=json.loads((out/'environment.json').read_text())
before=json.loads((out/'source_before.json').read_text())
after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
(out/'source_after.json').write_text(json.dumps(after,sort_keys=True,indent=2)+'\n')
assert before==after
def cases(path):
    return {(c.attrib['classname'],c.attrib['name']) for c in ET.parse(path).iter('testcase')}
baselines={
  'pr53':('docs/collab/chatgpt/evidence/2026-11-16_issue52_778d1ed8/pytest.xml','final_pr53.xml',283),
  'stage_a':('docs/collab/codex/evidence/2026-11-17_issue54_a1/revision1/final_stage_a_cpu.xml','final_stage_a.xml',50),
  'related':('docs/collab/codex/evidence/2026-11-17_issue54_a1/revision1/final_producer_viewer.xml','final_related.xml',45)}
preserved={}
for name,(old,current,count) in baselines.items():
    a,b=cases(old),cases(out/current)
    assert len(a)==count and not a-b,(name,sorted(a-b))
    preserved[name]=dict(old=count,retained=len(a&b),missing=[])
summary={}
for name in ('pr53','stage_a','related','role_probes'):
    root=ET.parse(out/('final_'+name+'.xml'))
    summary[name]={k:sum(int(s.attrib[k]) for s in root.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    summary[name]['skipped_cases']=[dict(test=c.attrib['classname']+'::'+c.attrib['name'],reason=c.find('skipped').attrib.get('message'))
        for c in root.iter('testcase') if c.find('skipped') is not None]
    assert summary[name]['failures']==0 and summary[name]['errors']==0
assert summary['pr53']['skipped']==0
assert summary['stage_a']['skipped']==(0 if env['pyarrow_available'] else 10)
assert all('test_stage_a_caption_parquet' in r['test'] for r in summary['stage_a']['skipped_cases'])
baseline=json.loads(Path('docs/collab/codex/evidence/2026-11-17_issue54_a1/revision1/source_before.json').read_text())
changed=[p for p,h in baseline.items() if before[p]!=h]
assert set(changed)=={'g2/offline/language_context.py','g2/offline/task_entities.py','g2/offline/stage_a.py','g2/tests/test_stage_a_contracts.py'}
review=Path('docs/collab/chatgpt/evidence/2026-11-17_issue54_27ccadb0/test_review_source_contracts.py')
assert hashlib.sha256(review.read_bytes()).hexdigest()=='860424fa81b6447cb361d7272ff0a365dfef6ef6087b0a3f51ab97f63fd306e0'
protected=['g2/latent_cache','tools/g2/build_spatial_view_vae_cache.py','tools/g2/verify_spatial_view_vae_cache.py',
  'g2/offline/episode.py','g2/offline/output_profile.py','g2/offline/spatial_metadata.py','g2/offline/scene_view_event_index.py',
  'g2/views','g2/viewer','cosmos-framework']
# No cache/streaming modifications; all three production changes are outside it.
subprocess.run(['git','diff','--exit-code','27ccadb051a71adf348ee14206d7ac59e9195d36','--',*protected],check=True,capture_output=True)
child=subprocess.check_output(['git','-C','cosmos-framework','rev-parse','HEAD'],text=True).strip()
assert child=='d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2'
assert not subprocess.check_output(['git','-C','cosmos-framework','status','--porcelain'],text=True)
gate=dict(schema='g2_issue54_f1_f2_author_gate_v1',scope='AUTHOR_CPU_NOT_GPT_REAL_SOURCE_ACCEPTANCE',
    results=summary,preserved_test_identities=preserved,source_hashes_stable=True,source_count=len(before),
    changed_baseline_source_files=changed,reviewer_source_untouched=True,child_gitlink=child,
    original_role_assertions='RED2_TO_GREEN2_UNCHANGED_AST_BODIES',
    original_parquet_assertion='GREEN' if env['pyarrow_available'] else 'NOT_RUN_MISSING_PYARROW',
    all_original_three_green=env['pyarrow_available'],
    static='PASS_SELECTED_RUFF_FORMAT_CLI_SYNTHETIC_PACKAGE',training_ready=False,
    not_run=['real RoboCasa captions/roles','native F27/pixel acceptance','GPU/Wan/weights','A2 consumer/ACK/recovery',
             'full production','state15','joint alignment','training','merge']+
             ([] if env['pyarrow_available'] else ['original F1 Parquet assertion','10 native-Parquet entry regressions']))
(out/'gate.json').write_text(json.dumps(gate,sort_keys=True,indent=2)+'\n')
print(json.dumps({'gate':'PASS_WITH_EXPLICIT_DEPENDENCY_NOT_RUN','results':summary,'preserved':preserved,
    'original_parquet_assertion':gate['original_parquet_assertion'],'source_count':len(before)},sort_keys=True))
PY
