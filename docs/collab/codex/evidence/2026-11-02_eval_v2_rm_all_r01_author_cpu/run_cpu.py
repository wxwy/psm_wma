"""Portable scoped RM-ALL-R01 author CPU driver, no real model/hardware."""
import argparse
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

p=argparse.ArgumentParser()
p.add_argument('--root-worktree',type=Path,default=Path('/workspace/psm-wma-eval-replan-all'))
p.add_argument('--phase',choices=['red','green','regression'],required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--frozen-test',type=Path,default=Path('/tmp/psm-eval-v2-rm-all-r01-20261102/red/frozen_test.py'))
p.add_argument('--expected-root')
p.add_argument('--expected-child')
a=p.parse_args()
root=a.root_worktree.resolve();child=root/'cosmos-framework';out=a.output.resolve()
assert not out.is_relative_to(root)
out.mkdir(exist_ok=False,parents=True)
test='tools/v3/eval_v2_replan_tests/ack_history_test.py'
production='cosmos_framework/inference/robocasa_batch_transactions.py'
old_child='0dd13d3d952aa7cbab39f966dfab04b23551f0c9'
git=lambda cwd,*args:subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def versions():
 return dict(root=git(root,'rev-parse','HEAD'),child=git(child,'rev-parse','HEAD'),gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),
  root_status=git(root,'status','--porcelain'),child_status=git(child,'status','--porcelain'))
before=versions()
formal=a.expected_root is not None
if formal:
 assert a.expected_child and before['root']==a.expected_root
 assert before['child']==before['gitlink']==a.expected_child
 assert before['root_status']==before['child_status']==''
if a.phase=='red':
 assert before['child']==before['gitlink']==old_child
 blob=subprocess.check_output(['git','show',old_child+':'+production],cwd=child)
 assert hashlib.sha256(blob).hexdigest()==sha(child/production)
 shutil.copyfile(root/test,out/'frozen_test.py')
else:
 assert a.frozen_test.read_bytes()==(root/test).read_bytes(),'test differs from frozen pre-RED bytes'
nodes={
 'red':[test+'::test_old_reservation_after_two_ACKs_never_allocates_spool',test+'::test_old_ACK_after_two_ACKs_is_idempotent'],
 'green':['tools/v3/eval_v2_replan_tests'],
 'regression':['cosmos-framework/cosmos_framework/inference/robocasa_batch_transactions_test.py',
               'cosmos-framework/cosmos_framework/simulation/robocasa/eval_v2_transactions_test.py'],
}[a.phase]
env_fields=dict(CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',LD_LIBRARY_PATH='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',
 HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',PYTEST_ADDOPTS='',
 PYTHONPATH=os.pathsep.join(map(str,[root,root/'scripts',child])),HF_HOME=str(out/'cache/hf'),
 MPLCONFIGDIR=str(out/'cache/mpl'),XDG_CACHE_HOME=str(out/'cache/xdg'),RUFF_CACHE_DIR=str(out/'cache/ruff'),
 OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
env=dict(os.environ,**env_fields)
command=[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','-q','-p','no:cacheprovider',f'--rootdir={root}',
 *nodes,f'--basetemp={out/"pytest_tmp"}',f'--junitxml={out/"junit.xml"}']
if a.phase!='red':command.append('-x')
watched=[root/test,child/production,root/'tools/v3/eval_v2_replan_tests/support.py']
fingerprints={str(f.relative_to(root)):sha(f) for f in watched}
(out/'invocation.json').write_text(json.dumps(dict(command=command,cwd=str(root),environment=env_fields,versions=before,
 python=sys.version,phase=a.phase,formal=formal,source_sha256=fingerprints,frozen_pre_red_test_sha256=sha(root/test),
 inputs='new synthetic CPU model/frames/video only; real public dispatcher/actor and CPU Encoder; no existing media/checkpoint/GPU',
 watchdog_s=300),indent=2)+'\n')
started=time.monotonic()
with (out/'pytest.log').open('w') as log:
 proc=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=proc.wait(timeout=300)
 except BaseException:
  os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=10);raise
assert versions()==before,'worktree changed during CPU run'
assert fingerprints=={str(f.relative_to(root)):sha(f) for f in watched},'watched source changed'
xml=ET.parse(out/'junit.xml').getroot()
counts={name:len(list(xml.iter(tag))) for name,tag in [('tests','testcase'),('failures','failure'),('errors','error'),('skipped','skipped')]}
if a.phase=='red':
 assert code==1 and counts==dict(tests=2,failures=2,errors=0,skipped=0),counts
 messages=[f.text or '' for f in xml.iter('failure')]
 assert any('already_saved' in m and "reserved" in m for m in messages)
 assert any('unknown or changed strict media ACK replay' in m for m in messages)
 status='EXPECTED_FROZEN_OLD_PRODUCTION_RED'
else:
 assert code==0 and counts['failures']==counts['errors']==counts['skipped']==0,(code,counts)
 status='AUTHOR_CLEAN_PAIR_CPU_PASS' if formal else 'DEVELOPMENT_CPU_PASS'
(out/'gate.json').write_text(json.dumps(dict(status=status,**before,**counts,phase=a.phase,python=sys.version,
 seconds=time.monotonic()-started,source_unchanged=True,frozen_test_sha256=sha(root/test)),indent=2)+'\n')
print(json.dumps(dict(status=status,**counts,seconds=round(time.monotonic()-started,3)),indent=2),flush=True)
