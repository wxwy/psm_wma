"""Read Git objects and frozen evidence only; no project code or tests execute."""
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

R = Path('/workspace/psm-wma-nottt-promotion')
C = R / 'cosmos-framework'
BASE = '2ee690b0c3b0a6d9219db12096813ef4eb26de2b'
COMMON = 'b260290ef09ef25a8a41259aef153df5efff3369'
CANDIDATE = 'cf1065bab335b7f268a183f302bf8b953e3e5e94'
FORMAL = '57e36decbec0e00ecb94dc1c080fd8976afff25d'
CHILD = 'baf1b5bf46853e9849a91518803b9738fc216235'
REVIEW = 'docs/collab/chatgpt/reviews/2026-10-31_V3_NoTTT_Issue12_13_Integrated_57e36dec_baf1b5bf_Composition_Incremental_Code_Gate_APPROVE_CODE.md'
PREFIX = 'docs/collab/codex/evidence/2026-10-31_nottt_issue12_13_composition_author_cpu/'
INBOX = 'docs/collab/chatgpt/CODEX_INBOX.md'


def git(where, *args):
    return subprocess.check_output(['git', '-C', str(where), *args])


def text(where, *args):
    return git(where, *args).decode().strip()


def tree(sha):
    return {line.split(b'\t', 1)[1].decode(): line.split(b'\t', 1)[0].decode()
            for line in git(R, 'ls-tree', '-r', '-z', sha).split(b'\0') if line}


def bookkeeping(name):
    return name in ('SESSION.md', 'TODO.md') or name.startswith('docs/')


assert not text(R, 'diff', '--name-only', '--diff-filter=U')
assert not text(R, 'diff', '--name-only'), 'stage metadata before freezing audit'
assert text(C, 'rev-parse', 'HEAD') == CHILD
assert not text(C, 'status', '--porcelain=v1')
index_tree = text(R, 'write-tree')
approved, prepared, canonical, candidate = (tree(s) for s in (FORMAL, index_tree, BASE, CANDIDATE))
approved_source = {k: v for k, v in approved.items() if not bookkeeping(k)}
prepared_source = {k: v for k, v in prepared.items() if not bookkeeping(k)}
assert approved_source == prepared_source, 'a source object differs from approved composition'
assert prepared['cosmos-framework'] == '160000 commit ' + CHILD
kept_canonical = [k for k in canonical if k.startswith('docs/') and k != INBOX]
kept_candidate = [k for k in candidate if k.startswith('docs/') and k != INBOX]
assert all(prepared[k] == canonical[k] for k in kept_canonical)
assert all(prepared[k] == candidate[k] for k in kept_candidate)
read = lambda path: git(R, 'show', index_tree + ':' + path)
inbox = read(INBOX)
old = git(R, 'show', BASE + ':' + INBOX)
common = git(R, 'show', COMMON + ':' + INBOX)
tail = git(R, 'show', CANDIDATE + ':' + INBOX)[len(common):]
assert inbox.startswith(old) and inbox.count(tail) == 1 and len(inbox) <= 131072
assert read(REVIEW) == git(R, 'show', BASE + ':' + REVIEW)
review = read(REVIEW).decode()
assert FORMAL in review and CHILD in review and '**正式技术结论：`APPROVE_CODE`' in review
manifest = json.loads(read(PREFIX + 'artifact_manifest.json'))
for name, item in manifest['files'].items():
    payload = read(PREFIX + name)
    assert len(payload) == item['bytes'] and hashlib.sha256(payload).hexdigest() == item['sha256'], name
totals = {k: sum(int(s.get(k, '0')) for s in ET.fromstring(read(PREFIX + 'junit.xml')).iter('testsuite'))
          for k in ('tests', 'failures', 'errors', 'skipped')}
assert totals == dict(tests=6, failures=0, errors=0, skipped=0)
bindings = json.loads(read(PREFIX + 'formal_source_bindings.json'))['files']
for row in bindings:
    where = R if row['repository'] == 'root' else C
    object_id = text(where, 'rev-parse', row['commit'] + ':' + row['path'])
    assert object_id == row['blob']
    assert hashlib.sha256(git(where, 'cat-file', 'blob', object_id)).hexdigest() == row['sha256']
protected = {}
for name in ('cosmos_framework/evaluation', 'cosmos_framework/inference', 'cosmos_framework/simulation',
             'cosmos_framework/model', 'cosmos_framework/checkpoint', 'cosmos_framework/configs'):
    observed = text(C, 'rev-parse', CHILD + ':' + name)
    assert observed == text(C, 'rev-parse', '0ae313e329d290fc6b8a50fda1112820fb7ac485:' + name)
    protected[name] = observed
delta = sorted(k for k in canonical.keys() | prepared.keys() if canonical.get(k) != prepared.get(k))
production_delta = [k for k in delta if not bookkeeping(k) and not k.startswith('tools/')]
assert set(production_delta) == {'cosmos-framework', 'scripts/no_ttt_console.py',
                               'scripts/train_v3_matched_no_ttt.sh', 'scripts/train_v3_matched_no_ttt_4gpu.sh'}
result = dict(status='PASS_GIT_ONLY_PROMOTION_AUDIT', canonical_base=BASE, approved_formal_root=FORMAL,
              candidate_head=CANDIDATE, child_gitlink=CHILD, prepared_tree_snapshot=index_tree,
              source_objects_equal_approved=len(approved_source), all_root_source_objects_equal_approved=True,
              child_whole_commit_unchanged=True, protected_child_trees=protected,
              canonical_docs_preserved=len(kept_canonical), candidate_docs_preserved=len(kept_candidate),
              inbox_canonical_prefix_preserved=True, candidate_suffix_preserved_once=True, inbox_bytes=len(inbox),
              artifact_sha256_verified=len(manifest['files']), formal_source_bindings_verified=len(bindings),
              original_junit_totals_read_only=totals, tests_reexecuted=False, gpu_experiments=False,
              runtime_job_checkpoint_config_accessed=False, production_delta_from_canonical=production_delta,
              review_path=REVIEW, review_blob=prepared[REVIEW], canonical_diff_paths=delta)
Path('/tmp/psm-nottt-promotion-20261031/source_audit.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('canonical_diff_paths', 'protected_child_trees')}, indent=2))
