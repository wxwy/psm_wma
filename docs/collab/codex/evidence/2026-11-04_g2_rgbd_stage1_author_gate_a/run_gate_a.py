import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path('/workspace/psm-wma-g2-rgbd-stage1')
BASE = Path('/tmp/psm-g2-rgbd-stage1-20261104')
OUT = BASE / sys.argv[1]
OUT.mkdir()
PYTHON = '/workspace/.venvs/psm-wma-cpu/bin/python'
ENV = dict(os.environ)
ENV.update({'PYTHONPATH': f'{ROOT}:{BASE / "cpu_extra"}',
    'CUDA_VISIBLE_DEVICES': '', 'COSMOS_DEVICE': 'cpu', 'MUJOCO_GL': 'disable',
    'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_ADDOPTS': '',
    'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'LD_LIBRARY_PATH': '',
    'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
    'HF_HOME': str(OUT / 'cache/hf'), 'MPLCONFIGDIR': str(OUT / 'cache/mpl'),
    'XDG_CACHE_HOME': str(OUT / 'cache/xdg'), 'RUFF_CACHE_DIR': str(OUT / 'cache/ruff')})
for name in ['hf', 'mpl', 'xdg', 'ruff']: (OUT / 'cache' / name).mkdir(parents=True)
sources = sorted((ROOT / 'tools/g2').rglob('*.py'))
def snapshot():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
before = snapshot()
def identity():
    def git(*args, cwd=ROOT):
        return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
    return {'root':git('rev-parse','HEAD'),'gitlink':git('rev-parse','HEAD:cosmos-framework'),
            'child':git('rev-parse','HEAD',cwd=ROOT/'cosmos-framework'),
            'root_status':git('status','--porcelain'),
            'child_status':git('status','--porcelain',cwd=ROOT/'cosmos-framework')}
ident_before=identity()
if OUT.name=='final_cpu':
    assert ident_before['root']=='3d163e91d42802efe487deb89286637cc91ed74c'
    assert ident_before['gitlink']==ident_before['child']=='1069fe78841228cadbbfbe6afbd767eaed6225da'
    assert not ident_before['root_status'] and not ident_before['child_status']
if OUT.name=='final83':
    assert ident_before['root']=='b67bc4ca9a2afb1ff26fac0846f8ee7042a589ab'
    assert ident_before['gitlink']==ident_before['child']=='1069fe78841228cadbbfbe6afbd767eaed6225da'
    assert not ident_before['root_status'] and not ident_before['child_status']
(OUT/'identity_before.json').write_text(json.dumps(ident_before,indent=2)+'\n')
sys.path.insert(0,str(BASE/'cpu_extra'))
(OUT/'versions.json').write_text(json.dumps({'python':sys.version,'interpreter':sys.executable,
    'packages':{n:importlib.metadata.version(n) for n in ['numpy','pyarrow','scipy','pytest','ruff','mujoco','glfw','PyOpenGL','etils']},
    'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
(OUT / 'source_before.json').write_text(json.dumps(before, indent=2)+'\n')
command = [PYTHON, '-m', 'pytest', '--noconftest', '-c', '/dev/null', '-q', '-p', 'no:cacheprovider',
    'tools/g2/test_rgbd_pose_export.py', '--basetemp', str(OUT / 'pytest_tmp'), '--junitxml', str(OUT / 'junit.xml')]
(OUT / 'invocation.json').write_text(json.dumps({'args': command, 'cwd': str(ROOT),
    'environment_overrides': {k:ENV[k] for k in ['PYTHONPATH','CUDA_VISIBLE_DEVICES','COSMOS_DEVICE','MUJOCO_GL',
    'PYTHONDONTWRITEBYTECODE','PYTEST_ADDOPTS','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','LD_LIBRARY_PATH',
    'OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','HF_HOME','MPLCONFIGDIR','XDG_CACHE_HOME','RUFF_CACHE_DIR']}}, indent=2)+'\n')
result = subprocess.run(command, cwd=ROOT, env=ENV, capture_output=True, text=True)
(OUT / 'pytest.log').write_text(result.stdout+result.stderr)
after = snapshot()
ident_after=identity()
(OUT/'identity_after.json').write_text(json.dumps(ident_after,indent=2)+'\n')
assert ident_before==ident_after
(OUT / 'source_after.json').write_text(json.dumps(after, indent=2)+'\n')
tree = ET.parse(OUT / 'junit.xml')
cases = tree.findall('.//testcase')
summary = {'returncode':result.returncode,'tests':len(cases),'failures':len(tree.findall('.//failure')),
    'errors':len(tree.findall('.//error')),'skips':len(tree.findall('.//skipped')),
    'source_unchanged':before==after,'real_source_data_accessed':False,'renderer_or_gpu_started':False}
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
print(json.dumps(summary, indent=2), flush=True)
print(result.stdout[-2000:], flush=True)
assert result.returncode == 0 and cases and len({(c.attrib['classname'],c.attrib['name']) for c in cases})==len(cases)
assert summary['failures']==summary['errors']==summary['skips']==0
assert before==after
