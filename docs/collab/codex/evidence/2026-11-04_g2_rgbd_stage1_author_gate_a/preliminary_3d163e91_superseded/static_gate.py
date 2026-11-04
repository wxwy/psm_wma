import ast
import hashlib
import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys

ROOT=Path('/workspace/psm-wma-g2-rgbd-stage1')
BASE=Path('/tmp/psm-g2-rgbd-stage1-20261104')
OUT=BASE/sys.argv[1]
OUT.mkdir()
ENV=dict(os.environ)
ENV.update({'PYTHONPATH':f'{ROOT}:{BASE/"cpu_extra"}','CUDA_VISIBLE_DEVICES':'','MUJOCO_GL':'disable',
            'PYTHONDONTWRITEBYTECODE':'1','RUFF_CACHE_DIR':str(BASE/'ruff_cache'),
            'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
commands=[]
for name,args in [
 ('ruff_version',['/workspace/.venvs/psm-wma-cpu/bin/ruff','--version']),
 ('ruff_check',['/workspace/.venvs/psm-wma-cpu/bin/ruff','check','tools/g2']),
 ('ruff_format',['/workspace/.venvs/psm-wma-cpu/bin/ruff','format','--check','tools/g2']),
 ('export_help',['/workspace/.venvs/psm-wma-cpu/bin/python','-m','tools.g2.export_robocasa_rgbd_pose','--help']),
 ('verify_help',['/workspace/.venvs/psm-wma-cpu/bin/python','-m','tools.g2.verify_robocasa_rgbd_pose','--help']),
 ('lazy_imports',['/workspace/.venvs/psm-wma-cpu/bin/python','-c',
  'import json,sys; import tools.g2.export_robocasa_rgbd_pose; import tools.g2.verify_robocasa_rgbd_pose; names=["torch","cosmos_framework","mujoco","robocasa","robosuite","lerobot"]; result={n:n in sys.modules for n in names}; print(json.dumps(result)); assert not any(result.values())']),
]:
 p=subprocess.run(args,cwd=ROOT,env=ENV,capture_output=True,text=True)
 (OUT/(name+'.log')).write_text(p.stdout+p.stderr)
 commands.append({'name':name,'args':args,'cwd':str(ROOT),'returncode':p.returncode})
 assert p.returncode==0,p.stdout+p.stderr
 if name=='ruff_version': assert p.stdout.strip()=='ruff 0.12.7'
print('Ruff/check/format/CLI help/lazy native imports PASS',flush=True)
sources=[]
for i,path in enumerate(sorted((ROOT/'tools/g2').rglob('*.py'))):
 data=path.read_bytes(); ast.parse(data)
 py_compile.compile(str(path),cfile=str(OUT/f'pycache/{i}.pyc'),doraise=True)
 sources.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest()})
(OUT/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
(OUT/'syntax.json').write_text(json.dumps({'status':'PASS','files':sources,'count':len(sources)},indent=2)+'\n')
print('AST/compile PASS',len(sources),'source files',flush=True)
