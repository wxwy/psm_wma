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
formal='2d1ad80f89ab4cc0e275ff4341f064954870abdd'
child_sha='c93f2abf4fb27d36176ff8db094379a853cec796'
branch='v3-eval-v2-media-profile-20261103'
base='docs/collab/codex/evidence/2026-11-03_eval_v2_media_profile_author_cpu'
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
  remote_branch='v3-eval-v2-replan-ack-r01-20261102' if name=='child' else branch
  git(cwd,'fetch','origin',f'refs/heads/{remote_branch}:refs/remotes/origin/{remote_branch}')
  refs={line.split()[1]:line.split()[0] for line in git(cwd,'ls-remote','origin',f'refs/heads/{remote_branch}',f'refs/heads/{official}').splitlines()}
  assert refs['refs/heads/'+remote_branch]==git(cwd,'rev-parse','refs/remotes/origin/'+remote_branch)==head
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
 bindings=json.loads(git(root,'show',expected+':'+base+'/static/source_bindings.json',raw=True))
 for path,proof in bindings.items():
  cwd,sha,p=(child,child_sha,path.removeprefix('cosmos-framework/')) if path.startswith('cosmos-framework/') else (root,expected,path)
  body=git(cwd,'show',sha+':'+p,raw=True)
  assert hashlib.sha256(body).hexdigest()==proof['sha256']
  assert git(cwd,'rev-parse',sha+':'+p)==proof['git_blob']
 state['source_bindings_verified']=len(bindings)
 gate=json.loads(git(root,'show',expected+':'+base+'/gate.json',raw=True))
 assert (gate['root'],gate['child'],gate['gitlink'])==(formal,child_sha,child_sha)
 assert gate['tests']==42 and gate['failures']==gate['errors']==gate['skipped']==0
 metadata=git(root,'diff','--name-only',formal,expected).splitlines()
 assert all(p in ['SESSION.md','TODO.md','docs/collab/chatgpt/CODEX_INBOX.md'] or p.startswith('docs/collab/codex/') for p in metadata),metadata
 state['successors_metadata_only']=True
 assert not git(child,'diff','--name-only','c93f2abf4fb27d36176ff8db094379a853cec796',child_sha)
 changed=git(root,'diff','--name-only','b19b9edf7f39a83013a853f95c543081e0216b28',expected).splitlines()
 assert [p for p in changed if p.startswith('scripts/')]==['scripts/robocasa_eval_v2/generated_media.py']
 state['single_Root_production_file_verified']=True
 for path in ['docs/collab/codex/evidence/2026-11-02_eval_v2_replan_all_author_cpu','docs/collab/codex/evidence/2026-11-02_eval_v2_rm_all_r01_author_cpu']:
  assert git(root,'ls-tree','b19b9edf7f39a83013a853f95c543081e0216b28','--',path)==git(root,'ls-tree',expected,'--',path)
 state['old_379_122_evidence_unchanged']=True
 offline=json.loads(git(root,'show',expected+':'+base+'/offline_reconciliation.json',raw=True))
 assert offline['status']=='PENDING_DS_ISOLATED_COPY_RECONCILIATION' and not offline['actual_R01_outputs_accessed']
 state['actual_19_offline_reconciliation']='PENDING_DS'
 live=git(root,'show',expected+':docs/collab/chatgpt/CODEX_INBOX.md',raw=True)
 assert len(live)<=131072
 assert live.count(b'Codex R01-MEDIA-PROFILE-01 2d1ad80f/c93f2abf incremental Code review request')==1
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
