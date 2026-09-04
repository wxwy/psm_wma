# ChatGPT re-review — R09-B TTT v0.3.2 C5A owner/segment CPU remediation @ ede084c

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root remediation SHA: `ede084c94019a6fc83728fc5a1229df6d5a872a3`
- child/Gitlink: `aa88aaacc1a1fad2d8348487fab260989c3aa067`
- request/bookkeeping SHA observed at re-review start: `0eb6fc2a8d4f69860e43e975090503fb85a7f776`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- superseded implementation pair: root `1ea0f6fa59753bb01d550795d176115aed5228bb` / child `76b27f2ce9bd17d35291261a62a9504cfe8f9b87`

Latest `V2` was rechecked immediately before review write and remained `0eb6fc2a8d4f69860e43e975090503fb85a7f776`, whose parent is the formal remediation root `ede084c...`. The bookkeeping SHA is not treated as the implementation target.

GitHub compare confirms child `aa88aaa...` is exactly one commit ahead of `76b27f2...` and modifies only the already-approved isolated `c5a_owner_segment.py` and `c5a_owner_segment_test.py`. Root `ede084c...` only updates SESSION/TODO status and advances the Gitlink. No production/runtime Cosmos wiring, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 scope drift was found.

## Findings

### 1. HIGH — segment chronology is implemented as batch-parallel independent fast states, not one owner state updated through time

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:101-118`

**Root cause:** `materialize()` encodes each pending timestep separately, appends `[1,256]` rows, concatenates them with `torch.cat(..., dim=0)` into `[T,256]`, initializes a fast state with batch size `T`, then calls `core.step_many()` exactly once. This treats the segment time axis as the C5 batch axis. Each timestep therefore gets an independent fast-state row instead of timestep `t+1` consuming the fast state updated at timestep `t`. The committed `_state_by_owner[owner_key]` consequently contains `T` state rows for one logical owner. A later segment/remainder also depends on matching that accidental previous segment length.

**Contract violation:** C5A v0.6 freezes chronology/segment materialization over one logical owner and the C5 path `... -> E_t[B,256] -> C5 K/V update + Q read_many`; segment rows must be applied sequentially to the owner fast state, e.g. as `[B,T,256]` through `scan_segment_many()` or an equivalent ordered series of `step_many()` calls. Batch rows represent independent owners/samples, not temporal positions of one owner.

**Acceptance condition:** represent the pending segment with an explicit time axis and apply C5 sequentially so every transition consumes the previous transition's candidate state. For one owner, committed fast state must remain batch size 1 regardless of N or terminal remainder. Add a deterministic N>=2 test where swapping timestep order changes the result and prove timestep 2 receives the post-update state from timestep 1; also cover a full-N segment followed by a shorter terminal remainder without state-shape mismatch.

### 2. HIGH — admitted source is still not byte-bound to the sealed capability; canonical digest is incomplete for the multi-tensor source

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:34-48`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:76-99`

**Root cause:** `AdmissionAuthority.issue()` records raw bytes for each tensor but only stores one global `source_shape`/`source_dtype` from the first tensor. Per-field dtype/shape are not part of the canonical serialization. More importantly, `admit(cap, source=...)` never recomputes the canonical bytes/dtype/shape for the provided source and never compares them with `cap.source_bytes/source_shape/source_dtype/digest`; it simply clones the caller's `source` and later feeds that clone to the encoder. Thus a capability issued for source A can be used to admit/materialize source B while retaining A's digest.

The `_seal` also does not bind the exact capability fields: code holding an issued capability can construct another `AdmissionCapability(..., _seal=cap._seal)` with modified fields. The current test intentionally does this for a conflicting digest, demonstrating that the seal alone is only producer-instance identity, not field-integrity authentication.

**Contract violation:** C5A v0.6 §2 requires fixed canonical little-endian digest binding over owner/source identity, source timestep, dtype, shape and contiguous immutable source bytes, plus capability/source-handle/input-row byte identity and rejection of copied/tampered capability fields before chronology/C5.

**Acceptance condition:** define one exact canonical serializer for the complete admitted raw source, including deterministic field name/order and each tensor's dtype, shape and contiguous bytes; authority issuance and admission validation must use the same serializer. `admit()` must recompute and compare the supplied/stored immutable source against the sealed capability before mutating any chronology/index or calling encoder/C5. Capability authenticity must bind the exact issued fields (e.g. opaque authority registry/token or equivalent), so copying the seal and changing any owner/source/timestep/digest-bearing field fails. Add fail-before-work spies for source substitution, non-first-field dtype/shape mutation, copied/tampered capability fields and forged digest.

### 3. HIGH — committed chronology/epoch/segment/N/terminal/reset lifecycle required by v0.6 is still absent

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:61-99`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:120-127`

**Root cause:** there is no committed per-owner epoch, last source timestep/episode step, segment id/cursor, reset operation, terminal flag or N grammar. Contiguity is checked only against the previous row inside the current pending transaction. After a commit, a new `begin(owner)` may admit any unseen timestep because there is no check against the committed owner's last timestep. There is no enforcement of non-terminal exactly N, default N=16, N=1/3 behavior, terminal `r=0`, `0<r<N`, `r=N`, old-epoch retry, or new-epoch visibility ordering.

**Contract violation:** C5A v0.6 §§2-4 explicitly require C5A to be the chronology authority, reject skip/out-of-order/cross-owner/epoch mismatches before C5, and implement the frozen N/default16 + terminal remainder/reset lifecycle.

**Acceptance condition:** add an explicit owner-local committed chronology record and pending transaction cursors/epoch/segment identity. New unseen admission must match the next committed/pending step exactly; cross-epoch/owner/skip/out-of-order inputs must reject before encoder/C5. Implement reset/epoch transition and terminal closure semantics exactly for N=1, N=3, default N=16 and `r=0`, `0<r<N`, `r=N`, including old-epoch retry ordering.

### 4. HIGH — abort/failure rollback is not atomic because pending identity authority leaks into committed lookup state

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:82-99`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:126-127`

**Root cause:** `_identity_index[identity] = cap.digest` is mutated during `admit()` before the pending row is fully validated, and `_identity_index` is global rather than part of the pending transaction. If the later contiguity check fails, or if a valid pending transaction is subsequently aborted, those identity entries remain. A later retry with corrected bytes for the same identity can be rejected as a conflicting digest even though the prior transaction never committed. `abort()` only removes `_pending_by_owner`; it does not restore identity/chronology side effects. The current test checks candidate fast-state isolation only and does not cover this leaked authority state.

**Contract violation:** C5A v0.6 requires committed C and pending P separation and states that failure/abort/duplicate commit must leave committed state unchanged; pending chronology/reverse-index effects must be promoted only on successful atomic commit.

**Acceptance condition:** keep all new identity/digest/chronology index mutations in P until commit, or snapshot/rollback them exactly. Inject failure after admission and after C5 materialization, then abort; prove committed owner state, committed reverse index, replay cache and chronology are value-identical to pre-begin state. Retrying the same logical transition after abort must behave as unseen/retry according to the frozen old-epoch semantics, not as a stale conflict from the aborted transaction.

### 5. HIGH — acceptance evidence remains far below the frozen C5A matrix; no runnable pytest PASS is provided

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:1-40`

**Root cause:** only three tests exist. They cover one single-step commit/replay, one conflict/forgery case, and candidate-state absence after abort. They do not exercise multi-timestep temporal accumulation, B>1 owner gather/scatter/permutation and row mismatch, exact source byte-binding, stateless-readout spy=0, actual C5 input `[B,256]`, ordinary outer backward and finite/nonzero gradients to encoder + C5 Q/K/V/slot/W0, pending replay, chronology-advance committed replay, rollback of all committed/index state, N=1/3/16, terminal r matrix, reset/epoch behavior, duplicate commit, or fast state absence from `named_parameters()`.

The closure request also explicitly reports that targeted pytest could not run because existing conftest import lacks `omegaconf`; therefore no passing CPU selector evidence exists for this remediation target.

**Contract violation:** C5A v0.6 §4 requires the complete synthetic CPU acceptance matrix listed above; `py_compile` and diff-check cannot substitute for behavioral acceptance.

**Acceptance condition:** add direct C5A wrapper tests that execute `issue/admit -> materialize -> ordinary outer backward -> commit/abort -> replay/reset` through the real Gate implementation with fail-before-work spies. Cover the complete v0.6 matrix and run it in a working CPU environment, reporting the exact selector count plus py_compile/diff-check.

## What the remediation did close

Compared with `76b27f2...`, this remediation materially improves the direction:
- caller-provided encoded E is no longer stored in pending state;
- pending raw source is graph-free cloned data and `LocalEvidenceEncoder` is rematerialized during `materialize()`;
- per-owner pending/committed containers now exist;
- candidate fast state is kept pending and committed state is detached/cloned;
- committed replay is detached/cloned and source-identity conflict lookup exists.

These are useful partial closures, but they do not satisfy the full frozen C5A contract because the temporal axis, source-byte authentication, committed chronology lifecycle, rollback authority and acceptance matrix remain incorrect/incomplete.

## Required next submission

A new remediation must remain within the already-approved isolated C5A CPU boundary unless design scope is explicitly reopened. Any child/root implementation SHA change requires a fresh same-SHA review; this `REQUEST_CHANGES` cannot be inherited as an approval.

Still prohibited:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
