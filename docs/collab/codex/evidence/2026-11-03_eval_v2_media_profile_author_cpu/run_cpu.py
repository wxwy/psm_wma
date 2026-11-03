"""R01 media profile targeted CPU evidence; no server/model/GPU/old media."""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

root=Path(os.environ.get('PSM_PROFILE_ROOT','/workspace/psm-wma-eval-replan-all')).resolve()
phase=sys.argv[1];out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
child=root/'cosmos-framework'
test='tools/v3/eval_v2_replan_tests/media_profile_test.py'
production='scripts/robocasa_eval_v2/generated_media.py'
git=lambda cwd,*a:subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
def versions():
 return dict(root=git(root,'rev-parse','HEAD'),child=git(child,'rev-parse','HEAD'),gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),
             root_status=git(root,'status','--porcelain'),child_status=git(child,'status','--porcelain'))
before=versions()
assert before['child']==before['gitlink']=='c93f2abf4fb27d36176ff8db094379a853cec796' and not before['child_status']
formal=len(sys.argv)>3
if formal:assert before['root']==sys.argv[3] and not before['root_status']
if phase=='red':
 raw=subprocess.check_output(['git','show','e7ce99d7a0bbb7a81ea7afcee7253548687dc223:'+production],cwd=root)
 assert raw==(root/production).read_bytes()
 shutil.copyfile(root/test,out/'frozen_test.py')
else:
 frozen=Path(os.environ.get('PSM_PROFILE_FROZEN_TEST','/tmp/psm-eval-v2-media-profile-20261103/red/frozen_test.py'))
 assert frozen.read_bytes()==(root/test).read_bytes()
nodes=[test+'::test_real_profile_summary_enters_every_receipt_and_file_hash_check[phase_b]',
       test+'::test_wrong_or_untyped_ACK_authority_remains_incomplete[phase_b-False]'] if phase=='red' else [
 test,'tools/v3/eval_v2_replan_tests/report_test.py','tools/v3/eval_v2_batch_tests/config_test.py']
fields=dict(CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',LD_LIBRARY_PATH='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
 PYTHONDONTWRITEBYTECODE='1',PYTEST_ADDOPTS='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',OMP_NUM_THREADS='1',
 OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',HF_HOME=str(out/'cache/hf'),MPLCONFIGDIR=str(out/'cache/mpl'),
 XDG_CACHE_HOME=str(out/'cache/xdg'),RUFF_CACHE_DIR=str(out/'cache/ruff'),
 PYTHONPATH=os.pathsep.join(map(str,[root,root/'scripts',child])))
env=dict(os.environ,**fields)
command=[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','-q','-p','no:cacheprovider',f'--rootdir={root}',*nodes,
         f'--basetemp={out/"pytest_tmp"}',f'--junitxml={out/"junit.xml"}']
if phase!='red':command.append('-x')
watched=[root/test,root/production,root/'scripts/robocasa_eval_v2/config.py',child/'cosmos_framework/evaluation/robocasa_v2/contract.py']
hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
(out/'invocation.json').write_text(json.dumps(dict(command=command,cwd=str(root),environment=fields,versions=before,
 phase=phase,formal=formal,python=sys.version,source_sha256=hashes,watchdog_s=180,
 inputs='fresh synthetic valid Manifest/Store/Core and CPU MP4 receipts only; no actual R01 files, GPU or model'),indent=2)+'\n')
start=time.monotonic()
with (out/'pytest.log').open('w') as log:
 p=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=p.wait(timeout=180)
 except BaseException:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10);raise
assert versions()==before
assert hashes=={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
x=ET.parse(out/'junit.xml').getroot()
counts={n:len(list(x.iter(t))) for n,t in [('tests','testcase'),('failures','failure'),('errors','error'),('skipped','skipped')]}
if phase=='red':
 assert code==1 and counts==dict(tests=2,failures=2,errors=0,skipped=0),counts
 assert all('test_' in (f.text or '') and 'AssertionError' in (f.text or '') for f in x.iter('failure'))
 status='EXPECTED_FROZEN_OLD_PROFILE_RED'
else:
 assert code==0 and counts['failures']==counts['errors']==counts['skipped']==0,(code,counts)
 status='AUTHOR_CLEAN_PAIR_CPU_PASS' if formal else 'DEVELOPMENT_CPU_PASS'
(out/'gate.json').write_text(json.dumps(dict(status=status,**before,**counts,python=sys.version,source_unchanged=True,
 frozen_test_sha256=hashes[test],seconds=time.monotonic()-start),indent=2)+'\n')
print(json.dumps(dict(status=status,**counts,seconds=round(time.monotonic()-start,3)),indent=2),flush=True)
