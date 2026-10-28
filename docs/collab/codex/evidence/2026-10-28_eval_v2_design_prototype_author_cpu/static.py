import hashlib,json,subprocess
from pathlib import Path
r=Path('/workspace/psm_wma');b=Path('/tmp/psm-v3-eval-v2-20261028');out=b/'static';out.mkdir(exist_ok=True)
files=sorted(str(p.relative_to(r)) for p in (r/'tools/v3/episode_eval_v2_prototype').glob('*.py'))
cmds=[['/workspace/.venvs/psm-wma-cpu/bin/ruff','--version'],['/workspace/.venvs/psm-wma-cpu/bin/ruff','check','--config','cosmos-framework/.ruff.toml',*files],['/workspace/.venvs/psm-wma-cpu/bin/ruff','format','--config','cosmos-framework/.ruff.toml','--check',*files],['git','diff','--check']]
checks=[]
for i,cmd in enumerate(cmds):
 p=subprocess.run(cmd,cwd=r,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/f'check_{i}.log').write_text(p.stdout);assert p.returncode==0,p.stdout;checks.append({'cwd':str(r),'argv':cmd,'exit_code':p.returncode,'log':f'check_{i}.log'})
for f in files:compile((r/f).read_bytes(),str(r/f),'exec')
h=json.loads((b/'final02/source_sha256.json').read_text());assert all(hashlib.sha256((r/f).read_bytes()).hexdigest()==v for f,v in h.items())
(out/'checks.json').write_text(json.dumps({'checks':checks,'syntax_files':files,'syntax':'PASS','frozen_source_sha256_match':True},indent=2));print(json.dumps({'static_python_files':len(files),'all_static':'PASS','frozen_hashes':len(h)}))
