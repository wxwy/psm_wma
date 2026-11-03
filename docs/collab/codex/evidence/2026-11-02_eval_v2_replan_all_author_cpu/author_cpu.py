import ast
import hashlib
import json
import os
import signal
import py_compile
import subprocess
import sys
import time
from pathlib import Path
import xml.etree.ElementTree as ET

root=Path(os.environ.get('PSM_REPLAN_ROOT','/workspace/psm-wma-eval-replan-all')).resolve()
child=root/'cosmos-framework'
out=Path(os.environ.get('PSM_REPLAN_EVIDENCE_BASE','/tmp/psm-eval-replan-all-20261102'))/sys.argv[1]
out.mkdir(exist_ok=False)
group=sys.argv[2]
nodes={
 'strict':['tools/v3/eval_v2_replan_tests/encoder_test.py','tools/v3/eval_v2_replan_tests/transport_test.py'],
 'all_new':['tools/v3/eval_v2_replan_tests'],
 'related':['tools/v3/eval_v2_batch_tests/media_cleanup_test.py','tools/v3/eval_v2_batch_tests/media_queue_close_fault_test.py',
    'tools/v3/eval_v2_batch_tests/media_process_cleanup_test.py','tools/v3/eval_v2_batch_tests/config_test.py',
    'tools/v3/eval_v2_batch_tests/rollout_policy_test.py','tools/v3/eval_v2_batch_tests/render_mapping_test.py',
    'tools/v3/eval_v2_batch_tests/owner_gpu_resource_policy_test.py','tools/v3/eval_v2_production_tests/worker_test.py',
    'tools/v3/eval_v2_production_tests/native_test.py','tools/v3/eval_v2_production_tests/media_test.py'],
 'inference':['cosmos-framework/cosmos_framework/inference/robocasa_batch_transactions_test.py',
    'cosmos-framework/cosmos_framework/simulation/robocasa/eval_v2_transactions_test.py',
    'cosmos-framework/cosmos_framework/scripts/robocasa_transactions_b1_test.py',
    'cosmos-framework/cosmos_framework/inference/robocasa_session_transactions_test.py'],
 'runtime':['tools/v3/eval_v2_batch_tests/runtime_test.py','tools/v3/eval_v2_batch_tests/dual_mode_test.py']
}[group]
env_fields=dict(CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',LD_LIBRARY_PATH='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',
 HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',HF_HOME=str(out/'cache/hf'),
 MPLCONFIGDIR=str(out/'cache/mpl'),XDG_CACHE_HOME=str(out/'cache/xdg'),RUFF_CACHE_DIR=str(out/'cache/ruff'),
 PYTHONPATH=os.pathsep.join(map(str,[root,root/'scripts',child])),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTEST_ADDOPTS='')
env=dict(os.environ,**env_fields)
cmd=[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','-q','-x','-p','no:cacheprovider',f'--rootdir={root}',
 *nodes,f'--basetemp={out/"pytest_tmp"}',f'--junitxml={out/"junit.xml"}']
git=lambda cwd,*a:subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
versions=dict(root=git(root,'rev-parse','HEAD'),child=git(child,'rev-parse','HEAD'),gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),
 root_status=git(root,'status','--porcelain'),child_status=git(child,'status','--porcelain'))
formal='--formal' in sys.argv[3:]
if formal:
 assert versions['root_status']==versions['child_status']==''
 assert versions['root']==os.environ['PSM_EXPECTED_ROOT']
 assert versions['child']==versions['gitlink']==os.environ['PSM_EXPECTED_CHILD']
sources={}
for cwd,base in [(root,'f49d52e5646e54a1eb45c31f3179901650694c20'),(child,'9a8cd6183424bfce245fbca393ca25ed59919ea6')]:
 changed=subprocess.check_output(['git','diff','--name-only',base],cwd=cwd,text=True).splitlines()
 untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=cwd,text=True).splitlines()
 for f in changed+untracked:
  p=cwd/f
  if p.is_file() and p.suffix=='.py':
   ast.parse(p.read_text())
   compiled=out/'syntax'/p.relative_to(root)
   compiled.parent.mkdir(parents=True,exist_ok=True)
   py_compile.compile(str(p),cfile=str(compiled)+'.pyc',doraise=True)
   sources[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
(out/'invocation.json').write_text(json.dumps(dict(command=cmd,cwd=str(root),environment=env_fields,versions=versions,
 python=sys.version,inputs='CPU synthetic frames/HTTP/owned subprocesses only; no model, data, GPU or historical media',
 source_sha256=sources,watchdog_s=600,formal=formal),indent=2)+'\n')
started=time.monotonic()
with (out/'pytest.log').open('w') as log:
 process=subprocess.Popen(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try: code=process.wait(timeout=600)
 except BaseException:
  os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10);raise
print('pytest',group,'exit',code,'seconds',round(time.monotonic()-started,3),flush=True)
assert sources=={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},'source changed during test'
assert versions==dict(root=git(root,'rev-parse','HEAD'),child=git(child,'rev-parse','HEAD'),gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),
 root_status=git(root,'status','--porcelain'),child_status=git(child,'status','--porcelain')),'worktree changed during test'
if (out/'junit.xml').exists():
 x=ET.parse(out/'junit.xml').getroot()
 counts={n:len(list(x.iter(t))) for n,t in [('tests','testcase'),('failures','failure'),('errors','error'),('skipped','skipped')]}
 (out/'gate.json').write_text(json.dumps(dict(status=('AUTHOR_CLEAN_PAIR_CPU_PASS' if formal else 'DEVELOPMENT_CPU_PASS') if code==0 else 'FAIL',**versions,**counts,group=group,
  source_unchanged=True,python=sys.version,seconds=time.monotonic()-started),indent=2)+'\n')
 print(counts,flush=True)
if code: print((out/'pytest.log').read_text(errors='replace')[-10000:],flush=True)
raise SystemExit(code)
