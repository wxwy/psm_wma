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
    str(child/'cosmos_framework/simulation/robocasa/sim_shared_vae_history_k_test.py'),
    str(root/'tools/v3/eval_v2_batch_tests/history_k_test.py'),
    str(child/'cosmos_framework/inference/robocasa_vae_worker_test.py'),
    str(child/'cosmos_framework/inference/robocasa_feature_evidence_test.py'),
    str(child/'cosmos_framework/inference/robocasa_local_memory_policy_test.py'),
    str(child/'cosmos_framework/simulation/robocasa/sim_shared_vae_client_test.py')]
commands = [
    ('lint_fix',[sys.executable,'-m','ruff','check','--fix',*files]),
    ('format',[sys.executable,'-m','ruff','format',*files]),
    ('sparse',[sys.executable,'-m','pytest','--noconftest','-o','addopts=','-p','no:cacheprovider','-q',
        '-c','/dev/null','--rootdir='+str(root), '--basetemp='+str(out/'pytest-temp'), '--junitxml='+str(out/'sparse.xml'),*tests[:3]]),
]
results=[]
for name,command in commands:
    with (out/(name+'.log')).open('w') as log:
        result = subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    results.append(dict(name=name,command=command,exit_code=result.returncode))
    print(name,result.returncode,flush=True)
    if result.returncode:
        print((out/(name+'.log')).read_text()[-4000:],flush=True)
        break
if not results[-1]['exit_code']:
    baseline = Path('/workspace/work/psm-wma-shared-vae-issue27/cosmos-framework')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=baseline,text=True).strip() == '60b252d05157b2753d2caebae32b11c878504bbe'
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=baseline,text=True).strip()
    for label,repo in [('old',baseline),('new',child)]:
        penv = dict(env,PYTHONPATH=str(repo))
        command = [sys.executable,str(out.parent/'dense_parity_probe.py'),str(out/(label+'.json'))]
        with (out/(label+'.log')).open('w') as log:
            result = subprocess.run(command,cwd=repo,env=penv,stdout=log,stderr=subprocess.STDOUT,timeout=90)
        results.append(dict(name=label,command=command,exit_code=result.returncode))
        print(label,result.returncode,flush=True)
        if result.returncode:
            print((out/(label+'.log')).read_text()[-4000:])
            break
    if not results[-1]['exit_code']:
        same = json.loads((out/'old.json').read_text()) == json.loads((out/'new.json').read_text())
        (out/'dense_parity.json').write_text(json.dumps(dict(status='PASS' if same else 'FAIL',bit_equal=same,
            baseline_child='60b252d05157b2753d2caebae32b11c878504bbe',real_Wan_or_Action=False),indent=2)+'\n')
        results.append(dict(name='dense_parity',exit_code=0 if same else 1))
        print('dense parity',same,flush=True)
(out/'commands.json').write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(results[-1]['exit_code'])
