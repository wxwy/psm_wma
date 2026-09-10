# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer Implementation Design v0.4

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`  
**Formal root:** `7a678c28d4c9b47ffe6e9e9df0659b843fc49f81`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.4.md`  
**Previous same-Gate formal pair:** `4e77930d3ce414c3ab233c5021f04c0697f2a56d / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.4.md:17)`

## 1. Repository-truth lock

- Latest `origin/V2` at review start is request/ledger HEAD `34f997f274cce1dcba73d0b8e801a2f65e27f0fd`; it declares the exact formal pair above and is not itself the formal design target.
- The formal root tree stores `cosmos-framework` exactly at Gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- The child commit is reachable/readable and unchanged from the previous same-Gate review.
- Incremental compare `4e77930... -> 7a678c2...` is root-docs only for this technical remediation; the new technical artifact is implementation design v0.4. Intervening review/Inbox/SESSION/TODO commits are persistence/bookkeeping and do not replace formal authority.
- No project code, tests, real I/O, CUDA/GPU, training, evaluation or inference was executed in this Design review.

## 2. Previous blocker lifecycle

### CLOSED — pre-scan expected authority and post-scan actual `result.gathered` are now correctly separated

The previous review's sole HIGH was that v0.3 required the actual `result.gathered` to participate in checks that were also required to fail before `adapter.scan()`, even though the actual result is created only inside `scan()`.

v0.4 closes that temporal defect:

1. pre-scan validation now derives an immutable `expected` traversal only from the exact frozen request/member/`SegmentBatch`, chronology/provenance and logical raw source;
2. that pre-scan expected traversal does not read or manufacture `CanonicalProductionScanResult`, `NativeConsumerBatch`, Local prefixes, or adapter state;
3. only after the pre-scan authority checks pass does the design call `adapter.scan(request)`;
4. the actual `result.gathered.item_count` / `identities` are then compared against the already-frozen expected traversal;
5. any post-scan mismatch uses the already-reviewed exact-once `abort_scan(request,result)` disposition before failure.

This is source-consistent with current `NativeConsumerBatch.from_segment()`, which independently constructs the stream-major expected `(slot_id, episode_id, step)` sequence from the frozen member and checks the actual gather only after scan inputs exist.

The prior HIGH's main pre/post-scan ordering issue is CLOSED.

## 3. Current blocker

### HIGH — the carrier raw-row storage ABI remains contradictory between retained v0.1 authority and v0.4

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.4.md:17`

v0.4 says that the `CanonicalRawRowCarrier` raw source **“保持 v0.1 logical [B,T] shape”**, while the file header simultaneously states that v0.1's typed-carrier contract remains effective. But the concrete v0.4 declaration is:

```text
logical_raw_rows: tuple[CanonicalRawNativeRow | None, ...]  # row-major b*T+t; PAD=None
row_model_samples: tuple[Mapping[str, Any] | None, ...]     # same logical index
```

and its validation requires `logical shape = B*T`.

The retained v0.1 typed-carrier contract is different and explicit:

```text
raw_rows: tuple[tuple[Mapping[str, Any] | None, ...], ...]  # logical [B,T]
```

with outer width `B`, inner width `T`, and PAD represented at `[b][t]`.

This is no longer the old gathered-vs-logical stage ambiguity: v0.4 correctly keeps the source stage logical and the actual scan gather post-scan. The remaining problem is the storage ABI itself. The document currently leaves two incompatible authoritative implementations for the same carrier:

- nested two-dimensional `raw_rows[B][T]` from retained v0.1; or
- flattened row-major `logical_raw_rows[B*T]` from v0.4.

A child implementation cannot satisfy both exact field/shape contracts. This matters directly to the promised pre-scan PAD/source/order validation and to the acceptance tests, so it must be resolved before `APPROVE_TO_IMPLEMENT...`.

**Violated frozen contract**

- implementation design must freeze one exact typed carrier ABI before child code is authorized;
- logical `[B,T]` vs gathered-valid stages must remain unambiguous, including the actual storage representation used by validation;
- foreign/order/PAD checks must be deterministic from a single authoritative field shape rather than depend on an implementer-chosen reinterpretation.

**Exact closure condition**

Make one narrow docs-only choice and state it explicitly:

1. **Retain v0.1 nested ABI:** keep `raw_rows: tuple[tuple[..., ...], ...]` with exact outer `B` / inner `T`; derive `flat=b*T+t` only as an expected traversal index and, if useful, define a separate flattened view that is not a second source of truth; or
2. **Adopt v0.4 flat ABI:** explicitly supersede the v0.1 `raw_rows[B][T]` field/shape, define `logical_raw_rows: tuple[..., ...]` as exact length `B*T`, and state that this flat row-major representation is the sole carrier raw-row storage authority going forward.

Whichever option is chosen, align `row_model_samples`, PAD checks, source-object attribution, `expected.logical_indexes`, and CPU/static fixtures to that one representation. No data-side, packer, trainer, GPU or runtime expansion is required.

## 4. Non-blocking findings

- The previous actual-result-before-scan HIGH is CLOSED.
- v0.3's `local_memory` key-presence fail-closed and pre/post `get_data_and_condition()` Local-neutral assertions remain valid.
- The one canonical Local-prefix adaptation remains sourced only from the exact actual `result.gathered.local_prefixes` after post-scan equality.
- The exact-once `abort_scan()` lifecycle remains an adequate CPU/static disposition for actual mismatch, helper exceptions and intentional pre-packer hard-stop.
- CP remains pre-scan fail-closed.
- The four-file whitelist remains narrow and sufficient once the carrier storage ABI is made singular.
- No new blocker is raised against No-Local parity, legacy zero-call, source attribution, expected traversal derivation, post-scan equality, or the prohibition on real I/O/GPU/training.

## 5. Blocker lifecycle / scope

Current blocker count: **1 HIGH**.

Authorized next action: docs-only remediation of this same implementation-design Gate.

Not authorized: child implementation under this Gate, real producer/data pipeline changes, dataset/dataloader/collate/packer/config/optimizer/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native training/evaluation/inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.4.md:17)`
