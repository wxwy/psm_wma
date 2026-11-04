import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path('/workspace/psm-wma-g2-rgbd-stage1')
CHILD=ROOT/'cosmos-framework'
BASE=Path('/tmp/psm-g2-rgbd-stage1-20261104')
OUT=BASE/'publication';OUT.mkdir()
BRANCH='v3-g2-rgbd-pose-stage1-20261104'
HEAD='e8a5f92d77e630f42756a75991bd3d6b443dcff6'
FORMAL='b67bc4ca9a2afb1ff26fac0846f8ee7042a589ab'
CHILD_SHA='1069fe78841228cadbbfbe6afbd767eaed6225da'
V3='083b36ac27ad43b6f5127d9a58aed4fac02eaaa7'
EVIDENCE='docs/collab/codex/evidence/2026-11-04_g2_rgbd_stage1_author_gate_a'
def git(*args,cwd=ROOT): return subprocess.check_output(['git',*args],cwd=cwd)
def txt(*args,cwd=ROOT): return git(*args,cwd=cwd).decode().strip()
def run(name,repo,args):
    p=subprocess.run(args,cwd=repo,capture_output=True,text=True)
    (OUT/(name+'.json')).write_text(json.dumps({'args':args,'cwd':str(repo),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n')
    print(name,'exit',p.returncode,flush=True)
    assert p.returncode==0,p.stdout+p.stderr
    return p.stdout
assert txt('rev-parse','HEAD')==HEAD
assert not txt('status','--porcelain') and not txt('status','--porcelain',cwd=CHILD)
run('01_root_push',ROOT,['git','push','--set-upstream','origin',f'HEAD:refs/heads/{BRANCH}'])
run('02_root_fetch',ROOT,['git','fetch','--no-recurse-submodules','origin',f'refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}','refs/heads/V3:refs/remotes/origin/V3'])
run('03_child_fetch',CHILD,['git','fetch','--no-recurse-submodules','origin','refs/heads/v3-local-ttt:refs/remotes/origin/v3-local-ttt'])
r=run('04_root_advertised',ROOT,['git','ls-remote','origin',f'refs/heads/{BRANCH}','refs/heads/V3'])
c=run('05_child_advertised',CHILD,['git','ls-remote','origin','refs/heads/v3-local-ttt'])
refs={line.split()[1]:line.split()[0] for line in r.splitlines()}
assert refs=={f'refs/heads/{BRANCH}':HEAD,'refs/heads/V3':V3}
assert c.split()[0]==CHILD_SHA and txt('rev-parse','origin/v3-local-ttt',cwd=CHILD)==CHILD_SHA
assert txt('rev-parse',f'origin/{BRANCH}')==HEAD
assert txt('rev-parse',HEAD+':cosmos-framework')==txt('rev-parse',FORMAL+':cosmos-framework')==CHILD_SHA
def file(path): return git('show',HEAD+':'+path)
manifest=json.loads(file(EVIDENCE+'/artifact_manifest.json'))
assert manifest['formal_root']==FORMAL and manifest['child_gitlink']==CHILD_SHA
for path,sha in manifest['sha256'].items():
    assert hashlib.sha256(file(EVIDENCE+'/'+path)).hexdigest()==sha,path
bindings=json.loads(file(EVIDENCE+'/source_bindings.json'))
for record in bindings:
    spec=FORMAL+':'+record['path']
    assert txt('rev-parse',spec)==record['git_blob']
    assert hashlib.sha256(git('show',spec)).hexdigest()==record['sha256']
changed=txt('diff','--name-only',FORMAL,HEAD).splitlines()
assert all(p in ['SESSION.md','TODO.md'] or p.startswith('docs/') for p in changed)
inbox=file('docs/collab/chatgpt/CODEX_INBOX.md')
assert inbox.startswith(git('show',FORMAL+':docs/collab/chatgpt/CODEX_INBOX.md'))
assert len(inbox)<=131072 and inbox.count(b'Codex G2 Stage-1 RGB-D/Pose b67bc4ca/1069fe78 fresh Code Gate request')==1
assert not txt('status','--porcelain') and not txt('status','--porcelain',cwd=CHILD)
record={'status':'REMOTE_READBACK_PASS','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'branch':BRANCH,'formal_root':FORMAL,'child_gitlink':CHILD_SHA,'published_evidence_head':HEAD,
    'artifact_sha256_matches':len(manifest['sha256']),'source_blob_sha256_matches':len(bindings),
    'official_v3_unchanged':V3,'official_child_unchanged':CHILD_SHA,'child_push_performed':False,
    'metadata_successor_only':True,'clean_worktrees':True,'unique_bounded_append_only_request':True,
    'request_remote_published':True,'not_reviewer_ack_or_approval':True,
    'server_fetch_or_tests_executed':False,'server_files_transferred':False}
(OUT/'readback.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
