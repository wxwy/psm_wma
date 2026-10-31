"""Read Git objects and frozen artifacts only; no project tests or runtime."""
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

R = Path('/workspace/psm-wma-nottt-boundary-promotion')
C = R / 'cosmos-framework'
BASE = '2667393e501a1ff7429bdff004e4806d45724e3f'
COMMON = 'cee6f53eef345579c3db1124148f350fd2edc618'
FORMAL = '3cf7453777a693ac029a79ed8b19afc55df0d4fa'
CANDIDATE = '22ca7cc387dc41e001408026d42fe1fea799f922'
CHILD = '6c83596d6a259e89c4cd3e79424024983426ac3d'
INBOX = 'docs/collab/chatgpt/CODEX_INBOX.md'
REVIEW = 'docs/collab/chatgpt/reviews/2026-10-31_V3_NoTTT_Issue13_StartingTrainingBoundary_3cf74537_6c83596d_Incremental_Code_Gate_APPROVE_CODE.md'
PREFIX = 'docs/collab/codex/evidence/2026-10-31_nottt_console_start_boundary_author_cpu/'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def text(repo, *args):
    return git(repo, *args).decode().strip()


def tree(sha):
    return {row.split(b'\t', 1)[1].decode(): row.split(b'\t', 1)[0].decode()
            for row in git(R, 'ls-tree', '-rz', sha).split(b'\0') if row}


def source(mapping):
    return {k: v for k, v in mapping.items() if k not in ('SESSION.md', 'TODO.md') and not k.startswith('docs/')}


assert not text(R, 'diff', '--name-only', '--diff-filter=U')
assert not text(R, 'diff', '--name-only')
assert text(C, 'rev-parse', 'HEAD') == CHILD and not text(C, 'status', '--porcelain=v1')
prepared_tree = text(R, 'write-tree')
prepared, approved, canonical, candidate = (tree(s) for s in (prepared_tree, FORMAL, BASE, CANDIDATE))
assert source(prepared) == source(approved)
assert prepared['cosmos-framework'] == canonical['cosmos-framework'] == '160000 commit ' + CHILD
prod_delta = sorted(n for n in canonical.keys() | prepared.keys()
                    if canonical.get(n) != prepared.get(n)
                    and n not in ('SESSION.md', 'TODO.md') and not n.startswith(('docs/', 'tools/')))
assert prod_delta == ['scripts/no_ttt_console.py']
launchers = ['scripts/train_v3_matched_no_ttt.sh', 'scripts/train_v3_matched_no_ttt_4gpu.sh']
assert all(prepared[p] == canonical[p] for p in launchers)
canonical_docs = {n: v for n, v in canonical.items() if n.startswith('docs/') and n != INBOX}
candidate_docs = {n: v for n, v in candidate.items() if n.startswith('docs/') and n != INBOX}
assert all(prepared[n] == v for n, v in canonical_docs.items())
assert all(prepared[n] == v for n, v in candidate_docs.items())
read = lambda p: git(R, 'show', prepared_tree + ':' + p)
inbox = read(INBOX)
assert inbox.startswith(git(R, 'show', BASE + ':' + INBOX)) and len(inbox) <= 131072
common_inbox = git(R, 'show', COMMON + ':' + INBOX)
candidate_tail = git(R, 'show', CANDIDATE + ':' + INBOX)[len(common_inbox):]
assert inbox.count(candidate_tail) == 1
assert read(REVIEW) == git(R, 'show', BASE + ':' + REVIEW)
assert FORMAL.encode() in read(REVIEW) and CHILD.encode() in read(REVIEW) and b'APPROVE_CODE' in read(REVIEW)
manifest = json.loads(read(PREFIX + 'artifact_manifest.json'))
for name, item in manifest['files'].items():
    payload = read(PREFIX + name)
    assert len(payload) == item['bytes'] and hashlib.sha256(payload).hexdigest() == item['sha256'], name
bindings = json.loads(read(PREFIX + 'formal_source_bindings.json'))['files']
for row in bindings:
    repo = R if row['repository'] == 'root' else C
    assert text(repo, 'rev-parse', row['commit'] + ':' + row['path']) == row['blob']
    assert hashlib.sha256(git(repo, 'cat-file', 'blob', row['blob'])).hexdigest() == row['sha256']
cases = list(ET.fromstring(read(PREFIX + 'junit.xml')).iter('testcase'))
assert len(cases) == len({(t.get('classname'), t.get('name')) for t in cases}) == 46
assert all(t.find(k) is None for t in cases for k in ('failure', 'error', 'skipped'))
result = dict(status='PASS_READONLY_BOUNDARY_PROMOTION_AUDIT', canonical_base=BASE,
              approved_formal_root=FORMAL, candidate_head=CANDIDATE, unchanged_child_gitlink=CHILD,
              prepared_tree_snapshot=prepared_tree, all_root_source_equal_approved=True,
              root_source_object_count=len(source(approved)), production_delta=prod_delta,
              both_launchers_unchanged=True, whole_child_unchanged=True,
              canonical_docs_preserved=len(canonical_docs), candidate_docs_preserved=len(candidate_docs),
              canonical_inbox_prefix_preserved=True, candidate_tail_preserved_once=True, inbox_bytes=len(inbox),
              artifact_sha256_verified=len(manifest['files']), source_bindings_verified=len(bindings),
              original_junit_cases_read_only=46, tests_reexecuted=False, GPU_training_or_simulation=False,
              current_resume_shared_directory_job_config_checkpoint_logs_accessed=False,
              mutations='new isolated cloud worktree only; remote V3 push pending', review_path=REVIEW,
              review_object=prepared[REVIEW])
Path('/tmp/psm-nottt-boundary-promotion-20261031/source_audit.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
