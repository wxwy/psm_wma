import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

base=Path('/tmp/psm-g2-spatial-policy-20261104')
mode=sys.argv[1]
old=mode.startswith('red')
root=Path('/workspace/psm-wma-g2-gateb-fix' if old else '/workspace/psm-wma-g2-spatial-policy')
out=base/mode
out.mkdir()
python='/workspace/.venvs/psm-wma-cpu/bin/python'
env=dict(os.environ)
env.update(PYTHONPATH=f'{root}:/tmp/psm-g2-rgbd-stage1-20261104/cpu_extra',
    CUDA_VISIBLE_DEVICES='',MUJOCO_GL='disable',COSMOS_DEVICE='cpu',
    PYTHONDONTWRITEBYTECODE='1',PYTEST_ADDOPTS='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
    OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
    HF_HOME=str(out/'cache/hf'),MPLCONFIGDIR=str(out/'cache/mpl'),XDG_CACHE_HOME=str(out/'cache/xdg'))
tests=[str(base/'frozen/test_spatial_photometric_policy.py')] if old else [
    'tools/g2/test_spatial_photometric_policy.py','tools/g2/test_rgbd_pose_export.py']
command=[python,'-m','pytest','--noconftest','-c','/dev/null','-q','-p','no:cacheprovider',*tests,
    '--basetemp',str(out/'pytest_tmp'),'--junitxml',str(out/'junit.xml')]
def dump(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def git(*args,cwd=root):return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
def source():return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted((root/'tools/g2').rglob('*.py'))}
def identity():
    result=dict(root=git('rev-parse','HEAD'),gitlink=git('rev-parse','HEAD:cosmos-framework'),status=git('status','--porcelain'))
    if (root/'cosmos-framework/.git').exists():
        result.update(child=git('rev-parse','HEAD',cwd=root/'cosmos-framework'),child_status=git('status','--porcelain',cwd=root/'cosmos-framework'))
    return result
before=source();ident=identity()
dump(out/'identity_before.json',ident);dump(out/'source_before.json',before)
keys=['PYTHONPATH','CUDA_VISIBLE_DEVICES','MUJOCO_GL','COSMOS_DEVICE','PYTHONDONTWRITEBYTECODE','PYTEST_ADDOPTS',
    'HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','HF_HOME','MPLCONFIGDIR','XDG_CACHE_HOME']
dump(out/'invocation.json',dict(command=command,cwd=str(root),environment_overrides={k:env[k] for k in keys},
    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,timeout=120)
(out/'pytest.log').write_text(result.stdout+result.stderr)
after=source();ident_after=identity()
dump(out/'identity_after.json',ident_after);dump(out/'source_after.json',after)
tree=ET.parse(out/'junit.xml');cases=tree.findall('.//testcase')
summary=dict(returncode=result.returncode,tests=len(cases),distinct=len({(c.get('classname'),c.get('name')) for c in cases}),
    failures=len(tree.findall('.//failure')),errors=len(tree.findall('.//error')),skipped=len(tree.findall('.//skipped')),
    source_unchanged=before==after,identity_unchanged=ident==ident_after,
    expected_old_contract_red=old,actual_renderer_or_gpu_or_server_data_used=False)
dump(out/'summary.json',summary)
print(json.dumps(summary,indent=2));print(result.stdout[-6000:])
assert cases and summary['tests']==summary['distinct'] and before==after and ident==ident_after
assert summary['errors']==summary['skipped']==0
if old:assert result.returncode==1 and summary['failures']>0
else:assert result.returncode==0 and summary['failures']==0
