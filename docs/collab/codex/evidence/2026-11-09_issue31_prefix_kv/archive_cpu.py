"""Archive only newly generated local CPU evidence; never read remote files."""
import ast
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
from pathlib import Path

root=Path('/workspace/work/psm-wma-prefix-kv-issue31')
child=root/'cosmos-framework'
source=Path(__file__).parent
formal_root='edf1e4eed8965a4fc20fc7a5a0d6116505654755'
formal_child='9f6cf6a1447983c10f9ff70895487165c6c65736'
base_root='ca3a08acf8697b5ff316fcc476c4f0820d8f3b13'
base_child='4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe'
out=root/'docs/collab/codex/evidence/2026-11-09_issue31_prefix_kv'
out.mkdir(exist_ok=False)
def git(repo,*args):
 return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def save(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,indent=2)+'\n')
assert git(root,'rev-parse','HEAD')==formal_root
assert git(child,'rev-parse','HEAD')==formal_child
assert git(root,'rev-parse',formal_root+':cosmos-framework')==formal_child
prod=['model/generator/'+s for s in ('omni_mot_model.py','mot/inference_text_kv_memory.py',
 'mot/unified_mot.py','mot/cosmos3_vfm_network.py')]
allowed_child={'cosmos_framework/'+s for s in prod}
allowed_child.add('cosmos_framework/model/generator/mot/prefix_text_kv_memory_test.py')
changed_child=set(git(child,'diff','--name-only',base_child,formal_child).splitlines())
changed_root=set(git(root,'diff','--name-only',base_root,formal_root).splitlines())
assert changed_child==allowed_child
assert changed_root=={'SESSION.md','TODO.md','cosmos-framework','tools/v3/benchmark_local_ttt_prefix_kv.py',
 'tools/v3/prefix_kv_benchmark_test.py'}
network='cosmos_framework/model/generator/mot/cosmos3_vfm_network.py'
old=ast.parse(git(child,'show',base_child+':'+network))
new=ast.parse(git(child,'show',formal_child+':'+network))
methods={}
for name in ('scan_local_memory','_encode_action','_decode_action'):
 a=next(n for n in ast.walk(old) if isinstance(n,ast.FunctionDef) and n.name==name)
 b=next(n for n in ast.walk(new) if isinstance(n,ast.FunctionDef) and n.name==name)
 encoded=ast.dump(a,include_attributes=False).encode()
 assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
 methods[name]=hashlib.sha256(encoded).hexdigest()
scope=dict(status='PASS',formal_root=formal_root,formal_child=formal_child,base_root=base_root,
 base_child=base_child,changed_root=sorted(changed_root),changed_child=sorted(changed_child),
 unchanged_method_ast_sha256=methods,
 protected_paths='All other tracked Root/Child files unchanged by exact Git diff; training/VAE/Sim/Worker/config/Resume/attention.py/memory_prefix.py preserved')
save(out/'scope.json',scope)
for label,repo,base,head in [('root',root,base_root,formal_root),('child',child,base_child,formal_child)]:
 (out/(label+'.diff')).write_bytes(subprocess.check_output(['git','-C',str(repo),'diff','--binary',base,head]))
for name in ('cpu_gate.py','archive_cpu.py'):
 shutil.copyfile(source/name,out/name)
for directory in ('dev01','dev02','dev03','dev04','dev05','dev06','author01','author02','author03',
                  'author04','author05','baseline01','compile_red','compile_green','compile_green02','compile_red02','counter_dev'):
 for path in sorted((source/directory).glob('*')):
  if path.is_file() and path.suffix in ('.log','.json','.xml'):
   target=out/'raw'/directory/path.name
   target.parent.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(path,target)
save(out/'cpu_versions.json',{name:importlib.metadata.version(name) for name in ('torch','pytest','ruff','omegaconf')})
red=Path('/workspace/work/issue31-compile-red-child')
test='cosmos_framework/model/generator/mot/prefix_text_kv_memory_test.py'
assert (child/test).read_bytes()==(red/test).read_bytes()
assert git(red,'diff','--name-only')==test
save(out/'controlled_compile_reproduction.json',dict(
 red_production_child=git(red,'rev-parse','HEAD'), red_worktree_status=git(red,'status','--porcelain'),
 new_production_child=formal_child, test_sha256=hashlib.sha256((child/test).read_bytes()).hexdigest(),
 red='raw/compile_red02/compiled.xml',green='raw/compile_green02/compiled.xml',
 old='1 static PASS / 1 dynamic BooleanAtom FAIL',new='2 PASS',
 note='Red worktree carries same new regression file; all production bytes are exact old commit.'))
baseline=Path('/workspace/work/issue31-baseline-child')
legacy_paths=['cosmos_framework/model/generator/mot/inference_text_kv_memory.py',
              'cosmos_framework/model/generator/mot/unified_mot.py']
ruff=['/workspace/.venvs/psm-wma-cpu/bin/ruff','check','--output-format','concise',*legacy_paths]
r=subprocess.run(ruff,cwd=baseline,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
assert r.returncode==1 and r.stdout.count('I001')==2
target=out/'raw/baseline01/ruff_inherited.log'
target.write_text(r.stdout)
save(out/'raw/baseline01/ruff_inherited.command.json',dict(argv=ruff,cwd=str(baseline),exit_code=r.returncode,
 baseline=git(baseline,'rev-parse','HEAD'),status=git(baseline,'status','--porcelain')))
payload={}
for path in sorted(out.rglob('*')):
 if path.is_file():
  content=path.read_bytes()
  payload[str(path.relative_to(out))]=dict(bytes=len(content),sha256=hashlib.sha256(content).hexdigest(),
       git_blob_sha1=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest())
save(out/'index.json',dict(kind='Codex author CPU/static evidence only',formal_root=formal_root,
 formal_child=formal_child,files=payload,private_server_files_exported=False,
 final_cpu='186 PASS,0 failure/error/skip;1 explicitly deselected preexisting W0 assertion retained with clean-baseline reproduction',
 inherited_ruff='two baseline I001 findings retained; all other scoped diagnostics passed'))
print(json.dumps(dict(status='PASS',output=str(out),files=len(payload),scope='PASS'),indent=2))
