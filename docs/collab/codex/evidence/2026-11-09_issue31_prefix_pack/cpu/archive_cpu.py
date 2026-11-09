"""Archive only newly generated local Stage2 CPU evidence; no remote files."""
import ast
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

root=Path('/workspace/work/psm-wma-prefix-pack-issue31')
child=root/'cosmos-framework'
source=Path(__file__).parent
formal_root='18be4a80a5ae4d97bc7d287034d24efab847c496'
formal_child='193627f42f4cd1ba6d563aefb8fa8f9428ecb56d'
base_root='590071c599c0531cd9feca9ae748eb0be1af1c89'
base_child='4446be0f6dad9b6dc887ef90af52d0af754d4682'
out=root/'docs/collab/codex/evidence/2026-11-09_issue31_prefix_pack/cpu'
git=lambda repo,*args:subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
save=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n')
assert git(root,'rev-parse','HEAD')==formal_root
assert git(child,'rev-parse','HEAD')==formal_child
assert git(root,'rev-parse','HEAD:cosmos-framework')==formal_child
assert not out.exists()
out.mkdir(parents=True)
changed_root=set(git(root,'diff','--name-only',base_root,formal_root).splitlines())
changed_child=set(git(child,'diff','--name-only',base_child,formal_child).splitlines())
assert changed_root=={'SESSION.md','TODO.md','cosmos-framework','tools/v3/benchmark_local_ttt_prefix_kv.py'}
prefix='cosmos_framework/model/generator/'
assert changed_child=={prefix+'omni_mot_model.py',prefix+'mot/prefix_text_kv_memory_test.py',prefix+'mot/prefix_pack_template_test.py'}
name=prefix+'omni_mot_model.py'
before=ast.parse(git(child,'show',base_child+':'+name))
after=ast.parse(git(child,'show',formal_child+':'+name))
protected={}
for method in ('_get_velocity','_update_inference_pack_template','_copy_timestep_to_template',
               '_can_reuse_inference_pack_templates','_can_reuse_inference_text_kv'):
 a=next(n for n in ast.walk(before) if isinstance(n,ast.FunctionDef) and n.name==method)
 b=next(n for n in ast.walk(after) if isinstance(n,ast.FunctionDef) and n.name==method)
 assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
 protected[method]=hashlib.sha256(ast.dump(a,include_attributes=False).encode()).hexdigest()
save(out/'scope.json',dict(status='PASS',formal_root=formal_root,formal_child=formal_child,
 base_root=base_root,base_child=base_child,changed_root=sorted(changed_root),changed_child=sorted(changed_child),
 unchanged_method_ast_sha256=protected,
 production_delta='Only generate_samples_from_batch: Prefix pack option and existing textKV eligibility computed before template allocation; existing native updater reused unchanged.',
 protected='All other tracked Child/Root production paths identical, including attention/cache/fast weights/training/VAE/Sim/Worker/Resume/mode-DCP checks.'))
for label,repo,base,head in [('root',root,base_root,formal_root),('child',child,base_child,formal_child)]:
 (out/(label+'.diff')).write_bytes(subprocess.check_output(['git','-C',str(repo),'diff','--binary',base,head]))
for n in ('cpu_gate.py','archive_cpu.py'):
 shutil.copyfile(source/n,out/n)
for directory in ('dev01','dev02','dev03','author01','author02','red01'):
 for p in sorted((source/directory).glob('*')):
  if p.is_file() and p.suffix in ('.json','.log','.xml'):
   q=out/'raw'/directory/p.name
   q.parent.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(p,q)
gate=json.loads((out/'raw/author02/gate.json').read_text())
assert gate['status']=='PASS' and gate['junit']==dict(tests=201,failures=0,errors=0,skipped=0)
assert gate['source_unchanged'] and gate['identity']['root']==formal_root
red=Path('/workspace/work/issue31-prefix-pack-red-child')
test=prefix+'mot/prefix_pack_template_test.py'
assert git(red,'rev-parse','HEAD')==base_child and not git(red,'diff','--name-only')
assert (child/test).read_bytes()==(red/test).read_bytes()
save(out/'controlled_red_green.json',dict(
 red_child=base_child,red_worktree_status=git(red,'status','--porcelain'),
 new_child=formal_child,test_sha256=hashlib.sha256((child/test).read_bytes()).hexdigest(),
 red='raw/red01/focused.xml',red_expected='assert obj.templates == 1; actual0',
 green='raw/author02/focused.xml',new='201 focused PASS including same positive test',
 qualification='Old production clean; only same new test file untracked. Red pytest -c /dev/null derives rootdir /dev; explicit test path and exact source hash identify test.',
 inherited_failure='Stage1 W0 failure preserved in inherited archive and independently confirmed by GPT on4cd5/4446; explicitly deselected, not rerun/fixed/countingPASS.'))
payload={}
for p in sorted(out.rglob('*')):
 if p.is_file():
  b=p.read_bytes()
  payload[str(p.relative_to(out))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),
   git_blob_sha1=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest())
save(out/'index.json',dict(kind='Stage2 author focused CPU/static only; independent approval NOT_CLAIMED',
 formal_root=formal_root,formal_child=formal_child,files=payload,private_server_files_exported=False,
 result='201 PASS/0failure/error/skip;1 inherited W0 assertion explicitly deselected;3 baselineI001 retained',
 initial_development='dev01 import-sort FAIL;dev02 187PASS/14newfixtureFAIL;corrected14PASSdev03;all raw retained'))
print(json.dumps(dict(status='PASS',files=len(payload),formal_root=formal_root,formal_child=formal_child),indent=2))
