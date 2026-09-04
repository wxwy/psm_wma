# ChatGPT re-review — R09-B TTT v0.3.2 C5A lifecycle remediation @ beba8c9

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `beba8c95475e93abda26dc722bf096b2df99ecc8`
- child/Gitlink: `789864a90410934c2ee1d0eb8edb1c04f077574f`
- request/bookkeeping SHA observed at review start and rechecked before write: `22ea46a7c5cc4016cfa1f84ac8299cdb1a7b12b0`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- prior reviewed pair: root `3dfc4cb574a448ebd3b936752589f20a8d6e8bae` / child `95ef1bc2c71d9239f63489383d91b7661587d0ca`

Latest `V2` was rechecked immediately before review write and remained `22ea46a7...`; it is bookkeeping only and its parent is the formal implementation root `beba8c9...`.

Scope check:
- child `95ef1bc... -> 789864a...` is four commits ahead cumulatively but modifies only `cosmos_framework/model/generator/mot/c5a_owner_segment.py` and `c5a_owner_segment_test.py`;
- root-side cumulative changes remain SESSION/TODO, Gitlink and review/Inbox bookkeeping;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Findings

### 1. HIGH — authority seal still does not authenticate the exact issued capability fields

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:26-61`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:92-107`

**Root cause:** `_seal` is a reusable object stored directly in the public frozen dataclass. Any holder of one legitimate capability can copy/`replace()` that capability while retaining the same `_seal`. `admit()` checks only `cap._seal is authority._seal`; line 106 then reconstructs a new `AdmissionCapability` from the already-modified fields and compares its digest with the digest of those same fields, which is tautological. Therefore a capability issued for timestep 0 can be changed to timestep 1 (or owner/source identity/schema fields changed coherently), retain the valid seal, and pass the current authenticity check if the supplied source bytes/schema match the modified capability and chronology expects that timestep.

`source_shape` / `source_dtype` are also public capability fields but are not covered by `digest`; changing them does not invalidate the capability.

**Contract violation:** C5A v0.6 §2 explicitly requires rejection of copied/tampered capability fields and capability/source byte binding before chronology/C5. A producer-instance marker is not field-integrity authentication.

**Acceptance condition:** authority issuance must create an opaque token/registry entry (or equivalent unforgeable field-integrity binding) whose exact issued owner/source identity/source timestep/schema/source bytes/digest are resolved and compared during `admit()`. Same-seal `replace(cap, source_timestep=...)`, owner/source-identity changes, schema/dtype/shape changes and byte changes must all reject before encoder/C5, with zero chronology/index/write mutation.

### 2. HIGH — transaction state machine allows committed chronology to advance without materialization/backward; `finish()` cannot implement the frozen atomic backward ordering

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:145-151`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:162-177`
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:45-64`

**Root cause:** `commit()` has no phase guard. It will pop a pending transaction and advance `_last_timestep` / `_identity_index` even when `pending.base_state is None`, no C5 materialization occurred, no replay was produced and no outer backward occurred. The existing chronology test at line 48 directly executes `begin -> admit -> commit` and therefore proves this invalid path is currently accepted.

`finish()` always calls `materialize()` itself and immediately commits. For terminal `0<r<=N`, the frozen contract requires one atomic ordinary outer backward before commit/detach, but `finish()` has no loss/backward handoff. If a caller instead performs the correct `materialize -> backward` sequence first and then calls `finish`, `finish()` re-materializes the same pending rows from the already-updated candidate state, causing a second C5 write for the same segment.

**Contract violation:** C5A v0.6 §3-4 freezes one segment materialization, ordinary outer `backward()`, then atomic commit/detach; failure/abort/duplicate commit must not advance C. Exactly-once C5 writes are part of the replay/transaction contract.

**Acceptance condition:** implement an explicit transaction phase machine such as `COLLECTED -> MATERIALIZED_ONCE -> BACKWARD_DONE -> COMMITTED`. `commit()` must fail before any committed-state mutation unless materialization and the required outer backward have completed exactly once. `finish()` must not rematerialize an already-materialized segment. Add spies proving (a) direct `admit -> commit` rejects with zero C5/chronology mutation, (b) `materialize -> backward -> finish/commit` performs exactly one Encoder/C5 segment pass, and (c) failure/duplicate commit leaves C unchanged.

### 3. HIGH — reset does not create an isolated new epoch; prior committed replay and reverse-index authority remain visible

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:108-112`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:149-160`
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:45-56`

**Root cause:** `reset()` removes only `_state_by_owner` and `_last_timestep`. It leaves `_committed` and `_identity_index` unchanged, and neither source keys nor identity keys contain an epoch. Consequently, after terminal/reset, the same owner/source identity/timestep/digest can hit the previous epoch's committed replay with zero C5 work; the same identity/timestep with different bytes can be rejected as a conflict from the previous epoch. The current reset test avoids this by changing `source_identity` from `s` to `s2`, so it does not prove epoch isolation.

**Contract violation:** v0.6 requires C5A to reject cross-epoch substitution, define old-epoch retry/new-epoch visibility ordering and reset semantics, and keep replay/chronology owner-local to the active epoch.

**Acceptance condition:** add explicit epoch ownership to the committed/pending registry/key space or otherwise scope/clear replay and identity indexes at the frozen epoch transition. After reset, a new epoch using the same owner/source identity/timestep must not see stale prior-epoch replay/conflict state. Add tests for same source identity/timestep across reset (same bytes and changed bytes), old-epoch retry before new epoch visibility, and rejection of stale old-epoch capability after new epoch starts.

### 4. HIGH — closure evidence remains far below the frozen C5A acceptance matrix, and B>1 owner gather/scatter is still not implemented

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:123-143`
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:1-65`

**Root cause:** the submitted isolated selector now reports `5 passed`, but only five tests exist. They cover one single-step replay, limited forged/conflict cases, one abort candidate check, one skip/reset check and one short-terminal grammar case. The implementation itself still requires `value.shape[0] == 1`, initializes one owner state with batch size 1 and exposes no owner-identity gather/scatter path, so the frozen B>1 batch-permutation/row-mismatch contract is not representable by this wrapper.

Missing acceptance coverage includes at least: same-seal field tampering; exact capability/source byte/schema binding; stateless-readout spy=0; actual C5 input `[B,256]`; B>1 owner gather/scatter permutation equivalence and row mismatch rejection; temporal N>=2 state carry; pending replay; committed replay after chronology advance; full rollback of committed/reverse-index state; ordinary outer backward with finite/nonzero encoder + C5 Q/K/V/slot/W0 gradients; N=1/3/default16; terminal `r=0`, `0<r<N`, `r=N`; epoch reset/old-epoch retry; duplicate commit; fast-state non-registration.

**Contract violation:** v0.6 §4 requires this complete synthetic CPU matrix before closure. `5 passed` plus py_compile/diff-check is valid partial evidence but cannot close the Gate.

**Acceptance condition:** implement the missing B>1 owner/gather-scatter semantics or an explicitly equivalent owner-batched CPU contract, then add direct tests for the entire v0.6 matrix. Run the isolated CPU selector in the working environment and report the exact passing count, plus py_compile and child/root diff-check.

## What this remediation did close

Compared with the prior `95ef1bc...` target, the cumulative remediation materially closes several previous issues:
- raw-source canonical serialization now includes deterministic field name/dtype/shape/bytes and `admit()` recomputes source bytes/schema;
- pending identity/digest mutations are transaction-local and only promoted on commit, so the prior abort leak is closed;
- temporal carry remains correct as `[B=1,T,256] -> scan_segment_many()` with one owner fast-state row;
- committed `_last_timestep` now rejects simple cross-transaction skips;
- `segment_steps` is sourced from `core.ttt_tbptt_steps`, and `finish()` now distinguishes nonterminal exact-N from terminal short remainder / `r=0` at a structural level;
- submitted isolated CPU evidence improved to 5 passing tests.

These are partial closures, but the field-integrity authority, atomic materialize/backward/commit state machine, epoch isolation, B>1 owner contract and full acceptance matrix remain blocking.

## Evidence note

The repository request records isolated `--noconftest` CPU pytest = `5 passed`, py_compile and child/root diff-check PASS. Those commands were not independently rerun in this review environment; the reported results are treated as submitted evidence. The static/source findings above are sufficient to block closure independently of the missing matrix.

## Required next submission

A remediation must remain within the already-approved isolated C5A CPU boundary unless scope is explicitly reopened. Any new child/root implementation SHA requires fresh same-SHA review.

Still prohibited:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
