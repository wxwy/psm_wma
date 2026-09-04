# ChatGPT re-review — R09-B TTT v0.3.2 C5A owner-batch remediation @ b371cf1

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `b371cf1f0b2e8a5846b3cf76df609338f96f56a5`
- child/Gitlink: `cebe8a95b705b120cee21a4f047acba60d239a48`
- request/bookkeeping SHA: `d9cce5ed2c76006d70625e5a97131232b5b2dee1`
- latest routing/bookkeeping HEAD observed before review write: `f36e66794ab830bbbc6ff025cee89e692b9387b6`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- prior formally reviewed pair: root `beba8c95475e93abda26dc722bf096b2df99ecc8` / child `789864a90410934c2ee1d0eb8edb1c04f077574f`

The canonical Inbox explicitly supersedes earlier C5A implementation targets and routes the current review only to `b371cf1... / cebe8a9...`. The current V2 HEAD `f36e667...` is routing bookkeeping and is not treated as the implementation SHA.

Scope check:
- root `b371cf1...` resolves to Gitlink `cebe8a95...`;
- the implementation-side first parent `6865068...` advances only SESSION/TODO status plus the Gitlink; the merge also preserves the prior ChatGPT Inbox handoff;
- child `789864a... -> cebe8a9...` is exactly two commits ahead and cumulatively changes only `cosmos_framework/model/generator/mot/c5a_owner_segment.py` and `c5a_owner_segment_test.py`;
- no production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Findings

### 1. HIGH — the authority still authenticates only a reusable producer seal, not the exact issued capability

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:26-61`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:95-112`

**Root cause:** `AdmissionCapability` still exposes the authority's reusable `_seal`, and `AdmissionAuthority` still has no registry/token mapping back to the exact immutable record it issued. A holder of one legitimate capability can therefore `replace()` owner/source identity/source timestep/schema-bearing fields while retaining the valid seal. The current `admit()` check recomputes source bytes/schema, but its final digest check reconstructs a new `AdmissionCapability` from the already-modified fields and compares that object with itself; it does not prove those fields equal a record previously issued by the authority. `source_shape` and `source_dtype` also remain public fields outside the digest.

**Contract violation:** C5A v0.6 §2 requires copied/tampered capability fields, forged digest, owner/envelope mismatch and cross-epoch substitution to fail before chronology allocation, encoder work or C5.

**Acceptance condition:** authority issuance must return an opaque token/handle or equivalent unforgeable record whose exact issued owner, source identity, source timestep, full per-field schema, canonical source bytes/digest and epoch can be resolved and compared during `admit()`. Same-seal copies that alter any authenticated field must reject before encoder/C5 and before pending/committed index mutation. Add explicit fail-before-work tests for owner change, source identity change, timestep change, schema/dtype/shape change, source-byte substitution and forged digest.

### 2. HIGH — the transaction phase guard still does not prove ordinary outer backward, and exactly-once materialization is not enforced

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:125-147`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:156-196`
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:45-76`

**Root cause:** the new phase field blocks the old direct `admit -> commit` path, which is a real improvement. However, `materialize()` merely sets `pending.phase = "MATERIALIZED_PENDING"`; `commit()` then accepts that phase and itself changes it to `"BACKWARD_OK"`. No operation records that an ordinary outer `loss.backward()` actually completed, so `materialize -> commit` still advances committed state without outer backward. `materialize()` also has no guard against a second call on the same pending segment. Finally, `finish()` unconditionally calls `materialize()` and then `commit()`, so terminal closure can commit without outer backward, while a correct caller that already performed `materialize -> backward` would be rematerialized and written a second time by `finish()`.

**Contract violation:** C5A v0.6 §§3-4 freeze one atomic segment materialization with inner `create_graph=True`, one ordinary outer `backward()`, then commit/detach. Failure/abort/duplicate commit must leave committed C unchanged, and replay/materialization must not perform duplicate C5 writes.

**Acceptance condition:** implement an explicit lifecycle such as `COLLECT_RAW -> MATERIALIZED_ONCE -> BACKWARD_DONE -> COMMITTED`, with a distinct operation/event that transitions to `BACKWARD_DONE` only after the caller's ordinary outer backward has succeeded. A second `materialize()` must reject before Encoder/C5. `commit()` must reject unless phase is `BACKWARD_DONE`; `finish()` must not rematerialize an already-materialized segment and must preserve the frozen terminal `r=0`, `0<r<N`, `r=N` ordering. Tests must prove exact one Encoder/C5 pass, direct materialize-without-backward commit rejection, finite/nonzero outer gradients to LocalEvidenceEncoder and C5 slow/Q/K/V/slot/W0, failure rollback and duplicate-commit rejection.

### 3. HIGH — reset now clears replay/index state, but epoch authority is still not bound to capabilities or keys

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:80-94`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:95-123`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:174-184`

**Root cause:** `_epoch_by_owner` is incremented on reset and owner replay/reverse-index entries are now removed, which closes the previous stale-cache visibility defect. But the epoch value is not part of `AdmissionCapability`, `source_key`, identity keys, `begin()` or `admit()` validation. Consequently, a capability issued in the old epoch remains syntactically valid after reset; after the reset clears chronology/indexes, that stale old-epoch capability can be admitted as timestep 0 in the new epoch. The current tests issue a fresh capability after reset and do not attempt stale-capability reuse.

**Contract violation:** v0.6 requires cross-epoch inputs to reject, defines old-epoch retry/new-epoch visibility ordering, and states that failure retries belong only to the old epoch.

**Acceptance condition:** bind the current owner epoch into the authority-issued capability/opaque record and owner-local registry key space. Before new-epoch visibility, an old-epoch retry must follow the frozen retry rule; once reset/new epoch is visible, stale old-epoch capabilities must reject before encoder/C5. A fresh new-epoch capability using the same owner/source identity/timestep must be admissible without seeing stale replay/conflict state. Add same-bytes and changed-bytes cases across reset plus stale-old-capability rejection.

### 4. HIGH — `materialize_many()` is an output stack over repeated B=1 materializations, not the frozen B>1 gather/scatter contract; the six-test evidence is still far below closure

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:125-154`
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:66-76`

**Root cause:** `materialize_many(owner_keys)` loops over owners and calls `materialize(owner_key)` independently; each underlying encoder/C5 path still hard-requires `value.shape[0] == 1` and invokes `scan_segment_many()` with batch size 1. It then stacks only the returned final owner rows. This does not gather active owner evidence into an actual C5 `[B,256]` batch with owner-local state rows/validity and scatter results back by identity. There is also no row-mismatch input to validate. The new test named `test_materialize_many_permutation_preserves_owner_rows` executes only one order `["a", "b"]` and asserts only `shape[0] == 2`; it never runs `["b", "a"]`, compares owner-keyed outputs, checks a row mismatch, or spies the C5 batch shape.

The submitted isolated selector is now `6 passed`, but the frozen v0.6 matrix still lacks direct evidence for stateless-readout spy=0; actual C5 input `[B,256]`; hostile capability tampering; true batch permutation equivalence and row mismatch; pending replay; committed replay after chronology advance; full C/P rollback; ordinary outer gradients; N=1/3/default16; terminal `r=0`, `0<r<N`, `r=N`; stale/fresh epoch behavior; duplicate materialization/commit; row-selective valid/done/reset; and fast-state absence from `named_parameters()`.

**Contract violation:** v0.6 §§2-4 explicitly require owner-identity gather/scatter, batch permutation equivalence, row mismatch rejection and the complete CPU acceptance matrix before closure.

**Acceptance condition:** implement a true owner-batched CPU transition path (or an explicitly equivalent path that still proves the frozen C5 `[B,256]` contract) that gathers owner rows, carries/scatters each owner's fast state independently, supports valid/inactive rows and row-selective done/reset, and rejects owner/row mismatches before C5. The permutation test must compare two independently initialized executions of `[a,b]` versus `[b,a]` after re-keying by owner, not just tensor shape. Complete the full v0.6 acceptance matrix and report the exact passing selector count plus py_compile and child/root diff-check.

## What this remediation did close

Relative to `beba8c9... / 789864a...`, this target does close two narrower defects:
- direct `admit -> commit` without any materialization is now rejected by a transaction phase guard;
- reset now clears the owner's committed replay/reverse-index state before incrementing an owner epoch counter.

It also adds an owner-list `materialize_many()` surface and raises the isolated submitted selector from 5 to 6 tests. These are useful partial steps, but they do not close exact-issued authority, real backward-phase atomicity, epoch-bound capability authority, or the frozen B>1/acceptance contract.

## Evidence note

The repository request records isolated `.venv --noconftest` CPU pytest = `6 passed`, py_compile and child/root diff-check PASS. Those commands were not independently rerun in this review environment and are treated as submitted evidence. The source/contract findings above independently block closure.

## Required next submission

A remediation must remain inside the already-approved isolated C5A CPU boundary unless scope is explicitly reopened. Any new child/root implementation SHA requires fresh same-SHA review; this `REQUEST_CHANGES` is not reusable as approval.

Still prohibited:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
