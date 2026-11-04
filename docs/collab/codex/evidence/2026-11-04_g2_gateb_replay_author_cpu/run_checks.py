import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

BASE = Path('/tmp/psm-g2-gateb-replay-20261104')
ROOT = Path('/workspace/psm-wma-g2-gateb-fix')
PYTHON = '/workspace/.venvs/psm-wma-cpu/bin/python'
EXTRA = '/tmp/psm-g2-rgbd-stage1-20261104/cpu_extra'
LIB = str(BASE / 'native/extracted/usr/lib/x86_64-linux-gnu')
mode = sys.argv[1]
out = BASE / mode
out.mkdir()
old = mode.startswith('red')
render = not mode.startswith('legacy83')
root = Path('/workspace/psm-wma-g2-rgbd-stage1') if old else ROOT
test = str(BASE / 'frozen/test_replay_render_visibility.py') if old else (
    'tools/g2/test_replay_render_visibility.py' if render else 'tools/g2/test_rgbd_pose_export.py')
env = dict(os.environ)
env.update(PYTHONPATH=f'{root}:{EXTRA}', CUDA_VISIBLE_DEVICES='', COSMOS_DEVICE='cpu',
    MUJOCO_GL='osmesa' if render else 'disable', PYOPENGL_PLATFORM='osmesa',
    LIBGL_ALWAYS_SOFTWARE='1', LD_LIBRARY_PATH=LIB if render else '',
    OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
    PYTHONDONTWRITEBYTECODE='1', PYTEST_ADDOPTS='', HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1', HF_HOME=str(out/'cache/hf'),
    MPLCONFIGDIR=str(out/'cache/mpl'), XDG_CACHE_HOME=str(out/'cache/xdg'))
command=[PYTHON,'-m','pytest','--noconftest','-c','/dev/null','-q','-p','no:cacheprovider',
    test,'--basetemp',str(out/'pytest_tmp'),'--junitxml',str(out/'junit.xml')]
def snapshot():
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((root/'tools/g2').rglob('*.py'))}
def identity():
    def git(*args): return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
    child=root/'cosmos-framework'
    return dict(root=git('rev-parse','HEAD'),gitlink=git('rev-parse','HEAD:cosmos-framework'),
        status=git('status','--porcelain'),
        child=subprocess.check_output(['git','rev-parse','HEAD'],cwd=child,text=True).strip(),
        child_status=subprocess.check_output(['git','status','--porcelain'],cwd=child,text=True).strip())
before=snapshot()
identity_before=identity()
(out/'source_before.json').write_text(json.dumps(before,indent=2)+'\n')
(out/'identity_before.json').write_text(json.dumps(identity_before,indent=2)+'\n')
keys=['PYTHONPATH','CUDA_VISIBLE_DEVICES','COSMOS_DEVICE','MUJOCO_GL','PYOPENGL_PLATFORM',
    'LIBGL_ALWAYS_SOFTWARE','LD_LIBRARY_PATH','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS',
    'MKL_NUM_THREADS','PYTHONDONTWRITEBYTECODE','PYTEST_ADDOPTS','HF_HUB_OFFLINE',
    'TRANSFORMERS_OFFLINE','HF_HOME','MPLCONFIGDIR','XDG_CACHE_HOME']
(out/'invocation.json').write_text(json.dumps(dict(command=command,cwd=str(root),
    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    environment_overrides={k:env[k] for k in keys}),indent=2)+'\n')
result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,timeout=180)
(out/'pytest.log').write_text(result.stdout+result.stderr)
after=snapshot()
identity_after=identity()
(out/'source_after.json').write_text(json.dumps(after,indent=2)+'\n')
(out/'identity_after.json').write_text(json.dumps(identity_after,indent=2)+'\n')
tree=ET.parse(out/'junit.xml')
cases=tree.findall('.//testcase')
summary=dict(returncode=result.returncode,tests=len(cases),
    distinct=len({(c.get('classname'),c.get('name')) for c in cases}),
    failures=len(tree.findall('.//failure')),errors=len(tree.findall('.//error')),
    skipped=len(tree.findall('.//skipped')),source_unchanged=before==after,
    identity_unchanged=identity_before==identity_after,
    native_cpu_software_render=render,real_source_or_server_data=False,gpu_used=False,
    expected_baseline_red=old)
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
print(result.stdout[-5000:])
assert before==after and identity_before==identity_after
assert summary['tests']==summary['distinct'] and cases
assert not summary['skipped'] and not summary['errors']
if old: assert result.returncode==1 and summary['failures']>0
else: assert result.returncode==0 and summary['failures']==0
