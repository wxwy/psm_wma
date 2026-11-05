"""Read-only Git/API publication verifier; imports no project code."""
from pathlib import Path
import subprocess
import json
import hashlib
import datetime
import tarfile
import xml.etree.ElementTree as ET

root = Path('/workspace/work/psm-wma-action-decode')
child = root / 'cosmos-framework'
formal = 'f4871059cf28a7e2142325738decbf1d53c3148b'
child_sha = 'b3098008375c275a36dd2f50cbaf757bedf493ea'
book = '461bdfeb49e48a242d55c3b1c7f87ccaeee0dc6a'
branch = 'v3-r05-action-decode-compile-20261105'
prefix = 'artifacts/vfm_action_decode/2026-11-05_cpu/'

def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()

def blob(repo, ref, path):
    return subprocess.check_output(['git', '-C', str(repo), 'show', ref+':'+path])

assert git(root, 'rev-parse', 'origin/'+branch) == book
assert git(child, 'rev-parse', 'origin/'+branch) == child_sha
assert git(root, 'rev-parse', formal+':cosmos-framework') == child_sha
assert git(root, 'rev-parse', book+':cosmos-framework') == child_sha
assert not git(root, 'status', '--porcelain') and not git(child, 'status', '--porcelain')
api = json.loads(Path('/workspace/work/action-decode-evidence/github_readback_blobs.json').read_text())
for item in api:
    repo, revision = (child, child_sha) if item['path'].startswith('cosmos_framework/') else (root, book)
    assert git(repo, 'rev-parse', revision+':'+item['path']) == item['git_blob'], item['path']
manifest = json.loads(blob(root, book, prefix+'files_manifest.json'))
for item in manifest:
    data = blob(root, book, prefix+item['path'])
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
summary = json.loads(blob(root, book, prefix+'final_summary.json'))
assert summary['formal_root'] == formal and summary['formal_child_gitlink'] == child_sha
assert summary['tests'] == 77 and summary['new_cases'] == 26
assert summary['source_unchanged'] and summary['source_files'] == 1229
assert summary['failures'] == summary['errors'] == summary['skipped'] == summary['shell_exit'] == 0
assert summary['dynamo_graph_counts'] == [2]*4 and summary['cpu_inductor_graph_counts'] == [3]*2
assert summary['recompile_limit_unchanged'] == 8 and summary['eager_baseline_comparisons'] == 96
junit = ET.fromstring(blob(root, book, prefix+'formal-targeted/junit.xml'))
assert len(list(junit.iter('testcase'))) == 77
assert not any(list(junit.iter(tag)) for tag in ['failure','error','skipped'])
inbox_path = 'docs/collab/chatgpt/CODEX_INBOX.md'
prior = blob(root, formal, inbox_path)
live = blob(root, book, inbox_path)
assert live.startswith(prior) and len(live) <= 131072
assert live[len(prior):].count(formal.encode()) == 1
assert child_sha.encode() in live[len(prior):]
assert all(p in ('SESSION.md','TODO.md') or p.startswith(('docs/','artifacts/')) for p in git(root,'diff','--name-only',formal,book).splitlines())
archive_manifest = json.loads(blob(root,book,prefix+'archive_manifest.json'))
archive_data = blob(root,book,prefix+'cpu_evidence.tar.gz')
assert hashlib.sha256(archive_data).hexdigest() == archive_manifest['sha256']
with tarfile.open(root/prefix/'cpu_evidence.tar.gz') as tar:
    before = json.load(tar.extractfile('cpu_evidence/formal-targeted/source_before.json'))
    after = json.load(tar.extractfile('cpu_evidence/formal-targeted/source_after.json'))
    assert before == after and before['root'] == formal and before['child'] == child_sha
    assert before['root_status'] == before['child_status'] == ''
    for path, digest in before['sha256'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest() == digest, path
    assert all(not member.issym() and 'cache' not in Path(member.name).parts for member in tar.getmembers())
official_root = git(root,'ls-remote','origin','refs/heads/V3').split()[0]
official_child = git(child,'ls-remote','origin','refs/heads/v3-local-ttt').split()[0]
assert official_root == '48ebeee15f7bd9fa634c395a426fadc91d052299'
assert official_child == '1069fe78841228cadbbfbe6afbd767eaed6225da'
receipt = dict(status='PUBLICATION_READBACK_PASS', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    formal_root=formal, formal_child_gitlink=child_sha, evidence_ledger_commit=book, branch=branch,
    official_root_V3=official_root, official_child_v3_local_ttt=official_child,
    api_readback=api, fetched_artifacts_sha256_verified=len(manifest), archive=archive_manifest,
    original_junit=dict(tests=77,failures=0,errors=0,skipped=0), source_fingerprints_verified=1229,
    inbox=dict(prefix_preserved=True,before_bytes=len(prior),after_bytes=len(live),request_unique=True),
    source_and_tests_after_formal='UNCHANGED', GPT_Code_Gate='PENDING', real_gpu='NOT_RUN')
out=root/'docs/collab/codex/evidence/2026-11-05_issue18_decode_publication'
out.mkdir(parents=True,exist_ok=False)
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k != 'api_readback'},indent=2))
