import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

root=Path('/workspace/psm-wma-g2-gateb-fix')
base=Path('/tmp/psm-g2-gateb-replay-20261104')
out=base/'static_final'
out.mkdir()
python='/workspace/.venvs/psm-wma-cpu/bin/python'
env=dict(os.environ)
env.update(PYTHONPATH=f'{root}:/tmp/psm-g2-rgbd-stage1-20261104/cpu_extra',
    CUDA_VISIBLE_DEVICES='',MUJOCO_GL='disable',PYTHONDONTWRITEBYTECODE='1',
    HF_HOME=str(out/'cache/hf'),MPLCONFIGDIR=str(out/'cache/mpl'),
    XDG_CACHE_HOME=str(out/'cache/xdg'),RUFF_CACHE_DIR=str(out/'cache/ruff'))
commands=[('ruff_version',[python,'-m','ruff','--version']),
    ('ruff_check',[python,'-m','ruff','check','tools/g2']),
    ('ruff_format',[python,'-m','ruff','format','--check','tools/g2']),
    ('export_help',[python,'-m','tools.g2.export_robocasa_rgbd_pose','--help']),
    ('verify_help',[python,'-m','tools.g2.verify_robocasa_rgbd_pose','--help']),
    ('lazy_import',[python,'-c',
      'import sys,json; import tools.g2.export_robocasa_rgbd_pose; '
      'import tools.g2.verify_robocasa_rgbd_pose; '
      'names=["torch","mujoco","robosuite","robocasa","lerobot","cosmos_framework"]; '
      'loaded=[n for n in names if n in sys.modules]; print(json.dumps({"unexpected_native_imports":loaded})); assert not loaded']),
    ('diff_check',['git','diff','--check'])]
results=[]
for name,command in commands:
    result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,timeout=40)
    (out/f'{name}.log').write_text(result.stdout+result.stderr)
    results.append(dict(name=name,command=command,returncode=result.returncode))
    if result.returncode: raise RuntimeError(name+': '+result.stdout+result.stderr)
files=[]
for path in sorted((root/'tools/g2').rglob('*.py')):
    content=path.read_text()
    ast.parse(content,filename=str(path));compile(content,str(path),'exec')
    files.append(dict(path=str(path.relative_to(root)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(out/'syntax.json').write_text(json.dumps(dict(ast_compile_pass=len(files),files=files),indent=2)+'\n')
(out/'commands.json').write_text(json.dumps(dict(cwd=str(root),commands=results),indent=2)+'\n')
print(json.dumps(dict(commands=len(results),ast_compile_pass=len(files),pass_all=True)))
