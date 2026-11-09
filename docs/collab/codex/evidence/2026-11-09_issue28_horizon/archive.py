"""Horizon-only correction evidence and append-only review handoff."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

root=Path('/workspace/work/psm-wma-history-k-issue28')
child=root/'cosmos-framework'
src=Path(__file__).parent
pair=dict(root='53b5273c7907e2d7a8fb1831ac0e0ec8b9fa973a',child='4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe')
def git(repo,*args):
 return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()
assert git(root,'rev-parse','HEAD')==pair['root'] and git(child,'rev-parse','HEAD')==pair['child']
assert not git(root,'status','--porcelain') and not git(child,'status','--porcelain')
gate=json.loads((src/'author01/gate.json').read_text())
assert gate['status']=='PASS' and gate['junit']==dict(tests=588,failures=0,errors=0,skipped=0)
assert gate['source_unchanged'] and gate['dense_H16_default_bit_equal']
assert json.loads((src/'author01/outer_tool_result.json').read_text())['exit_code']==0
assert (src/'author01/source_before.json').read_bytes()==(src/'author01/source_after.json').read_bytes()
watch=json.loads((src/'author01/source_after.json').read_text())
assert all(sha(root/name)==value for name,value in watch.items())
old=root/'docs/collab/codex/evidence/2026-11-09_issue28_history_k'
old_index=json.loads((old/'archive_manifest.json').read_text())['files']
assert all(sha(old/name)==value for name,value in old_index.items())
rel='docs/collab/codex/evidence/2026-11-09_issue28_horizon'
dest=root/rel
dest.mkdir(parents=True,exist_ok=False)
for label in ('dev01','author01'):
 for path in (src/label).iterdir():
  if path.is_file():
   target=dest/label/path.name
   target.parent.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(path,target)
 for path in (src/label).rglob('*'):
  if not path.is_file() or path.parent==src/label:
   continue
  local=path.relative_to(src/label)
  keep=path.name.endswith('os_behavior.json') or path.name=='manifest.json'
  keep=keep or ('_internal/runtime' in str(local) and path.name.startswith('shared_vae_worker_'))
  if keep:
   target=dest/label/local
   target.parent.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(path,target)
for name in ('dev_gate.py','owner_requirement.json','archive.py'):
 shutil.copyfile(src/name,dest/name)
shutil.copyfile('/workspace/work/issue28-history-k-evidence/dense_parity_probe.py',dest/'dense_parity_probe.py')
for label,repo,base,ref,paths in [('root',root,'050e45d87fe5faf3a830bcaf4629fd7d16ba47a7',pair['root'],['scripts','tools']),
 ('child',child,'59746af006748488a678aa9a55dfc3e200668219',pair['child'],['cosmos_framework'])]:
 patch=subprocess.check_output(['git','diff','--binary',base,ref,'--',*paths],cwd=repo)
 (dest/(label+'_increment.patch')).write_bytes(patch)
stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
provenance=dict(timestamp=stamp,formal_pair=pair,gitlink=git(root,'rev-parse','HEAD:cosmos-framework'),
 previous_formal_root='050e45d87fe5faf3a830bcaf4629fd7d16ba47a7',previous_child='59746af006748488a678aa9a55dfc3e200668219',
 review_root_metadata='c622ac1925778b431e1206d3e34f007e250b33ac',author_tests=566,subtests=22,junit=588,
 source_unchanged=True,static_files=22,dense_H16_default_bit_equal=True,source_files=len(watch),
 dev01='558 tests+22subtests passed,8 failures in legacy Registry fixture missing protocol/INFO H; raw retained',
 old_evidence_unchanged_files=len(old_index),historical631_plus207='retained, not rerun/relabelled as this increment',
 versions={n:importlib.metadata.version(n) for n in ('torch','pytest','ruff','omegaconf')},
 GPU_real_model_RoboCasa_SR_training_900_V3='NOT_RUN',independent_code_verdict='REQUEST_FRESH_REVIEW')
(dest/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
hashes={str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}
(dest/'archive_manifest.json').write_text(json.dumps(dict(files=hashes),indent=2)+'\n')
handoff_rel='docs/collab/codex/reviews/2026-11-09_Issue28_Horizon_53b5273c_4cd5fc8c_Incremental_Review_Request.md'
handoff=root/handoff_rel
handoff.write_text(f'''# Issue28 Horizon-derived K — incremental Code Gate request

Formal Root `{pair['root']}` / Child-Gitlink `{pair['child']}`.
Review only the increment from prior050e45d87fe5faf3a830bcaf4629fd7d16ba47a7 /
59746af006748488a678aa9a55dfc3e200668219. Latest REQUEST_CHANGES review was
fresh-fetched/read and preserved via c622ac19. Same independent Draft RootPR30 /
ChildPR9; their qualified #27 bases and official V3 are unchanged by this work.
Later evidence commits are not new implementation targets.

## Correction

Root/Child public K defaults are None. Unified validate_history_k(K,H) resolves
None to H and accepts exact positive integer divisors only; selected_history_step
uses H//K and chunk-relative j, always j0, without source renumbering. Helpers
cover arbitrary positive H/relative anchors, including H12/K3 and H24 cases.
There is no fixed K enumeration or K sampling calculation16//K in production.

H comes from the existing frozen Native protocol Action Chunk size, not Episode
rollout horizons. Its original16 is named ACTION_CHUNK_SIZE in the authoritative
contract and reused by Manifest/model identity. Root resolves K from it and
compares actual Policy INFO.action_chunk_size to the frozen Manifest. Policy
Owner receives resolved model cfg H; the existing Local consumer receives Owner
H and freezes it per Session. Sparse Worker bootstrap/READY/assignment carry H
with K; Sim compares it to Actor/native settings. Native Worker/Owner/Sim retain
the current model H16 restriction. This adds no public H knob or real H12 model/
simulator capability, architecture, engine, scheduler, training or model change.

K=H uses the original dense wire/fingerprint/canonical Manifest omission of K.
Strict K/H/M/B/source Resume, all actual completion receipts, cached j0, original
T1 transactions and No-TTT/sharedB1/native batching/Session/End remain. Relative
helper anchors can be arbitrary; real Native chunk authority still requires its
original valid H16 boundaries.

## Exact clean-pair author evidence

**566 top-level tests +22subtests PASS =588 JUnit,0failed/error/skipped**;
shell0, gate.status=PASS, source_unchanged=true. Ruff/format/AST22 changed Python
files PASS. Raw `{rel}/author01/`; immutable index `{rel}/archive_manifest.json`;
exact Root/Child incremental patches and source before/after inventories included.

Covers H1..48/default/divisors/K1/dense/j0/true IDs and boundary rejection,
H12/H24 pure helper/T1 consumer cases, invalid types/non-divisors, omitted/None/
explicit dense canonical config/Manifest identity, Episode horizon distinction,
actual Policy H mismatch before Worker start, Worker/Sim/Session H fences,
current H16 all-K/0→16→32/partialEnd/retry/abort/late/No-TTT/Native transactions,
existing shared FD/OwnerHTTP/UnixIPC/topology/32Session/B8+B8/owned cleanup.
Model/physics/kernel/device/current-boundary boundaries are CPU doubles.

Same unchanged probe/seed28/CPU processes on old Child59746 and new4cd5fc8c:
Feature wire/cached boundary/actual Local FastState/Prefix/synthetic Action hashes
are identical for default H16. This is not real Wan/DCP/diffusion/GPU evidence.

Dev01 raw558PASS+22subtests/8FAIL preserved: one legacy Registry fixture lacked
the protocol Manifest and Policy INFO H required by the new identity check;
explicit fixture H was supplied, no production fallback/bypass. Final clean
author run includes all8. Original631+207/dense evidence and every349 archived
file remain unchanged and are not added to new counts. No old965/900EP rerun.

## Reproduce and review

Use archived dev_gate.py with its exact --formal-root/--formal-child above,
--run NEW-directory-name (external directory, no --format for a Formal run),
same CPU venv and a clean baseline Child59746. As-executed paths/commands/env
are in author01/commands.json/environment.json; probe is archived adjacent.
The script's fixed worktree/evidence/probe paths reflect this execution; change
only those paths to a new isolated checkout when reproducing elsewhere.

Please independently review this exact H-derivation increment and raw evidence;
author PASS does not close the existing MEDIUM or claim APPROVE_CODE. Do not
infer GPU/real model/performance/SR/merge authorization. No server files, active
jobs, training, GPU/realSim/SR/900EP or V3/#27 operations occurred.
''')
inbox=root/'docs/collab/chatgpt/CODEX_INBOX.md'
entry=f'''\n\n## {stamp} — Issue28 Horizon correction: new incremental Code Gate request\n
Formal Root `{pair['root']}` / Child-Gitlink `{pair['child']}`.
Same DraftRootPR30/ChildPR9. Corrects prior050e45d8/59746af0 REQUEST_CHANGES:
K omitted/None->actual Action Chunk H, exact positive divisors, relative strideH//K
and j0; no fixed K enumeration/default16. Frozen protocol/model/Worker/Sim/Local
H binding, current NativeH16 unchanged; dense wire/fingerprint/Manifest preserved.
Exact clean author566tests+22subtests=588JUnit PASS,0failure/error/skip,shell0/
sourceunchanged,static22PASS, defaultH16 old59746/new4cd5 CPU bit parity. Generic
H1..48/H12/K3/H24 plus identity/NoTTT/Session/IPC/topology regressions covered.
Original dev fixture8FAIL and historical631+207 evidence retained, not relabelled.
Handoff `{handoff_rel}`; raw/index `{rel}/`.
Please fresh incremental review; prior MEDIUM is not author-closed. No GPU/
realSim/SR/900EP/training/server files/active-job/V3/#27 merge authorization.\n'''
old_bytes=inbox.read_bytes()
assert len(old_bytes)+len(entry.encode())<=131072
inbox.write_bytes(old_bytes+entry.encode())
todo=root/'TODO.md'
text=todo.read_text().replace('**ISSUE28-LOCAL-TTT-HISTORY-K** — IN_PROGRESS','**ISSUE28-LOCAL-TTT-HISTORY-K** — REVIEW',1)
assert text!=todo.read_text()
todo.write_text(text)
session=root/'SESSION.md'
session.write_text(f'''# {stamp} — Issue28 Horizon correction exact CPU PASS, incremental review prepared

Formal Root {pair['root']} / Child-Gitlink {pair['child']}; clean exact author01
566tests+22subtests=588JUnit PASS,0failed/error/skipped,shell0/gatePASS/source
unchanged;22 staticfiles PASS; same old59746/new4cd5 CPU defaultH16 feature,
FastState,Prefix,syntheticAction hashes equal. Original dev558+22/8fixtureFAIL
retained; fixed explicit fixture protocol/INFO H only. Previous349 archived files
reverified unchanged; original631+207 not relabelled or blindly rerun.
Generic H/divisor/default/j0/relativeIDs, Model/Worker/Sim/Session H mismatch,
strict Manifest/K/M-B/source Resume and relevant NoTTT/IPC/topology/End covered.
Current Native model/protocol H16 and original flow/training/scheduler unchanged.
Review handoff {handoff_rel}; raw {rel}.

TaskREVIEW, author evidence only; previous REQUEST_CHANGES remains independent
authority until GPT new-pair review. Next Child-first and Root normal pushes to
same PR30/9 branches, update descriptions to latest H rule, remote source/Gitlink/
raw evidence/Inbox readback. No new PR/runtime or #27/V3 merge. No GPU/server
files/active jobs/realSim/SR/900EP/training operations. Source work complete.

'''+session.read_text())
assert all(sha(root/name)==value for name,value in watch.items())
assert all(sha(dest/name)==value for name,value in hashes.items())
print(json.dumps(dict(status='ARCHIVED',pair=pair,files=len(hashes),inbox_bytes=inbox.stat().st_size,
 old_archive_unchanged=len(old_index)),indent=2))
