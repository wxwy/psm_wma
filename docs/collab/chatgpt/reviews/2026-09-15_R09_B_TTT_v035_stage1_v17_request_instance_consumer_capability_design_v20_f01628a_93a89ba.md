# ChatGPT review — Stage-1 v1.7 request-instance consumer capability design v2.0

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSUMER-CAPABILITY-DESIGN`
- Formal root: `f01628aad9775cfb327822c038a5b49e1a393ea9`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_consumer_capability_design_v2.0.md:10)`
- Blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

## Formal target / scope

The formal root resolves, is exactly one commit after the approved V19 coordination head, and changes only `SESSION.md`, `TODO.md`, and `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_consumer_capability_design_v2.0.md`. Its formal tree binds `cosmos-framework` as mode `160000` exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`; the child commit resolves in `wxwy/cosmos-framework`. No child/runtime implementation change is part of this target.

The V2.0 design correctly addresses the consumer-resolution failure class in several respects: it moves capability discovery before C; forbids PATH/tool-name/Python-import/manual-copy acquisition; requires a no-I/O capability probe; freezes an immutable descriptor and two-path allowlist; requires same-object opaque handoff, exact-once invocation, exhaustive APPLIED / REJECTED_NO_WRITE / PARTIAL_OR_UNKNOWN result semantics, byte-exact readback, and terminal no-retry behavior.

## HIGH 1 — future construction reuses the already terminal v0.4 output pair

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_consumer_capability_design_v2.0.md:10`

V2.0 states both:

1. V1.8's only C is consumed with zero output and its v0.4 pair may not be completed, repaired, or retried; and
2. a future construction, after later approval, would still use the same two previously frozen v0.4 output paths.

Those statements are incompatible under the inherited one-shot/no-retry authority model. The failure mode was terminal after C began. Introducing a new consumer capability does not retroactively unconsume that C, and a later construction that targets the same v0.4 pair would be an implicit retry/completion of the terminal pair even if wrapped in a new Gate.

The earlier recovery history already established the required pattern: once a construction authority is consumed, a replacement construction must obtain fresh reviewed authority and freeze a new, non-overlapping output pair. V16 did exactly this when moving the rejected/consumed v0.3 pair to v0.4. V19 did not supersede the no-retry rule; it authorized only design of a consumer-capability recovery.

### Acceptance

Revise the design so any future construction authority, if later granted, targets a newly frozen non-overlapping request pair (for example a new versioned pair such as v0.5), with the old v0.4 pair permanently terminal and forbidden as input/output/repair target. Preserve the current C-before no-I/O capability probe, injected `PatchConsumerV1`, opaque same-object handoff, exact-once invocation, result semantics, byte-exact postcondition and no-retry rules. If the project intends to reuse v0.4 anyway, that would require an explicit higher-authority refreeze that directly supersedes the prior terminal no-retry semantics; V2.0 currently does not contain such a supersession.

## Verdict / boundary

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_consumer_capability_design_v2.0.md:10)`

No consumer-capability implementation-design authority is granted for this exact pair.

Still NOT authorized: reuse/repair/retry/completion of the consumed V18 C or its v0.4 pair; consumer implementation or invocation; P0/P1/C; materialization or launcher/runtime execution; real source/checkpoint/manifest/data/cache I/O; collection/receipt/record/publication; child/runtime/config mutation; GPU/CUDA/torchrun; training; evaluation; inference; LIBERO4IN1.
