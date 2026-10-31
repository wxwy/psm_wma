"""Read-only static/admission/import checks of the composed candidate."""
import ast,json,os,subprocess,sys
from pathlib import Path
ROOT=Path('/workspace/work/psm-wma-v3-eval-merge')
BASE=Path(__file__).parent
OUT=BASE/'static-and-entries'
OUT.mkdir()
audit=json.loads((BASE/'object_audit.json').read_text())
paths=[p for p in audit['root']['candidate_changed_paths'] if p.endswith('.py') and p.startswith(('scripts/', 'tools/'))]
paths+=['cosmos-framework/'+p for p in audit['child']['candidate_changed_paths'] if p.endswith('.py')]
paths=sorted(set(paths))
assert len(paths)==24
for p in paths: compile((ROOT/p).read_bytes(),str(ROOT/p),'exec')
commands=[([sys.executable,'-m','ruff','check',*paths],'ruff_check.log'),
          ([sys.executable,'-m','ruff','format','--check',*[p for p in paths if p!='scripts/eval_robocasa_18task_queue.py']],'ruff_format.log'),
          ([sys.executable,'-m','ruff','format','--check','--range','92-133','scripts/eval_robocasa_18task_queue.py'],'queue_format_range.log'),
          (['bash','-n','scripts/run_robocasa_eval_v2.sh','scripts/train_v3_matched_no_ttt_4gpu.sh','scripts/train_v3_matched_no_ttt.sh'],'bash_syntax.log'),
          (['git','diff','--check','369f3f4d82b8694b7efee5d5b16589d82aa00547','4139ad245b73cc1c16c9d4954241cecb81478992','--','scripts','tools','configs'],'root_diff_check.log'),
          (['git','-C','cosmos-framework','diff','--check','baf1b5bf46853e9849a91518803b9738fc216235','6c83596d6a259e89c4cd3e79424024983426ac3d'],'child_diff_check.log')]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',LD_LIBRARY_PATH='',
         PYTHONPATH=f'{ROOT}:{ROOT}/scripts:{ROOT}/cosmos-framework',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
         MKL_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHON=sys.executable)
records=[]
for argv,name in commands:
    result=subprocess.run(argv,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (OUT/name).write_text(result.stdout)
    records.append({'argv':argv,'exit':result.returncode,'log':name})
    assert result.returncode==0,result.stdout
code="""
import json
from pathlib import Path
from robocasa_eval_v2 import cli
from robocasa_eval_v2.identity import verify_source
from cosmos_framework.inference import robocasa_session_transactions, robocasa_transaction_mode
from cosmos_framework.trainer import matched_no_ttt, no_ttt_async_loader
root=Path.cwd()
pair=verify_source('4139ad245b73cc1c16c9d4954241cecb81478992')
assert pair==('4139ad245b73cc1c16c9d4954241cecb81478992','6c83596d6a259e89c4cd3e79424024983426ac3d','4139ad245b73cc1c16c9d4954241cecb81478992')
origins={m.__name__:m.__file__ for m in (cli,robocasa_session_transactions,robocasa_transaction_mode,matched_no_ttt,no_ttt_async_loader)}
assert all(Path(v).is_relative_to(root) for v in origins.values())
print(json.dumps({'status':'PASS','pair':pair,'origins':origins},indent=2))
"""
argv=[sys.executable,'-c',code]
r=subprocess.run(argv,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(OUT/'source_guard_import.stdout').write_text(r.stdout)
(OUT/'source_guard_import.stderr').write_text(r.stderr)
assert r.returncode==0,r.stderr
imports=json.loads(r.stdout)
argv=['bash','scripts/run_robocasa_eval_v2.sh','--help']
r=subprocess.run(argv,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(OUT/'eval_launcher_help.log').write_text(r.stdout)
assert r.returncode==0 and '--local-memory-mode {off,required}' in r.stdout,r.stdout
result={'status':'PASS','syntax_files':len(paths),'commands':records,'source_guard_import':imports,
        'launcher_help':{'argv':argv,'exit':0,'mode_option':'--local-memory-mode {off,required}'}}
(OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'PASS','syntax_files':len(paths),'static_commands':len(commands),'source_guard':'PASS','eval_entry_help':'PASS'}))
