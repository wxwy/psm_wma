"""Canonical Git ref and immutable source/evidence check; no runtime access."""
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

R = Path('/workspace/psm-wma-nottt-boundary-promotion')
C = R / 'cosmos-framework'
PROMOTED = '437fdd04aef3e18f25b06f508e11024ef72b9a5a'
FORMAL = '3cf7453777a693ac029a79ed8b19afc55df0d4fa'
CHILD = '6c83596d6a259e89c4cd3e79424024983426ac3d'
BASE = '2667393e501a1ff7429bdff004e4806d45724e3f'
CANDIDATE = '22ca7cc387dc41e001408026d42fe1fea799f922'
PREFIX = 'docs/collab/codex/evidence/2026-10-31_nottt_console_start_boundary_author_cpu/'
INBOX = 'docs/collab/chatgpt/CODEX_INBOX.md'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], timeout=55)


def text(repo, *args):
    return git(repo, *args).decode().strip()


def tree(sha):
    return {row.split(b'\t', 1)[1].decode(): row.split(b'\t', 1)[0].decode()
            for row in git(R, 'ls-tree', '-rz', sha).split(b'\0') if row}


git(R, 'fetch', 'origin', 'refs/heads/V3:refs/remotes/origin/V3')
advertised = text(R, 'ls-remote', 'origin', 'refs/heads/V3').split()[0]
child_advertised = text(C, 'ls-remote', 'origin', 'refs/heads/v3-local-ttt').split()[0]
assert advertised == text(R, 'rev-parse', 'origin/V3') == PROMOTED
assert child_advertised == text(C, 'rev-parse', 'HEAD') == text(R, 'rev-parse', 'origin/V3:cosmos-framework') == CHILD
for ancestor in (BASE, CANDIDATE):
    git(R, 'merge-base', '--is-ancestor', ancestor, PROMOTED)
approved, published = tree(FORMAL), tree('origin/V3')
source = lambda m: {k: v for k, v in m.items() if k not in ('SESSION.md', 'TODO.md') and not k.startswith('docs/')}
assert source(approved) == source(published)
doc_counts = []
for ancestor in (BASE, CANDIDATE):
    old = {k: v for k, v in tree(ancestor).items() if k.startswith('docs/') and k != INBOX}
    assert all(published[k] == v for k, v in old.items())
    doc_counts.append(len(old))
read = lambda p: git(R, 'show', 'origin/V3:' + p)
inbox = read(INBOX)
assert inbox.startswith(git(R, 'show', BASE + ':' + INBOX)) and len(inbox) <= 131072
manifest = json.loads(read(PREFIX + 'artifact_manifest.json'))
for name, item in manifest['files'].items():
    data = read(PREFIX + name)
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
bindings = json.loads(read(PREFIX + 'formal_source_bindings.json'))['files']
for row in bindings:
    repo = R if row['repository'] == 'root' else C
    assert text(repo, 'rev-parse', row['commit'] + ':' + row['path']) == row['blob']
    assert hashlib.sha256(git(repo, 'cat-file', 'blob', row['blob'])).hexdigest() == row['sha256']
assert not text(R, 'status', '--porcelain=v1') and not text(C, 'status', '--porcelain=v1')
receipt = dict(status='PASS_CANONICAL_BOUNDARY_PROMOTION_READBACK',
               observed_cst=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
               code_review_formal_root=FORMAL, promotion_root=PROMOTED, V3_advertised=advertised,
               unchanged_child_official_head=child_advertised, root_gitlink=CHILD,
               all_source_equal_approved=True, root_source_object_count=len(source(approved)),
               canonical_docs_preserved=doc_counts[0], candidate_docs_preserved=doc_counts[1],
               canonical_inbox_prefix_preserved=True, inbox_bytes=len(inbox),
               artifact_sha256_verified=len(manifest['files']), source_bindings_verified=len(bindings),
               tests_static_or_GPU_reexecuted=False, training_or_simulation=False,
               active_shared_resume_code_directory_process_job_config_checkpoint_logs_accessed=False,
               code_file_mutations='new isolated cloud worktree only; existing source worktrees unchanged',
               no_force_or_history_loss=True, worktrees_clean=True)
Path('/tmp/psm-nottt-boundary-promotion-20261031/publication_readback.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
