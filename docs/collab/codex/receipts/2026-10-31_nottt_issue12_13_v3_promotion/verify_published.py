"""Read canonical refs/Git objects only; no training environment or tests."""
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

R = Path('/workspace/psm-wma-nottt-promotion')
C = R / 'cosmos-framework'
PROMOTED = '953931b509550b96abbe2708b2ea5f84be150fef'
FORMAL = '57e36decbec0e00ecb94dc1c080fd8976afff25d'
CHILD = 'baf1b5bf46853e9849a91518803b9738fc216235'
BASE = '2ee690b0c3b0a6d9219db12096813ef4eb26de2b'
CANDIDATE = 'cf1065bab335b7f268a183f302bf8b953e3e5e94'
PREFIX = 'docs/collab/codex/evidence/2026-10-31_nottt_issue12_13_composition_author_cpu/'
INBOX = 'docs/collab/chatgpt/CODEX_INBOX.md'


def git(where, *args):
    return subprocess.check_output(['git', '-C', str(where), *args], timeout=55)


def text(where, *args):
    return git(where, *args).decode().strip()


def tree(sha):
    return {r.split(b'\t', 1)[1].decode(): r.split(b'\t', 1)[0].decode()
            for r in git(R, 'ls-tree', '-rz', sha).split(b'\0') if r}


git(C, 'fetch', 'origin', 'refs/heads/v3-local-ttt:refs/remotes/origin/v3-local-ttt')
advertised = text(R, 'ls-remote', 'origin', 'refs/heads/V3').split()[0]
child_advertised = text(C, 'ls-remote', 'origin', 'refs/heads/v3-local-ttt').split()[0]
assert advertised == text(R, 'rev-parse', 'origin/V3') == PROMOTED
assert child_advertised == text(C, 'rev-parse', 'origin/v3-local-ttt') == text(C, 'rev-parse', 'HEAD') == CHILD
assert text(R, 'rev-parse', 'origin/V3:cosmos-framework') == CHILD
git(R, 'merge-base', '--is-ancestor', BASE, PROMOTED)
git(R, 'merge-base', '--is-ancestor', CANDIDATE, PROMOTED)
approved, published = tree(FORMAL), tree('origin/V3')
source = lambda mapping: {k: v for k, v in mapping.items()
                          if k not in ('SESSION.md', 'TODO.md') and not k.startswith('docs/')}
assert source(approved) == source(published)
canonical_docs = {k: v for k, v in tree(BASE).items() if k.startswith('docs/') and k != INBOX}
candidate_docs = {k: v for k, v in tree(CANDIDATE).items() if k.startswith('docs/') and k != INBOX}
assert all(published[k] == v for k, v in canonical_docs.items())
assert all(published[k] == v for k, v in candidate_docs.items())
read = lambda path: git(R, 'show', 'origin/V3:' + path)
inbox = read(INBOX)
assert inbox.startswith(git(R, 'show', BASE + ':' + INBOX)) and len(inbox) <= 131072
manifest = json.loads(read(PREFIX + 'artifact_manifest.json'))
for name, record in manifest['files'].items():
    body = read(PREFIX + name)
    assert len(body) == record['bytes'] and hashlib.sha256(body).hexdigest() == record['sha256']
bindings = json.loads(read(PREFIX + 'formal_source_bindings.json'))['files']
for row in bindings:
    repo = R if row['repository'] == 'root' else C
    assert text(repo, 'rev-parse', row['commit'] + ':' + row['path']) == row['blob']
    assert hashlib.sha256(git(repo, 'cat-file', 'blob', row['blob'])).hexdigest() == row['sha256']
assert not text(R, 'status', '--porcelain=v1') and not text(C, 'status', '--porcelain=v1')
receipt = dict(status='PASS_CANONICAL_V3_PUBLICATION_READBACK',
               observed_cst=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
               code_review_formal_root=FORMAL, promotion_root=PROMOTED,
               canonical_V3_advertised=advertised, child_v3_local_ttt_advertised=child_advertised,
               root_gitlink=CHILD, root_source_objects_equal_approved=len(source(approved)),
               all_source_objects_equal_approved=True, canonical_docs_preserved=len(canonical_docs),
               candidate_docs_preserved=len(candidate_docs), inbox_prefix_preserved=True, inbox_bytes=len(inbox),
               artifact_sha256_verified=len(manifest['files']), formal_source_bindings_verified=len(bindings),
               old_tests_or_gpu_rerun=False, original_job_config_checkpoint_touched=False,
               training_started=False, canonical_and_candidate_histories_preserved=True,
               force_push=False, root_and_child_worktrees_clean=True)
Path('/tmp/psm-nottt-promotion-20261031/publication_readback.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
