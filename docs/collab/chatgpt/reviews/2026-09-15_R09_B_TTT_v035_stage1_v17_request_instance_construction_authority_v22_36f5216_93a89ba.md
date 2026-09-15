# ChatGPT Formal Review — Stage-1 v1.7 request-instance construction authority V22

Formal pair:
- root: `36f5216428a28027ac4d33c17ba4456fb93eb359`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AUTHORITY-V22`

Final verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_construction_authority_v2.2.md:11)`

Blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production/implementation: `0`; Evidence/Scope: `0`; child/runtime: `0`.

## Positive closure

- Formal root resolves and its `cosmos-framework` entry is mode `160000`, type `commit`, SHA exactly the declared child; the child commit resolves independently.
- V22 is docs-only and has not executed real pre-C/C, request-pair construction, materialization, source-evidence, child/runtime/config mutation, GPU or training.
- The already-closed ContractV05 / FreshnessGuard CPU-static contract is preserved: C01--C15 closure, nine-entry local freshness domain, remote-pre-C-only rule, same-object patch handoff, exactly-one opaque apply, exact readback, hard stop and terminal no-retry.

## HIGH 1 — V22 delegates the real one-shot write to future capability identities that are not independently frozen before this construction approval

V22 upgrades the project from a pure CPU/static contract to authority for one real future v0.5 pair. It says real pre-C will seal the unique `PatchConsumerV1`, `FreshnessGuardV1` and post-write verifier identity, but it does not freeze their exact provider/module/path/blob/callable identities in this reviewed authority, nor require a second independent exact-plan review after real pre-C and before C.

The inherited production validator is insufficient for that escalation: `PatchConsumerV1` and `FreshnessGuardV1` accept any non-empty provider/module/path, any lower-hex 64-byte blob string, and a callable whose runtime qualname matches the supplied field; the verifier similarly only checks callable + qualname consistency. Those checks prove shape/self-consistency, not that the real host capabilities are an independently reviewed frozen authority.

Therefore, if V22 were approved as written, a future real pre-C could inject a different self-consistent guard/consumer/verifier and immediately proceed to the one-shot write under this prior approval. That leaves the actual code entrusted with the irreversible C outside the exact-pair review boundary.

## Required remediation

Choose one explicit authority model and freeze it before construction:

1. **Single-stage authority**: V22 itself must name the exact real `PatchConsumerV1`, `FreshnessGuardV1` and post-write verifier provider/module/path/blob/callable identities (plus exact ABI/transport), and the real pre-C must fail closed unless they equal those reviewed literals; or
2. **Two-stage authority**: this Gate may authorize only one real non-consuming pre-C rehearsal. After that rehearsal, publish the exact sealed plan/capability/verifier identities and obtain an independent exact-plan approval before the one opaque C call.

In either model, keep the existing nine-entry freshness domain, remote-pre-C-only rule, exact pair bytes/paths, one-call/no-retry semantics, and hard stop. Do not allow a construction approval issued before real pre-C to authorize an arbitrary later self-consistent host capability.

Until this is closed, real pre-C/C, request-pair construction, materialization/source-evidence, real I/O, child mutation, GPU and training remain forbidden.
