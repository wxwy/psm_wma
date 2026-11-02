import ast
import hashlib
import json
import os
import py_compile
import subprocess
from pathlib import Path

root=Path('/workspace/psm-wma-eval-replan-all')
child=root/'cosmos-framework'
out=Path('/tmp/psm-eval-replan-all-20261102/final_static')
out.mkdir(exist_ok=False)
formal_root='d2041e388eda084e42a2d6b0d115db8beedfab44'
formal_child='0dd13d3d952aa7cbab39f966dfab04b23551f0c9'
root_base='f49d52e5646e54a1eb45c31f3179901650694c20'
child_base='9a8cd6183424bfce245fbca393ca25ed59919ea6'
git=lambda cwd,*a:subprocess.check_output(['git',*a],cwd=cwd,text=True).strip()
assert git(root,'rev-parse','HEAD')==formal_root
assert git(child,'rev-parse','HEAD')==git(root,'rev-parse','HEAD:cosmos-framework')==formal_child
assert not git(root,'status','--porcelain') and not git(child,'status','--porcelain')
changed={str(cwd):git(cwd,'diff','--name-only',base,'HEAD').splitlines() for cwd,base in [(root,root_base),(child,child_base)]}
allowed_root={'SESSION.md','TODO.md','cosmos-framework','docs/collab/chatgpt/CODEX_INBOX.md',
 'docs/collab/chatgpt/archive/CODEX_INBOX_20261102_REPLAN_ALL_f49d52e.md',
 'docs/build/PSM-WMA_V3_EvalV2_Replan_All_Durable_Media_Implementation_r1_2026-11-02.md',
 *['scripts/robocasa_eval_v2/'+n+'.py' for n in ['config','runtime','cli','generated_media']],
 'tools/v3/eval_v2_production_tests/worker_test.py','tools/v3/eval_v2_batch_tests/rollout_policy_test.py',
 *['tools/v3/eval_v2_replan_tests/'+n+'.py' for n in ['__init__','support','encoder_test','transport_test','native_test','config_test','report_test']]}
allowed_child={'cosmos_framework/'+p for p in ['evaluation/robocasa_v2/media.py','evaluation/robocasa_v2/generated_video.py',
 'inference/robocasa_batch_transactions.py','inference/robocasa_batch_transactions_test.py','scripts/action_policy_server_robocasa.py',
 'simulation/robocasa/eval_v2_adapter.py','simulation/robocasa/eval_v2_transactions.py','simulation/robocasa/eval_v2_transactions_test.py',
 'simulation/robocasa/eval_v2_worker.py']}
assert set(changed[str(root)])==allowed_root
assert set(changed[str(child)])==allowed_child
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',COSMOS_DEVICE='cpu',LD_LIBRARY_PATH='',RUFF_CACHE_DIR=str(out/'cache/ruff'),
 PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
commands=[]
sources={}
for name,cwd,base in [('root',root,root_base),('child',child,child_base)]:
 files=[p for p in changed[str(cwd)] if p.endswith('.py')]
 for p in files:
  absolute=cwd/p
  rel=str(absolute.relative_to(root))
  ast.parse(absolute.read_text(),filename=rel)
  compiled=out/'syntax'/rel
  compiled.parent.mkdir(parents=True,exist_ok=True)
  py_compile.compile(str(absolute),cfile=str(compiled)+'.pyc',doraise=True)
  sources[rel]=dict(git_blob=git(cwd,'rev-parse','HEAD:'+p),sha256=hashlib.sha256(absolute.read_bytes()).hexdigest())
 for check,argv in [('ruff',['/workspace/.venvs/psm-wma-cpu/bin/python','-m','ruff','check',*files]),
                    ('format',['/workspace/.venvs/psm-wma-cpu/bin/python','-m','ruff','format','--check',*files]),
                    ('diff_check',['git','diff','--check',base,'HEAD'])]:
  result=subprocess.run(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
  (out/f'{name}_{check}.log').write_bytes(result.stdout)
  commands.append(dict(command=argv,cwd=str(cwd),exit_code=result.returncode))
  assert result.returncode==0,result.stdout.decode(errors='replace')
 (out/f'{name}.patch').write_bytes(subprocess.check_output(['git','diff','--binary',base,'HEAD'],cwd=cwd))
protections={}
for name,cwd,base,paths in [
 ('root',root,root_base,['configs','third_party','scripts/robocasa_eval_v2/resources.py','scripts/robocasa_eval_v2_processes.py','scripts/train_v3_matched_no_ttt.sh']),
 ('child',child,child_base,['cosmos_framework/model','cosmos_framework/trainer','cosmos_framework/checkpoint','cosmos_framework/data',
  'cosmos_framework/configs','cosmos_framework/callbacks','examples','cosmos_framework/evaluation/robocasa_v2/store.py',
  'cosmos_framework/evaluation/robocasa_v2/scheduler.py','cosmos_framework/simulation/robocasa/closed_loop_eval.py',
  'cosmos_framework/simulation/robocasa/render_devices.py',
  *['cosmos_framework/inference/'+p+'.py' for p in ['robocasa_session_transactions','robocasa_transaction_client','local_memory_state','local_memory_online','robocasa_local_memory_policy']]])]:
 for p in paths:
  before=git(cwd,'ls-tree',base,'--',p)
  after=git(cwd,'ls-tree','HEAD','--',p)
  assert before==after,(name,p)
  protections[f'{name}/{p}']=dict(before=before,after=after,unchanged=True)
archive=root/'docs/collab/chatgpt/archive/CODEX_INBOX_20261102_REPLAN_ALL_f49d52e.md'
original=subprocess.check_output(['git','show',root_base+':docs/collab/chatgpt/CODEX_INBOX.md'],cwd=root)
assert archive.read_bytes()==original
assert (root/'docs/collab/chatgpt/CODEX_INBOX.md').stat().st_size<=131072
assert not git(root,'status','--porcelain') and not git(child,'status','--porcelain')
(out/'source_bindings.json').write_text(json.dumps(sources,indent=2)+'\n')
(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
(out/'scope.json').write_text(json.dumps(dict(changed=changed,protected=protections,rollover_byte_identical=True,
 actual_timens_offsets_available=Path('/proc/self/timens_offsets').exists(),source_unchanged=True),indent=2)+'\n')
(out/'gate.json').write_text(json.dumps(dict(status='AUTHOR_CLEAN_PAIR_STATIC_PASS',root=formal_root,child=formal_child,
 gitlink=formal_child,ruff='0.12.7',syntax_files=len(sources),source_bindings=len(sources),source_unchanged=True),indent=2)+'\n')
print('PASS clean pair static, scope/protected trees, byte-exact rollover;',len(sources),'Python source bindings')
