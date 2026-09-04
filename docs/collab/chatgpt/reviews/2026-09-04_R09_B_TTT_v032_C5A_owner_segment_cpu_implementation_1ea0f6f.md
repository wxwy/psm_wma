# ChatGPT review — R09-B TTT v0.3.2 C5A owner/segment synthetic CPU implementation @ 1ea0f6f

Date: 2026-09-04

## Verdict

**REQUEST_CHANGES**

Formal Gate:
`G0-R09-B-TTT-V032-C5A-CHRONOLOGY-OWNER-SEGMENT-IMPLEMENTATION`

Formal implementation pair:
- root implementation SHA: `1ea0f6fa59753bb01d550795d176115aed5228bb`
- child/Gitlink: `76b27f2ce9bd17d35291261a62a9504cfe8f9b87`
- implementation parent/root baseline: `ef78d3e5cd6093f1dbca98265573e87645c8165e`
- child baseline: `6de8f2056c62cb10c89791d70335a44a6ab232fc`
- request/bookkeeping SHA observed at review start: `88fc7dcec9716860fe23a772482b926cdf08656a`
- frozen C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`

Latest `V2` observed before review write was `88fc7dcec9716860fe23a772482b926cdf08656a`; it is bookkeeping whose parent is the formal implementation root `1ea0f6f...`, not a replacement implementation target. GitHub compare confirms the root implementation changes only `SESSION.md`, `TODO.md`, and the child Gitlink; child `76b27f2...` is exactly one commit ahead of `6de8f20...` and adds only `c5a_owner_segment.py` and `c5a_owner_segment_test.py`. No production/Cosmos/config/GPU/training scope drift was found.

A literal local `git fetch origin V2` was attempted in the review runtime but the container could not resolve `github.com`; branch/head, commit ancestry, Gitlink and diffs were therefore independently locked through the GitHub connector/API instead.

## Findings

### 1. HIGH — `COLLECT_RAW` stores caller-supplied encoded tensors and admission is not bound to the rematerialized source

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:38-42`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:72-84`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:87-99`

**Root cause:** `_Pending.rows` is declared as `list[tuple[AdmissionCapability, torch.Tensor]]`; `admit(..., encoded=...)` accepts an arbitrary encoded tensor and stores it in `_pending.rows`. This directly violates the frozen `COLLECT_RAW` rule that pending state contains only immutable raw source/capability/source-key and never graph-bearing `E_t`. The stored `encoded` tensor is then ignored by `materialize()`, which rematerializes a separate caller-provided history tensor bundle without any byte/digest binding back to the admitted capability/source.

**Contract violation:** C5A v0.6 §3 requires `COLLECT_RAW` to store only immutable source/capability/S and `MATERIALIZE_PENDING` to rematerialize `LocalEvidenceEncoder -> E_t[B,256]` from that admitted immutable source inside the atomic segment. It also requires capability/source-handle/input-row byte identity.

**Acceptance condition:** remove graph-bearing/caller-encoded tensors from pending state and from the admission API. Pending rows must retain only the immutable admitted source/capability/S plus owner/chronology metadata. `materialize()` must deterministically rematerialize each admitted row from exactly that stored immutable source and reject any source/input-row mismatch before `LocalEvidenceEncoder`/C5. Add a spy-based test proving no graph-bearing `E_t` is retained across COLLECT_RAW and that a byte-mismatched materialization input fails before encoder/C5.

### 2. HIGH — canonical digest/authenticity/conflicting-digest rejection from v0.6 is not implemented

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:16-34`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:60-65`

**Root cause:** `AdmissionCapability` is freely caller-constructible and authenticity is reduced to `provenance_class == "R08_COMPLETED_CAUSAL"` plus `isinstance(source_bytes, bytes)`. The digest serializes owner/source identity, decimal-string timestep, and source bytes only; it omits the frozen dtype and shape fields and does not implement the fixed canonical source serialization. `_lookup()` indexes the full `(owner, source_identity, timestep, digest)` key only, so the same owner/source/timestep with a different digest is treated as a new unseen source instead of a conflicting digest that must be rejected.

**Contract violation:** C5A v0.6 §2 requires trusted R08 capability semantics, canonical little-endian length-prefix SHA-256 over owner/source identity, source_timestep, dtype, shape, contiguous immutable source bytes, capability/source/input-row byte binding, and explicit conflicting-digest rejection before chronology allocation/C5.

**Acceptance condition:** use/represent an unforgeable trusted-R08 admission capability boundary (a copied dataclass or caller-set provenance string must not pass); implement the exact frozen canonical serialization including dtype and shape; maintain a reverse identity index sufficient to reject a different digest for the same owner/source/timestep; and prove copied/tampered fields, forged digest, source-handle/input-row byte mismatch, and conflicting digest all reject before chronology allocation, encoder, or C5 via spies.

### 3. HIGH — transaction is not atomic: `materialize()` commits fast state before `commit()`, and `abort()` cannot roll it back or cut the graph

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:97-104`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:106-114`

**Root cause:** `materialize()` immediately sets `self._state = state` and increments `c5_write_count`; `commit()` only copies replay records and clears pending; `abort()` only clears `_pending`. Therefore an aborted/failed transaction leaves the post-C5 fast state installed and the write count advanced. `commit()` also does not detach the committed fast state, so a graph-bearing `ContinualTTTFastState` can cross the segment boundary.

**Contract violation:** C5A v0.6 §3 requires committed C and pending P separation, failure/abort/duplicate-commit to leave C unchanged, committed replay graph-free, and no cross-segment graph; §4 requires one atomic backward before commit/detach for terminal remainder semantics.

**Acceptance condition:** keep candidate fast state/write accounting entirely in pending transaction state until successful outer backward + commit. `abort()`/failure must restore bitwise/value-equivalent committed C and counters with no leaked graph. Successful commit must promote only the pending candidate and detach/clone the committed fast state so every committed state tensor has `grad_fn is None`. Add failure injection after C5 but before commit, abort, duplicate-commit, and next-segment tests proving C/counters unchanged on failure and no cross-segment graph.

### 4. HIGH — owner/row/chronology/segment contract is largely absent; current implementation is effectively single-global-owner and B=1

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:49-58`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:67-84`
- `cosmos_framework/model/generator/mot/c5a_owner_segment.py:97-100`

**Root cause:** the wrapper has one global `epoch`, `last_step`, `_state`, `_pending`, and `_committed`, with no owner-local committed registry/gather-scatter. Different owners can be appended into the same pending transaction. Chronology validation only checks `source_timestep > previous_source_timestep`, so skipped timesteps, cross-owner/epoch, owner/envelope/state mismatches and row mismatch are not represented/rejected. `materialize()` initializes C5 state with batch size `1` regardless of `evidence_history.shape[0]`, while passing a valid mask with the full batch size; this cannot satisfy batch permutation/owner gather-scatter and fails for B>1 against the C5 state-shape contract.

**Contract violation:** C5A v0.6 §2 requires owner-local chronology authority, cross-owner/epoch rejection, out-of-order/skip rejection, owner gather/scatter, batch-row permutation equivalence and row-mismatch rejection. §4 requires N/default16 and terminal/reset lifecycle semantics.

**Acceptance condition:** implement owner-keyed committed/pending state and chronology, deterministic gather/scatter for batched owners, exact unseen-step allocation with skip/out-of-order/cross-owner/epoch/row-mismatch rejection before C5, and state batch sizing consistent with the gathered owner rows. Add B>1 permutation-equivalence + row-mismatch tests and explicit owner A/B independence tests. Implement/test N=1,3,16/default16, terminal `r=0`, `0<r<N`, `r=N`, reset/epoch transition and old-epoch retry behavior.

### 5. HIGH — required acceptance evidence is not present; the three tests do not execute the implemented materialization/transaction path

**Location:**
- `cosmos_framework/model/generator/mot/c5a_owner_segment_test.py:11-44`

**Root cause:** only three tests exist. Two directly mutate the private `_pending.replay` dictionary instead of obtaining replay through `materialize()`, and none calls `materialize()`. Consequently the current tests cannot detect the non-atomic `_state` mutation, B=1 state bug, Encoder→E_t→C5 topology, C5 input shape, gradients, source-byte binding, owner permutation/mismatch, rollback, terminal/reset lifecycle, N=1/3/16, or fast-state ownership. The closure request correctly states targeted pytest did not run because the environment lacks `omegaconf`, so no passing pytest evidence exists either.

**Contract violation:** C5A v0.6 §4 explicitly requires CPU coverage for stateless spy=0 + C5 input `[B,256]`; all hostile admission classes; canonical digest/byte-binding; permutation equivalence + row mismatch; lookup-before-allocation including replay after chronology advance; pending/committed no-graph replay; rollback; N=1/3/16; all terminal remainder cases; reset; and fast state absent from `named_parameters()`. §3 also requires ordinary outer backward with finite nonzero gradients reaching the evidence encoder and C5 slow/Q/K/V/slot/W0 parameters.

**Acceptance condition:** replace/expand the current helper-level tests into direct production-of-this-Gate CPU fixtures that exercise `admit -> materialize -> backward -> commit/abort/replay/reset` through the real C5A wrapper, with spies for fail-before-work and write counts. The full frozen acceptance matrix must pass in a runnable CPU environment; `py_compile`/`diff-check` alone is insufficient for closure.

## Scope findings

Accepted:
- child diff is exactly one commit ahead of C5 baseline and adds only the two approved isolated C5A CPU files;
- root implementation only advances the Gitlink plus SESSION/TODO status;
- no Cosmos production forward/packer/attention wiring, config/optimizer/checkpoint/trainer/inference changes, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 work was found.

## Required next submission

A remediation commit must remain inside the already approved C5A synthetic CPU boundary (the two C5A files plus root status/ledger docs unless a new design explicitly expands scope), implement the acceptance conditions above, and provide a new root implementation SHA + child/Gitlink SHA. Because the implementation SHA changes, it requires a fresh same-SHA review; this verdict must not be reused.

Still prohibited even after remediation closure unless separately frozen/approved:
- production/runtime Cosmos wiring;
- config/optimizer/checkpoint/trainer/inference/parallelization;
- GPU/CUDA/torchrun and real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5, B2-T and LIBERO4IN1.
