from pathlib import Path
import ast,hashlib,json,subprocess
root=Path('/workspace/psm_wma');out=Path('/tmp/psm-v3-eval-v2-r2-20261028/static');out.mkdir(exist_ok=True)
files=sorted(str(p.relative_to(root)) for p in root.glob('tools/v3/episode_eval_v2_prototype/*.py'))
commands=[['/workspace/.venvs/psm-wma-cpu/bin/ruff','--version'],['/workspace/.venvs/psm-wma-cpu/bin/ruff','check','--config','cosmos-framework/.ruff.toml',*files],['/workspace/.venvs/psm-wma-cpu/bin/ruff','format','--config','cosmos-framework/.ruff.toml','--check',*files],['git','diff','--check']]
checks=[]
for i,cmd in enumerate(commands):
 r=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=60);(out/f'check_{i}.log').write_text(r.stdout+r.stderr);checks.append({'argv':cmd,'cwd':str(root),'exit_code':r.returncode,'log':f'check_{i}.log'});assert r.returncode==0,(cmd,r.stdout,r.stderr)
for f in files:ast.parse((root/f).read_bytes(),filename=f)
sha={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files}
assert sha==json.loads(Path('/tmp/psm-v3-eval-v2-r2-20261028/final02/source_sha256.json').read_text())
result={'checks':checks,'syntax_files':files,'syntax':'PASS','source_sha256':sha,'frozen_source_match':True}
(out/'checks.json').write_text(json.dumps(result,indent=2));print(json.dumps({'ruff':'0.12.7','check':'PASS','format':'PASS','syntax_files':len(files),'frozen_source_match':True}))
