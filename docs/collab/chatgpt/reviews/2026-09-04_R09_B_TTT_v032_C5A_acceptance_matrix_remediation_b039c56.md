# ChatGPT re-review — R09-B TTT v0.3.2 C5A acceptance-matrix remediation @ b039c56

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation/evidence SHA: `b039c56f4b264dbd04fae3980727b64510583c03`
- child/Gitlink: `4ae44604eeb63f2ebc258f8d73fb2d0a12e82e76`
- separate canonical request/ledger SHA observed at review start: **none**; the user supplied the exact pair directly, and `origin/V2` itself was `b039c56...`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- prior formally reviewed pair: root `b371cf1f0b2e8a5846b3cf76df609338f96f56a5` / child `cebe8a95b705b120cee21a4f047acba60d239a48`

Scope check:
- root `b371cf1... -> b039c56...` changes only SESSION/TODO, Gitlink, ChatGPT review/Inbox bookkeeping;
- child `cebe8a95... -> 4ae44604...` is five commits ahead and cumulatively changes only `cosmos_framework/model/generator/mot/c5a_owner_segment.py` and `c5a_owner_segment_test.py`;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Closed relative to the prior target

The current remediation materially closes several prior blockers:
- `AdmissionAuthority` now keeps an exact issued-capability registry and `verify()` compares the full immutable issued record, so same-token field tampering no longer authenticates;
- `epoch` is bound into the issued capability/digest and `admit()` rejects stale owner epochs;
- `materialize()` now rejects a second materialization;
- `commit()` requires `BACKWARD_OK`, and `finish()` no longer rematerializes an already-materialized segment;
- `materialize_many()` now forms one actual `[B,T,256]` evidence tensor and calls one batched `scan_segment_many()`; the permutation fixture now compares `[a,b]` vs `[b,a]` by owner identity;
- submitted isolated evidence increased to `14 passed`.

These are real closures, but the Gate still has implementation and evidence blockers below.

## Findings

### 1. HIGH — unseen transitions can still be appended after atomic materialization

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:102-131`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:152-156`

**Root cause:** `materialize()` correctly changes the pending phase from `COLLECT_RAW` to `MATERIALIZED_PENDING`, but `admit()` does not gate unseen admissions on that phase. It first permits cached replay, which is required, but when no cache is found it continues to chronology allocation and appends a new `(cap, payload)` to `pending.rows` even if the segment has already been materialized. A caller can therefore materialize timestep 0, then admit a new timestep 1, call `mark_backward_done()` and `commit()`. `commit()` uses `pending.rows[-1]` for `_last_timestep`, so chronology can advance through a transition that never passed Encoder/C5 and has no replay record.

**Contract violation:** v0.6 §3 freezes `COLLECT_RAW -> MATERIALIZE_PENDING` as an atomic segment boundary. After materialization, replay of an already-known S may be zero-write, but unseen S must not mutate the materialized transaction.

**Acceptance condition:** after `pending.phase != COLLECT_RAW`, `admit()` may return only an exact pending/committed replay already present in the ledgers. Any unseen source key must reject before `pending.rows`, identity index, chronology or C5 mutation. Add a direct fixture: admit t0 -> materialize -> admit unseen t1 must reject; same-S t0 replay must still succeed with zero extra C5 writes; final committed `_last_timestep`, replay set and state must remain exactly t0.

### 2. HIGH — `BACKWARD_OK` remains caller-asserted rather than tied to a successful ordinary outer backward

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:224-228`
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:21-25,45-65,83-93,111-132,150-179`

**Root cause:** `mark_backward_done()` only checks `pending.phase == MATERIALIZED_PENDING` and then sets `BACKWARD_OK`; it does not execute, observe or otherwise bind itself to a successful ordinary outer `loss.backward()`. Most current fixtures call `mark_backward_done()` without any backward at all and then commit successfully. The one gradient fixture does execute `loss.backward()`, but that is merely test convention rather than a state-machine guarantee.

**Contract violation:** v0.6 §§3-4 require one ordinary outer backward to complete successfully before atomic commit/detach. Caller-asserted phase marking can still commit without backward and does not fail closed if backward would have raised.

**Acceptance condition:** use a wrapper-owned `backward_and_mark(owner, loss)` / callback / equivalent mechanism whose phase advances only after ordinary backward returns successfully; if backward raises, phase and committed C remain unchanged. A raw public `mark_backward_done()` that can be called without backward is not sufficient. Add fail-before-commit tests for no-backward and failing-backward cases, plus successful ordinary backward. Gradient evidence must separately prove finite/nonzero reachability for the evidence encoder and the required C5 slow groups Q/K/V, slot queries and W0, not merely `any()` one parameter across both modules.

### 3. HIGH — committed replay drops the frozen presence record, and row-level reset is not owner-epoch atomic

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:73-94`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:180-208`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:233-241`

**Root cause:** pending and committed replay are stored as `Tensor` only. In `materialize_many()`, `scan_segment_many()` returns `present`, but `present` is discarded and every row stores only `tokens[...]`. An invalid row therefore replays as an ordinary zero tensor with no explicit `present=False`, even though v0.6 requires committed numerical replay to preserve value/shape/presence. In the same batched path, `done_before` resets only the gathered fast state through `core.reset_mask()`; it does not advance the C5A owner epoch, clear owner chronology/replay, or require that the owner has already passed through `reset()`. A stateful owner can therefore have its fast state reset while remaining in the same C5A epoch/chronology.

**Contract violation:** v0.6 §3 requires detached/cloned value/shape/presence replay records; §§2/4 require owner/epoch/reset authority to remain coherent and cross-epoch state to fail closed.

**Acceptance condition:** store an explicit detached replay record containing at least value, shape and presence, and return that record consistently for pending and committed replay. For row-level done/reset, either (a) remove `done_before` from C5A materialization and require the owner to be epoch-reset before admission, or (b) make the row reset atomically update C5A owner epoch/chronology/replay authority before accepting the new-epoch source. Add a stateful owner test across reset, not only an all-new-state `done_before=True` row.

### 4. HIGH — the authority still does not authenticate the frozen completed-causal provenance class

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:26-67`

**Root cause:** the exact-issued registry now authenticates the fields that exist, but `AdmissionCapability` has no `provenance_class` field and `AdmissionAuthority.issue()` has no requirement equivalent to `R08_COMPLETED_CAUSAL`. The frozen design explicitly states that the R08 capability authenticates completed-causal provenance and that history/future/GT substitution must reject before C5. The current synthetic authority can issue any tensor dictionary that passes its basic tensor checks; provenance is not represented or verified.

**Contract violation:** v0.6 §2 requires `provenance_class=R08_COMPLETED_CAUSAL` in the trusted capability and hostile history/future/GT provenance rejection before C5.

**Acceptance condition:** bind an exact completed-causal provenance class (or equivalent trusted R08 capability type) into the authority-issued record and verify it during admission. Add negative fixtures for non-R08 / future / GT provenance that prove rejection before Encoder/C5 and before chronology/index mutation.

### 5. HIGH — the submitted 14-test evidence still does not satisfy the frozen v0.6 acceptance matrix

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:21-190`

**Root cause / missing evidence:** the matrix is improved but still incomplete and some status wording overclaims coverage:
- no explicit `StatelessLocalReplayReadout` spy proving zero calls;
- hostile admission is limited mainly to bad bytes/foreign seal/stale epoch, not the frozen owner/source/timestep/schema/dtype/shape/provenance matrix;
- no pending replay no-graph fixture and no explicit `grad_fn is None`/clone evidence;
- committed replay is tested immediately after one commit, but not replay of an older S after chronology has advanced further;
- rollback assertions do not snapshot and compare the entire committed state/reverse index/chronology before and after failure/abort;
- outer-gradient assertion uses `any(...)` across encoder+core rather than proving the required encoder and each C5 slow group is finite/nonzero;
- the parameterized terminal test does **not** test terminal `r=N`: full N is tested only with `terminal=False`; its terminal branch tests `r=0` for N=1 and `r=N-1` for N=3/16, not the frozen terminal `r=0..N` matrix;
- the fast-state ownership fixture enumerates `runtime.core.named_parameters()` but does not directly prove the carried fast-state object is outside optimizer/module parameter ownership at the C5A wrapper boundary.

**Contract violation:** v0.6 §4 explicitly requires the complete synthetic CPU matrix before closure. `14 passed` plus py_compile/diff-check is useful evidence, but it is not closure evidence for the frozen contract.

**Acceptance condition:** add the missing direct fixtures above; in particular terminal=True must cover r=0, all required 0<r<N remainders and r=N for N=1/3/16 as frozen, and the exact C5A acceptance selector must pass in the working CPU environment. Report the exact selector count plus py_compile and child/root diff-check.

## Evidence note

The repository status records isolated CPU pytest=`14 passed`, py_compile and diff-check PASS. Those commands were not independently rerun in this connector environment and are treated as submitted evidence. The implementation defects above independently block closure.

## Required next submission

Remediation must remain inside the already-approved isolated C5A CPU boundary unless scope is explicitly reopened. Any new root/child implementation SHA requires fresh same-SHA review.

Still prohibited:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
