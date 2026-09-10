# ChatGPT 独立 Canonical Segment Production Integration Design Review

Formal reviewed pair:
- root design SHA: `ce8e3502af5226d42c270dca4d5387cec8bed412`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_design_v0.1.md`
- frozen authority: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §18, §20.1, §20.2
- prerequisite closed pair: `ae14754de9ca6c5d74b3ec8a72222fe0280e0bcc / 3a078f28f3d107bb633c932271f86498f7c427f7`
- request/bookkeeping SHA observed: `9b4e22780c474afbfa2f4ae37c5bce48acbbdf47`; request/review/session SHAs do not replace the formal pair.

Verdict: `APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_INTEGRATION_SOURCE_ABI`

## Review result

The design is safe to authorize the next **docs-only source-ABI audit** and does not authorize implementation.

### 1. Canonical segment semantics are preserved

The design retains the v0.3.5 production target rather than treating the legacy row-wise active-wiring path as a parameterized equivalent:

- one native microbatch is one logical `[B_stream,T]` segment batch;
- shifted previous evidence and update-then-read chronology remain authoritative;
- S0 remains a valid consumer with Local/evidence absent;
- PAD is logical only, contributes no update/read/loss, and is preferentially gathered out before native Cosmos forward;
- flatten order remains stream-major `flat(b,t)=b*T+t`;
- the full differentiable TTT graph lives inside one native microbatch and is closed by exactly one outer backward;
- state/cursor detach+commit occurs only after successful backward;
- slow gradients may span the native GA window and variable-valid members use the frozen `N_valid_micro/N_valid_window` weighting, degenerating to native `1/GA` when all members are full-valid.

This matches the v0.3.5 §18/§20.1 contract and does not revive closing-row replay/materialized witness semantics.

### 2. Legacy row-wise authority is explicitly superseded

The design correctly separates the old `1 micro-batch = 1 evidence row` lifecycle from the canonical segment path. `GAWindowPlan`, `RankLocalSegmentScheduler`, `LocalMemoryTransaction`, old runtime owner/bridge/active-wiring components may only be inspected as historical provenance or narrowly reusable fail-closed helpers; they are not granted scheduler/state/graph authority for the new production path.

This is sufficient for the next audit Gate because P0 must produce an explicit retain/reuse/supersede table before any implementation design may be created.

### 3. §20.2 A--F are covered and G/H remain separately gated

P0 requires source-level `file:line` findings for:

- A: real dataset/packer/native-batch variable-valid gather/mask/flatten behavior;
- B: native consumer-loss reduction owner and the exact trainer backward seam;
- C: pre-load planned valid-count authority for the whole GA window;
- D: scheduler/producer metadata boundary, chronology/provenance/count ownership;
- E: real feature-disable path for state/dt/age rather than constant-valued fake inputs;
- F: explicit old-owner/bridge/active-wiring retain/bypass/supersession mapping.

It also separately audits Memory Prefix shape and S0-absent representation, which is necessary to connect the canonical segment contract to the real native model seam.

G (single-GPU memory/throughput/higher-order-gradient/fp32 fast-state smoke) and H (runtime sidecar/distributed/world-size/long-train resume) remain outside P0 and are explicitly deferred to independent later Gates.

### 4. The next Gate is read-only and fail-closed

The design does not authorize child changes, adapter/trainer/packer edits, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training, evaluation, or inference. P0 PASS requires a reproducible source map and a concrete disposition for every A--F item. If variable-valid gather, safe native loss weighting, or S0-absent Memory Prefix cannot be established from real source, the audit must fail or split a new design Gate rather than use zero-PAD samples, post-hoc loss patching, constant disabled features, or row-wise replay.

### 5. Formal-pair/scope check

The child/Gitlink remains exactly `3a078f28f3d107bb633c932271f86498f7c427f7`; this design pair contains no child code change. Relative to the already closed scheduler pair, root-side changes consist of the new production-integration design plus review/ledger/session bookkeeping. No implementation scope is smuggled into this design Gate.

## Non-blocking interpretation pinned for P0

Two details remain intentionally unresolved by this design and must be treated as **audit questions**, not assumed implementation facts:

1. `S0 prefix absent` must be resolved against the real Memory Prefix ABI. The stated `[N_valid,1,*]` target shape does not itself prove how per-sample absence is represented; P0 must identify the real optional/presence/mask or equivalent native mechanism and fail closed if none exists.
2. The producer/scheduler boundary must preserve `CanonicalBatchScheduler.freeze_plan(...)` as the member-plan authority. P0 may identify producer-owned immutable chronology/catalog/count metadata, but must not reinterpret the wording as allowing the producer or trainer to fabricate a foreign `MicrobatchPlanMember` outside the frozen scheduler authority.

These are already within the P0 audit scope and do not block authorizing that read-only audit.

## Scope of approval

Current blockers: none.

`APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_INTEGRATION_SOURCE_ABI`

This approval authorizes only creation/execution of the next **docs-only source-ABI audit** for formal pair `ce8e3502af5226d42c270dca4d5387cec8bed412 / 3a078f28f3d107bb633c932271f86498f7c427f7`.

It does **not** authorize any child implementation, producer/packer/model/trainer/config/optimizer/checkpoint modification, real I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training/evaluation/inference, P3/P4 execution, or production binding. Any later design/implementation formal SHA change requires fresh independent review.
