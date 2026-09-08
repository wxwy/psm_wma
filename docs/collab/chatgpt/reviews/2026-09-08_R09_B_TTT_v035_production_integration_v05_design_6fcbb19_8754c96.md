# ChatGPT independent review — Local Memory v0.3.5 production integration implementation design v0.5

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root design SHA: `6fcbb19715e39ade8c5a5d568b2b200346e935b8`
- child/Gitlink SHA: `8754c96a6bde002269751eca55c01dee694f6caa`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION-DESIGN`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC`

This is a fresh incremental design review. The already-closed v0.4 synthetic CPU/static transaction implementation remains CLOSED and is not technically re-reviewed here. The v0.5 direction is otherwise sound: it keeps the old lifecycle/materialize/C6 paths out of the new route, reuses the existing canonical `ContinualTTTLocalMemoryCore.scan_segment_masked_encoded_many()` and `SegmentBatch.gather_consumers()` seams, keeps trainer as the unique loss/backward/transaction owner, and retains the CPU/static-only prohibition boundary.

## Current blockers

### 1. HIGH — sidecar cursor/identity continuity is underfrozen and can create a second chronology authority

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:26,42,58`
- `cosmos_framework/model/generator/mot/local_memory_segment.py:24-36,85-105,155-162,271-320`

**Root cause:** v0.5 says `LocalMemorySegmentSidecar` is keyed by stable slot/episode/source identity, reads state only for a continuous cursor, and must fail closed on cursor/source mismatch. But the frozen adapter entry `CanonicalLocalMemorySegmentAdapter.scan(segment, *, state_in)` supplies no canonical segment cursor/`SegmentIdentity`, while `SegmentBatch` itself contains slot/episode/category plus `SegmentProvenance` and per-consumer `consumer_step`, not the scheduler's segment cursor. `SegmentBatch.gather_consumers()` emits consumer identities `(slot_id, episode_id, consumer_step)`; those are consumer-step identities, not `SegmentIdentity.cursor`.

Repository truth places the continuity/admission authority in `SegmentIdentity` (`cursor`, `segment_id`, `source_digest`) and `RankLocalSegmentScheduler._is_admissible()`, which requires exact episode/source continuity and `cursor == previous.cursor + 1`. If the new sidecar derives a cursor from `consumer_step`, `segment_id`, local scan order, or a private counter, it becomes a second chronology authority and can disagree with the already-canonical scheduler/transaction lifecycle.

**Violated contract:** v0.5 §1 says canonical v0.3.9 + closed transaction core are the unique authority; §3 says the sidecar owns no scheduler authority. A sidecar-private continuity source contradicts that boundary.

**Acceptance:** freeze one exact, implementation-visible identity source and call order before implementation is authorized:
1. sidecar read/commit/reset must consume the exact already-admitted canonical `SegmentIdentity`, or a newly named immutable sidecar identity that is defined as a one-to-one projection of that exact `SegmentIdentity`; no cursor may be inferred from consumer step, segment scan index, `segment_id`, or a private sidecar counter;
2. freeze the exact key fields and cursor/source fields (`slot_id`, `episode_id`, canonical `cursor`, `segment_id`, `source_digest`, plus category/terminal bit if used);
3. freeze call order as scheduler/admission + transaction identity validation -> sidecar read/state_in -> canonical masked scan -> consumer/backward -> `transaction.successful_backward()` -> sidecar detach-copy commit using that same validated identity;
4. terminal/rebind/reset must be driven by the existing canonical scheduler/identity event rather than independently rediscovered by the sidecar;
5. CPU fixtures must prove stale/duplicate canonical cursor rejection, source mismatch rejection, terminal/rebind fresh state, and that no sidecar-private cursor authority exists.

### 2. MEDIUM — exact new-symbol whitelist contradicts the frozen adapter return ABI

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:17,26`

**Root cause:** the exact whitelist authorizes the new adapter file to introduce only `CanonicalLocalMemorySegmentAdapter` and `LocalMemorySegmentSidecar`, but the frozen `scan()` ABI returns a named `SegmentScanResult(...)`. No `SegmentScanResult` symbol exists in formal child `8754c96`, so implementing the written ABI requires an unapproved third class/dataclass/NamedTuple (or an unspecified substitute), defeating the exact-symbol whitelist.

**Violated contract:** v0.5 §2 requires an exact implementation surface and forbids any other symbol/path expansion after approval.

**Acceptance:** before approval, either:
1. explicitly add `SegmentScanResult` to the exact whitelist and freeze its exact immutable type, field names/order/types and ownership semantics; or
2. replace it with an already-authorized, precisely specified built-in return shape that requires no new symbol.
No post-approval symbol expansion or unnamed container is acceptable.

## Non-blocking confirmations

- Formal child contains `ContinualTTTLocalMemoryCore.scan_segment_masked_encoded_many()` with compact-row-first invalid masking; v0.5 does not need to modify `local_evidence.py`.
- `SegmentBatch.gather_consumers()` is already the authoritative stream-major valid gather and opaque payload carrier.
- v0.5 keeps model forward, registry/default/config, real runtime/checkpoint sidecar I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 prohibited.
- The v0.4 transaction closure remains CLOSED; these findings are only about the next adapter-design authority surface.

No implementation is authorized by this verdict. A new docs-only formal root that closes the two blockers requires fresh review; any later implementation SHA is separately gated.