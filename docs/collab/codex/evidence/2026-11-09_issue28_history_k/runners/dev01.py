import json
import os
from pathlib import Path
import subprocess
import sys

root = Path('/workspace/work/psm-wma-history-k-issue28')
child = root / 'cosmos-framework'
out = Path(__file__).with_suffix('')
out.mkdir(exist_ok=False)
env = dict(os.environ, CUDA_VISIBLE_DEVICES='', LD_LIBRARY_PATH='', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
    OPENBLAS_NUM_THREADS='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1', PYTHONPATH=os.pathsep.join(map(str,(root,child,root/'scripts'))),
    XDG_CACHE_HOME=str(out/'cache'), RUFF_CACHE_DIR=str(out/'ruff'))
files = []
for repo in (root, child):
    names = subprocess.check_output(['git','diff','--name-only'],cwd=repo,text=True).splitlines()
    names += subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=repo,text=True).splitlines()
    files += [str(repo/name) for name in names if name.endswith('.py')]
tests = [str(child/'cosmos_framework/inference/robocasa_history_k_test.py'),
    str(child/'cosmos_framework/simulation/robocasa/sim_shared_vae_history_k_test.py')]
commands = [
    ('lint_fix',[sys.executable,'-m','ruff','check','--fix',*files]),
    ('format',[sys.executable,'-m','ruff','format',*files]),
    ('sparse',[sys.executable,'-m','pytest','--noconftest','-o','addopts=','-p','no:cacheprovider','-q',
        '--junitxml='+str(out/'sparse.xml'),*tests]),
]
results=[]
for name,command in commands:
    with (out/(name+'.log')).open('w') as log:
        result = subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    results.append(dict(name=name,command=command,exit_code=result.returncode))
    print(name,result.returncode,flush=True)
    if result.returncode:
        print((out/(name+'.log')).read_text()[-24000:],flush=True)
        break
(out/'commands.json').write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(results[-1]['exit_code'])
