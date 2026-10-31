"""Git object/archived-evidence readback only. No project code/tests execute."""
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

R = Path('/workspace/psm-wma-train-eval-promotion')
C = R / 'cosmos-framework'
BASE = 'b0c56553afcdd0cec99cdbae6bdef1043bb9c0bd'
TRAIN_ROOT = '369f3f4d82b8694b7efee5d5b16589d82aa00547'
EVAL_ROOT = 'd18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163'
FORMAL = '4139ad245b73cc1c16c9d4954241cecb81478992'
CANDIDATE = '6bfb05f8a916aad51e619c557231463ed6e3f1ce'
TRAIN = 'baf1b5bf46853e9849a91518803b9738fc216235'
EVAL = '2f7334c4ada6ace1d21185985aae90539052bf18'
CHILD = '6c83596d6a259e89c4cd3e79424024983426ac3d'
INBOX = 'docs/collab/chatgpt/CODEX_INBOX.md'
REVIEW = 'docs/collab/chatgpt/reviews/2026-10-31_V3_EvalV2_NoTTT_TrainEval_4139ad24_6c83596d_Union_Incremental_Code_Gate_APPROVE_CODE.md'
PREFIX = 'docs/collab/codex/evidence/2026-10-31_eval_v2_current_v3_composition/'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def text(repo, *args):
    return git(repo, *args).decode().strip()


def tree(repo, sha):
    return {row.split(b'\t', 1)[1].decode(): row.split(b'\t', 1)[0].decode()
            for row in git(repo, 'ls-tree', '-rz', sha).split(b'\0') if row}


def source(mapping):
    return {k: v for k, v in mapping.items() if k not in ('SESSION.md', 'TODO.md') and not k.startswith('docs/')}


def union(base, left, right, *, gitlink=None):
    result, overlap = {}, []
    for name in base.keys() | left.keys() | right.keys():
        b, l, r = base.get(name), left.get(name), right.get(name)
        if name == 'cosmos-framework' and gitlink:
            value = '160000 commit ' + gitlink
        elif l == r:
            value = l
        elif l == b:
            value = r
        elif r == b:
            value = l
        else:
            overlap.append(name)
            continue
        if value is not None:
            result[name] = value
    assert not overlap, overlap
    return result


assert not text(R, 'diff', '--name-only', '--diff-filter=U')
assert not text(R, 'diff', '--name-only'), 'all intended metadata must be staged'
assert text(C, 'rev-parse', 'HEAD') == CHILD and not text(C, 'status', '--porcelain=v1')
assert text(C, 'show', '-s', '--format=%P', CHILD).split() == [TRAIN, EVAL]
ct, ce, cu = (tree(C, sha) for sha in (TRAIN, EVAL, CHILD))
cb = tree(C, text(C, 'merge-base', TRAIN, EVAL))
assert cu == union(cb, ct, ce)
eval_delta = sorted(n for n in ct.keys() | cu.keys() if ct.get(n) != cu.get(n))
train_delta = sorted(n for n in ce.keys() | cu.keys() if ce.get(n) != cu.get(n))
assert len(eval_delta) == len(train_delta) == 13
assert set(eval_delta).isdisjoint(train_delta)
assert all(cu[n] == ct[n] for n in train_delta)
assert all(cu[n] == ce[n] for n in eval_delta)

prepared_tree = text(R, 'write-tree')
prepared, approved, canonical, candidate = (tree(R, s) for s in (prepared_tree, FORMAL, BASE, CANDIDATE))
assert source(prepared) == source(approved)
assert prepared['cosmos-framework'] == '160000 commit ' + CHILD
root_common = text(R, 'merge-base', TRAIN_ROOT, EVAL_ROOT)
root_union = union(source(tree(R, root_common)), source(tree(R, TRAIN_ROOT)),
                   source(tree(R, EVAL_ROOT)), gitlink=CHILD)
assert source(approved) == root_union
for sha, mapping in ((BASE, canonical), (CANDIDATE, candidate)):
    assert all(prepared[n] == value for n, value in mapping.items() if n.startswith('docs/') and n != INBOX), sha
read = lambda p: git(R, 'show', prepared_tree + ':' + p)
common_inbox = git(R, 'show', TRAIN_ROOT + ':' + INBOX)
candidate_inbox = git(R, 'show', CANDIDATE + ':' + INBOX)
assert candidate_inbox.startswith(common_inbox)
candidate_tail = candidate_inbox[len(common_inbox):]
inbox = read(INBOX)
assert inbox.startswith(git(R, 'show', BASE + ':' + INBOX))
assert inbox.count(candidate_tail) == 1 and len(inbox) <= 131072
review = read(REVIEW)
assert review == git(R, 'show', BASE + ':' + REVIEW)
assert FORMAL.encode() in review and CHILD.encode() in review and b'APPROVE_CODE' in review

manifest = json.loads(read(PREFIX + 'artifact_sha256.json'))
for name, item in manifest.items():
    payload = read(PREFIX + name)
    assert hashlib.sha256(payload).hexdigest() == item['sha256'] and len(payload) == item['bytes'], name
root = ET.fromstring(read(PREFIX + 'raw/light-cpu/junit.xml'))
cases = list(root.iter('testcase'))
assert len(cases) == len({(t.get('classname'), t.get('name')) for t in cases}) == 84
assert all(not any(t.find(k) is not None for k in ('failure', 'error', 'skipped')) for t in cases)
summary = json.loads(read(PREFIX + 'summary.json'))
assert summary['source_pair'] == dict(root=FORMAL, child=CHILD)
assert summary['source_unchanged'] is True
result = dict(status='PASS_READONLY_TRAIN_EVAL_PROMOTION_AUDIT', canonical_base=BASE,
              approved_formal_root=FORMAL, approved_child_gitlink=CHILD, candidate_head=CANDIDATE,
              prepared_tree_snapshot=prepared_tree, root_source_objects_equal_approved=len(source(approved)),
              all_root_source_equal_approved=True, root_source_equals_disjoint_parent_union=True,
              child_objects_equal_parent_union=len(cu), child_parents=[TRAIN, EVAL],
              child_union_has_no_source_overlap=True, eval_delta_from_train=eval_delta,
              train_delta_from_eval=train_delta, old_no_ttt_training_preserved=True,
              approved_eval_v2_preserved=True,
              canonical_docs_preserved=sum(n.startswith('docs/') and n != INBOX for n in canonical),
              candidate_docs_preserved=sum(n.startswith('docs/') and n != INBOX for n in candidate),
              inbox_canonical_prefix_preserved=True, candidate_tail_preserved_once=True, inbox_bytes=len(inbox),
              artifact_sha256_verified=len(manifest), original_junit_cases_read_only=84,
              original_junit_failure_error_skip=[0, 0, 0], original_real_OS_planned_deselected=1,
              tests_or_gpu_reexecuted=False, runtime_data_model_job_dcp_touched=False,
              review_path=REVIEW, review_object=prepared[REVIEW])
Path('/tmp/psm-train-eval-promotion-20261031/source_audit.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('eval_delta_from_train', 'train_delta_from_eval')}, indent=2))
