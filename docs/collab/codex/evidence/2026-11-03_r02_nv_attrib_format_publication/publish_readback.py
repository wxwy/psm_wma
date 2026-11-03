import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('/workspace/psm-wma-eval-r02-format')
CHILD = ROOT / 'cosmos-framework'
OUT = Path('/tmp/psm-eval-v2-r02-format-20261103')
PUB = OUT / 'publication'
PUB.mkdir(exist_ok=True)
BRANCH = 'v3-eval-v2-r02-format-20261103'
ROOT_HEAD = '8fab3d135b51f1929134578202d5b7b703176972'
FORMAL_ROOT = '46c08127b2a13155bb22204069a1456cb01424d7'
FORMAL_CHILD = '1069fe78841228cadbbfbe6afbd767eaed6225da'
OFFICIAL_ROOT = '324d6983a068424a0c0c60ad6a94e512e39ed96c'
OFFICIAL_CHILD = 'c93f2abf4fb27d36176ff8db094379a853cec796'
EVIDENCE = 'docs/collab/codex/evidence/2026-11-03_r02_nv_attrib_format_author_cpu'


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd)


def txt(*args, cwd=ROOT):
    return git(*args, cwd=cwd).decode().strip()


def command(name, repo, args):
    result = subprocess.run(args, cwd=repo, capture_output=True, text=True)
    p = PUB / (name + '.json')
    assert not p.exists(), p
    p.write_text(json.dumps({'args': args, 'cwd': str(repo),
                             'returncode': result.returncode,
                             'stdout': result.stdout, 'stderr': result.stderr},
                            indent=2) + '\n')
    print(name, 'exit', result.returncode, flush=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


assert txt('rev-parse', 'HEAD') == ROOT_HEAD
assert txt('rev-parse', 'HEAD', cwd=CHILD) == FORMAL_CHILD
assert not txt('status', '--porcelain') and not txt('status', '--porcelain', cwd=CHILD)
command('01_child_push', CHILD, ['git', 'push', '--set-upstream', 'origin', f'HEAD:refs/heads/{BRANCH}'])
command('02_root_push', ROOT, ['git', 'push', '--set-upstream', 'origin', f'HEAD:refs/heads/{BRANCH}'])
command('03_child_fetch', CHILD, ['git', 'fetch', '--no-recurse-submodules', 'origin',
    f'refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}',
    'refs/heads/v3-local-ttt:refs/remotes/origin/v3-local-ttt'])
command('04_root_fetch', ROOT, ['git', 'fetch', '--no-recurse-submodules', 'origin',
    f'refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}',
    'refs/heads/V3:refs/remotes/origin/V3'])
child_ad = command('05_child_advertised', CHILD, ['git', 'ls-remote', 'origin',
    f'refs/heads/{BRANCH}', 'refs/heads/v3-local-ttt'])
root_ad = command('06_root_advertised', ROOT, ['git', 'ls-remote', 'origin',
    f'refs/heads/{BRANCH}', 'refs/heads/V3'])
root_refs = {row.split()[1]: row.split()[0] for row in root_ad.splitlines()}
child_refs = {row.split()[1]: row.split()[0] for row in child_ad.splitlines()}
assert root_refs == {f'refs/heads/{BRANCH}': ROOT_HEAD, 'refs/heads/V3': OFFICIAL_ROOT}, root_refs
assert child_refs == {f'refs/heads/{BRANCH}': FORMAL_CHILD, 'refs/heads/v3-local-ttt': OFFICIAL_CHILD}, child_refs
assert txt('rev-parse', f'origin/{BRANCH}') == ROOT_HEAD
assert txt('rev-parse', f'origin/{BRANCH}', cwd=CHILD) == FORMAL_CHILD
assert txt('rev-parse', ROOT_HEAD + ':cosmos-framework') == FORMAL_CHILD
assert txt('rev-parse', FORMAL_ROOT + ':cosmos-framework') == FORMAL_CHILD

def remote_file(path):
    return git('show', f'{ROOT_HEAD}:{path}')

artifact_manifest = json.loads(remote_file(EVIDENCE + '/artifact_manifest.json'))
assert artifact_manifest['formal_root'] == FORMAL_ROOT
assert artifact_manifest['formal_child_gitlink'] == FORMAL_CHILD
for path, sha in artifact_manifest['sha256'].items():
    assert hashlib.sha256(remote_file(EVIDENCE + '/' + path)).hexdigest() == sha, path
bindings = json.loads(remote_file(EVIDENCE + '/static/source_bindings.json'))
for binding in bindings:
    repo = ROOT if binding['repository'] == 'root' else CHILD
    spec = binding['commit'] + ':' + binding['path']
    assert txt('rev-parse', spec, cwd=repo) == binding['git_blob']
    assert hashlib.sha256(git('show', spec, cwd=repo)).hexdigest() == binding['sha256']
changes = txt('diff', '--name-only', FORMAL_ROOT, ROOT_HEAD).splitlines()
assert all(p in ['SESSION.md', 'TODO.md'] or p.startswith('docs/') for p in changes)
inbox = remote_file('docs/collab/chatgpt/CODEX_INBOX.md')
original_inbox = git('show', FORMAL_ROOT + ':docs/collab/chatgpt/CODEX_INBOX.md')
assert inbox.startswith(original_inbox) and len(inbox) <= 131072
assert inbox.count(b'Codex R02 NVIDIA attribute format-only 46c08127/1069fe78 incremental Code review request') == 1
assert not txt('status', '--porcelain') and not txt('status', '--porcelain', cwd=CHILD)
receipt = {
    'status': 'REMOTE_READBACK_PASS', 'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'branch': BRANCH, 'formal_root': FORMAL_ROOT, 'formal_child_gitlink': FORMAL_CHILD,
    'published_root_evidence_head': ROOT_HEAD, 'published_child_head': FORMAL_CHILD,
    'root_and_child_advertised_refs': {'root': root_refs, 'child': child_refs},
    'artifact_sha256_matches': len(artifact_manifest['sha256']),
    'source_blob_sha256_matches': len(bindings), 'root_gitlink_matches_child': True,
    'evidence_successor_metadata_only': True, 'inbox_append_only_unique_bounded': True,
    'worktrees_clean': True, 'official_refs_unchanged': True,
    'review_request_published': True, 'not_reviewer_approval': True,
    'gpu_or_v3_promotion_executed': False,
}
(PUB / 'readback.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps(receipt, indent=2), flush=True)
