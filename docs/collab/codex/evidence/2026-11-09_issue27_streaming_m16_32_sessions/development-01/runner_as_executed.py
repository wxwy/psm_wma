"""Issue27 Evidence-only M16 supplement, CPU boundary doubles, no real Sim/GPU."""
import argparse,hashlib,importlib.metadata,json,os,signal,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--evidence-dir',type=Path,required=True)
p.add_argument('--expected-root');p.add_argument('--format',action='store_true');a=p.parse_args()
r=a.root.resolve();c=r/'cosmos-framework';out=a.evidence_dir.resolve();out.mkdir(parents=True,exist_ok=False)
def git(d,*args):return subprocess.check_output(['git','-C',str(d),*args],text=True).strip()
child='60b252d05157b2753d2caebae32b11c878504bbe';old='15dbc97bf13437905ec38247382834067e5341ae'
assert git(c,'rev-parse','HEAD')==child and not git(c,'status','--porcelain')
assert git(r,'rev-parse','HEAD:cosmos-framework')==child
assert not git(r,'diff',old,'--','scripts'), 'Root production must remain byte-identical'
if a.expected_root:
 assert not a.format and git(r,'rev-parse','HEAD')==a.expected_root and not git(r,'status','--porcelain')
files=[r/'tools/v3/eval_v2_batch_tests'/x for x in ['shared_vae_routing_test.py','shared_vae_streaming_m16_test.py','shared_vae_daemon_fixture.py']]
tests=[str(files[0]),str(files[1]),str(r/'tools/v3/eval_v2_batch_tests/shared_vae_test.py')+'::test_registry_worker_is_peer_survives_sim_end_and_closes_with_private_fd_proof']
env=os.environ.copy();overrides=dict(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONPATH=os.pathsep.join(map(str,(r,c,r/'scripts'))),RUFF_CACHE_DIR=str(out/'cache/ruff'),XDG_CACHE_HOME=str(out/'cache/xdg'))
env.update(overrides);(out/'environment_overrides.json').write_text(json.dumps(overrides,indent=2)+'\n')
(out/'versions.json').write_text(json.dumps(dict(python=sys.version,packages={x:importlib.metadata.version(x) for x in ['torch','pytest','ruff','omegaconf']}),indent=2)+'\n')
state=dict(status='RUNNING',scope='ISSUE27_TEST_ONLY_STREAMING_M16_32_SESSIONS',steps=[],created_cst=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),formal_identity=dict(root=git(r,'rev-parse','HEAD'),child=child,gitlink=child),root_production_base=old,real_gpu_checkpoint_sim_sr='NOT_RUN')
def save():(out/'gate.json').write_text(json.dumps(state,indent=2)+'\n')
def run(name,argv,timeout=150):
 step=dict(name=name,argv=list(map(str,argv)),cwd=str(r),timeout_s=timeout);state['steps'].append(step);save();started=time.monotonic()
 with (out/(name+'.log')).open('wb') as log:
  proc=subprocess.Popen(step['argv'],cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:proc.wait(timeout)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGKILL);proc.wait(5);raise
 step.update(exit_code=proc.returncode,elapsed_s=time.monotonic()-started);save();print(name,proc.returncode,flush=True)
 if proc.returncode:raise RuntimeError(name+' failed')
def snapshot():
 paths=list(c.rglob('*.py'))+list((r/'scripts').rglob('*.py'))+list((r/'tools').rglob('*.py'))
 return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.is_file() and '__pycache__' not in p.parts}
before=None
try:
 if a.format:
  run('format',[sys.executable,'-m','ruff','format',*files])
  run('lint_fix',[sys.executable,'-m','ruff','check','--fix',*files])
 before=snapshot();(out/'source_before.json').write_text(json.dumps(before,indent=2)+'\n')
 run('ruff_check',[sys.executable,'-m','ruff','check',*files])
 run('ruff_format',[sys.executable,'-m','ruff','format','--check',*files])
 for f in files:compile(f.read_text(),str(f),'exec')
 state['syntax_files']=len(files)
 run('pytest',[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','-p','no:cacheprovider','-q',*tests,'--junitxml='+str(out/'focused.xml'),'--basetemp='+str(out/'tmp')])
 tree=ET.parse(out/'focused.xml').getroot();suites=list(tree.iter('testsuite'))
 state['junit']={key:sum(int(s.get(key,'0')) for s in suites) for key in ['tests','failures','errors','skipped']}
 assert state['junit']['tests'] and not any(state['junit'][x] for x in ['failures','errors','skipped'])
 proofs=sorted((out/'tmp').rglob('streaming_m16_evidence.json'))
 assert len(proofs)==2, 'both physical layout proofs required'
 for i,f in enumerate(proofs):
  proof=json.loads(f.read_text());assert proof['total_sim_sessions']==32 and proof['sims_per_server']==16
  assert len(set(proof['session_ids']))==32 and proof['scoped_ends']==proof['native_ends']==32
  (out/f'm16_os_behavior_{i}.json').write_bytes(f.read_bytes())
 state['m16_layout_proofs']=2;state['status']='PASS'
except Exception as error:state.update(status='FAIL',error=repr(error))
finally:
 if before is not None:
  after=snapshot();(out/'source_after.json').write_text(json.dumps(after,indent=2)+'\n');state['source_unchanged']=before==after
  if before!=after:state.update(status='FAIL',error='source changed during execution')
 state['root_production_unchanged']=not git(r,'diff',old,'--','scripts')
 state['child_unchanged']=git(c,'rev-parse','HEAD')==child and not git(c,'status','--porcelain')
 if not state['root_production_unchanged'] or not state['child_unchanged']:state.update(status='FAIL',error='production identity changed')
 if a.expected_root:
  state['exact_pair_clean_after']=not git(r,'status','--porcelain') and not git(c,'status','--porcelain')
  if not state['exact_pair_clean_after']:state.update(status='FAIL',error='exact Pair dirty after validation')
 save()
print(json.dumps({k:state.get(k) for k in ['status','junit','source_unchanged','root_production_unchanged','child_unchanged','m16_layout_proofs']}))
raise SystemExit(0 if state['status']=='PASS' else 1)
