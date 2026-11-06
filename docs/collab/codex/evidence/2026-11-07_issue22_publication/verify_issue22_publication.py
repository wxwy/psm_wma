"""Compare published Git/API objects; no model, simulation or test execution."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import tarfile
import xml.etree.ElementTree as ET

root=Path('/workspace/work/psm-wma-local-ttt-pipeline-issue22')
child=root/'cosmos-framework'
base=Path('/workspace/work/issue22-pipeline-evidence')
candidate='5fe2b8def58f4caae8c63581ed3649ac8fb3e0c6'
book='39ba3eb4bf49dbbbe77d4e1bc85407c369820746'
context='631a36225f4d4d93ffe30076ea95a2f890085363'
old_child='1ca308055fc41fb69efaeb9efaa23808f164a18e'
branch='v3-local-ttt-pipeline-issue22-20261107'
prefix='artifacts/local_ttt_pipeline/2026-11-07_issue22_cpu/'

def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()

def blob(repo,ref,path):
    return subprocess.check_output(['git','-C',str(repo),'show',ref+':'+path])

assert git(root,'rev-parse','origin/'+branch)==book
assert git(child,'rev-parse','origin/'+branch)==candidate
assert not git(child,'status','--porcelain') and git(root,'status','--porcelain')=='M cosmos-framework'
assert git(root,'rev-parse',book+':cosmos-framework')==old_child
api=json.loads((base/'publication_api_snapshot.json').read_text())
pr=json.loads((base/'publication_pr_readback.json').read_text())
assert pr['draft'] is True and pr['merged'] is False and pr['state']=='open'
assert pr['head_sha']==candidate and pr['base_sha']==old_child
assert pr['base']=='v3-local-ttt' and pr['head']==branch
assert pr['changed_files']==20 and pr['commits']==1
for item in api['api_readback']:
    directory,ref=(child,candidate) if item['path'].startswith('cosmos_framework/') else (root,book)
    assert git(directory,'rev-parse',ref+':'+item['path'])==item['git_blob']
manifest=json.loads(blob(root,book,prefix+'files_manifest.json'))
for item in manifest:
    data=blob(root,book,prefix+item['path'])
    assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
assert len(manifest)==34
summary=json.loads(blob(root,book,prefix+'final_summary.json'))
assert summary['candidate_child']==candidate and summary['tests']==428
assert summary['new_tests']==155 and summary['prior_tests']==273
assert summary['root_gitlink_unchanged']==old_child and summary['matching_new_root_child_pair'] is False
assert summary['source_unchanged'] and summary['source_fingerprint_entries']==1273
cases=ET.fromstring(blob(root,book,prefix+'author-final/junit.xml'))
assert len(list(cases.iter('testcase')))==428
assert not any(list(cases.iter(tag)) for tag in ('failure','error','skipped'))
inbox='docs/collab/chatgpt/CODEX_INBOX.md'
before=blob(root,context,inbox); after=blob(root,book,inbox)
assert after.startswith(before) and len(after)<=131072
assert after[len(before):].count(candidate.encode())==1
assert all(path in ('SESSION.md','TODO.md') or path.startswith(('docs/','artifacts/')) for path in git(root,'diff','--name-only',context,book).splitlines())
archive_manifest=json.loads(blob(root,book,prefix+'archive_manifest.json'))
assert hashlib.sha256(blob(root,book,prefix+'cpu_evidence.tar.gz')).hexdigest()==archive_manifest['sha256']
with tarfile.open(root/prefix/'cpu_evidence.tar.gz') as tar:
    old=json.load(tar.extractfile('cpu_evidence/author-final/source_before.json'))
    new=json.load(tar.extractfile('cpu_evidence/author-final/source_after.json'))
    assert old==new and old['child']==candidate and old['root']==context
    assert old['child_status']=='' and old['root_status']=='M cosmos-framework'
    for path,digest in old['sha256'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
official_root=git(root,'ls-remote','origin','refs/heads/V3').split()[0]
official_child=git(child,'ls-remote','origin','refs/heads/v3-local-ttt').split()[0]
assert official_root=='2ff873bde87465a2cc8815eb801d69692f54a396' and official_child==old_child
receipt=dict(status='PUBLICATION_READBACK_PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    candidate_child=candidate,child_parent=old_child,root_evidence_commit=book,root_cpu_context=context,
    root_gitlink_unchanged=old_child,matching_integrated_pair=False,
    official_V3=official_root,official_child_v3_local_ttt=official_child,
    draft_pr=dict(url=pr['url'],number=pr['number'],draft=True,merged=False,head_sha=candidate,base_sha=old_child),
    artifacts_sha256_verified=34,api_blobs_verified=api['api_readback'],source_fingerprint_entries_verified=1273,
    junit=dict(tests=428,failures=0,errors=0,skipped=0),archive=archive_manifest,
    inbox=dict(prefix_preserved=True,before_bytes=len(before),after_bytes=len(after)),
    source_tests_after_frozen_child='UNCHANGED',independent_GPT_Code_Gate='PENDING',real_hardware_performance='OPEN_NOT_RUN')
out=root/'docs/collab/codex/evidence/2026-11-07_issue22_publication'
out.mkdir(parents=True,exist_ok=False)
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='api_blobs_verified'},indent=2))
