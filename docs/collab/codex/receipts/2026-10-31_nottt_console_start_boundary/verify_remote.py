"""Read published isolated candidate refs and artifacts; no runtime/tests."""
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

R = Path('/workspace/psm-wma-nottt-boundary')
C = R / 'cosmos-framework'
BRANCH = 'v3-nottt-console-start-boundary-20261031'
FORMAL = '3cf7453777a693ac029a79ed8b19afc55df0d4fa'
CHILD = '6c83596d6a259e89c4cd3e79424024983426ac3d'
DOCS = '9022cbc44848e153a17211165367460da8d6e6cc'
BASE = 'cee6f53eef345579c3db1124148f350fd2edc618'
PREFIX = 'docs/collab/codex/evidence/2026-10-31_nottt_console_start_boundary_author_cpu/'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], timeout=55)


def text(repo, *args):
    return git(repo, *args).decode().strip()


git(R, 'fetch', 'origin', f'refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}')
advertised = text(R, 'ls-remote', 'origin', f'refs/heads/{BRANCH}').split()[0]
ref = f'origin/{BRANCH}'
assert advertised == text(R, 'rev-parse', ref) == DOCS
assert text(R, 'rev-parse', ref + ':cosmos-framework') == text(C, 'rev-parse', 'HEAD') == CHILD
child_remote = text(C, 'ls-remote', 'origin', 'refs/heads/v3-local-ttt').split()[0]
assert child_remote == CHILD
git(R, 'merge-base', '--is-ancestor', FORMAL, ref)
delta = text(R, 'diff', '--name-only', FORMAL, ref).splitlines()
assert all(p in ('SESSION.md', 'TODO.md', 'docs/collab/chatgpt/CODEX_INBOX.md') or p.startswith('docs/collab/codex/') for p in delta)
read = lambda p: git(R, 'show', ref + ':' + p)
gate = json.loads(read(PREFIX + 'gate.json'))
assert gate['status'] == 'PASS' and gate['totals'] == dict(tests=46, failures=0, errors=0, skipped=0)
assert gate['identities'] == dict(root=FORMAL, child=CHILD, gitlink=CHILD)
manifest = json.loads(read(PREFIX + 'artifact_manifest.json'))
for name, item in manifest['files'].items():
    body = read(PREFIX + name)
    assert len(body) == item['bytes'] and hashlib.sha256(body).hexdigest() == item['sha256']
bindings = json.loads(read(PREFIX + 'formal_source_bindings.json'))['files']
for row in bindings:
    repo = R if row['repository'] == 'root' else C
    assert text(repo, 'rev-parse', row['commit'] + ':' + row['path']) == row['blob']
    assert hashlib.sha256(git(repo, 'cat-file', 'blob', row['blob'])).hexdigest() == row['sha256']
inbox = read('docs/collab/chatgpt/CODEX_INBOX.md')
assert inbox.startswith(git(R, 'show', BASE + ':docs/collab/chatgpt/CODEX_INBOX.md')) and len(inbox) <= 131072
canonical = text(R, 'ls-remote', 'origin', 'refs/heads/V3').split()[0]
assert canonical == BASE
assert not text(R, 'status', '--porcelain=v1') and not text(C, 'status', '--porcelain=v1')
receipt = dict(status='PASS_ISOLATED_CONSOLE_BOUNDARY_READBACK',
               observed_cst=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
               formal_root=FORMAL, unchanged_child_gitlink=CHILD, branch=BRANCH,
               published_evidence_head=advertised, child_canonical_unchanged=child_remote,
               canonical_V3_unchanged=canonical, artifact_sha256_verified=len(manifest['files']),
               source_bindings_verified=len(bindings), inbox_prefix_preserved=True, inbox_bytes=len(inbox),
               author_CPU_cases=46, raw_current_resume_logs_job_DCP_accessed=False,
               real_GPU_training_or_simulation=False, canonical_merge=False,
               review='fresh GPT request published; no new verdict inferred', clean=True)
Path('/tmp/psm-nottt-boundary-20261031/publication_readback.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
