"""Light approved-composition checks only; no OS Sim/GPU/real data/checkpoints."""
import hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve()
BASE=Path(__file__).parent
OUT=BASE/'light-cpu'
OUT.mkdir()
EXPECT_ROOT='4139ad245b73cc1c16c9d4954241cecb81478992'
EXPECT_CHILD='6c83596d6a259e89c4cd3e79424024983426ac3d'
TESTS=['tools/v3/eval_v2_batch_tests/config_test.py','tools/v3/eval_v2_production_tests/entry_test.py',
       'tools/v3/eval_v2_batch_tests/dual_mode_test.py',
       'cosmos-framework/cosmos_framework/inference/robocasa_dual_mode_test.py',
       'tools/v3/no_ttt_integrated_entry_test.py']
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
AUDIT=json.loads((BASE/'object_audit.json').read_text())
assert AUDIT['status']=='PASS'
watched=set(TESTS)
for n in AUDIT['root']['candidate_changed_paths']:
 if n.endswith('.py'): watched.add(n)
for n in AUDIT['child']['candidate_changed_paths']+AUDIT['child']['canonical_changed_paths']:
 if n.endswith('.py'): watched.add('cosmos-framework/'+n)
for n in ('scripts/no_ttt_console.py','scripts/train_v3_matched_no_ttt_4gpu.sh',
          'scripts/train_v3_matched_no_ttt.sh','scripts/run_robocasa_eval_v2.sh'):
 watched.add(n)
def snapshot():
 return {'root':git(ROOT,'rev-parse','HEAD'),'child':git(ROOT/'cosmos-framework','rev-parse','HEAD'),
         'gitlink':git(ROOT,'rev-parse','HEAD:cosmos-framework'),
         'root_status':git(ROOT,'status','--porcelain=v1'),'child_status':git(ROOT/'cosmos-framework','status','--porcelain=v1'),
         'sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(watched)}}
before=snapshot()
assert before['root']==EXPECT_ROOT and before['child']==before['gitlink']==EXPECT_CHILD
assert before['root_status']==before['child_status']==''
overrides={'CUDA_VISIBLE_DEVICES':'','COSMOS_DEVICE':'cpu','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
           'LD_LIBRARY_PATH':'','PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTEST_ADDOPTS':'',
           'OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
           'PYTHONPATH':f'{ROOT}:{ROOT}/scripts:{ROOT}/cosmos-framework',
           'PYTHON':sys.executable,'HF_HOME':str(OUT/'cache/hf'),'XDG_CACHE_HOME':str(OUT/'cache/xdg'),
           'MPLCONFIGDIR':str(OUT/'cache/mpl')}
env=dict(os.environ,**overrides)
argv=[sys.executable,'-m','pytest','--noconftest','-c','/dev/null',f'--rootdir={ROOT}','-p','no:cacheprovider',
      '-q','-s','--tb=long',f'--basetemp={OUT}/tmp',f'--junitxml={OUT}/junit.xml','-k','not real_OS',*TESTS]
record={'cwd':str(ROOT),'argv':argv,'environment_overrides':overrides,'source_before':before}
(OUT/'before.json').write_text(json.dumps(record,indent=2)+'\n')
start=time.monotonic()
with (OUT/'console.log').open('w') as stream:
 result=subprocess.run(argv,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
(OUT/'shell-exit.txt').write_text(str(result.returncode)+'\n')
after=snapshot()
record.update(shell_exit=result.returncode,duration_s=time.monotonic()-start,source_after=after,source_unchanged=before==after)
if (OUT/'junit.xml').exists():
 cases=list(ET.parse(OUT/'junit.xml').getroot().iter('testcase'))
 record['counts']={'collected':len(cases),'failures':sum(c.find('failure') is not None for c in cases),
                   'errors':sum(c.find('error') is not None for c in cases),'skipped':sum(c.find('skipped') is not None for c in cases)}
(OUT/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ('shell_exit','duration_s','source_unchanged','counts') if k in record}))
assert before==after
sys.exit(result.returncode)
