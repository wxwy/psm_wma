# ChatGPT independent review — R09-B TTT v0.3.5 canonical CPU/static implementation

**Date:** 2026-09-08

**Gate:** `G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION`

**Formal target:**
- root implementation SHA: `0d8db576534c92a72fc1ee98c2babc4a835897a5`
- child/Gitlink SHA: `89f9fc83c5c9ad9f7dea405b9f2ab025d726fd37`
- approved implementation-design baseline: root `1f6c0bad0faa4aabae1c71b01738ad95a4ea902c` / child `80aec090688e3c710c41e1dfd86b6500773db2c7`

## Verdict

`REQUEST_CHANGES`

The child diff is correctly limited to the four files authorized by implementation design v0.3. The canonical feature inventory and compact-row K/Q/V scan direction are partially implemented, and the previous v0.2 feature-owner HIGH remains closed. However this formal implementation pair does not yet satisfy the frozen v0.3/v0.2 CPU/static contract and cannot close the Gate.

## Blockers

### 1. HIGH — shifted SegmentBatch ABI does not fail closed for non-S0 valid consumers

**Files:**
- `cosmos_framework/model/generator/mot/local_memory_segment.py:64-73`
- `cosmos_framework/model/generator/mot/local_memory_segment.py:75-92`

**Root cause:** `SegmentBatch.validate()` enforces only `evidence_valid => evidence_source_step == consumer_step - 1`. It does not enforce the converse required by the frozen shifted ABI: every valid consumer with `consumer_step > 0` must have valid previous evidence. Therefore a valid step1+ row with `evidence_valid=False` and `evidence_source_step=-1` is currently accepted. `gather_consumers()` likewise converts any `local_present=False` valid row to `None`, so Local absence is not restricted to S0.

**Violated contract:** implementation design v0.2 §2, inherited unchanged by v0.3 §3: valid S0 must have absent evidence; every other valid row must bind `source_step = consumer_step - 1`; S0 Local is `None`, other valid consumers carry `[K_local,32]` Local.

**Acceptance:** fail closed unless `(consumer_valid & consumer_step==0) => !evidence_valid` and `(consumer_valid & consumer_step>0) => evidence_valid & source_step==consumer_step-1`. Bind `local_present` consistently so only valid S0 may produce Local `None`; valid non-S0 missing Local must fail rather than silently become absent. Add negative CPU fixtures for valid non-S0 missing evidence/source and valid non-S0 missing Local, while preserving PAD exclusion/no-read behavior.

### 2. HIGH — required scheduler / GA transaction / recovery implementation is absent

**File:** `cosmos_framework/model/generator/mot/local_memory_segment.py:95-168`

**Root cause:** the file currently stops at a minimal `GAWindowPlan` (members, planned counts, attempt, objective) and a simple weighted-deficit `RankLocalSegmentScheduler`. The frozen design requires the same file to implement the pure-Python transaction owner with plan-chain identity, immutable suffix snapshot, first/later-member failure disposition, one suffix recovery, `LOCAL_MEM_RETRY_EXHAUSTED`, partial slow-grad discard semantics, GradScaler-skip separation, and episode-scheduler vs slow-LR-scheduler behavior. The scheduler snapshot must also retain the frozen reconstruction state (stable slot/category/episode/cursor, queue seed/epoch/permutation, segment/provenance digests) and support tail PAD, terminal/rebind, `training_stream_end`, and same-snapshot rebuild. None of those mechanisms is present in this formal child.

**Violated contract:** implementation design v0.2 §4-§5, explicitly inherited by v0.3 §3.

**Acceptance:** implement the frozen pure-Python transaction/recovery state machine and complete scheduler snapshot/rebuild semantics within the approved `local_memory_segment.py` scope, without trainer/dataset/production wiring. Add the required synthetic fixtures for deterministic snapshot/admission/exposure, tail PAD, terminal/rebind/`training_stream_end`, planned==actual, first/later failure, A/B/C/D retry terminal, and GradScaler-skip episode-vs-slow-LR behavior.

### 3. HIGH — invalid-first contract is not end-to-end; invalid rows are still read/finite-checked before masking

**Files:**
- `cosmos_framework/model/generator/mot/local_evidence.py:146-159`
- `cosmos_framework/model/generator/mot/local_evidence.py:684-705`
- `cosmos_framework/model/generator/mot/local_evidence.py:451-467`

**Root cause:** canonical `LocalEvidenceEncoder.encode_segment()` finite-checks and projects the full dense `[B,T]` visual/action tensors and has no valid-row seam. Separately, `scan_segment_masked_many()` calls `_validate_state(state, batch)` before selecting `valid[:,t]`; `_validate_state()` performs `torch.isfinite(...).all()` on every fast-state row. Thus the current public pieces do not implement the frozen rule that all-invalid/mixed-invalid rows reach neither encoder/finite-check nor read/write participation before compact-row selection. The existing masked-scan test only inserts NaNs in invalid *evidence* with finite initial state; it does not observe encoder participation or the pre-mask state finite-check.

**Violated contract:** implementation design v0.2 §3 and v0.3 §3: select valid rows first; all-invalid must not access evidence, encoder, finite check, K/Q/V projection, read or write; mixed batches operate only on the compact valid sub-batch and preserve invalid state bytes.

**Acceptance:** provide an allowed synthetic orchestration seam that selects valid rows before canonical encoder finite-check/projection, and separate structural state validation from value finite-checks so invalid rows are not value-read before compact selection. Add spy/counting CPU evidence for encoder, finite-check, K/Q/V projection, read and write participation on mixed and all-invalid timesteps, including byte-preservation of invalid fast-state rows.

### 4. MEDIUM — legacy `LocalEvidenceEncoder.forward` signature/error behavior regressed

**File:** `cosmos_framework/model/generator/mot/local_evidence.py:90-98`

**Root cause:** the legacy signature changed from required keyword-only `history_age_steps`, `history_dt_s`, then `history_mask` to `history_mask` followed by optional `history_age_steps=None` / `history_dt_s=None`. This changes the frozen public signature and missing-argument error behavior for default/legacy construction.

**Violated contract:** implementation design v0.3 §2 requires default/legacy construction to preserve module tree, forward signature, parameters/buffers, numerics and error behavior compatibly; canonical use is through the separate `encode_segment()` path.

**Acceptance:** restore the pre-`89f9fc8` legacy forward signature/requiredness exactly while retaining canonical fail-closed behavior and `encode_segment()` as the canonical route. Add explicit signature/error-behavior regression plus legacy `state_dict`/numeric-output parity evidence.

### 5. MEDIUM — mandatory CPU acceptance Evidence is incomplete and pytest has not run

**Files:**
- root `SESSION.md:9`
- `cosmos_framework/model/generator/mot/local_memory_segment_test.py:35-77`
- `cosmos_framework/model/generator/mot/local_evidence_test.py:244-255`

**Root cause:** the formal root explicitly records that pytest was not collected. Moreover the committed tests cover only a small subset of the frozen matrix: current segment tests cover basic shifted gather, one step0 rejection/count mismatch, and simple scheduler exposure; the masked test does not directly observe encoder/K/Q/V/read/write participation. Required transaction/recovery, tail/rebind/end, GradScaler-skip, full dual-mode legacy/canonical evidence, and several other §5 fixtures are absent.

**Violated contract:** implementation design v0.3 §2-§3 and inherited v0.2 §5 require the full synthetic CPU matrix plus `py_compile`, related pytest, and both diff-checks to PASS. Test count or uncollected tests cannot close the Gate.

**Acceptance:** after code blockers are fixed, add the complete frozen CPU fixture matrix and provide an actual PASS run of the related CPU pytest set in a supported environment. `py_compile`/diff-check PASS may be retained as static evidence but cannot substitute for pytest behavioral Evidence.

## Scope / closed items

- **CLOSED:** v0.2 feature-owner blocker. The canonical owner is now `LocalEvidenceEncoder` with `EvidenceFeatureConfig`; no `SegmentEvidenceEncoder` was introduced.
- **CLOSED:** child diff scope is exactly the four approved files; no dataset/trainer/model-forward/config/optimizer/checkpoint/production projector file was modified.
- **PARTIAL, not closure:** canonical disabled names are absent from the tested canonical `state_dict`; compact-row K/Q/V projection is present in `scan_segment_masked_many()`; S0/PAD opaque-payload gather happy-path exists.

No real model/data/cache/checkpoint I/O, GPU/CUDA/torchrun, training, evaluation or inference was performed or authorized by this review.

This verdict binds only formal pair `0d8db576534c92a72fc1ee98c2babc4a835897a5` + `89f9fc83c5c9ad9f7dea405b9f2ab025d726fd37`. Review/bookkeeping commits do not change the formal implementation target. The Gate remains open, and later production wiring/runtime/trainer/config/optimizer/checkpoint/GPU/training Gates remain unauthorized.
