# ChatGPT re-review — R09-B TTT v0.3.2 C5A temporal-carry remediation @ 3dfc4cb

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate: `G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `3dfc4cb574a448ebd3b936752589f20a8d6e8bae`
- child/Gitlink: `95ef1bc2c71d9239f63489383d91b7661587d0ca`
- request/bookkeeping SHA observed at review start: `c8de597509fb9ff0781334128cd890332a4a76e3`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- previous remediation pair: root `ede084c94019a6fc83728fc5a1229df6d5a872a3` / child `aa88aaacc1a1fad2d8348487fab260989c3aa067`

Latest `V2` was locked at `c8de597509fb9ff0781334128cd890332a4a76e3`; this is bookkeeping only and its parent `3dfc4cb...` remains the formal implementation target.

Child `95ef1bc...` is a single-file remediation over `aa88aaa...`, changing only `c5a_owner_segment.py`. No production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real I/O, training/eval/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Closed from prior review

### Prior HIGH-1 — CLOSED

`c5a_owner_segment.py:109-126` now preserves the segment as `evidence=[B=1,T,D]`, initializes/uses one owner fast-state row, and calls `core.scan_segment_many(...)`. Each timestep therefore consumes the candidate state produced by the preceding timestep. Replay indexing is correspondingly `tokens[0,row]`, and the committed owner state remains batch-size 1 regardless of segment length. This fixes the prior temporal-as-batch defect.

## Remaining blockers

### 1. HIGH — admitted source still is not byte-bound to the sealed capability

**Location:** `c5a_owner_segment.py:15-48,76-99`

No code in `95ef1bc...` changes `AdmissionAuthority.issue()` or `admit()`. The authority still serializes per-field raw bytes without binding every field's dtype/shape in one canonical schema, while `admit(cap, source=...)` still does not recompute the canonical serialization/digest of the supplied source and compare it to the issued capability before mutating indexes. A capability for source A can therefore still be paired with source B. Reusing `cap._seal` also remains sufficient to construct a modified capability object.

**Acceptance condition:** one canonical serializer for the complete source must include deterministic field order/name, every tensor dtype/shape and contiguous bytes; issuance and admission must use the same serializer. `admit()` must verify the exact supplied immutable source against the authority-issued record before any chronology/index/encoder/C5 work. Tampered owner/source/timestep/digest-bearing fields, copied seal, source substitution, and non-first-field dtype/shape mutation must fail before work.

### 2. HIGH — committed chronology / epoch / segment / N / terminal / reset lifecycle remains absent

**Location:** `c5a_owner_segment.py:61-99,128-135`

The remediation does not add committed per-owner epoch/last-step/segment cursor, reset, terminal state, or N grammar. Contiguity is still checked only inside the current pending transaction. After commit, a new transaction can admit an arbitrary unseen timestep; default `N=16`, N=1/3, non-terminal exactly-N, terminal `r=0`, `0<r<N`, `r=N`, old-epoch retry and new-epoch visibility ordering remain unimplemented.

**Acceptance condition:** explicit committed chronology record plus pending cursors; next admission must match committed/pending next step exactly; implement frozen N/default16 and terminal/reset/epoch semantics, with fail-before-C5 rejection of skip/out-of-order/cross-epoch/owner mismatch.

### 3. HIGH — abort/failure rollback still leaks `_identity_index`

**Location:** `c5a_owner_segment.py:82-99,134-135`

`_identity_index[identity] = cap.digest` is still mutated during `admit()` and remains global committed-looking state. `abort()` removes only `_pending_by_owner`; an aborted transaction therefore leaves identity/digest authority behind. The temporal-carry patch does not touch this path.

**Acceptance condition:** keep new identity/digest/chronology mutations in pending state until commit or roll them back exactly. Inject failure after admission and after materialization, abort, and prove committed state/reverse index/replay/chronology are byte/value-identical to pre-begin state and a retry is not rejected due to stale aborted state.

### 4. HIGH — frozen C5A acceptance matrix still has no behavioral evidence

**Location:** `c5a_owner_segment_test.py:1-40` unchanged from `aa88aaa...`

The child remediation adds no tests. The request still reports pytest blocked by missing `omegaconf`, so there is no passing C5A selector for this SHA. The existing three tests do not prove multi-timestep temporal carry, source byte-binding, B>1 owner permutation/row mismatch, stateless spy=0, actual `[B,256]` C5 input, ordinary outer backward plus finite/nonzero encoder/C5 gradients, pending replay, chronology-advance committed replay, complete rollback, N=1/3/16, terminal remainder matrix, reset/epoch lifecycle, duplicate commit, or fast-state parameter ownership.

**Acceptance condition:** add direct synthetic CPU wrapper tests for the full v0.6 matrix and run them in a working CPU environment. At minimum the temporal-carry remediation itself needs a deterministic N>=2 sequential-state test plus full-N -> shorter terminal remainder carry; all remaining design acceptance clauses must also be covered before closure. Report exact pytest selector count, py_compile and diff-check.

## Scope

Allowed remediation remains only the already-approved isolated C5A synthetic CPU files and adjacent tests plus root status/ledger bookkeeping. Any new root/child implementation SHA requires fresh same-SHA review.

Still prohibited: production/runtime Cosmos wiring; config/optimizer/checkpoint/trainer/inference/parallelization; GPU/CUDA/torchrun; real model/data/cache/checkpoint I/O; training/evaluation/inference; P4/P5; B2-T; LIBERO4IN1.
