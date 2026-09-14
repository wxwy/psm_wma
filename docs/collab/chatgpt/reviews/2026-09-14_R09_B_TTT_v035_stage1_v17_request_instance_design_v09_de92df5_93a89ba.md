# ChatGPT review — Stage-1 v1.7 request-instance design v0.9

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`
- Formal root: `de92df512e1a239e7c2fd2d8d6ea60c5fc9ca02c`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.9.md:22)`
- Blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production: `0`; Evidence: `0`; child/runtime: `0`.

## Scope / lineage

This is a fresh formal pair relative to the last ChatGPT-reviewed pair `6a2f52d6adc641edb0ac9215c72481a7dfca620a / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal root Gitlink is exactly `93a89ba61306d840a008813f62f26a34d54850f4`, and that child is reachable in `wxwy/cosmos-framework`.

The effective authority chain remains v0.5 -> v0.6 -> v0.7 -> v0.8 remediation -> v0.9 remediation, with later documents superseding only the explicitly rewritten P0/P1/C and object-source rules. v0.7's C-before-first-freshness consumption point, one-attempt/no-retry rule, detached request identity, two-query freshness contract and prohibition boundary remain in force.

The immediate v0.9 delta is docs-only and adds `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.9.md`.

## Closed from prior review

### CLOSED — prior HIGH: contradictory P0 object-source allowlist

v0.9 removes the generic `future formal root/its frozen parent` acquisition rule and replaces it with an explicit closed table of already-existing immutable roots/paths. The replay base, replay helper and adapter sources are bound to already-existing immutable Git objects; the projection helper is also pinned to the previously closed implementation root `079167743685247d6aae62a671436e834411a3cb` and exact path. P0 is required to reject every root/path/blob outside the table.

### CLOSED — prior HIGH: replayed outer incorrectly modeled as another Git source object

v0.9 now requires `outer_payload_bytes` to be derived only via `replay_outer_payload(base_source, binding)`, then checked against exact `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`. It explicitly states that the outer is a derived result rather than a Git path/blob source and that only this derived outer plus the verified adapter bytes enter P1.

## HIGH — canonical `ReplayBinding` authority is still not closed by the P0 allowlist

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.9.md:22`

### Root cause

v0.9 says P0 "acquires and verifies base, helper/binding and adapter", but the closed table freezes only the replay helper module source, not the complete canonical `ReplayBinding` value or an allowed immutable source from which that value may be obtained.

The approved replay implementation at `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f:tools/psm_wma/stage1_v17_launcher_replay.py` defines the `ReplayBinding` dataclass and validates a *supplied* binding. It does not expose a canonical binding constructor/value. In particular, the helper checks digests of `parser_replacements` / `source_replacements`, but the actual canonical replacement rows and complete constructor arguments are not present there as an executable canonical binding object.

The complete canonical tuple currently appears in `tools/psm_wma/test_stage1_v17_launcher_replay.py` at the same implementation root. That test object is not present in v0.9's closed P0 allowlist. Because v0.9 also requires P0 to reject all roots/paths/blobs outside the table, a future constructor cannot lawfully obtain the canonical binding from that test source. The remaining alternatives are an unstated copied constant set, ambient/history inference, or a forbidden additional object read.

This leaves the replay derivation authority under-specified even though the final outer identity is frozen.

### Violated frozen contract

The prior v0.8 review acceptance required the replay path to acquire/verify the exact closed replay helper/**binding authority**, then derive the outer only from that closed authority. v0.9 closes the helper source but does not close the binding source/value itself.

It also conflicts with v0.9's own "closed immutable-object allowlist" claim: the data needed to instantiate the canonical binding is not fully available from the permitted sources as written.

### Why existing Evidence does not close it

The already-closed replay helper tests prove that a supplied canonical binding can replay to the frozen parser/outer identities and reject drift. They do not prove that the future P0/P1 construction path can obtain that exact binding using only v0.9's allowed sources.

This is a design/authority blocker, not a production or runtime implementation blocker.

### Exact acceptance

Freeze one and only one canonical binding authority without ambient/test leakage. Any of the following is acceptable if made exact and fail-closed:

1. embed the complete canonical `ReplayBinding` fields in the next design as frozen literals and require construction to instantiate exactly those values; or
2. freeze a pure canonical-binding implementation object/factory under an exact immutable root/path/blob/raw identity and add it to the P0 allowlist; or
3. if the previously frozen replay test object is intentionally promoted to binding authority, explicitly add its exact root/path/blob/raw identity to the allowlist and state that only its canonical binding tuple may be consumed, with no other test/fixture authority inherited.

Whichever route is chosen, the design must bind all fields needed by `ReplayBinding` (`formal_parent`, base path/blob/raw/bytes, ordered parser replacements, ordered source replacements, owner-FD flag/value, expected parser identity and expected outer identity) and require pre-replay rejection of any drift or alternate source.

## Boundary

No request construction is approved for `de92df512e1a239e7c2fd2d8d6ea60c5fc9ca02c`.

Still prohibited: Stage-1 materialization/execution/retry; launcher/materializer execution; source/checkpoint/manifest/data/cache/runtime I/O outside a future specifically approved construction allowlist; child/runtime mutation; GPU/CUDA/torchrun; training; evaluation; inference; LIBERO4IN1.
