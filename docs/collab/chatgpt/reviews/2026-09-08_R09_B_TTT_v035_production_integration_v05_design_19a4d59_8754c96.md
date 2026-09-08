# ChatGPT independent review — Local Memory v0.3.5 production integration implementation design v0.5 identity remediation

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root design SHA: `19a4d59e0e7535e71c483f3a147a747fee7d5f2a`
- child/Gitlink SHA: `8754c96a6bde002269751eca55c01dee694f6caa`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-IMPLEMENTATION-DESIGN`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_INTEGRATION_CPU_STATIC`
- request/bookkeeping SHA observed at review start: `94e2757dc56381ec1c1d068b086d14939568668c`

Fresh incremental review relative to formal pair `6fcbb19715e39ade8c5a5d568b2b200346e935b8 / 8754c96a6bde002269751eca55c01dee694f6caa`. The already-closed v0.4 transaction implementation remains CLOSED and was not re-reviewed.

Repository compare confirms the remediation is docs/review/bookkeeping-only relative to `6fcbb19`: the only technical design delta is `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md`; child code is unchanged.

## Prior blocker status

### Prior HIGH — sidecar chronology authority: OPEN, materially narrowed but not closed

The remediation correctly closes the original authority-source defect: `scan()` now receives an exact scheduler-admitted `SegmentIdentity`; cursor may not be inferred from consumer step/scan index/segment id/private counter; terminal/reset/rebind are tied to the same scheduler/identity events.

However, the frozen lifecycle is still not implementable against formal child `8754c96` without inventing new transaction/sidecar semantics.

#### HIGH — frozen pre-scan transaction validation and sidecar carry order contradict existing canonical APIs

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:26-44`
- `cosmos_framework/model/generator/mot/local_memory_segment.py:203-221`
- `cosmos_framework/trainer/__init__.py:550-603`
- `cosmos_framework/model/generator/mot/local_memory_segment.py:271-320`

**Root cause 1 — impossible validation order / split transaction authority:** v0.5 freezes:

`transaction.validate_success() -> sidecar read -> masked scan -> gather -> consumer spy -> trainer seam -> successful_backward()`.

But repository truth is `LocalMemoryTransaction.validate_success(index, identity, actual_n_valid)`. Both `member_index` and especially `actual_n_valid` are part of the validation contract; `actual_n_valid` is only available after gather/consumer production. The existing unique trainer seam already computes the objective, calls `transaction.validate_success(member_index, identity, actual_n_valid)` immediately before backward, then calls `transaction.successful_backward(...)`. The adapter signature has no `member_index` and cannot perform the written pre-scan call without deriving/guessing transaction position or fabricating `actual_n_valid`, which would create a second transaction authority and contradict §2/§4's trainer-owner rule.

**Root cause 2 — full current `SegmentIdentity` cannot by itself be the sidecar lookup key for the next segment:** v0.5 calls the one-to-one projection containing `cursor` and `segment_id` the sidecar's unique key. A newly admitted next segment necessarily has a different cursor/segment id, so before its commit there is no state stored under that exact current identity. To carry the previous committed state, implementation would need an unspecified predecessor lookup, a private last-cursor map, or an inferred predecessor identity. None is frozen. This reintroduces chronology ambiguity even though the source identity itself is now canonical.

There is also an unresolved terminal branch: `RankLocalSegmentScheduler.commit()` turns `training_stream_end` into terminal state during `successful_backward()`, while the generic v0.5 sequence then says to detach-copy `state_out` after commit. The design must say whether terminal success deletes/does-not-write sidecar state rather than performing the normal carry commit.

**Violated contract:** canonical scheduler + transaction remain the sole admission/chronology/commit authorities; trainer remains the unique primary/aux validation/backward/transaction owner; sidecar is only a detached-state cache and may not invent GA position or cursor chronology.

**Acceptance:** freeze an executable order that matches the existing APIs, with no new authority:
1. scheduler admits the exact canonical `SegmentIdentity`;
2. sidecar read uses that identity only to verify continuity and obtain the last committed detached state; it must not call `transaction.validate_success()` and must not derive `member_index` or `actual_n_valid`;
3. masked scan + canonical gather + consumer spy produce `actual_n_valid`;
4. the existing trainer seam remains the sole caller of `transaction.validate_success(member_index, identity, actual_n_valid)`, objective/backward, and `transaction.successful_backward(...)`;
5. only after trainer success may sidecar commit detached `state_out`; terminal success must explicitly delete/suppress carry state, and terminal rebind starts fresh;
6. freeze one exact storage model that permits cross-segment carry without cursor invention — e.g. a stable stream lookup key with the exact last committed `SegmentIdentity` stored alongside state, or an equivalently precise model. The sidecar may verify `current.cursor == last_committed.cursor + 1` against the canonical identities, but may never generate/increment cursor itself;
7. CPU fixtures must cover first segment/no prior state, second consecutive segment carry, stale/duplicate current identity, source mismatch, terminal success no-write/delete, terminal rebind fresh state, and prove no adapter-side transaction-position authority.

### Prior MEDIUM — `SegmentScanResult` exact whitelist: OPEN, partially remediated

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.5.md:17,26`

The remediation correctly adds `SegmentScanResult` as an explicitly authorized new symbol and freezes field order. That closes the unapproved-symbol defect, but the prior acceptance also required its exact immutable type, field types and ownership/graph semantics. v0.5 still only says “不可变 `SegmentScanResult`” and lists names/order.

**Why this remains blocking:** the implementation can still choose materially different contracts (frozen dataclass vs `NamedTuple`; mutable lists vs tuples; detached vs graph-bearing `state_out`/`locals`; copied vs identity-preserving opaque payload containers). In this Gate, `state_out` must remain graph-bearing until successful backward/commit, gathered Local tensors must preserve the consumer graph, and opaque payload identity must not be copied/reconstructed.

**Acceptance:** freeze the exact `SegmentScanResult` representation and field contracts before implementation: immutable concrete container type; exact field types/shapes; whether tuple/list containers are allowed; `payloads` identity-preservation; `locals` graph ownership; `state_out` graph-bearing lifetime before sidecar detach-copy; and no hidden detach/copy/materialization in the result object.

## Confirmed non-blocking closures/boundaries

- The remediation now uses scheduler-admitted `SegmentIdentity` as the only identity source and explicitly bans sidecar-private cursor generation.
- `SegmentScanResult` is now inside the exact file/symbol whitelist.
- Formal child already provides `ContinualTTTLocalMemoryCore.scan_segment_masked_encoded_many()` and canonical `SegmentBatch.gather_consumers()`; no `local_evidence.py` or `local_memory_segment.py` modification is needed/authorized by this Gate.
- The existing trainer seam remains the canonical loss/backward/transaction implementation and must not be duplicated in the adapter.
- Model forward, registry/default/config, real runtime/checkpoint sidecar I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain prohibited.

No implementation is authorized by this verdict. A new docs-only formal root closing the two blockers requires fresh review; any implementation SHA is separately gated.