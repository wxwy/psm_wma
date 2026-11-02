import ast
import hashlib
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

root=Path('/workspace/psm-wma-eval-replan-all');child=root/'cosmos-framework'
out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
root_base='ec8a8bf31d6e4cd2cc1a387b77d8510aef57e06f'
child_base='0dd13d3d952aa7cbab39f966dfab04b23551f0c9'
test='tools/v3/eval_v2_replan_tests/ack_history_test.py'
production='cosmos_framework/inference/robocasa_batch_transactions.py'
git=lambda cwd,*args:subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()
formal=len(sys.argv)>2
if formal:
 assert git(root,'rev-parse','HEAD')==sys.argv[2]
 assert git(child,'rev-parse','HEAD')==git(root,'rev-parse','HEAD:cosmos-framework')==sys.argv[3]
 assert not git(root,'status','--porcelain') and not git(child,'status','--porcelain')
assert (root/test).read_bytes()==Path('/tmp/psm-eval-v2-rm-all-r01-20261102/red/frozen_test.py').read_bytes()
assert git(child,'diff','--name-only',child_base).splitlines()==[production]
changes=git(root,'diff','--name-only',root_base).splitlines()
assert all(p in ['SESSION.md','TODO.md','cosmos-framework',test] for p in changes),changes
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',LD_LIBRARY_PATH='',RUFF_CACHE_DIR=str(out/'cache/ruff'),PYTHONDONTWRITEBYTECODE='1')
commands=[];bindings={}
for name,cwd,path in [('root',root,test),('child',child,production)]:
 for kind,args in [('ruff',['check',path]),('format',['format','--check',path])]:
  command=['/workspace/.venvs/psm-wma-cpu/bin/python','-m','ruff',*args]
  run=subprocess.run(command,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
  (out/f'{name}_{kind}.log').write_bytes(run.stdout)
  commands.append(dict(command=command,cwd=str(cwd),exit_code=run.returncode))
  assert run.returncode==0,run.stdout.decode()
 absolute=cwd/path;relative=str(absolute.relative_to(root))
 ast.parse(absolute.read_text())
 py_compile.compile(str(absolute),cfile=str(out/(name+'.pyc')),doraise=True)
 bindings[relative]=dict(sha256=hashlib.sha256(absolute.read_bytes()).hexdigest(),git_blob=git(cwd,'hash-object',path))
protected={}
for name,cwd,base,paths in [('root',root,root_base,['scripts','configs','third_party','tools/v3/eval_v2_production_tests',
 'tools/v3/eval_v2_batch_tests','docs/collab/codex/evidence/2026-11-02_eval_v2_replan_all_author_cpu',
 'docs/collab/chatgpt/archive/CODEX_INBOX_20261102_REPLAN_ALL_f49d52e.md']),
 ('child',child,child_base,['cosmos_framework/model','cosmos_framework/trainer','cosmos_framework/checkpoint','cosmos_framework/data',
 'cosmos_framework/evaluation','cosmos_framework/simulation','cosmos_framework/scripts','cosmos_framework/inference/robocasa_session_transactions.py',
 'cosmos_framework/inference/robocasa_transaction_client.py','cosmos_framework/inference/robocasa_batch_transactions_test.py'])]:
 for path in paths:
  old=git(cwd,'ls-tree',base,'--',path)
  now=git(cwd,'ls-tree','HEAD','--',path)
  # None of these paths is modified in this narrow implementation.
  assert old==now and not git(cwd,'diff','--name-only',base,'--',path)
  protected[name+'/'+path]=dict(before=old,after=now,unchanged=True)
for name,cwd,base in [('root',root,root_base),('child',child,child_base)]:
 check=subprocess.run(['git','diff','--check',base],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 assert check.returncode==0
 (out/f'{name}_diff_check.log').write_bytes(check.stdout)
 (out/f'{name}.patch').write_bytes(subprocess.check_output(['git','diff','--binary',base],cwd=cwd))
(out/'source_bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
(out/'scope.json').write_text(json.dumps(dict(root_base=root_base,child_base=child_base,root_changes=changes,
 child_changes=[production],protected=protected,old_379_evidence_unchanged=True,
 frozen_test_unchanged=True),indent=2)+'\n')
(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
(out/'gate.json').write_text(json.dumps(dict(status='AUTHOR_CLEAN_PAIR_STATIC_PASS' if formal else 'DEVELOPMENT_STATIC_PASS',
 root=git(root,'rev-parse','HEAD'),child=git(child,'rev-parse','HEAD'),gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),
 ruff='0.12.7',source_bindings=2,syntax_files=2,formal=formal),indent=2)+'\n')
print('PASS Ruff/format/AST/py_compile2, narrow scope, frozen test and previous379 evidence unchanged',flush=True)
