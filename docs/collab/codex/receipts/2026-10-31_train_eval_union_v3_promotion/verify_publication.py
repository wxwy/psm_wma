"""Read canonical Git refs/source/archived evidence; no project tests/runtime."""
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

R = Path('/workspace/psm-wma-train-eval-promotion')
C = R / 'cosmos-framework'
PROMOTED = 'e1ec802ceff91661559e9086452700488c5db035'
FORMAL = '4139ad245b73cc1c16c9d4954241cecb81478992'
CHILD = '6c83596d6a259e89c4cd3e79424024983426ac3d'
BASE = 'b0c56553afcdd0cec99cdbae6bdef1043bb9c0bd'
CANDIDATE = '6bfb05f8a916aad51e619c557231463ed6e3f1ce'
PREFIX = 'docs/collab/codex/evidence/2026-10-31_eval_v2_current_v3_composition/'
INBOX = 'docs/collab/chatgpt/CODEX_INBOX.md'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], timeout=55)


def text(repo, *args):
    return git(repo, *args).decode().strip()


def tree(repo, sha):
    return {row.split(b'\t', 1)[1].decode(): row.split(b'\t', 1)[0].decode()
            for row in git(repo, 'ls-tree', '-rz', sha).split(b'\0') if row}


git(R, 'fetch', 'origin', 'refs/heads/V3:refs/remotes/origin/V3')
git(C, 'fetch', 'origin', 'refs/heads/v3-local-ttt:refs/remotes/origin/v3-local-ttt')
advertised = text(R, 'ls-remote', 'origin', 'refs/heads/V3').split()[0]
child_advertised = text(C, 'ls-remote', 'origin', 'refs/heads/v3-local-ttt').split()[0]
assert advertised == text(R, 'rev-parse', 'origin/V3') == PROMOTED
assert child_advertised == text(C, 'rev-parse', 'origin/v3-local-ttt') == text(C, 'rev-parse', 'HEAD') == CHILD
assert text(R, 'rev-parse', 'origin/V3:cosmos-framework') == CHILD
for ancestor in (BASE, CANDIDATE):
    git(R, 'merge-base', '--is-ancestor', ancestor, PROMOTED)
parents = text(C, 'show', '-s', '--format=%P', CHILD).split()
assert parents == ['baf1b5bf46853e9849a91518803b9738fc216235', '2f7334c4ada6ace1d21185985aae90539052bf18']
approved, published = tree(R, FORMAL), tree(R, 'origin/V3')
source = lambda m: {k: v for k, v in m.items() if k not in ('SESSION.md', 'TODO.md') and not k.startswith('docs/')}
assert source(approved) == source(published)
docs_counts = []
for ancestor in (BASE, CANDIDATE):
    old = {k: v for k, v in tree(R, ancestor).items() if k.startswith('docs/') and k != INBOX}
    assert all(published[k] == value for k, value in old.items())
    docs_counts.append(len(old))
read = lambda name: git(R, 'show', 'origin/V3:' + name)
inbox = read(INBOX)
assert inbox.startswith(git(R, 'show', BASE + ':' + INBOX)) and len(inbox) <= 131072
manifest = json.loads(read(PREFIX + 'artifact_sha256.json'))
for name, item in manifest.items():
    body = read(PREFIX + name)
    assert len(body) == item['bytes'] and hashlib.sha256(body).hexdigest() == item['sha256']
assert not text(R, 'status', '--porcelain=v1') and not text(C, 'status', '--porcelain=v1')
receipt = dict(status='PASS_UNIFIED_V3_CANONICAL_READBACK',
               observed_cst=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
               approved_formal_root=FORMAL, promotion_root=PROMOTED, root_V3_advertised=advertised,
               child_v3_local_ttt_advertised=child_advertised, root_gitlink=CHILD, child_parents=parents,
               all_source_equal_approved=True, root_source_objects=len(source(approved)),
               child_objects=len(tree(C, CHILD)), canonical_docs_preserved=docs_counts[0],
               candidate_docs_preserved=docs_counts[1], inbox_prefix_preserved=True, inbox_bytes=len(inbox),
               artifact_sha256_verified=len(manifest), original_tests_rerun=False,
               GPU_OS_training_or_simulation_started=False, original_job_config_checkpoint_touched=False,
               normal_nonforce_child_first_root_second=True, both_histories_preserved=True,
               root_child_worktrees_clean=True)
Path('/tmp/psm-train-eval-promotion-20261031/publication_readback.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
