"""Focused CPU development validation; no model loading or hardware execution."""
from pathlib import Path
import json,os,subprocess,sys
r=Path('/workspace/work/psm-wma-shared-vae-issue27');c=r/'cosmos-framework';o=Path('/workspace/work/issue27-shared-vae-evidence/development-01');o.mkdir(exist_ok=False)
env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONPATH=os.pathsep.join(map(str,(r,c,r/'scripts'))),RUFF_CACHE_DIR=str(o/'cache/ruff'),XDG_CACHE_HOME=str(o/'cache/xdg'))
scope=[]
for repo,base in [(r,'e58cef1f53d2382d39c871ce5a50e4acdd5ce268'),(c,'b0dbd115d03e801ec4d0788c30ee0b0e9655d4db')]:
 paths=subprocess.check_output(['git','-C',str(repo),'diff','--name-only',base,'--','*.py'],text=True).splitlines();scope +=[repo/p for p in paths]
scope +=[r/'tools/v3/eval_v2_batch_tests/shared_vae_topology_test.py',c/'cosmos_framework/inference/robocasa_shared_policy_batch_test.py']
commands=[('format',[sys.executable,'-m','ruff','format',*scope]),('ruff_fix',[sys.executable,'-m','ruff','check','--fix',*scope]),('pytest',[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','-p','no:cacheprovider','-q',r/'tools/v3/eval_v2_batch_tests/shared_vae_topology_test.py',c/'cosmos_framework/inference/robocasa_shared_policy_batch_test.py',c/'cosmos_framework/inference/robocasa_boundary_capture_test.py','--junitxml='+str(o/'junit.xml'),'--basetemp='+str(o/'tmp')])]
results=[]
for name,argv in commands:
 with (o/(name+'.log')).open('w') as log:p=subprocess.run(list(map(str,argv)),cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 results.append(dict(name=name,argv=list(map(str,argv)),exit_code=p.returncode));(o/'steps.json').write_text(json.dumps(results,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
