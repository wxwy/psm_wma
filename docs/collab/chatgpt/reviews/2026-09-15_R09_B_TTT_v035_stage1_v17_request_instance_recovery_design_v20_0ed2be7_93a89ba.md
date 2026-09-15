# ChatGPT independent review — Stage-1 v1.7 request-instance recovery design V20

- Formal root: `0ed2be7e27d7219f29f7d3601e6a3a0399ae6bfa`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V20`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v2.0.md:42)`
- Blockers: `1 HIGH`

## Positive closure

- Formal root resolves and its `cosmos-framework` Gitlink equals the declared child.
- Scope is docs-only; no real pre-C/C, v0.5 request pair, materialization, source-evidence, child/runtime/config mutation, GPU or training is executed by this pair.
- V20 correctly preserves the permanently consumed v1.8 authority, C995 ContractV05/C01--C15, one opaque capability, same-object patch handoff, terminal no-retry and hard stop after exact pair readback.

## HIGH — C-time freshness source is not frozen, so the real construction transaction is still ambiguous

V20 seals a typed live closure during non-consuming pre-C, then defines C as `freshness snapshot equality -> one opaque write -> byte-for-byte readback -> hard stop`, while simultaneously forbidding query/discovery/path/schema/import/identity decisions inside C. The currently approved CPU/static API exposes this gap as `consume_once_v05(plan, current_closure)`: it compares an externally supplied `current_closure` with `plan.closure`, but neither V20 nor ContractV05 defines how a real C obtains that current closure without violating the no-query/no-discovery rule.

Two interpretations are both unacceptable for a real one-shot authority:

1. Re-run remote/local/path observations to build `current_closure` in C — violates the explicit C-time query/discovery prohibition.
2. Reuse the pre-C closure object — makes the freshness check tautological and gives no TOCTOU protection between rehearsal and the irreversible consumer call.

This is a Design/Atomicity blocker for granting `APPROVE_TO_CONSTRUCT...`; it is not a new C01--C15 field Gate.

### Acceptance criterion

Refreeze the C-time freshness ABI in V20 before construction authority is granted. The design must classify every freshness input and define one exact mechanism that requires no C-time discovery:

- fixed/immutable ContractV05 facts: no re-observation; compare only their sealed identities;
- mutable local facts that must remain fresh: seal the exact observation handle/capability/predicate during pre-C and define the exact C-time read/compare operation;
- remote-query facts: either explicitly declare them pre-C-only and not re-queried in C, or provide an already-authorized sealed freshness capability whose invocation is explicitly permitted by the controlling lifecycle (V31 currently says no C-time query);
- output absence/readback paths: exact sealed paths and exact permitted freshness/readback operations;
- update the production API/contract so C does not accept an arbitrary externally reconstructed `ClosureV1` with unspecified provenance.

Provide CPU/static direct evidence that the frozen freshness mechanism detects mutable drift before `apply_opaque_v1`, does not perform forbidden discovery/query, and that no alternative reconstruction path is accepted.

Until then, real pre-C/C, future request-pair construction, materialization/source-evidence, real Git/network/source/data/cache I/O, child/runtime/config mutation, GPU and training remain forbidden.
