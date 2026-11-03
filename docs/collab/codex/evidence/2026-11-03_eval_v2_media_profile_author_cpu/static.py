import ast
import hashlib
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

root=Path('/workspace/psm-wma-eval-replan-all');child=root/'cosmos-framework'
base='b19b9edf7f39a83013a853f95c543081e0216b28';child_sha='c93f2abf4fb27d36176ff8db094379a853cec796'
out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
files=['scripts/robocasa_eval_v2/generated_media.py','tools/v3/eval_v2_replan_tests/media_profile_test.py']
git=lambda cwd,*a:subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
formal=len(sys.argv)>2
assert git(child,'rev-parse','HEAD')==git(root,'rev-parse','HEAD:cosmos-framework')==child_sha
assert not git(child,'status','--porcelain')
if formal:assert git(root,'rev-parse','HEAD')==sys.argv[2] and not git(root,'status','--porcelain')
old=subprocess.check_output(['git','show',base+':'+files[0]],cwd=root,text=True)
assert old.count('== "phase_b"')==1
assert ast.dump(ast.parse(old.replace('== "phase_b"','== "phase_b_native_batch_v1"')))==ast.dump(ast.parse((root/files[0]).read_text()))
assert (root/files[1]).read_bytes()==Path('/tmp/psm-eval-v2-media-profile-20261103/red/frozen_test.py').read_bytes()
changes=git(root,'diff','--name-only',base).splitlines()
assert all(p in files+['SESSION.md','TODO.md'] for p in changes),changes
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',PYTHONDONTWRITEBYTECODE='1',RUFF_CACHE_DIR=str(out/'cache/ruff'))
commands=[];bindings={}
for name,args in [('ruff',['check',*files]),('format',['format','--check',*files])]:
 command=['/workspace/.venvs/psm-wma-cpu/bin/python','-m','ruff',*args]
 p=subprocess.run(command,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
 (out/(name+'.log')).write_bytes(p.stdout);commands.append(dict(command=command,cwd=str(root),exit_code=p.returncode))
 assert p.returncode==0,p.stdout.decode()
for i,file in enumerate(files):
 ast.parse((root/file).read_text());py_compile.compile(str(root/file),cfile=str(out/(str(i)+'.pyc')),doraise=True)
 bindings[file]=dict(git_blob=git(root,'hash-object',file),sha256=hashlib.sha256((root/file).read_bytes()).hexdigest())
for path in ['cosmos-framework','configs','third_party','docs/collab/codex/evidence/2026-11-02_eval_v2_replan_all_author_cpu',
             'docs/collab/codex/evidence/2026-11-02_eval_v2_rm_all_r01_author_cpu']:
 assert git(root,'ls-tree',base,'--',path)==git(root,'ls-tree','HEAD','--',path)
 assert not git(root,'diff','--name-only',base,'--',path)
patch=subprocess.check_output(['git','diff','--binary',base],cwd=root);(out/'root.patch').write_bytes(patch)
p=subprocess.run(['git','diff','--check',base],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);assert p.returncode==0
(out/'diff_check.log').write_bytes(p.stdout)
(out/'source_bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
(out/'scope.json').write_text(json.dumps(dict(base=base,root_changes=changes,child=child_sha,child_unchanged=True,
 production_AST_only_native_profile_literal=True,frozen_test_unchanged=True,old_379_122_evidence_unchanged=True),indent=2)+'\n')
(out/'gate.json').write_text(json.dumps(dict(status='AUTHOR_CLEAN_PAIR_STATIC_PASS' if formal else 'DEVELOPMENT_STATIC_PASS',
 root=git(root,'rev-parse','HEAD'),child=child_sha,gitlink=child_sha,ruff='0.12.7',source_bindings=2,syntax_files=2),indent=2)+'\n')
print('PASS static2; AST only native-profile literal changed; Child and prior evidence unchanged',flush=True)
