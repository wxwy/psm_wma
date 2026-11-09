"""Copy immutable CPU evidence, append review request; no network or source edits."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

root=Path('/workspace/work/psm-wma-history-k-issue28')
child=root/'cosmos-framework'
src=Path(__file__).parent
formal_root='050e45d87fe5faf3a830bcaf4629fd7d16ba47a7'
formal_child='59746af006748488a678aa9a55dfc3e200668219'
rel='docs/collab/codex/evidence/2026-11-09_issue28_history_k'
dest=root/rel
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
assert git(root,'rev-parse','HEAD')==formal_root and git(child,'rev-parse','HEAD')==formal_child
assert not git(root,'status','--porcelain') and not git(child,'status','--porcelain')
gate=json.loads((src/'author03/gate.json').read_text())
assert gate['status']=='PASS' and gate['source_unchanged'] and gate['dense_K16_bit_equal']
assert gate['junit']==dict(tests=838,failures=0,errors=0,skipped=0)
assert gate['pytest_top_level']==631 and gate['pytest_subtests']==207
assert json.loads((src/'author03/outer_tool_result.json').read_text())['exit_code']==0
assert (src/'author03/source_before.json').read_bytes()==(src/'author03/source_after.json').read_bytes()
assert sha(src/'author_gate.py')==json.loads((src/'author03/environment.json').read_text())['tools']['author_gate.py']
assert sha(src/'author02/runner_as_executed.py')==json.loads((src/'author02/environment.json').read_text())['tools']['author_gate.py']
old_runner=(src/'author02/runner_as_executed.py').read_text().replace(
    "        static.extend(str(repo/n) for n in git(repo,'diff','--name-only',base,'HEAD').splitlines()\n            if n.endswith('.py') and (n.startswith(('scripts/','tools/')) if repo == root else n.startswith('cosmos_framework/')))",
    "        static.extend(str(repo/n) for n in git(repo,'diff','--name-only',base,'HEAD').splitlines() if n.endswith('.py'))")
assert hashlib.sha256(old_runner.encode()).hexdigest()==json.loads((src/'author01/environment.json').read_text())['tools']['author_gate.py']
assert not (src/'author01/runner_as_executed.py').exists()
(src/'author01/runner_as_executed.py').write_text(old_runner)
red=json.loads((src/'boundary_red/result.json').read_text())
green=json.loads((src/'boundary_green/result.json').read_text())
assert red['expected_outcome'] and green['expected_outcome'] and red['test_sha256']==green['test_sha256']
for name,value in red['production_sha256'].items():
    raw=subprocess.check_output(['git','show','6b5c191527d83f08f9612b12f83f35dcb39c5f45:cosmos_framework/'+name],cwd=child)
    assert hashlib.sha256(raw).hexdigest()==value
assert red['test_sha256']==sha(child/'cosmos_framework/inference/robocasa_history_k_test.py')
dest.mkdir(parents=True,exist_ok=False)
for folder in ('dev01','dev02','dev03','boundary_red','boundary_green','author01','author02','author03'):
    for path in (src/folder).iterdir():
        if path.is_file():
            target=dest/folder/path.name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
    # Retain actual process/READY/close/manifest/OS proofs, not caches, sockets,
    # synthetic checkpoints or private configuration directories.
    for path in (src/folder).rglob('*'):
        if not path.is_file() or path.parent==src/folder:
            continue
        name=path.relative_to(src/folder)
        take=path.name.endswith('os_behavior.json') or path.name=='manifest.json'
        take=take or ('_internal/runtime' in str(name) and path.name.startswith('shared_vae_worker_'))
        take=take or ('/logs/' in str(name) and path.name.startswith('vae_') and path.suffix=='.log')
        if take:
            target=dest/folder/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)
for name in ('dev01.py','dev02.py','dev03.py','author_gate.py','dense_parity_probe.py','boundary_probe.py','archive_handoff.py'):
    target=dest/'runners'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src/name,target)
shutil.copyfile(src/'author_gate.py',dest/'author03/runner_as_executed.py')
roll=root/'docs/collab/chatgpt/archive/CODEX_INBOX_20261109_125637_73d8644.md'
assert sha(roll)=='7e027a9f1eb2649bd6bdfe4590cd9ea00d6e354a8a5ca960825ae04b707b07d7'
write(dest/'provenance.json',dict(formal_root=formal_root,formal_child=formal_child,
    gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),root_metadata_base='73d8644df3096e192a83fff2f2d8098a4ac11e64',
    qualified_base_root='9b1756f9099955d6637743f8ad2fa0ee54987b7a',qualified_base_child='60b252d05157b2753d2caebae32b11c878504bbe',
    aggregate_root_diff=git(root,'diff','--stat','73d8644df3096e192a83fff2f2d8098a4ac11e64','HEAD'),
    aggregate_child_diff=git(child,'diff','--stat','60b252d05157b2753d2caebae32b11c878504bbe','HEAD'),
    scope='author CPU/static only; synthetic model/env/kernel/device/current-boundary',
    old_author01='FAIL before tests: runner scope included immutable archived scripts; source untouched',
    old_author02='intermediate df043615/6b5c1915 PASS 623+207=830; not final acceptance',
    boundary_red='8 expected failures on prior sparse candidate plus new uncommitted regression',
    boundary_green='same test SHA 8PASS with minimal uncommitted fix; final clean Gate repeated afterward',
    final_gate=gate['junit'],pytest_top_level=631,pytest_subtests=207,source_fingerprint_files=len(json.loads((src/'author03/source_before.json').read_text())),
    source_unchanged=True,GPU_Wan_DCP_RoboCasa_SR_training='NOT_RUN',independent_review='REQUESTED_NOT_CLAIMED'))
hashes={str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}
write(dest/'archive_manifest.json',dict(schema='issue28-immutable-raw-evidence-v1',files=hashes))
handoff_rel='docs/collab/codex/reviews/2026-11-09_Issue28_HistoryK_050e45d8_59746af0_Code_Review_Request.md'
handoff=root/handoff_rel
handoff.parent.mkdir(parents=True,exist_ok=True)
handoff.write_text(f'''# Issue #28 — request fresh incremental Code Gate

Formal Root **`{formal_root}`** / Child-Gitlink **`{formal_child}`**.
Both source worktrees were clean during final author Gate. Evidence/docs commits
after this Root do not replace the review target. Review the entire aggregate
increment from qualified #27 Root `9b1756f9099955d6637743f8ad2fa0ee54987b7a`
(metadata base `73d8644df3096e192a83fff2f2d8098a4ac11e64`) and Child
`60b252d05157b2753d2caebae32b11c878504bbe`, not only the last Gitlink commit.
Root PR #29 / Child PR #8 are unchanged. New independent stacked Draft PRs will
target those candidate branches; no automatic V3 or base-branch merge.

## Implementation

One public `local_ttt_history_k=1/2/4/8/16`, default16. For actual completed H16
chunk [T,T+15], select j%(16/K)==0; at next Replan T+16 use O[T+j] and the
canonical action actually executed at that source. j0 reuses the prior Policy
current-frame Visual96. O[T+16] belongs to the next chunk, no future action or
reindexing. Extra Worker Encode1/FW counts per chunk: 0/1,1/2,3/4,7/8,15/16.
Cold Replan updates0; partial tail Ends, never prepares an incomplete H16 update.

Native Sim selects before history RGB capture. Unselected sources have no RGB,
PNG, Frame, dummy feature or FW update. All16 true completion receipts and
canonical action/lease/chunk/Actor/epoch/frontier/original deadline fences stay.
K<16 has explicit versioned skip receipts/payload; Owner validates every row
before selecting the real evidence for the original T1 scan. Worker uses a
bounded authorized skip ledger on existing control RPC; async earlier Frames
cannot be bypassed. Original native atomic commit/abort/replay/ACK/End/reset,
No-TTT, source verification, scheduler and resource authority remain.

K freezes in execution/Manifest, Policy, Worker bootstrap/READY, assignment and
Local Session; full M/B/source Resume restrictions remain. Default16 preserves
the original dense wire/fingerprint/numerical path. Worker remains B1/wait0,
Policy Native batching1..8. A retained Sim connector B1 guard is aligned to the
already approved1..8 range here, with an actual constructor test; #27 is untouched.
No training/model/weights/new scheduler or second sparse engine change.

## Final exact-pair author evidence

Raw: `{rel}/author03/`; index `{rel}/archive_manifest.json`.

| Group | Tests | Subtests | JUnit | Failure/error/skip |
|---|---:|---:|---:|---|
| Sparse new paths |108|0|108|0/0/0|
| Local/No-TTT/transactions |171|22|193|0/0/0|
| Worker/protocol/Sim |288|185|473|0/0/0|
| Existing topology |64|0|64|0/0/0|
| Total |631|207|838|0/0/0|

Shell0, gate.status=PASS, source_unchanged=true,21 changed Python files Ruff,
format and syntax PASS. All5 K,0→16→32, no skipped image/encode/update, exact
original source IDs, full completion admission, partialEnd, late/forged/changed
bytes, abort/retry/replay, actual constructor B8 and frozenK/M/B rejection covered.
Real CPU Worker FD daemon/Unix IPC/Owner HTTP tests all5 K with shared Sessions,
plus sparse K4 2Policy×16Sim=32 Sessions/one Worker/native B8+B8 per Server,
permissions/ACK/End/owned exit0/IPC cleanup/external survival. Device/kernel/
current Policy boundary/physics/model-generation boundaries are explicit doubles.

Same probe in separate old60b/new59746 Child CPU processes, seed28/one thread:
signed feature wire, cached boundary, actual Local FastState/Prefix and synthetic
linear Action hashes exactly equal for K16. These are not real Wan/DCP/diffusion
Action/GPU equivalence or performance/SR evidence.

## Failure history and limits

All development failure JUnit/logs retained: dev01 fixture cleanup/exception/kernel
input errors; dev02 missing synthetic Session identity, correctly rejected;
dev03 new98PASS and dense parity. Author01 static-runner archive-scope error was
fixed only in the external runner; archived scripts were not formatted. Original
as-executed runner reconstructed and checked against its recorded SHA. Author02
830PASS belongs to the intermediate Pair. Controlled H16 negative:8 expected RED
failures on prior6b production with only new test dirty;8GREEN on same test hash
after sparse-only guard; final clean new Pair rerun includes all8. Do not add
historical counts to the final631+207. No old900 or historical965 Gate rerun.

Reproduce using adjacent archived `runners/author_gate.py` and
`runners/dense_parity_probe.py`, clean checkout of the exact pair, a separate clean
Child60b baseline, CPU venv Torch2.10.0+cpu/Pytest9.0.2/Ruff0.12.7 and a NEW external
output directory. Commands/environment/timeouts are recorded in author03/gate.json
and environment.json; entry arguments are --root-worktree, --expected-root,
--expected-child, --baseline-child, --evidence-dir. Gate rejects dirty/mismatched
source and preserves complete raw logs/JUnit/proofs. Archive caches/private test
configuration/synthetic checkpoints are excluded; full raw test logs are retained.

Please independently review the aggregate production/test increment and CPU
evidence for this exact Pair. Author does not claim APPROVE_CODE, GPU closure,
real model parity, speed/SR benefit or permission to merge V3. Later hardware
smoke, paired SR and performance need their separate authorization. No GPU,
remote server files, training, live evaluations or running-job operations occurred.
''')
stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
inbox=root/'docs/collab/chatgpt/CODEX_INBOX.md'
entry=f'''\n\n## {stamp} — Issue28 new sparse-history incremental Code Gate request\n
Formal Root `{formal_root}` / Child-Gitlink `{formal_child}`. Qualified baseline
#27 Root9b1756f9/Child60b252d0 APPROVE_CODE CPU only. Review aggregate from that
baseline, not just final Gitlink commit. New independent branch/stacked Draft PRs,
#27PR29/8 and officialV3 untouched. K1/2/4/8/16 default16; j0 cached/current prior
frame, full16 completion authority, pre-capture skip, original T1 consumer and
transactions, strict K/fullM-B/source Resume. No model/training/scheduler change.

Exact clean final author03:631 top-level+207subtests=838JUnit PASS,0fail/error/skip,
shell0/gatePASS/sourceunchanged;21staticfiles PASS, defaultK16 old/new CPU bit parity
(features/FastState/Prefix/syntheticAction). Actual FD daemon/UnixIPC/OwnerHTTP
all5K+K4 32Sessions/B8+B8 each/cleanup; synthetic model/env/kernel/device boundaries.
Controlled H16 RED8/GREEN8 and original development/runner failures retained, no
historical-count summation. This is a fresh REVIEW request, not author approval.
Handoff `{handoff_rel}`; raw/index `{rel}/`.
Allowed scope Code/CPU/static review only. No GPU/Wan/DCP/realSim/performance/SR/
900EP/training/remote-file/running-job/V3 merge operation or closure claimed.
'''
before=inbox.read_bytes()
assert len(before)+len(entry.encode())<=131072
inbox.write_bytes(before+entry.encode())
todo=root/'TODO.md'
text=todo.read_text().replace('**ISSUE28-LOCAL-TTT-HISTORY-K** — IN_PROGRESS','**ISSUE28-LOCAL-TTT-HISTORY-K** — REVIEW',1)
assert text!=todo.read_text()
todo.write_text(text)
session=root/'SESSION.md'
session.write_text(f'''# {stamp} — Issue28 final author PASS; independent Code Gate REVIEW

Formal Root {formal_root} / Child-Gitlink {formal_child}; clean exact author03.
631tests+207subtests=838JUnit PASS,0fail/error/skip,shell0/source_unchanged=true;
21staticfiles PASS, defaultK16 old/new feature/FastState/Prefix/syntheticAction
bit-equal. Controlled H16 RED8/GREEN8 same test hash; final Gate includes8. No
historical-count relabeling; intermediate830PASS and original dev/runner failures
preserved. Source/proofs/raw logs/JUnit archive {rel}; handoff {handoff_rel}.

K1/2/4/8/16 default16, pre-RGB skip, all16 completion authority, cachedj0,
existingT1/Native transactions; strict K/M-B/source Resume, sharedWorkerB1/wait0,
generic legal topologies including K4/32Session/B8+B8 each. No model/training or
scheduler changes. One inherited Sim connector B1 guard aligned1..8 here only.
Fresh fetch/advertised/tracking officialRootV3 e58cef1f53d2382d39c871ce5a50e4acdd5ce268,
#27Root73d8644d, Childofficialb0dbd115/#27Child60b252d0; isolated frozen feature
not merged with those branches. Exact #27 review readback still APPROVE_CODE CPU.

Next normal Child-first/newRoot branch pushes, NEW independent stacked Draft PRs
against qualified#27 candidate branches, then remote source/Gitlink/evidence/Inbox
readback. #27PR29/8 untouched. Review request is author-only, fresh GPT verdict
pending; no implied APPROVE_CODE/hardware/merge permission. No GPU/remote files/
realSim/SR/900EP/training/live evaluation/running-job/V3 operations. TaskREVIEW.

'''+session.read_text())
write(dest/'archive_write_receipt.json',dict(timestamp=stamp,files_hashed=len(hashes),
    canonical_inbox_before_bytes=len(before),canonical_inbox_after_bytes=inbox.stat().st_size,
    old_inbox_archive_sha256=sha(roll),source_unchanged_again=all(sha(root/n)==v
        for n,v in json.loads((src/'author03/source_before.json').read_text()).items())))
assert json.loads((dest/'archive_write_receipt.json').read_text())['source_unchanged_again']
hashes['archive_write_receipt.json']=sha(dest/'archive_write_receipt.json')
write(dest/'archive_manifest.json',dict(schema='issue28-immutable-raw-evidence-v1',files=hashes))
for name,value in hashes.items():
    assert sha(dest/name)==value
print(json.dumps(dict(archive=rel,raw_files=len(hashes),handoff=handoff_rel,
    inbox_bytes=inbox.stat().st_size,status='ARCHIVED_REQUEST_PREPARED'),indent=2))
