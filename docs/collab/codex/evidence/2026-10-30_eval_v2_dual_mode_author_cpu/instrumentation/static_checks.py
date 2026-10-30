"""Static source-scope checks; no production model/runtime execution."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir()
root_base='608f55dccff6077e276e78644af6a578b4087781'
child_base='53c3c95202e14d3b72d236eee6899a80acf82989'
child=root/'cosmos-framework'
def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def blob(repo,ref,name):
    return subprocess.check_output(['git','-C',str(repo),'show',ref+':'+name])
def changed(repo,base):
    return set(git(repo,'diff','--name-only',base).splitlines()) | set(git(repo,'ls-files','--others','--exclude-standard').splitlines())
root_names=changed(root,root_base)-{'cosmos-framework','SESSION.md','TODO.md'}
child_names=changed(child,child_base)
assert all(n.endswith('.py') for n in root_names|child_names)
assert all(n.startswith(('scripts/robocasa_eval_v2/','tools/v3/eval_v2_')) or n=='scripts/eval_robocasa_18task_queue.py' for n in root_names)
allowed_child={
'evaluation/robocasa_v2/contract.py','evaluation/robocasa_v2/evidence.py','evaluation/robocasa_v2/store.py',
'inference/robocasa_session_transactions.py','inference/robocasa_batch_transactions.py','inference/robocasa_transaction_client.py',
'inference/robocasa_transaction_mode.py','inference/robocasa_dual_mode_test.py',
'scripts/action_policy_server_robocasa.py','scripts/robocasa_transactions_b1_test.py',
'simulation/robocasa/eval_v2_adapter.py','simulation/robocasa/eval_v2_transactions.py','simulation/robocasa/eval_v2_worker.py'}
assert child_names == {'cosmos_framework/'+n for n in allowed_child},child_names
names=sorted(root_names | {'cosmos-framework/'+n for n in child_names})
protected_root=['scripts/robocasa_vendor.py','scripts/robocasa_episode_resume/model_identity.py','scripts/robocasa_eval_v2/resources.py',
                'scripts/robocasa_eval_v2/cli.py','tools/v3/run_eval_v2_batch_b2_cpu_gate.py']
assert all((root/n).read_bytes()==blob(root,root_base,n) for n in protected_root)
def ast_node(raw,name):
    return ast.dump(next(n for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name),include_attributes=False)
assert ast_node((root/'scripts/robocasa_eval_v2/identity.py').read_text(),'verify_source')==ast_node(blob(root,root_base,'scripts/robocasa_eval_v2/identity.py'),'verify_source')
for name in ('safe','mkdir','_publish','read','write','write_report','write_runtime_probe'):
    assert ast_node((child/'cosmos_framework/evaluation/robocasa_v2/store.py').read_text(),name)==ast_node(blob(child,child_base,'cosmos_framework/evaluation/robocasa_v2/store.py'),name)
for name in names:
    compile((root/name).read_bytes(),str(root/name),'exec')
commands=[['-m','ruff','check',*names],['-m','ruff','format','--check',*[n for n in names if n!='scripts/eval_robocasa_18task_queue.py']],
          ['-m','ruff','format','--check','--range','92-133','scripts/eval_robocasa_18task_queue.py']]
checks=[]
for i,arguments in enumerate(commands):
    command=[sys.executable,*arguments]
    result=subprocess.run(command,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/f'check_{i}.log').write_text(result.stdout)
    checks.append({'argv':command,'exit':result.returncode,'log':f'check_{i}.log'})
    assert result.returncode==0,result.stdout
for repo,label in ((root,'root'),(child,'child')):
    result=subprocess.run(['git','-C',str(repo),'diff','--check'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/f'{label}_diff_check.log').write_text(result.stdout)
    checks.append({'argv':['git','-C',str(repo),'diff','--check'],'exit':result.returncode})
    assert result.returncode==0
    (out/f'{label}.diff').write_text(git(repo,'diff',root_base if label=='root' else child_base))
value={'status':'PASS','syntax_files':len(names),'changed_paths':names,'checks':checks,
       'protected_root_blobs':{n:git(root,'hash-object',n) for n in protected_root},
       'verify_source_AST_unchanged':True,'Store_safe_mkdir_publish_small_JSON_F5_writer_AST_unchanged':True,
       'legacy_queue_format_scope':'changed validation function range only; pre-existing unrelated formatting preserved',
       'root':git(root,'rev-parse','HEAD'),'child':git(child,'rev-parse','HEAD'),
       'source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}}
(out/'static.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:value[k] for k in ('status','syntax_files','root','child')}))
