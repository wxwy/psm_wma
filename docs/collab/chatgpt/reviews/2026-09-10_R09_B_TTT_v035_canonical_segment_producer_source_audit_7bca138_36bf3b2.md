# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer Source Audit v0.1

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-SOURCE-AUDIT`  
**Formal root:** `7bca13823f448ef08faa21d7d16f035abe7ecfc6`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_source_audit_v0.1.md`  
**Prior approved authority:** producer ABI v0.2 at `c57e77c42b13e0a397d42c5d7979c8382b1ee144 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_source_audit_v0.1.md:22)`

## 1. Repository-truth lock

- Latest `origin/V2` was relocked during review at bookkeeping/status HEAD `78af6e5e05dc1f1d7697acf2a25c42fe2a335059`; that commit only records review-waiting state in `SESSION.md` / `TODO.md` and does not replace the formal target.
- The Codex request/ledger commit is `0897acb30957c0ef04026147c2f6aa87bdd19243`; it declares formal root `7bca13823f448ef08faa21d7d16f035abe7ecfc6` and child/Gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- The formal root tree stores `cosmos-framework` exactly at gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- The child is reachable/readable and unchanged from the prior approved producer-ABI Design pair, so this is a fresh incremental **source-audit** review; no repeated child implementation verdict is inherited.
- No project code, tests, real I/O, CUDA/GPU, training, evaluation or inference was executed. This review independently inspected the source locations claimed by the audit.

## 2. What the source audit gets right

The majority of the audit maps current child source correctly:

1. `joint_dataloader.py:128-207,793-821` shows the current collate/packed-dataloader field shapes and confirms that collate preserves raw/native values rather than materializing `GenerationDataClean`, model-generated text indexes or diffusion timesteps.
2. `canonical_segment_production_adapter.py:112-145`, `canonical_segment_adapter_scheduler.py:293-321` and `local_memory_segment.py:64-106` correctly establish the existing canonical scan/gather authority: registered encoder/core scan -> `NativeConsumerBatch.from_segment()` -> stream-major valid payload/prefix/identity gather, with exact count checking, PAD exclusion and `None` Local only for valid S0.
3. `omni_mot_model.py:1008-1053,1100-1150,1295-1327` correctly shows that ordinary `_prepare_training_data()` / `_get_training_inputs()` is not Local-neutral: `_inject_local_history()` is unconditional and enabled TTT reaches `_ttt_local_memory_tokens()` / legacy `TTTLifecycle`; ordinary CP owner preparation therefore cannot simply be reused as the canonical safe path.
4. The audit correctly leaves diffusion timestep/noise/packer/loss ownership model-side and post-preparation, and correctly preserves the No-Local ordinary path.
5. The audit does not authorize child implementation or broaden runtime/GPU/I/O scope.

Those findings are not blockers.

## 3. Current blocker

### HIGH — §2.1 proves collate field preservation, but not the required canonical raw-row extraction/carrier seam

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_source_audit_v0.1.md:22`  
**Related audit text:** §2.1 lines 18-22 and §3 item 1.  
**Relevant live source:**
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:26-33` — `CanonicalProductionSegmentRequest` carries scheduler/plan/transaction/member/member_index/`SegmentBatch`, but no collate `data_batch`, raw-row tuple or typed raw-row capability.
- `cosmos_framework/model/generator/omni_mot_model.py:1394-1400` — `_canonical_production_segment_forward()` receives only `(request, iteration)`.
- `cosmos_framework/model/generator/omni_mot_model.py:1425-1431` — `training_step()` still has the collated `data_batch`, resolves the canonical request, then calls `_canonical_production_segment_forward(canonical_request, iteration)` without passing that raw batch.
- `cosmos_framework/model/generator/mot/local_memory_segment.py:55-91` — `SegmentBatch.consumer_payload` is merely opaque `Any`; validity rules prove presence/absence but do not prove that each payload is the exact collate-native row or retains all fields required by the proposed model-safe materialization builder.
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:112-137` / `canonical_segment_adapter_scheduler.py:293-321` — the existing production adapter can scan and gather the opaque `consumer_payload`, but no current contract types that payload as `CanonicalRawNativeRow` or binds it to a collate-row snapshot.

**Root cause**

Producer ABI v0.2 explicitly required the source audit to identify both the raw fields that truly exist after collate **and the minimal immutable raw-row extraction seam**. The current audit establishes only the first half. It points to `custom_collate_fn()` and packed-dataloader shapes, then concludes at line 22 that `CanonicalGatheredRawBatch.raw_rows` “can be” opaque collate-truth snapshots and that no dataloader/collate change is needed.

That conclusion skips the actual lifecycle gap. Current canonical production has no source-backed carrier that takes the logical `[B_stream,T]` consumer rows from collate/segment construction into the model canonical branch:

- the request does not contain raw rows;
- the current canonical model forward drops the still-live `data_batch` from its call signature;
- `SegmentBatch.consumer_payload` is intentionally opaque and only constrained to be non-`None` for valid consumers;
- current CPU/static tests even use arbitrary string payloads, demonstrating that the existing contract does not mean “exact collate row”.

Therefore “collate preserves these fields” is insufficient to establish `CanonicalGatheredRawBatch.raw_rows`. Without an audited carrier/extraction boundary, the next implementation design would have to invent where `[B,T]` raw rows are captured, how they survive segment accumulation, and how they are identity-bound to `result.gathered`. That is exactly the source-level ownership question v0.2 required this Gate to answer rather than leave implicit.

This is not a requirement to implement a producer now, nor evidence that dataloader/collate must change. It is a requirement for the **source audit** to state accurately that the current carrier is absent (unless a real one is found) and to map the smallest existing call boundary/owner at which a later design may introduce it.

**Violated frozen contract**

- Producer ABI v0.2 §3.1: source audit must give `file:line` for the actual raw fields **and minimal immutable raw-row extraction seam**.
- Source audit findings must distinguish current repository truth from proposed future design; they may not infer an existing ABI from field availability alone.
- `CanonicalGatheredRawBatch` row/prefix/identity/count must be bound to the same frozen member/segment/gather authority; no foreign/reconstructed row source or silent reinterpretation of opaque `consumer_payload`.
- Source audit approval must be sufficient to constrain the next implementation design rather than defer a material ownership/lifecycle choice to implementation.

**Exact closure condition**

Revise this docs-only source audit narrowly so it does all of the following:

1. Explicitly inspect and record the current carrier truth: `CanonicalProductionSegmentRequest` has no raw-row field; `_canonical_production_segment_forward()` receives no `data_batch`; `SegmentBatch.consumer_payload: Any` is not by itself proof of collate-row identity/type.
2. Identify the smallest source-backed capture/ownership boundary available to a later implementation design. For example, if the intended seam is the still-live collated `data_batch` at `training_step()` before canonical diversion, say so explicitly and map the exact `file:line`; then state how the later design must retain/associate the required logical `[B,T]` rows through segment construction. Do **not** claim this mechanism already exists if it does not.
3. Alternatively, if a current segment producer really does store exact collate-row objects into `consumer_payload`, cite that concrete owner/path and prove object/field identity and `[B,T]` alignment. The current `Any` declaration and synthetic string tests are not such proof.
4. Bind any future raw-row carrier to exact `member` / `SegmentBatch` / `result.gathered` identities and stream-major cardinality. `local_prefixes` must continue to come only from the canonical scan/gather authority; they must not be reconstructed from raw rows.
5. State the scope consequence precisely: if the minimal carrier can be added only in an already-authorizable model/producer seam, the next docs-only implementation design may freeze it; if it requires dataloader/collate/dataset/packer changes, this audit must fail closed and route to a separate design Gate.
6. Preserve the otherwise-correct legacy-injection, CP, Local-prefix, timestep/noise/loss, S0/PAD and No-Local findings.

## 4. Blocker lifecycle / scope

- Prior producer ABI v0.2 Design approval remains valid; this review does not reopen its closed lifecycle HIGH.
- Current SOURCE-AUDIT blocker count: **1 HIGH**.
- No additional blocker is raised against canonical scan/gather authority, S0/PAD/order/count, legacy-edge mapping, No-Local parity, model-owned timestep/noise/loss, or the docs-only scope.

This verdict authorizes only narrow docs-only remediation of the source audit's raw-row extraction/carrier map.

Not authorized: implementation design approval, producer/builder implementation, child production changes, dataset/dataloader/collate/packer/config/optimizer/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 5. Exact verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_source_audit_v0.1.md:22)`
