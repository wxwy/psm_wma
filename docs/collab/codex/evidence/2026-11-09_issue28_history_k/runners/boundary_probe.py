import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

root=Path('/workspace/work/psm-wma-history-k-issue28')
child=root/'cosmos-framework'
phase=sys.argv[1]
out=Path(__file__).parent/('boundary_'+phase)
out.mkdir(exist_ok=False)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',LD_LIBRARY_PATH='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
    OPENBLAS_NUM_THREADS='1',PYTHONPATH=str(child),PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
    HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',RUFF_CACHE_DIR=str(out/'cache'))
command=[sys.executable,'-m','pytest','--noconftest','-c','/dev/null','--rootdir='+str(root),'-p','no:cacheprovider',
    '-q',str(child/'cosmos_framework/inference/robocasa_history_k_test.py'),'-k','sparse_partial_tail',
    '--junitxml='+str(out/'boundary.xml')]
identity={}
for label,repo in [('root',root),('child',child)]:
    identity[label]=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    identity[label+'_status']=subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True)
with (out/'boundary.log').open('w') as log:
    result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60)
suites=list(ET.parse(out/'boundary.xml').getroot().iter('testsuite'))
counts={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
expected=(result.returncode==1 and counts==dict(tests=8,failures=8,errors=0,skipped=0)) if phase=='red' else (
    result.returncode==0 and counts==dict(tests=8,failures=0,errors=0,skipped=0))
record=dict(phase=phase,command=command,identity=identity,pytest_exit=result.returncode,counts=counts,
    expected_outcome=expected,source_worktree_dirty_for_new_regression=True,
    test_sha256=hashlib.sha256((child/'cosmos_framework/inference/robocasa_history_k_test.py').read_bytes()).hexdigest(),
    production_sha256={name:hashlib.sha256((child/'cosmos_framework'/name).read_bytes()).hexdigest()
        for name in ('inference/local_memory_online.py','inference/robocasa_feature_evidence.py')})
(out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
raise SystemExit(0 if expected else 1)
