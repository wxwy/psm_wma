import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

root=Path('/workspace/psm-wma-eval-replan-all')
child=root/'cosmos-framework'
out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
expected=sys.argv[2]
formal='e7ce99d7a0bbb7a81ea7afcee7253548687dc223'
child_sha='c93f2abf4fb27d36176ff8db094379a853cec796'
branch='v3-eval-v2-replan-ack-r01-20261102'
base='docs/collab/codex/evidence/2026-11-02_eval_v2_rm_all_r01_author_cpu'
steps=[]
def git(cwd,*args,raw=False):
 p=subprocess.run(['git',*args],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
 steps.append(dict(cwd=str(cwd),arguments=args,exit_code=p.returncode))
 if p.returncode:
  raise RuntimeError('git '+args[0]+' failed; exit '+str(p.returncode))
 return p.stdout if raw else p.stdout.decode().strip()
state=dict(status='CHECKING',expected_head=expected,formal_root=formal,formal_child=child_sha)
try:
 assert re.fullmatch('[0-9a-f]{40}',expected)
 assert git(root,'rev-parse','HEAD')==expected
 assert not git(root,'status','--porcelain') and not git(child,'status','--porcelain')
 for name,cwd,head,official in [('child',child,child_sha,'v3-local-ttt'),('root',root,expected,'V3')]:
  git(cwd,'fetch','origin',f'refs/heads/{branch}:refs/remotes/origin/{branch}')
  refs={line.split()[1]:line.split()[0] for line in git(cwd,'ls-remote','origin',f'refs/heads/{branch}',f'refs/heads/{official}').splitlines()}
  assert refs['refs/heads/'+branch]==git(cwd,'rev-parse','refs/remotes/origin/'+branch)==head
  state[name+'_advertised']=head
  state['official_'+name]=refs['refs/heads/'+official]
 assert state['official_root']=='7e2be5ca40891915a1e86eea935ed054ec1984dd'
 assert state['official_child']=='8664267704da3206e719f3c7eef2b5ed86e2a417'
 assert git(root,'rev-parse',expected+':cosmos-framework')==child_sha
 assert git(child,'rev-parse','HEAD')==child_sha
 sums=json.loads(git(root,'show',expected+':'+base+'/SHA256SUMS.json',raw=True))
 for path,sha in sums.items():
  body=git(root,'show',expected+':'+base+'/'+path,raw=True)
  assert hashlib.sha256(body).hexdigest()==sha,path
 state['artifact_hashes_verified']=len(sums)
 bindings=json.loads(git(root,'show',expected+':'+base+'/final/static/source_bindings.json',raw=True))
 for path,proof in bindings.items():
  cwd,sha,p=(child,child_sha,path.removeprefix('cosmos-framework/')) if path.startswith('cosmos-framework/') else (root,expected,path)
  body=git(cwd,'show',sha+':'+p,raw=True)
  assert hashlib.sha256(body).hexdigest()==proof['sha256']
  assert git(cwd,'rev-parse',sha+':'+p)==proof['git_blob']
 state['source_bindings_verified']=len(bindings)
 gate=json.loads(git(root,'show',expected+':'+base+'/gate.json',raw=True))
 assert (gate['root'],gate['child'],gate['gitlink'])==(formal,child_sha,child_sha)
 assert gate['tests']==122 and gate['failures']==gate['errors']==gate['skipped']==0
 metadata=git(root,'diff','--name-only',formal,expected).splitlines()
 assert all(p in ['SESSION.md','TODO.md','docs/collab/chatgpt/CODEX_INBOX.md'] or p.startswith('docs/collab/codex/') for p in metadata),metadata
 state['successors_metadata_only']=True
 child_delta=git(child,'diff','--name-only','0dd13d3d952aa7cbab39f966dfab04b23551f0c9',child_sha).splitlines()
 assert child_delta==['cosmos_framework/inference/robocasa_batch_transactions.py']
 state['single_production_file_verified']=True
 old_evidence='docs/collab/codex/evidence/2026-11-02_eval_v2_replan_all_author_cpu'
 assert git(root,'ls-tree','ec8a8bf31d6e4cd2cc1a387b77d8510aef57e06f','--',old_evidence)==git(root,'ls-tree',expected,'--',old_evidence)
 state['old_379_evidence_unchanged']=True
 live=git(root,'show',expected+':docs/collab/chatgpt/CODEX_INBOX.md',raw=True)
 assert len(live)<=131072
 assert live.count(b'Codex RM-ALL-R01 e7ce99d7/c93f2abf incremental Code Gate request')==1
 state['inbox_bytes']=len(live)
 archive='docs/collab/chatgpt/archive/CODEX_INBOX_20261102_REPLAN_ALL_f49d52e.md'
 assert git(root,'rev-parse',expected+':'+archive)=='dd00d0981b57c55fb7ea21aa978ccd92f1603817'
 state['rollover_blob_verified']=True
 assert not git(root,'status','--porcelain') and not git(child,'status','--porcelain')
 state.update(status='PASS_FRESH_ADVERTISED_REFS_AND_GIT_OBJECT_READBACK',root_head=expected,child_head=child_sha,gitlink=child_sha,
              formal_root=formal,formal_child=child_sha,request_unique=True,worktrees_clean=True,official_refs_unchanged=True)
except BaseException as error:
 state.update(status='FAIL',error=repr(error))
 raise
finally:
 state['observed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (out/'readback.json').write_text(json.dumps(state,indent=2)+'\n')
 (out/'commands.json').write_text(json.dumps(steps,indent=2)+'\n')
print(json.dumps(state,indent=2),flush=True)
